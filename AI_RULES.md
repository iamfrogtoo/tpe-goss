````markdown
# ⚠️ GOSS v4 專案：嚴格環境與部署守則 (Strict Environment Architecture)

本專案採用「本地開發」、「後端伺服器」與「邊緣接收端」完全分離的三節點架構。AI 在提供終端機指令、撰寫腳本或給出檔案路徑時，**必須嚴格區分以下三個環境，絕不可混淆：**

---

## 1. 遠端伺服器 (Production Server) - 程式唯一執行地與大腦

* **硬體設備**：Intel i5 6th Gen 舊筆電 (24/7 不關機伺服器)
* **作業系統**：Ubuntu Server Linux
* **區網 IP**：`192.168.31.19`
* **SSH 帳號**：`xinzhi`（密碼：`zhi52401314`）
* **專案根目錄（正式環境）**：`/home/xinzhi/goss-v4/`
  * **⚠️ 重要變更**：v4 版本使用 **SQLite3** 資料庫 (`goss_v4.db`)，不再使用 Google Sheets
  * 核心腳本直接放在此目錄下（例如 `/home/xinzhi/goss-v4/bridge_v4.py`）
  * 此目錄下**無 venv**，直接使用系統 `python3`
  * 資料庫檔案：`goss_v4.db`（包含 `live_traffic`, `flight_schedule` 等表）
* **⚠️ 舊版目錄（已棄用）**：`/home/xinzhi/goss-system/` — 這是 v3 舊版程式碼，**請勿再使用**
* **⚠️ 絕對限制**：所有的 Python 後端腳本、資料庫處理、網頁伺服器，**都只能在這裡執行**。所有 `nohup`、`systemctl` 或背景執行指令，預設都是針對此伺服器。

---

## 2. 數據接收端 (ADS-B Receiver Node) - 專職無線電接收的眼睛

* **硬體設備**：Raspberry Pi 4 (搭配 SDR 網卡與天線)
* **主機名稱 / 區網 IP**：`tpe-goss-pi.local` / `192.168.31.221`
* **核心任務**：執行 `ultrafeeder` Docker 容器，負責：
  * `readsb` - 解析高頻無線電訊號
  * `tar1090` - 網頁視覺化
  * `fr24feed` - 餵送 Flightradar24
  * `piaware` - 餵送 FlightAware
* **關鍵端口**：
  * `8080` - HTTP JSON 數據接口 (`http://192.168.31.221:8080/data/aircraft.json`)
  * `30005` - Beast TCP 數據流（供 FR24/FA 外送）
* **數據路徑**：`~/adsb-stack/data/aircraft.json`
* **⚠️ 絕對限制**：**這台機器只負責「收訊」並產生本地 `aircraft.json`**。絕不可將 GOSS 系統的後端 Python 腳本、爬蟲或資料庫部署到樹莓派上。所有繁重的運算與資料融合，都必須交由 i5 伺服器 (192.168.31.19) 跨機讀取樹莓派的資料來處理。

---

## 3. 本地操作端 (Local Dev Machine) - 僅供打字與瀏覽的遙控器

* **設備**：使用者的日常電腦或手機
* **本地專案路徑**：`C:\Users\Xin_Zhi\Desktop\google_ai\tpe-goss\goss-v4\`
* **用途**：撰寫程式碼、透過瀏覽器查看結果、透過 SSH 連線伺服器/樹莓派，或透過 SCP/SFTP 傳輸檔案。
* **⚠️ 絕對限制**：**永遠不要**建議在本地機器上直接執行 Python 後端腳本或架設背景服務。

---

## 4. 雲端前端伺服器 (Vercel) - 面對使用者的展示櫥窗

* **部署平台**：Vercel
* **專案關聯**：連接至 GitHub `iamfrogtoo/tpe-goss` 專案庫上的 `main` 分支。
* **用途**：負責呈現 `tpegoss.com` 的 Next.js 網頁，讀取後台產生的資料庫/JSON 轉化成使用者 UI。
* **⚠️ 絕對限制**：它不負責抓取航空站/飛機原始資料，沒有自己的後台 Cron Job。

---

## 🔄 執行與部署流程規定 (Execution Workflow)

當建立或修改檔案，或是設計資料流向時，標準流程永遠是：

1. **開發**：在「本地操作端」編輯 `.py` 或前端程式碼。

2. **部署 Python 後端**：透過 SCP 將檔案上傳至「i5 伺服器」 `/home/xinzhi/goss-v4/` 下的對應位置。
   ```bash
   # 範例：部署 bridge_v4.py
   scp bridge_v4.py xinzhi@192.168.31.19:/home/xinzhi/goss-v4/bridge_v4.py
   
   # 部署多個檔案
   scp *.py xinzhi@192.168.31.19:/home/xinzhi/goss-v4/
   ```
   **⚠️ 注意**：目標路徑是 `/home/xinzhi/goss-v4/` 根目錄下，不要傳到舊的 `/home/xinzhi/goss-system/`。

3. **執行 Python 後端**：透過 SSH 在「i5 伺服器」上執行重啟指令。
   ```bash
   # 連線伺服器
   ssh xinzhi@192.168.31.19
   
   # 進入工作目錄
   cd /home/xinzhi/goss-v4
   
   # 初始化資料庫（首次部署時）
   python3 init_db.py
   
   # 啟動數據融合引擎（背景執行）
   pkill -f 'python3.*bridge_v4' 2>/dev/null
   nohup python3 -u bridge_v4.py >> bridge.log 2>&1 &
   
   # 啟動戰情室面板（前景執行，用於監控）
   python3 war_room_v4_viewer.py
   ```
   **⚠️ 注意**：使用 `pkill -f` 時要精確指定腳本名稱，避免誤殺其他程序或 SSH session。

4. **部署 Next.js 前端 (Vercel)**：
   若修改了 `app/`、`package.json` 等前端介面相關的程式碼，不需上傳伺服器，只需執行 Git 指令推送到 Github：
   ```bash
   git add .
   git commit -m "更新前端 UI"
   git push origin main
   ```
   Vercel 將會自動偵測 GitHub 上的變更並全自動編譯發布到線上環境 (`tpegoss.com`)。

5. **資料流向**：i5 伺服器 (192.168.31.19) 內的程式主動抓取樹莓派 (192.168.31.221) 的即時數據，融合官方資料後寫入 SQLite 資料庫；而雲端託管前端 (Vercel) 再純粹拉取這些資料展示。

---

## 📂 伺服器目錄結構 (Server Directory Layout)

```
/home/xinzhi/goss-v4/              ← v4 正式環境（所有程式都在這跑）
├── goss_v4.db                     ← SQLite3 資料庫（核心資產）
├── bridge_v4.py                   ← 數據融合引擎（本地優先，雲端補位）
├── fetch_tpe_v4.py                ← 桃機班表抓取器（客機+貨機）
├── war_room_v4_viewer.py          ← 戰情室即時面板
├── init_db.py                     ← 資料庫初始化腳本
├── fetch_opensky_v4.py            ← OpenSky API 備援抓取
├── fetch_adsb_v4.py               ← ADS-B Exchange API（備用）
├── bridge.log                     ← 融合引擎 log
├── war_room.log                   ← 戰情室 log
└── key/                           ← 認證金鑰目錄
    └── piaware_key.txt            ← FlightAware 金鑰

---

## ✅ 部署檢查清單 (Deployment Checklist)

每次更新程式後，**必須確認以下核心組件都已 SCP 傳到伺服器並正在執行**：

| 腳本 | 功能 | 啟動指令 | Log 檔 |
|---|---|---|---|
| `bridge_v4.py` | 數據融合引擎（每秒對接 Pi + OpenSky） | `nohup python3 -u bridge_v4.py >> bridge.log 2>&1 &` | `bridge.log` |
| `fetch_tpe_v4.py` | 班表同步（定期執行） | `python3 fetch_tpe_v4.py` | 終端輸出 |
| `war_room_v4_viewer.py` | 戰情室面板（前景監控） | `python3 war_room_v4_viewer.py` | 終端輸出 |

> **⚠️ 快速檢查指令**：
> ```bash
> # 檢查 bridge 是否在運行
> ps aux | grep bridge_v4 | grep -v grep
> 
> # 檢查資料庫狀態
> sqlite3 goss_v4.db "SELECT COUNT(*) FROM live_traffic;"
> 
> # 檢查最近更新的航班
> sqlite3 goss_v4.db "SELECT flight_no, source, updated_at FROM live_traffic ORDER BY updated_at DESC LIMIT 5;"
> ```

---

## 🗄️ 資料庫結構 (Database Schema)

### live_traffic 表（即時航情）
```sql
CREATE TABLE live_traffic (
    hex TEXT PRIMARY KEY,        -- ICAO 24-bit 地址
    flight_no TEXT,              -- 航班號碼
    alt TEXT,                    -- 高度（支援數字或 "ground"）
    gs REAL,                     -- 地速
    gate TEXT,                   -- 機坪（來自 flight_schedule）
    is_cargo INTEGER,            -- 1=貨機, 0=客機
    source TEXT,                 -- 'LOCAL' 或 'OPENSKY'
    updated_at DATETIME          -- 最後更新時間
);
```

### flight_schedule 表（班表）
```sql
CREATE TABLE flight_schedule (
    flight_no TEXT PRIMARY KEY,  -- 航班號碼
    direction TEXT,              -- A=入境, D=出境
    gate TEXT,                   -- 機坪
    scheduled_time TEXT,         -- 預定時間
    is_cargo INTEGER,            -- 1=貨機, 0=客機
    updated_at DATETIME          -- 最後更新時間
);
```

---

## 🔑 認證方式說明 (Authentication)

* **OpenSky Network API**：
  * 使用 OAuth2 認證，憑證檔：`/home/xinzhi/goss-v4/credentials.json`
  * Client ID: `xinzhi-api-client`
  * Role: `OPENSKY_API_DEFAULT` (4000 Credits)
  * URL: `https://opensky-network.org/api/states/all?lamin=24.0&lomin=120.0&lamax=26.0&lomax=122.5`

* **FlightAware (PiAware)**：
  * 金鑰檔案：`/home/xinzhi/goss-v4/key/piaware_key.txt`
  * 用於樹莓派上的 piaware 容器認證

---

## 🍓 樹莓派 (Pi) 維護指令

```bash
# SSH 連線樹莓派
ssh xinzhi@192.168.31.221

# 檢查容器狀態
docker ps -a

# 檢查 ultrafeeder 日誌
docker logs ultrafeeder --tail 50

# 重啟 ultrafeeder
cd ~/adsb-stack
docker compose restart

# 檢查數據流
curl -s http://localhost:8080/data/aircraft.json | head -20

# 檢查 Beast 端口
ss -tlnp | grep 30005

# 檢查硬體
lsusb | grep RTL
```

---

## 🚑 常見問題排解 (Troubleshooting)

### 問題：bridge_v4.py 無法連線到樹莓派
**檢查步驟**：
1. 確認樹莓派 IP 是否可達：`ping 192.168.31.221`
2. 確認 ultrafeeder 容器運行中：`docker ps | grep ultrafeeder`
3. 確認 aircraft.json 可存取：`curl http://192.168.31.221:8080/data/aircraft.json`

### 問題：資料庫顯示為空或無更新
**檢查步驟**：
1. 確認 bridge_v4.py 正在運行：`ps aux | grep bridge_v4`
2. 檢查資料庫權限：`ls -la goss_v4.db`
3. 手動測試抓取：`python3 -c "import requests; print(requests.get('http://192.168.31.221:8080/data/aircraft.json', timeout=2).json())"`

### 問題：戰情室面板顯示異常（高度/速度格式錯誤）
**解法**：`war_room_v4_viewer.py` 已內建容錯處理，可處理 `ground` 字串和 `None` 值。

---

## 📋 版本歷史

| 版本 | 日期 | 主要變更 |
|---|---|---|
| v3 | 2026-03-01 | Google Sheets 架構，四支獨立 tracker |
| **v4** | **2026-03-25** | **SQLite3 架構，數據融合引擎，貨機標籤支援** |

---

## 📝 AI 操作提示

當用戶詢問 GOSS 系統相關問題時：
1. **永遠確認版本**：詢問是 v3 (Google Sheets) 還是 v4 (SQLite3)
2. **永遠確認環境**：本地開發端、i5 伺服器、還是樹莓派
3. **永遠使用正確路徑**：v4 使用 `/home/xinzhi/goss-v4/`，不是舊的 `/home/xinzhi/goss-system/`
````

