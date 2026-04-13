# TPE GOSS 系統完整診斷清單

> **診斷日期**：2026-04-12
> **診斷範圍**：前端頁面、後端腳本、資料庫、部署流程、資料流向
> **結論**：系統存在 **6 層嚴重問題**，建議建立 GOSS 4.1 乾淨架構

---

## 🔴 問題總覽：你到底在跟什麼打仗？

```
                    你以為的架構
    ┌──────────────────────────────────────────┐
    │  前端頁面 → API 路由 → SQLite 資料庫      │
    └──────────────────────────────────────────┘

                    實際的架構（混亂版）
    ┌──────────────────────────────────────────────────────┐
    │  首頁 → /api/live-data → CDN(jsdelivr) → GitHub      │
    │         → public/live_data.json (空的，4/8停更)       │
    │                                                      │
    │  其他頁面 → Google Sheets CSV (4/6 舊資料!!!)         │
    │           → 從來沒有被改成讀 API                      │
    │                                                      │
    │  伺服器 → bridge_v4.py + api_server → live_data.json  │
    │         → push_to_github.py (停用/會 reset --hard)   │
    │         → 編碼亂碼 (cp950 vs utf-8)                   │
    └──────────────────────────────────────────────────────┘
```

---

## 📋 完整檢查清單

### 第一層：首頁即時入境資料 (`app/page.tsx`)

| # | 檢查項目 | 當前狀態 | 問題描述 |
|---|---------|---------|---------|
| 1.1 | 首頁資料來源 | ⚠️ 有問題 | 使用 `/api/live-data` 代理到 CDN `jsdelivr.net` |
| 1.2 | CDN 資料來源 | 🔴 已壞 | CDN 讀取 GitHub `public/live_data.json`，內容是 **空陣列** (`flights: []`)，timestamp 停在 `2026-04-08` |
| 1.3 | `goss-v4/live_data.json` | 🔴 過期+亂碼 | 有8筆資料但 timestamp 停在 `2026-04-09`，且 `actype` 欄位全是亂碼 (`準時ON TIME` → `�Ǯ�ON TIME`) |
| 1.4 | `push_to_github.py` 定時任務 | 🔴 已停用 | crontab 已移除，導致 `public/live_data.json` 不再更新 |
| 1.5 | `bridge_v4.py` 數據融合引擎 | ❓ 未確認 | 不確定伺服器上是否仍在運行 |
| 1.6 | `api_server_fixed.py` | ❓ 未確認 | 04-11 日誌記載 PID 1308188 已停止 |
| 1.7 | `live_traffic` 表是否有即時資料 | ❓ 未確認 | 需要 SSH 到伺服器查詢 |

**檢查步驟：**
```bash
# 1. 檢查 CDN 資料(你的瀏覽器可以直接開)
curl "https://cdn.jsdelivr.net/gh/iamfrogtoo/tpe-goss@main/public/live_data.json"
# 預期：看到 flights:[] 或過期資料

# 2. SSH 到 i5 伺服器 (192.168.31.19)
ssh xinzhi@192.168.31.19

# 3. 檢查伺服器上的 bridge 和 api_server 是否在跑
ps aux | grep python
# 預期：看到 bridge_v4.py 和 api_server 的行程

# 4. 檢查伺服器上的 live_data.json
cat /home/xinzhi/goss-v4/live_data.json | head -5
# 預期：看到 timestamp 和 flights 陣列

# 5. 檢查資料庫中 live_traffic 有多少筆
cd /home/xinzhi/goss-v4
sqlite3 goss_v4.db "SELECT COUNT(*) FROM live_traffic WHERE updated_at > datetime('now', '-10 minutes');"
# 預期：大於 0

# 6. 檢查 push_to_github.py crontab
crontab -l
# 預期：看到是否有 push_to_github.py 的項目
```

---

### 第二層：其他頁面讀取舊 CSV ⭐ 最關鍵的問題

| # | 頁面 | 當前資料來源 | 問題描述 |
|---|------|------------|---------|
| 2.1 | `/schedule` (航班時刻表) | 🔴 Google Sheets CSV | `gid=1969230956` 和 `gid=2070565332` — **資料停留在 4/6** |
| 2.2 | `/map` (機場地圖) | 🔴 Google Sheets CSV | `gid=0` 和 `gid=2059190189` — **資料停留在 4/6** |
| 2.3 | `/outbound` (出境航班) | 🔴 Google Sheets CSV | `gid=2059190189` — **資料停留在 4/6** |
| 2.4 | `/gate/[gate]` (登機門) | 🔴 Google Sheets CSV | 三個 gid (ARR/DEP/BAY) — **資料停留在 4/6** |

> [!CAUTION]
> **04-11 日誌所記載的「遷移完成」是假的！**
>
> 日誌聲稱建立了 3 個新 API 路由 (`/api/gate-data`, `/api/schedule-data`, `/api/map-data`)
> 並且更新了 4 個前端頁面。但實際上：
> - 這些 API 路由 **不存在**（`app/api/` 下只有 `feedback/` 和 `live-data/`）
> - 所有前端頁面 **仍然使用 Google Sheets CSV URL**
> - 可能是在伺服器上修改後被 `git reset --hard` 回復了

**檢查步驟：**
```bash
# 1. 確認 Google Sheet 的資料日期
# 在瀏覽器打開以下 URL，看最後更新日期：
# https://docs.google.com/spreadsheets/d/e/2PACX-1vSU9r4JTOOhZ3qQKEXNZpHqR9B-EQ35U3XwR74LKkJk1v1Rdan8VMgZjKWb1khjCU_VVp4hJ2sJPnx3/pub?gid=0&single=true&output=csv

# 2. 檢查前端頁面原始碼中的資料來源
grep -r "google.com/spreadsheets" app/
# 預期：在 schedule, map, outbound, gate 頁面都能找到

# 3. 檢查 API 路由是否存在
ls app/api/
# 預期：只有 feedback/ 和 live-data/
# 缺少：gate-data/, schedule-data/, map-data/

# 4. 確認 Google Sheets 匯出腳本是否在運行
ssh xinzhi@192.168.31.19
ps aux | grep export
# 看 export_to_gsheets.py 等腳本是否有在跑
```

**根本問題：Google Sheet 為什麼沒更新？**
- `export_to_gsheets.py` — 匯出到 Google Sheets 的腳本可能已停止
- 即使腳本在跑，它寫入的是 `flight_trajectory` 表（跑道軌跡），不是航班時刻表
- `export_arrivals_to_gsheets.py` — 只匯出昨日入境航班，不是即時資料
- **結論：Google Sheets 從 4/6 起就沒有被任何腳本更新**

---

### 第三層：伺服器端 Python 腳本

| # | 腳本 | 功能 | 狀態 | 問題 |
|---|------|------|-----|------|
| 3.1 | `bridge_v4.py` | 數據融合引擎 | ❓ | 需確認是否在跑 |
| 3.2 | `api_server_fixed.py` | HTTP API 伺服器 | 🔴 已停止 | 04-11 手動停止 |
| 3.3 | `push_to_github.py` | 推送 live_data.json | 🔴 已停用 | crontab 已移除 |
| 3.4 | `fetch_tpe_v4.py` | 抓取桃機班表 | ❓ | 需確認 crontab |
| 3.5 | `export_to_gsheets.py` | 匯出到 Google Sheets | 🔴 已停止 | 沒在 crontab 中 |
| 3.6 | `export_arrivals_to_gsheets.py` | 匯出昨日入境 | 🔴 已停止 | 沒在 crontab 中 |

**檢查步驟：**
```bash
# SSH 到伺服器
ssh xinzhi@192.168.31.19

# 1. 檢查所有 Python 行程
ps aux | grep python3

# 2. 檢查 crontab
crontab -l

# 3. 檢查各腳本 log
tail -50 /home/xinzhi/goss-v4/bridge.log
tail -50 /home/xinzhi/goss-v4/api.log

# 4. 檢查資料庫最後更新時間
cd /home/xinzhi/goss-v4
sqlite3 goss_v4.db "SELECT MAX(updated_at) FROM source_airport;"
sqlite3 goss_v4.db "SELECT MAX(updated_at) FROM live_traffic;"
sqlite3 goss_v4.db "SELECT MAX(updated_at) FROM flight_schedule;"
```

---

### 第四層：編碼問題

| # | 檢查項目 | 狀態 | 問題 |
|---|---------|------|------|
| 4.1 | `actype` 欄位亂碼 | 🔴 | `live_data.json` 中 `actype: "準時ON TIME"` 變成 `"�Ǯ�ON TIME"` |
| 4.2 | `status` 欄位 | ⚠️ | 中英文混合 (`已到ARRIVED`, `準時ON TIME`) |
| 4.3 | cp950 vs utf-8 | ⚠️ | 桃園機場 TXT 用 cp950，資料庫用 utf-8，轉換出錯 |
| 4.4 | `safe_string_encoder` | 🔴 | `api_server_fixed.py` 的 encoder 會把所有非 ASCII 字元砍掉 |

**問題源頭分析：**
```
桃園機場 TXT (cp950) 
    → fetch_tpe_v4.py (cp950 decode) 
    → SQLite 資料庫 (UTF-8 storage) 
    → api_server_fixed.py (safe_string_encoder 砍中文!)
    → live_data.json (亂碼)
    → CDN → 前端
```

`safe_string_encoder` 第165行有致命 bug：
```python
# 這行會把所有中文字全砍掉！只保留 ASCII
cleaned = ''.join(c for c in obj if 32 <= ord(c) <= 126 or c in '\n\r\t')
```

---

### 第五層：部署流程

| # | 檢查項目 | 狀態 | 問題 |
|---|---------|------|------|
| 5.1 | `git reset --hard` | ⚠️ 已註解 | `push_to_github.py` 第152行已註解但仍 `git fetch` |
| 5.2 | 本地 vs GitHub不同步 | 🔴 | 6 個檔案已修改但未 commit: `bridge_v4.py`, `push_to_github.py`, `next.config.ts` 等 |
| 5.3 | 大量 untracked 檔案 | ⚠️ | 50+ 個 fix/check/test 腳本散落各處 |
| 5.4 | Vercel 部署 | ⚠️ | 最後一次有效前端部署: `4d1a567 fix: 修改 API 路由使用 CDN 資料源` |
| 5.5 | GitHub 大量 live_data 提交 | 🔴 | 數百個 `chore: 更新实时航班数据` 提交汙染 git history |

**檢查步驟：**
```bash
# 在本地開發端
git status
git log --oneline -20
git diff HEAD

# 確認最新部署的 Vercel 狀態
# 打開 https://vercel.com/dashboard 確認部署狀態
```

---

### 第六層：架構設計缺陷

| # | 缺陷 | 嚴重度 | 說明 |
|---|------|--------|------|
| 6.1 | 資料流不統一 | 🔴 致命 | 首頁讀 CDN JSON、其他頁讀 Google Sheets CSV、兩者來源完全不同 |
| 6.2 | Vercel 無法連內網 | 🔴 致命 | Vercel serverless 無法存取 `192.168.31.19` 的 SQLite |
| 6.3 | 用 GitHub 當資料庫 | ⚠️ 糟糕 | 每分鐘 commit 一次 live_data.json，嚴重汙染 repo |
| 6.4 | CDN 快取延遲 | ⚠️ | jsdelivr CDN 有快取，不是真正即時 |
| 6.5 | 沒有健康檢查機制 | 🔴 | 任何一環斷掉都沒有告警 |
| 6.6 | 重複腳本氾濫 | ⚠️ | `fix_*.py`, `check_*.py`, `test_*.py` 共 50+ 個臨時腳本 |
| 6.7 | 資料庫和 API Key 未保護 | 🔴 | `google_service_account.json`, FlightAware API Key 直接硬編碼 |

---

## 🔁 錯誤回審機制

### 每次修改前的必做檢查：
```
1. 確認修改在哪個環境生效（本地 / 伺服器 / Vercel）？
2. 修改後是否會被其他腳本覆蓋（git reset --hard、crontab）？
3. 前端頁面的資料來源是什麼（CDN / API / Google Sheets）？
4. 資料經過了幾層轉換？哪一層可能出錯？
5. 編碼是否正確（cp950 → UTF-8 → JSON）？
```

### 每次部署後的驗證清單：
```
1. 瀏覽器打開 https://www.tpegoss.com/ → 看到即時航班資料？
2. 打開 /schedule → 看到今天的日期？
3. 打開 /map → 機坪有航班顯示？
4. 打開 /outbound → 看到離場航班？
5. 打開 /gate/A1 → 看到今天航班動態？
6. F12 開 Console → 沒有紅色錯誤？
7. 檢查 Network tab → API 回應不是空的？
```

---

## 🏗️ 最終建議：建立 GOSS 4.1

> [!IMPORTANT]
> **建議打掉重練**。目前的架構有太多不可修復的設計缺陷（Vercel 無法連 SQLite、Google Sheets 作為中間層、CDN 延遲、git 汙染），繼續修補只會越改越亂。

### GOSS 4.1 核心改動

```
    GOSS 4.0 (現在的爛架構)
    ┌──────────────────────────────────────────────────┐
    │  i5 伺服器 [SQLite + bridge + api_server]        │
    │       ↓ push_to_github.py (每分鐘)              │
    │  GitHub public/live_data.json                    │
    │       ↓ jsdelivr CDN                             │
    │  Vercel /api/live-data (proxy to CDN)            │
    │       ↓                                          │
    │  首頁 → CDN JSON (只有入境即時資料)               │
    │  其他頁 → Google Sheets CSV (完全斷裂!!!)         │
    └──────────────────────────────────────────────────┘

    GOSS 4.1 (乾淨架構)
    ┌──────────────────────────────────────────────────┐
    │  i5 伺服器 [SQLite + bridge + 統一 API 伺服器]   │
    │       ↓ 每 30 秒匯出                            │
    │  GitHub /public/data/live.json                   │
    │  GitHub /public/data/schedule.json               │
    │  GitHub /public/data/gates.json                  │
    │       ↓ jsdelivr CDN (統一資料來源)               │
    │  Vercel API 路由 (proxy to CDN, 統一介面)        │
    │       ↓                                          │
    │  所有頁面統一透過 /api/* 取得資料                  │
    └──────────────────────────────────────────────────┘
```

### GOSS 4.1 實作步驟

| 步驟 | 動作 | 詳細說明 |
|------|------|---------|
| 1 | 整理伺服器端 | 確認 `bridge_v4.py` + `fetch_tpe_v4.py` 正常運作 |
| 2 | 建立統一匯出腳本 | 一個 `export_all.py` 同時產出 `live.json` + `schedule.json` + `gates.json` |
| 3 | 修正編碼問題 | 移除 `safe_string_encoder`，用正確的 `ensure_ascii=False` |
| 4 | 建立 Vercel API 路由 | `/api/live-data`, `/api/schedule`, `/api/gates`, `/api/gate/[id]` |
| 5 | 改寫前端頁面 | 所有頁面統一使用 `/api/*` 路由，完全移除 Google Sheets CSV |
| 6 | 清理 git repo | 移除臨時腳本、`.gitignore` 加上 `*.db`, `*.json`，squash commits |
| 7 | 建立健康檢查 | `/api/health` 端點 + 前端顯示系統狀態 |
| 8 | 保護 API Key | 移到環境變數，不再硬碼 |

### 要不要開 `goss-v4.1/` 資料夾？

**不需要另開資料夾**。建議直接在現有的 `goss-v4/` 目錄裡做清理：
- 刪除所有 `fix_*.py`, `check_*.py`, `test_*.py` 臨時腳本
- 建立 `goss-v4/export_all.py` 統一匯出
- 前端頁面直接原地修改

如果你擔心改壞東西，可以先 `git checkout -b goss-4.1` 開一個分支。

---

## 📊 問題嚴重度排序

| 優先級 | 問題 | 影響 | 修復難度 |
|--------|------|------|---------|
| 🔴 P0 | 其他頁面讀 Google Sheets CSV (4/6 舊資料) | 所有使用者看到過期一週的資料 | 中 |
| 🔴 P0 | CDN `live_data.json` 為空 | 首頁顯示「沒有航班資訊」 | 低 |
| 🔴 P1 | `api_server` / `push_to_github` 停止運作 | 資料不再更新 | 低 |
| 🟡 P1 | 編碼亂碼 (`actype` 欄位) | 航班資料顯示亂碼 | 中 |
| 🟡 P2 | git history 汙染 | repo 膨脹，版本管理混亂 | 低 |
| 🟡 P2 | API Key / credentials 硬碼 | 安全風險 | 低 |
| 🔵 P3 | 臨時腳本氾濫 | 維護困難 | 低 |

---

> **下一步**：告訴我你想怎麼做？
> 1. **快速修補**：先把伺服器端跑起來 + 前端頁面改成讀 API → 可以在 2-3 小時內完成
> 2. **GOSS 4.1 完整重構**：按上面的步驟做全面清理 → 需要 1-2 天
> 3. **混合方案**：先快速修補讓網站能用，再慢慢重構
