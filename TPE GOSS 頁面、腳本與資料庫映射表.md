# TPE GOSS 頁面、腳本與資料庫映射表

本文件記錄了 TPE GOSS (Taoyuan Airport Ground Operations Surveillance System) v4 版本的前端頁面、後端腳本與資料庫表之間的對應關係。

## 前端頁面 (Next.js)

| 功能名稱 | 頁面路徑 | 主要功能 | 對應後端腳本 | 對應資料庫表 |
| :--- | :--- | :--- | :--- | :--- |
| **首頁** | `app/page.tsx` | 顯示即時航班資訊 | `bridge_v4.py` | `live_traffic` |
| **地圖** | `app/map/page.tsx` | 地圖展示航班位置 | `bridge_v4.py` | `live_traffic` |
| **出港** | `app/outbound/page.tsx` | 顯示離場航班 | `fetch_tpe_v4.py` | `flight_schedule` |
| **航班計畫** | `app/schedule/page.tsx` | 查詢航班計畫 | `fetch_tpe_v4.py` | `flight_schedule` |
| **登機門** | `app/gate/[gate]/page.tsx` | 查詢特定登機門航班 | `fetch_tpe_v4.py` | `flight_schedule` |
| **關於** | `app/about/page.tsx` | 系統資訊 | - | - |
| **回饋** | `app/feedback/page.tsx` | 使用者回饋 | `app/api/feedback/route.ts` | - |

## 後端腳本 (Python)

| 腳本名稱 | 主要功能 | 對應資料庫表 | 執行方式 |
| :--- | :--- | :--- | :--- |
| **bridge_v4.py** | 數據融合引擎，整合本地天線和 OpenSky 數據 | `live_traffic`, `source_antenna`, `source_opensky` | `nohup python3 -u bridge_v4.py >> bridge.log 2>&1 &` |
| **api_server.py** | HTTP API 伺服器，提供即時數據接口 | `live_traffic`, `flight_schedule` | `nohup python3 api_server.py >> api.log 2>&1 &` |
| **push_to_github.py** | 數據導出並推送至 GitHub | `live_traffic` | `cron: * * * * * python3 push_to_github.py` |
| **fetch_tpe_v4.py** | 桃機班表抓取器，抓取客機和貨機班表 | `flight_schedule`, `source_airport` | `python3 fetch_tpe_v4.py` |
| **fetch_opensky_v4.py** | OpenSky API 備援抓取 | `source_opensky` | `python3 fetch_opensky_v4.py` |
| **fetch_fr24_v4.py** | FlightRadar24 數據抓取 | `source_fr24` | `python3 fetch_fr24_v4.py` |
| **fetch_adsb_v4.py** | ADS-B Exchange API 抓取 | - | `python3 fetch_adsb_v4.py` |
| **fetch_calair_v4.py** | 華航郵件數據抓取 | `source_calair` | `python3 fetch_calair_v4.py` |
| **war_room_v4_viewer.py** | 戰情室即時面板 | `live_traffic` | `python3 war_room_v4_viewer.py` |
| **init_db.py** | 資料庫初始化 | 所有表 | `python3 init_db.py` |
| **test_partition.py** | 分區架構測試 | 所有表 | `python3 test_partition.py` |

## 資料庫表 (SQLite3)

| 表名 | 類型 | 主要功能 | 數據來源 |
| :--- | :--- | :--- | :--- |
| **live_traffic** | 核心表 | 實時航班交通數據 | `bridge_v4.py` (融合本地天線和 OpenSky 數據) |
| **flight_schedule** | 核心表 | 航班計畫表 | `fetch_tpe_v4.py` (桃機班表) |
| **source_airport** | 分區表 | 機場原始數據 | `fetch_tpe_v4.py` (桃機班表) |
| **source_opensky** | 分區表 | OpenSky 原始數據 | `fetch_opensky_v4.py` 和 `bridge_v4.py` |
| **source_antenna** | 分區表 | 本地天線原始數據 | `bridge_v4.py` (樹莓派 ADS-B) |
| **source_fr24** | 分區表 | FlightRadar24 原始數據 | `fetch_fr24_v4.py` |
| **source_flightaware** | 分區表 | FlightAware 原始數據 | 待開發 |
| **source_calair** | 分區表 | 華航郵件原始數據 | `fetch_calair_v4.py` |
| **flight_trajectory** | 軌跡表 | 飛行軌跡記錄 | `runway_tracker.py` |
| **runway_info** | 跑道表 | 跑道基本資訊 | `init_db.py` |
| **runway_tracks** | 追蹤表 | 跑道使用追蹤 | `runway_tracker.py` |

## 數據流向

1. **數據抓取**：
   - `fetch_tpe_v4.py` 從桃園機場官方 TXT 抓取班表數據，存入 `source_airport` 和 `flight_schedule` 表
   - `bridge_v4.py` 從樹莓派 ADS-B 抓取本地天線數據，存入 `source_antenna` 表
   - `bridge_v4.py` 和 `fetch_opensky_v4.py` 從 OpenSky API 抓取數據，存入 `source_opensky` 表
   - `fetch_fr24_v4.py` 從 FlightRadar24 抓取數據，存入 `source_fr24` 表

2. **數據融合**：
   - `bridge_v4.py` 將 `source_antenna` 和 `source_opensky` 的數據融合，存入 `live_traffic` 表
   - 融合策略：本地天線數據優先，OpenSky 數據作為備份

3. **數據導出與發布**：
   - `api_server.py` 提供 HTTP API 接口，將 `live_traffic` 數據轉換為 JSON 格式
   - `push_to_github.py` 定期將數據導出並推送至 GitHub 倉庫
   - GitHub + jsdelivr CDN 提供穩定的數據訪問服務

4. **數據使用**：
   - 前端頁面透過 jsdelivr CDN 獲取 `live_data.json` 數據
   - 本地開發時可透過 `api_server.py` 直接獲取即時數據
   - `war_room_v4_viewer.py` 顯示 `live_traffic` 表的即時數據

## 部署與執行

1. **初始化**：
   ```bash
   # 初始化資料庫
   python3 init_db.py
   
   # 同步航班計畫
   python3 fetch_tpe_v4.py
   ```

2. **啟動服務**：
   ```bash
   # 啟動數據融合引擎
   nohup python3 -u bridge_v4.py >> bridge.log 2>&1 &
   
   # 定期同步其他數據源
   python3 fetch_opensky_v4.py
   python3 fetch_fr24_v4.py
   python3 fetch_calair_v4.py
   ```

3. **前端部署**：
   - 推送程式碼到 GitHub `iamfrogtoo/tpe-goss` 專案的 `main` 分支
   - Vercel 自動偵測變更並部署到 `tpegoss.com`

## 技術架構

- **前端**：Next.js (Vercel 部署)
- **後端**：Python + SQLite3 (i5 伺服器執行)
- **數據源**：樹莓派 ADS-B + OpenSky API + FlightRadar24 API + 桃機班表
- **架構**：三節點架構 (本地開發端 + i5 伺服器 + 樹莓派接收端)

## 版本資訊

| 版本 | 日期 | 主要變更 |
| :--- | :--- | :--- |
| v4 | 2026-03-25 | SQLite3 架構，數據融合引擎，貨機標籤支援 |

## 附註

- 本映射表基於 TPE GOSS v4 版本，如有更新請同步修改
- 後續計畫整合 FlightAware 和華航郵件數據，屆時將更新對應表和腳本