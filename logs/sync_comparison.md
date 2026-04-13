# 本地 vs 伺服器 Python 檔案同步對照表

> 初次對照：2026-04-10 17:45 (Taiwan Time)
> **同步完成：2026-04-10 18:05 (Taiwan Time)** ✅
> 
> - **本地**: `c:\Users\Xin_Zhi\Desktop\google_ai\tpe-goss\goss-v4\`
> - **伺服器**: `xinzhi@192.168.31.19:/home/xinzhi/goss-v4/`

---

## ✅ 已同步修復的關鍵檔案 — 共 5 個

> [!TIP]
> 以下檔案已於 18:00 上傳至伺服器，並驗證運作正常。

### 已上傳並驗證

| 檔案 | 原伺服器大小 | 上傳後大小 | 修復內容 |
|------|------------|-----------|----------|
| **fetch_tpe_v4.py** | 4,859 | **11,254** | ✅ 新增 80+ 家航空公司 IATA→ICAO 對照表、編碼修復、延誤航班處理。已手動執行，更新 3,755+275 筆班表 |
| **push_to_github.py** | 5,196 | **6,260** | ✅ 修復 PROJECT_ROOT 路徑邏輯：自動偵測 `.git` 位置（支援本地/伺服器不同目錄結構）。cron 每分鐘推送已恢復正常 |
| **init_db.py** | 6,941 | **7,155** | ✅ 補齊欄位/索引定義 |
| **export_data.py** | 2,965 | **3,056** | ✅ 小幅修正 |
| **pull_from_server.py** | 5,963 | **6,137** | ✅ 小幅修正 |

---

## 🟡 僅換行符差異（無需處理）— 約 17 個

以下檔案大小差異均在 **正常 CRLF↔LF 換行轉換範圍**（每行多 1 byte `\r`），實質內容相同，不影響功能：

| 檔案 | 本地 | 伺服器 | 差(bytes) |
|------|------|--------|-----------|
| alter_db.py | 1,439 | 1,402 | +37 |
| analyze_landing_points.py | 3,135 | 3,045 | +90 |
| check_antenna_data.py | 679 | 655 | +24 |
| check_live_traffic.py | 1,218 | 1,181 | +37 |
| check_table_structure.py | 973 | 942 | +31 |
| compare_data.py | 1,543 | 1,494 | +49 |
| export_arrivals_to_gsheets.py | 4,799 | 4,666 | +133 |
| export_runway_tracks.py | 6,112 | 5,952 | +160 |
| export_to_gsheets.py | 5,634 | 5,480 | +154 |
| extract_landing_phase.py | 3,734 | 3,622 | +112 |
| fetch_adsb_v4.py | 471 | 457 | +14 |
| fetch_calair_v4.py | 8,062 | 7,868 | +194 |
| fetch_flightaware_v4.py | 6,467 | 6,282 | +185 |
| fetch_fr24_v4.py | 8,453 | 8,240 | +213 |
| fetch_opensky_v4.py | 5,474 | 5,321 | +153 |
| fetch_yesterday_arrivals.py | 5,465 | 5,313 | +152 |
| run_pull_loop.py | 1,251 | 1,210 | +41 |
| runway_classifier.py | 8,932 | 8,693 | +239 |
| runway_classifier_final.py | 7,546 | 7,330 | +216 |
| runway_tracker.py | 3,860 | 3,748 | +112 |
| runway_tracker_v2.py | 6,387 | 6,225 | +162 |
| track_landing.py | 9,815 | 9,552 | +263 |
| update_runway_table.py | 1,058 | 1,025 | +33 |
| war_room_v4_viewer.py | 1,807 | 1,763 | +44 |

---

## 🟢 原本就已同步（MD5 一致）— 共 4 個

| 檔案 | 大小 | 說明 |
|------|------|------|
| **bridge_v4.py** | 33,526 | ✅ 核心引擎完全一致 |
| **api_server.py** | 5,184 | ✅ |
| **api_server_fixed.py** | 8,878 | ✅ |
| **taoyuan_data_processor.py** | 15,587 | ✅ |

---

## 📂 僅存在於本地（伺服器沒有）— 共 16 個

| 檔案 | 大小 | 說明 |
|------|------|------|
| bridge_v4_improved.py | 9,510 | 改進版 bridge（半成品） |
| check_db_status.py | 2,051 | 調試工具 |
| check_db_structure.py | 719 | 調試工具 |
| check_flightaware_match.py | 2,443 | 調試工具 |
| check_real_tables.py | 1,125 | 調試工具 |
| check_server_db.py | 657 | 調試工具 |
| check_server_tables.py | 1,382 | 調試工具 |
| comprehensive_db_check.py | 5,738 | 調試工具 |
| debug_flightaware.py | 1,671 | 調試工具 |
| fix_encoding_issues.py | 8,574 | 編碼修復 |
| fix_issues.py | 8,087 | 綜合修復 |
| fixed_db_check.py | 4,208 | 調試工具 |
| improved_fix_encoding.py | 13,074 | 編碼修復 |
| test_flightaware.py | 1,136 | 測試 |
| test_flightaware2.py | 1,119 | 測試 |
| test_flightaware3.py | 1,200 | 測試 |
| test_flightaware4.py | 1,088 | 測試 |

---

## 📂 僅存在於伺服器（本地沒有）— 共 1 個

| 檔案 | 大小 | 說明 |
|------|------|------|
| **test_status_format.py** | 1,222 | 狀態格式測試（伺服器獨有） |

---

## ✅ 已解決的問題（2026-04-10 18:05 完成）

### 1. `fetch_tpe_v4.py` 版本差異 → 已修復
- 上傳本地最新版（4,859 → 11,254 bytes）
- 手動執行一次，成功更新 **3,755 筆客機 + 275 筆貨機**班表
- 航班號碼格式統一為 ICAO（`CAL`, `EVA`），與 `bridge_v4.py` 天線資料格式一致

### 2. `push_to_github.py` 路徑錯誤 → 已修復
- **原問題**：`PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)` 在伺服器上會指向 `/home/xinzhi`（沒有 `.git`）
- **修復方式**：自動偵測 `.git` 位置
```python
if os.path.exists(os.path.join(SCRIPT_DIR, ".git")):
    PROJECT_ROOT = SCRIPT_DIR  # 伺服器：.git 在腳本同目錄
else:
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  # 本地：.git 在上層
```
- cron 每分鐘推送已恢復正常：`[18:04:07] ✅ 成功推送到 GitHub`

### 3. 服務重啟
- 暫停舊 `bridge_v4.py`（PID 1303038）和 `taoyuan_data_processor.py`（PID 1279249）
- 重新啟動所有服務，確認正常運行

---

## 📊 伺服器最終運行狀態

| 服務 | PID | 狀態 | 功能 |
|------|-----|------|------|
| `bridge_v4.py` | 1492048 | 🟢 運行中 | 每 2 秒融合天線 + OpenSky 資料 |
| `api_server_fixed.py` | 1308188 | 🟢 運行中 (自 Apr 09) | 每 10 秒匯出 20 筆入境航班至 JSON |
| `taoyuan_data_processor.py` | 1492867 | 🟢 運行中 | 每 10 分鐘從官網更新班表 |
| `push_to_github.py` | cron 每分鐘 | 🟢 正常推送 | 匯出 → git push → GitHub Pages |

### ⚠️ 殘留問題
- `actype` 欄位仍有編碼亂碼（如 `�w��ARRIVED`），來自機場官網 TXT 的 cp950/UTF-8 混合編碼
- `test_status_format.py` 僅存在於伺服器，尚未拉回本地
