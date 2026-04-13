📡 TPE GOSS 4.0 航情戰情室 - 階段性成果報告

📊 系統架構圖 (System Architecture)

1\. 數據源層 (Data Sources / 道具箱)

本地天線 (Local SDR):

硬體：藍色 RTL2832U Stick。

狀態：已通 ✅。實現 0 延遲監控，甚至能抓到地面的 UPS61 訊號。

雲端補位 (OpenSky API):

狀態：已通 ✅。當本地天線受限於地形時，自動抓取全台航情。

外送管線 (FR24 / FlightAware):

狀態：已通 ✅。透過樹莓派 30005 端口穩定上傳，維持 Business/Enterprise 高級會員權限。

2\. 核心大腦層 (Dell i5 Collector)

數據融合引擎 (bridge\_v4.py):

功能：每秒對接樹莓派與雲端，自動過濾重複飛機。

邏輯：本地優先，雲端備援。

貨機情報庫 (goss\_v4.db):資產：包含 18 欄位 的貨機專屬班表。

自動對齊：系統會自動根據 Flight No 標註 ⚠️貨機 標籤並帶出預定機坪 (如 504, 601 等)。

3\. 視覺化層 (War Room Viewer)

即時戰情面板 (war\_room\_v4\_viewer.py):狀態：已通 ✅。

功能：即時顯示班號、高度、速度、機坪及數據來源。

強健性：已修復 Ground 狀態導致的格式化報錯。



🛠️目前掌握的技術要點
組件                        技術細節                                                                備註

樹莓派,                Docker Compose / readsb,                              解決了 30005 端口佔用衝突

通訊協議             Beast TCP (30005) / JSON,                                跨機器的數據交換標準

數據處理             Python / SQLite3 / SQL ON CONFLICT           確保數據不重複且更新迅速

業務邏輯             貨機標籤與機坪自動對標,                                    核心競爭力：比 FR24 更懂貨機



🍓 樹莓派端：GOSS 4.0 數據發射站 (Feeder Station)

1\. 環境配置

硬體: Raspberry Pi (建議 3B+ 以上) + 藍色 RTL2832U SDR Stick。



作業系統: Raspberry Pi OS (64-bit)。



容器化方案: Docker + Docker Compose (核心組件)。



2\. 安裝核心：Ultrafeeder 部署

使用 docker-compose.yml 進行標準化部署，確保「雷達引擎」與「外送插件」在同一個沙盒運行。



## 關鍵配置實錄：

services:

&#x20; ultrafeeder:

&#x20;   image: ghcr.io/sdr-enthusiasts/docker-adsb-ultrafeeder:latest

&#x20;   privileged: true  # 必須開啟，否則無法存取 USB 棒子

&#x20;   environment:

&#x20;     - READSB\_DEVICE\_TYPE=rtlsdr

&#x20;     - READSB\_WRITE\_JSON=/run/readsb  # 數據生產路徑

&#x20;     - ENABLE\_FR24=true

&#x20;     - ENABLE\_PIAWARE=true

&#x20;   volumes:

&#x20;     - /home/xinzhi/adsb-stack/data:/run/readsb # 實體路徑映射

&#x20;   ports:

&#x20;     - "8080:80"     # 網頁 API 端口

## &#x20;     - "30005:30005" # Beast 數據碼頭 (外送關鍵)

3. 戰鬥除錯過程 (Troubleshooting Log)

在安裝過程中，我們克服了三個重大障礙：



A. 端口衝突 (Port Binding Conflict) ❌

現象: 日誌顯示 Error opening the listening port 30005: bind: Address already in use。



原因: 系統內建的 readsb 或舊的 dump1090 服務在背景搶佔了 30005 端口。



解法:



執行 sudo killall -9 readsb dump1090 強制清場。



停用系統原生服務，改由 Docker 全權接管。



B. 數據管線斷裂 (JSON Missing) ❌

現象: ls 找不到 aircraft.json，Nginx 噴出 404 錯誤。



原因: readsb 引擎因為端口衝突未啟動，或是 Volume 掛載路徑不一致。



解法: 重新校準 volumes 映射，確保容器內的 /run/readsb 正確指向樹莓派的 \~/adsb-stack/data。



C. 身分識別與註冊 (Registration) ✅

FR24: 透過 docker run --rm 臨時容器完成 signup，取得 fr24key。



FlightAware: 透過 docker logs 擷取 Feeder ID (UUID)，並配合 IP 進行官網 Claim 認領。



4\. 驗證指令集 (常用工具箱)

在維護 GOSS 4.0 時，這幾行指令是你的「聽診器」：



檢查硬體: lsusb (確認看到 Realtek RTL2832U)。



檢查數據流: ss -tlnp | grep 30005 (確認碼頭已開門)。



檢查收訊統計:

curl -s http://localhost:8080/data/stats.json | jq '.total.messages'

檢查即時航情 (JSON raw):

cat \~/adsb-stack/data/aircraft.json

🏆 最終成果

樹莓派現在是一個穩定的 「數據噴泉」。它不僅能每秒鐘為 Dell i5 提供即時的 UPS/貨機地面訊號，還同時維持著兩個高級商業帳號的權限。



目前 21:10，貨機潮應該開始入港了！ 你的面板現在有刷出新的 ⚠️貨機 班號了嗎？

📑 GOSS 4.0 系統交接清單 (Handover Document)

🏗️ 1. 節點架構與容器 (Nodes \& Containers)

Node A: Raspberry Pi (數據水源站)

IP: 192.168.31.221



容器名稱: ultrafeeder



鏡像: ghcr.io/sdr-enthusiasts/docker-adsb-ultrafeeder:latest



關鍵端口:



8080 (HTTP): Nginx 轉發的 JSON 數據接口。



30005 (Beast): ADS-B 原始數據流碼頭（外送 FR24/FA 的關鍵）。



實體路徑: \~/adsb-stack/data -> 映射容器內 /run/readsb。



硬體: RTL2832U Blue Stick (Bus 001 Device 003)。



Node B: Dell i5 Server (大腦處理站)

工作目錄: \~/goss-v4



核心組件:



goss\_v4.db (SQLite3): 存儲即時航情、貨機班表、機坪數據。



bridge\_v4.py: 數據融合引擎（對接 Pi 與 OpenSky）。



war\_room\_v4\_viewer.py: 終極戰情室面板。

⚙️ 2. 核心代碼架構指令 (Core Scripts)

數據對接邏輯 (Bridge Logic)
-------------------------------------------------------
Python
# 核心邏輯：本地優先，雲端補位

LOCAL\_URL = "http://192.168.31.221:8080/data/aircraft.json"

OPENSKY\_URL = "https://opensky-network.org/api/states/all?lamin=24.0\&lomin=120.0\&lamax=26.0\&lomax=122.0"



\# SQL 對齊 18 欄位貨機表

"SELECT gate, is\_cargo FROM flight\_schedule WHERE flight\_no = ?"
---------------------------------------------------------------------
資料庫表結構 (Schema)
-------------------------------------
SQL
CREATE TABLE live\_traffic (

&#x20;   hex TEXT PRIMARY KEY,

&#x20;   flight\_no TEXT,

&#x20;   alt TEXT,        -- 支援數字或 "ground"

&#x20;   gs REAL,

&#x20;   gate TEXT,       -- 來自 flight\_schedule

&#x20;   is\_cargo INTEGER, -- 1=貨機, 0=客機

&#x20;   source TEXT,     -- 'LOCAL' 或 'OPENSKY'

&#x20;   updated\_at DATETIME

);
----------------------------------------------
🛠️ 3. 樹莓派部署關鍵指令 (Deployment)

啟動命令
---------------------------------------------------
Bash
cd \~/adsb-stack

docker compose up -d --force-recreate
------------------------------------------------
環境變數精華 (Environment Variables)

READSB\_DEVICE\_TYPE=rtlsdr



READSB\_WRITE\_JSON=/run/readsb



ENABLE\_FR24=true (使用 FR24KEY 驗證)



ENABLE\_PIAWARE=true (使用 FEEDER\_ID 驗證)

🚑 4. 已知的坑與解決方案 (Troubleshooting Log)

30005 端口佔用:



現象: readsb 無限重啟，報 Address already in use。



解法: sudo killall -9 readsb dump1090，確保 Docker 拿到端口控制權。



JSON 404/Empty:



現象: ls 找不到 aircraft.json。



原因: readsb 啟動失敗或硬體沒讀到。



檢查: lsusb 確認棒子在線，docker logs ultrafeeder 看錯誤日誌。



高度格式化報錯:



現象: NoneType.\_\_format\_\_ 或 ground 字串崩潰。



解法: 在 Viewer 邏輯中加入 float() 轉換與 is None 判斷。



🏁 5. 交接給新 AI 的提示詞 (Prompt)

「我正在運行 GOSS 4.0 ADS-B 監控系統。數據源為樹莓派 (192.168.31.221) 的 ultrafeeder，處理站為 Dell i5 上的 Python + SQLite3 系統。目前已實現本地/雲端數據融合、貨機班表對齊及機坪標註。請基於此架構，協助我進行下一步功能擴充。」



