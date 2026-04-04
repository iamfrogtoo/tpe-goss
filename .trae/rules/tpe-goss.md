# 專案背景

- 專案名稱：TPE GOSS (Taoyuan Airport Ground Operations Surveillance System)
- 版本：goss-v4 (SQLite3 架構)
- 核心功能：ADS-B 航機追蹤、數據融合、貨機標註、機坪自動對標

# 技術架構

- 三節點架構：本地開發端、i5 伺服器、樹莓派接收端
- 後端：Python + SQLite3 (goss\_v4.db)
- 前端：Next.js (Vercel 部署)
- 數據源：樹莓派 ADS-B + OpenSky API 備援

# 部署信息

- 伺服器 IP：192.168.31.19
- 樹莓派 IP：192.168.31.221
- 部署路徑：/home/xinzhi/goss-v4/
- SSH 設定：已配置免密登入

# 核心腳本

- bridge\_v4.py：數據融合引擎
- fetch\_tpe\_v4.py：桃機班表抓取
- war\_room\_v4\_viewer.py：戰情室面板
- init\_db.py：資料庫初始化

