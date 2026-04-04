
# TPE-GOSS 系統架構升級方案 v3.0

**文件作者：** Gemini AI
**日期：** 2026-03-16

## 1. 核心目標

為了解決當前系統因多程序同時讀寫 Google Sheets 造成的 API 瓶頸、資料衝突與即時性不足等問題，我們將對後端架構進行一次重大升級。本次升級的核心是引入 **本地 SQLite 資料庫** 作為即時資料的「單一真相來源 (Single Source of Truth)」，將高頻的即時讀寫操作與低頻的雲端備份操作徹底分離。

---

## 2. 新版系統架構圖 (Data Flow v3.0)

```mermaid
graph TD
    subgraph "外部資料源 (External Sources)"
        A[桃園機場 TXT]
        B[OpenSky API]
        C[本地 SDR 天線]
    end

    subgraph "後端伺服器 (192.168.31.19)"
        subgraph "資料抓取層 (Trackers)"
            T1[tracker_inbound.py]
            T2[tracker_outbound.py]
            T3[tracker_schedule.py]
        end
        
        DB[(本地 SQLite DB\ngoss.db)]
        
        subgraph "資料產出層 (Generators)"
            J1[inbound.json]
            J2[outbound.json]
            J3[schedule.json]
        end

        S[sync_to_sheets.py]
    end

    subgraph "雲端 (Cloud)"
        GS[Google Sheets]
        V[Vercel 前端]
    end

    A --> T3
    B --> T1
    C --> T1
    
    T1 -->|寫入| DB
    T2 -->|寫入| DB
    T3 -->|寫入| DB
    
    DB -->|讀取| T1
    DB -->|讀取| T2
    DB -->|讀取| T3

    T1 -->|產生| J1
    T2 -->|產生| J2
    T3 -->|產生| J3

    J1 --> V
    J2 --> V
    J3 --> V

    DB -->|讀取 (每5分鐘)| S
    S -->|同步備份| GS
```

**資料流說明：**
1.  **抓取與寫入**：所有 `tracker_*.py` 腳本從外部抓取資料後，**唯一**的寫入目標是伺服器上的 `goss.db` (SQLite)。
2.  **即時產出**：`tracker_*.py` 在每次更新資料庫後，會**立即**從 `goss.db` 讀取最新資料，並產生對應的 `.json` 靜態檔案。
3.  **前端讀取**：Vercel 上的前端網站只讀取這些 `.json` 檔案，確保毫秒級的頁面載入速度。
4.  **非同步備份**：獨立的 `sync_to_sheets.py` 會定期 (例如每 5 分鐘) 從 `goss.db` 讀取資料，並將其同步到 Google Sheets，此路徑的延遲不影響主站即時性。

---

## 3. SQLite 資料庫 Schema 設計

- **檔案位置**: `/home/xinzhi/goss-system/goss.db`
- **主資料表**: `flights`

```sql
CREATE TABLE IF NOT EXISTS flights (
    flight_key TEXT PRIMARY KEY, -- 主鍵，由 airline_code + flight_no 組成，例如 'CI751'
    direction TEXT,              -- 'A' (Arrival) 或 'D' (Departure)
    airline_code TEXT,           -- IATA 航空公司代碼，例如 'CI'
    flight_no TEXT,              -- 航班號，例如 '751'
    scheduled_time TEXT,         -- 表定時間 (HH:MM:SS)
    estimated_time TEXT,         -- 預計時間 (HH:MM:SS)
    actual_time TEXT,            -- 實際時間 (HH:MM:SS)
    gate TEXT,                   -- 機坪/登機門
    terminal TEXT,               -- 航廈
    carousel TEXT,               -- 行李轉盤
    ac_type TEXT,                -- 機型
    ac_reg_official TEXT,        -- 官方公告的機身註冊號
    ac_reg_radar TEXT,           -- 雷達訊號抓到的機身註冊號
    altitude INTEGER,            -- 高度 (英尺)
    status_text TEXT,            -- 狀態文字，例如 'On Time', 'Landed', 'Departed'
    route TEXT,                  -- 航線，例如 'TPE-NRT'
    last_updated_source TEXT,    -- 最後更新此筆資料的來源，例如 'taoyuan_txt', 'opensky'
    last_updated_utc TEXT        -- 最後更新時間 (UTC)
);
```

---

## 4. 程式修改重點 (Refactoring Plan)

### 4.1. `central_db.py` -> `central_db_sqlite.py` (核心重構)

- **目標**：建立一個與 SQLite 互動的類別 (Class)，取代現有直接操作 `gspread` 的函式。
- **重點**：
    1.  **初始化**：建立 `CentralDB_SQLite` 類別，在 `__init__` 中連接資料庫並檢查/建立 `flights` 表。
    2.  **UPSERT 操作**：建立一個 `upsert_flight(flight_data)` 方法。此方法會根據 `flight_key` 判斷資料是否存在：
        - 若存在，則 `UPDATE` 該筆資料。
        - 若不存在，則 `INSERT` 新資料。
        - **程式碼範例**：
          ```python
          def upsert_flight(self, flight_data):
              # flight_data is a dictionary matching table columns
              cursor = self.conn.cursor()
              cursor.execute("SELECT 1 FROM flights WHERE flight_key = ?", (flight_data['flight_key'],))
              if cursor.fetchone():
                  # UPDATE logic here
              else:
                  # INSERT logic here
              self.conn.commit()
          ```
    3.  **查詢操作**：建立 `get_flights(criteria)` 方法，用來取代舊的 `get_flights_by_criteria`。

### 4.2. `tracker_inbound.py` (修改)

- **目標**：將資料來源從 Google Sheets 改為 SQLite，並將抓取結果寫入 SQLite。
- **重點**：
    1.  **移除 `gspread`**：刪除所有與 `gspread` 相關的 import 和函式呼叫。
    2.  **引入 `CentralDB_SQLite`**：`from central_db_sqlite import CentralDB_SQLite`。
    3.  **修改 `get_inbound_watchlist`**：此函式不再讀取 CSV，而是呼叫 `db.get_flights({'direction': 'A'})` 來從 SQLite 獲取入境航班清單。
    4.  **修改主迴圈**：
        - 在抓到 OpenSky/SDR 資料後，將其整理成符合 `flights` 表結構的字典。
        - 呼叫 `db.upsert_flight(flight_data)` 將資料寫入 SQLite。
        - 從 SQLite 讀取完整的 `final_list`。
        - **移除 `connect_google_sheet()` 和 `sheet.append_rows()`**。
        - 維持產生 `inbound.json` 的邏輯不變。

### 4.3. `tracker_outbound.py` & `tracker_schedule.py` (修改)

- **修改邏輯與 `tracker_inbound.py` 完全相同**：移除 `gspread`，引入 `CentralDB_SQLite`，將資料讀寫的目標全部指向本地資料庫，並維持產生 `.json` 的邏輯。

### 4.4. `sync_to_sheets.py` (新增)

- **目標**：建立一個全新的獨立腳本，負責將 SQLite 的資料同步到 Google Sheets。
- **重點**：
    1.  **排程執行**：此腳本將被設定為每 5 分鐘執行一次。
    2.  **讀取 SQLite**：呼叫 `db.get_flights()` 獲取所有航班資料。
    3.  **連接 Google Sheets**：保留 `gspread` 的連接邏輯。
    4.  **整批更新**：使用 `sheet.clear()` 和 `sheet.update()` 將從 SQLite 讀出的所有資料一次性覆蓋到 Google Sheets 的 `Central_Database` 分頁。

---

## 5. 部署與執行流程變更

- **初始化**：第一次部署時，需在伺服器上手動執行一次 `central_db_sqlite.py` 來建立 `goss.db` 檔案。
- **啟動指令**：`deploy_script.py` 需要被更新，除了啟動 4 個 tracker 外，還需要啟動 `sync_to_sheets.py` 的排程。
- **建議啟動方式**：
    - **高頻 Tracker**：維持使用 `nohup` 背景執行。
    - **低頻同步腳本**：建議使用 `cron` 來設定排程，確保穩定執行。
      ```bash
      # crontab -e
      # Add this line to run every 5 minutes
      */5 * * * * cd /home/xinzhi/goss-system && python3 sync_to_sheets.py >> sync.log 2>&1
      ```

---

## 6. 執行結果與完成摘要 (v3.0)

- **完成日期**: 2026-03-16
- **執行狀態**: **已完成**

**摘要**:
所有在「4. 程式修改重點」中規劃的項目皆已完成。
1.  `central_db_sqlite.py` 已建立，包含完整的 `UPSERT` 與查詢邏輯。
2.  `tracker_inbound.py`, `tracker_outbound.py`, `tracker_schedule.py` 已全面重構，資料來源與寫入目標均改為本地 SQLite 資料庫。
3.  `sync_to_sheets.py` 已建立，負責將 SQLite 資料定期備份至 Google Sheets。
4.  `deploy_script.py` 已更新，納入新檔案的上傳與新服務的啟動。

系統現在以 SQLite 為核心運作，前端頁面透過讀取伺服器本地產生的 `.json` 檔案來獲取資料，Google Sheets 則做為非同步的備份目的地。

---

## 7. 交接維護說明 (Handover Summary)

### 7.1. 核心組件 (Backend Components)
- **`goss.db`**: SQLite 3 資料庫，儲存所有航班即時狀態。位於伺服器 `goss-system` 目錄。
- **`central_db_sqlite.py`**: 資料庫操作介面 (DAO)，負責所有 UPSERT 邏輯。
- **`sync_to_sheets.py`**: 背景同步服務，每 5 分鐘執行一次，負責將 SQLite 映射回 Google Sheets。

### 7.2. 資料流與更新頻率
1.  **Tracker 層**: `inbound` (30s), `outbound` (300s), `schedule` (600s), `bay` (600s)。
    - 更新順序：抓取外部資料 -> 寫入 SQLite -> 產生本地 `.json`。
2.  **前端層**: 讀取伺服器本地 `/dashboard/data/*.json`，反應速度為毫秒級。
3.  **同步層**: `sync_to_sheets.py` 每 5 分鐘執行，更新 Google Sheets 上的 4 個主要標籤頁。

### 7.3. Google Sheets 欄位對齊 (Central_Database)
為了保持與舊系統相容，`sync_to_sheets.py` 採用了嚴格的映射邏輯：
- **A-E**: Terminal, Direction, Airline Code, Airline Name, Flight No.
- **F-G**: Boarding Gate (merged), Parking Gate.
- **H-K**: Scheduled/Estimated Date & Time.
- **O-P**: Status, Aircraft Type.
- **T-V**: Carousel/Counter, Aircraft Reg.
- **Y-AC**: Modification Time, Source, Radar Reg, Altitude, Landing Status.

### 7.4. 維護指令
- **重啟所有服務**: 執行本地 `deploy_v3.bat`。
- **檢查日誌**: 
  - `tail -f inbound.log` (即時入境)
  - `tail -f sync.log` (Google Sheets 同步狀態)
- **手動清空程序 (緊急情況)**: `sudo pkill -f tracker_` 或 `sudo pkill -f sync_to_sheets`。
