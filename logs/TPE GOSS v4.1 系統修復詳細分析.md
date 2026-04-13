# TPE GOSS v4.1 系統修復詳細分析

## 📋 文件目錄
1. [現有架構分析](#1-現有架構分析)
2. [問題診斷](#2-問題診斷)
3. [如何修改](#3-如何修改)
4. [修改步驟](#4-修改步驟)
5. [不需要打掉重練的理由和優點](#5-不需要打掉重練的理由和優點)

---

## 1. 現有架構分析

TPE GOSS v4 是一個基於 SQLite3 的桃園機場地面作業監控系統，採用三節點分散式架構。系統核心功能包括：ADS-B 航機即時追蹤、多源數據融合（樹莓派 + OpenSky API）、航班時刻表整合、貨機標註及機坪自動對標。

本系統主要由三大模組構成：
1. **後端數據處理層**（i5 伺服器 192.168.31.19）：負責數據抓取、融合與存儲
2. **數據同步層**：透過 GitHub + jsDelivr CDN 實現即時數據推送
3. **前端展示層**（Next.js + Vercel）：提供網頁介面與多個功能頁面

### 1.1 當前系統堆疊

```mermaid
graph TB
    subgraph "後端 (i5 伺服器 192.168.31.19)"
        A1[ADS-B 天線<br/>樹莓派 192.168.31.221] --> A2[fetch_adsb_v4.py]
        A3[桃園機場官網] --> A4[fetch_tpe_v4.py]
        A5[OpenSky API] --> A6[fetch_opensky_v4.py]
        A2 & A4 & A6 --> A7[bridge_v4.py<br/>數據融合引擎]
        A7 --> A8[(goss_v4.db<br/>SQLite3)]
        A8 --> A9[push_to_github.py<br/>定時任務]
    end

    subgraph "數據同步層"
        A9 -->|僅推送 live_data.json| B1[GitHub Repo<br/>iamfrogtoo/tpe-goss]
        B1 -->|CDN 加速| B2[jsdelivr CDN]
    end

    subgraph "前端 (Vercel)"
        C1[Next.js App]
        C2[app/page.tsx<br/>首頁]
        C3[app/schedule/page.tsx<br/>航班時刻表]
        C4[app/outbound/page.tsx<br/>出境航班]
        C5[app/map/page.tsx<br/>機場地圖]
        C6[app/gate/[gate]/page.tsx<br/>登機門]
        
        C7[app/api/live-data/route.ts<br/>即時數據 API]
        
        C2 -->|fetch| C7
        C3 -->|fetch ❌ 舊 CSV| D1[Google Sheets CSV]
        C4 -->|fetch ❌ 舊 CSV| D1
        C5 -->|fetch ❌ 舊 CSV| D1
        C6 -->|fetch ❌ 舊 CSV| D1
        
        C7 -->|fetch| B2
    end

    subgraph "問題點"
        E1[push_to_github.py<br/>曾有 git reset --hard]
        E2[API 路由遺失<br/>schedule-data/gate-data/map-data]
        E3[前端頁面退回<br/>舊 CSV 來源]
    end
```

### 1.2 目錄結構

```
tpe-goss/
├── app/                          # Next.js 前端
│   ├── page.tsx                  # 首頁（使用 /api/live-data）✅
│   ├── schedule/page.tsx         # 航班時刻表（退回舊 CSV）❌
│   ├── outbound/page.tsx         # 出境航班（退回舊 CSV）❌
│   ├── map/page.tsx              # 機場地圖（退回舊 CSV）❌
│   ├── gate/[gate]/page.tsx      # 登機門（退回舊 CSV）❌
│   └── api/
│       ├── live-data/route.ts    # 即時數據 API ✅
│       ├── schedule-data/route.ts # 班表 API（遺失）❌
│       ├── gate-data/route.ts     # 登機門 API（遺失）❌
│       └── map-data/route.ts      # 地圖 API（遺失）❌
├── goss-v4/                      # Python 後端
│   ├── bridge_v4.py              # 數據融合引擎
│   ├── fetch_tpe_v4.py           # 桃機班表抓取
│   ├── push_to_github.py         # GitHub 推送（git reset 已註解）⚠️
│   └── goss_v4.db                # SQLite 資料庫
└── public/
    └── live_data.json            # 即時數據 JSON
```

### 1.3 資料庫結構重點

| 資料表 | 用途 | 關聯頁面 |
|--------|------|----------|
| `live_traffic` | 即時 ADS-B 航機 | 首頁 |
| `flight_schedule` | 航班時刻表 | schedule/outbound |
| `source_airport` | 機場來源數據（含終端、登機門、機型等） | schedule/outbound/map/gate |

---

## 2. 問題診斷

### 2.1 問題根因時間線

```
4/11 ✅ 完成 API 遷移
     ├── 建立 3 個 API 路由（schedule-data/gate-data/map-data）
     ├── 修改 4 個前端頁面（schedule/outbound/map/gate）
     ├── 提交 df501198 並部署成功
     └── 公開網站顯示即時資料

4/11~4/12 ⚠️ 問題發生
     ├── push_to_github.py 執行 git reset --hard（已註解但可能還在運行）
     ├── API 路由檔案被刪除
     ├── 前端頁面被覆蓋回舊版本
     └── 公開網站退回 4/6 舊 CSV 資料

現在 📋 需要修復
```

### 2.2 具體問題清單

| 問題 | 嚴重性 | 影響 |
|------|--------|------|
| API 路由 `schedule-data` 遺失 | 🔴 高 | schedule/outbound 頁面無法取得班表 |
| API 路由 `gate-data` 遺失 | 🔴 高 | gate 頁面無法運作 |
| API 路由 `map-data` 遺失 | 🔴 高 | map 頁面無法運作 |
| `schedule/page.tsx` 退回舊 CSV | 🔴 高 | 顯示 4/6 舊資料 |
| `outbound/page.tsx` 退回舊 CSV | 🔴 高 | 顯示 4/6 舊資料 |
| `push_to_github.py` 安全性 | 🟡 中 | 可能仍有 git reset 風險 |

---

## 3. 如何修改

### 3.1 修改原則

> **數據代碼徹底分離** - 這是最核心的原則
> - 代碼：`app/`, `components/`, `goss-v4/*.py`（除了 public/）
> - 數據：`public/live_data.json`, `goss_v4.db`
> - `push_to_github.py` **只能**觸碰 `public/live_data.json`

### 3.2 需要建立的 API 路由

#### 3.2.1 `/api/schedule-data/route.ts`
```typescript
// 功能：從 goss_v4.db 讀取 flight_schedule 和 source_airport
// 參數：type=arr (入境), type=dep (出境), type=all (全部)
// 輸出：JSON 格式航班資料
```

#### 3.2.2 `/api/gate-data/route.ts`
```typescript
// 功能：查詢指定登機門的航班
// 參數：gate=A1
// 輸出：該登機門的航班列表
```

#### 3.2.3 `/api/map-data/route.ts`
```typescript
// 功能：提供地圖頁面所需數據
// 輸出：分離入境和出境航班，按航廈分組
```

### 3.3 需要修改的前端頁面

| 頁面 | 修改內容 | 替換目標 |
|------|----------|----------|
| `app/schedule/page.tsx` | 移除 `CSV_ARR`, `CSV_DEP` | 改 fetch `/api/schedule-data` |
| `app/outbound/page.tsx` | 移除 `CSV_URL` | 改 fetch `/api/schedule-data?type=dep` |
| `app/map/page.tsx` | 移除 CSV 來源 | 改 fetch `/api/map-data` |
| `app/gate/[gate]/page.tsx` | 移除 CSV 來源 | 改 fetch `/api/gate-data?gate=${gate}` |

### 3.4 需要確認的後端腳本

| 腳本 | 檢查項目 |
|------|----------|
| `goss-v4/push_to_github.py` | 確認 `git reset --hard` 已永久註解或刪除 |
| `goss-v4/fetch_tpe_v4.py` | 確認 CP950 編碼正確解碼為 UTF-8 |
| `goss-v4/bridge_v4.py` | 確認數據融合正常寫入 goss_v4.db |

---

## 4. 修改步驟

### 階段 0：準備與 Git 歷史檢查（建議先做）

```bash
# 1. 檢查當前分支狀態
git status

# 2. 檢查 Git 歷史，尋找 4/11 的提交
git log --oneline --since="2026-04-10" --until="2026-04-12"

# 3. 如果找到 df501198，創建恢復分支
git checkout -b goss-v4.1-recovery
git cherry-pick df501198  # 如果成功，跳到階段 3

# 4. 如果無法從 Git 恢復，繼續階段 1 手動重建
```

---

### 階段 1：重建 API 路由（手動方式）

#### 步驟 1.1 建立 `/api/schedule-data/route.ts`

```typescript
// app/api/schedule-data/route.ts
import { NextRequest, NextResponse } from 'next/server';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';

const DB_PATH = process.env.DB_PATH || './goss-v4/goss_v4.db';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const type = searchParams.get('type') || 'all'; // arr, dep, all

  try {
    const db = await open({
      filename: DB_PATH,
      driver: sqlite3.Database
    });

    let query = `
      SELECT 
        fs.flight_no,
        fs.direction,
        fs.scheduled_time,
        fs.actual_time,
        fs.status,
        sa.terminal,
        sa.gate,
        sa.aircraft_type,
        sa.reg
      FROM flight_schedule fs
      LEFT JOIN source_airport sa ON fs.flight_no = sa.flight_no
      WHERE 1=1
    `;

    if (type === 'arr') {
      query += " AND fs.direction = 'A'";
    } else if (type === 'dep') {
      query += " AND fs.direction = 'D'";
    }

    const flights = await db.all(query);
    await db.close();

    return NextResponse.json({ flights, timestamp: new Date().toISOString() });
  } catch (error) {
    return NextResponse.json(
      { error: 'Database error', details: error.message },
      { status: 500 }
    );
  }
}
```

#### 步驟 1.2 建立 `/api/gate-data/route.ts`

```typescript
// app/api/gate-data/route.ts
import { NextRequest, NextResponse } from 'next/server';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';

const DB_PATH = process.env.DB_PATH || './goss-v4/goss_v4.db';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const gate = searchParams.get('gate');

  if (!gate) {
    return NextResponse.json(
      { error: 'Missing gate parameter' },
      { status: 400 }
    );
  }

  try {
    const db = await open({
      filename: DB_PATH,
      driver: sqlite3.Database
    });

    const flights = await db.all(`
      SELECT * FROM source_airport 
      WHERE gate = ? 
      ORDER BY scheduled_time ASC
    `, gate);

    await db.close();

    return NextResponse.json({ flights, gate, timestamp: new Date().toISOString() });
  } catch (error) {
    return NextResponse.json(
      { error: 'Database error', details: error.message },
      { status: 500 }
    );
  }
}
```

#### 步驟 1.3 建立 `/api/map-data/route.ts`

```typescript
// app/api/map-data/route.ts
import { NextResponse } from 'next/server';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';

const DB_PATH = process.env.DB_PATH || './goss-v4/goss_v4.db';

export async function GET() {
  try {
    const db = await open({
      filename: DB_PATH,
      driver: sqlite3.Database
    });

    const allFlights = await db.all(`
      SELECT 
        fs.flight_no,
        fs.direction,
        sa.terminal,
        sa.gate,
        sa.aircraft_type
      FROM flight_schedule fs
      LEFT JOIN source_airport sa ON fs.flight_no = sa.flight_no
    `);

    const arrivals = allFlights.filter(f => f.direction === 'A');
    const departures = allFlights.filter(f => f.direction === 'D');

    await db.close();

    return NextResponse.json({
      arrivals,
      departures,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Database error', details: error.message },
      { status: 500 }
    );
  }
}
```

---

### 階段 2：修改前端頁面

#### 步驟 2.1 修改 `app/schedule/page.tsx`

```typescript
// 替換開頭的 CSV_URL 定義
// 舊：
// const CSV_ARR = "https://docs.google.com/spreadsheets/...";
// const CSV_DEP = "https://docs.google.com/spreadsheets/...";

// 新：
const API_URL = "/api/schedule-data";

// 修改 fetchData 函數
const fetchData = async () => {
  try {
    setLoading(true);
    
    // 同時獲取入境和出境
    const [arrRes, depRes] = await Promise.all([
      fetch(`${API_URL}?type=arr&t=${Date.now()}`).then(r => r.json()),
      fetch(`${API_URL}?type=dep&t=${Date.now()}`).then(r => r.json())
    ]);

    // 處理 arrRes.flights 和 depRes.flights...
    // 其餘邏輯保持不變
  }
};
```

#### 步驟 2.2 修改 `app/outbound/page.tsx`

```typescript
// 替換 CSV_URL
const API_URL = "/api/schedule-data?type=dep";

// 修改 fetchData
const fetchData = async () => {
  try {
    const res = await fetch(`${API_URL}&t=${Date.now()}`);
    const data = await res.json();
    // 處理 data.flights...
  }
};
```

#### 步驟 2.3 修改 `app/map/page.tsx` 和 `app/gate/[gate]/page.tsx`
（類似方式，替換為對應的 API 調用）

---

### 階段 3：確認後端安全

#### 步驟 3.1 永久修復 `push_to_github.py`

```python
# goss-v4/push_to_github.py
# 確認以下程式碼已被永久刪除或註解：

# ❌ 刪除這些：
# subprocess.run(['git', 'reset', '--hard', 'origin/main'], ...)

# ✅ 只保留這些：
subprocess.run(['git', 'add', 'public/live_data.json'], ...)
subprocess.run(['git', 'commit', '-m', ...], ...)
subprocess.run(['git', 'push', 'origin', 'main'], ...)
```

#### 步驟 3.2 建立 .gitignore 保護（如果需要）

```
# .gitignore 增加（如果不希望資料庫被提交）
goss-v4/goss_v4.db
goss-v4/*.db
```

---

### 階段 4：測試與部署

#### 步驟 4.1 本地測試

```bash
# 1. 安裝 sqlite 依賴（如果需要）
npm install sqlite sqlite3

# 2. 本地運行
npm run dev

# 3. 測試 API
# 訪問 http://localhost:3000/api/schedule-data
# 訪問 http://localhost:3000/api/gate-data?gate=A1
# 訪問 http://localhost:3000/api/map-data
```

#### 步驟 4.2 頁面功能測試
- [ ] 首頁顯示即時入境航班
- [ ] schedule 頁面入境/出境切換正常
- [ ] outbound 頁面顯示正確
- [ ] map 頁面顯示正確
- [ ] gate 頁面顯示正確
- [ ] 無編碼亂碼

#### 步驟 4.3 部署

```bash
git add .
git commit -m "fix: 重建 API 路由並修復前端頁面"
git push origin main
# Vercel 會自動部署
```

---

## 5. 不需要打掉重練的理由和優點

### 5.1 為什麼不需要打掉重練？

| 理由 | 說明 |
|------|------|
| ✅ **4/11 已經完成過一次** | 所有工作（API 路由、前端修改）在 4/11 都已完成並成功部署，只是被 `git reset` 摧毀了 |
| ✅ **Git 歷史可能還在** | 提交 `df501198` 很可能還在 Git reflog 或歷史中，可以直接恢復 |
| ✅ **後端運作正常** | `bridge_v4.py`、`fetch_tpe_v4.py`、`goss_v4.db` 都在正常運作，問題只在前端 API 層 |
| ✅ **首頁已經正常** | `app/page.tsx` 和 `/api/live-data` 已經工作，證明代碼庫基礎是穩定的 |
| ✅ **打掉重練浪費時間** | 重建 goss4.1 資料夾需要複製所有檔案、重新設定、重新測試，至少耗費 2-3 倍時間 |

### 5.2 保留現有結構的優點

#### 優點 1：保留完整 Git 歷史
```
保留歷史 → 可以追蹤每個變更 → 未來除錯更容易
         ↓
    可以看到 4/11 到底改了什麼
         ↓
    將來出問題可以 git blame / git bisect
```

#### 優點 2：減少部署風險
```
在現有 main 分支修復 → Vercel 部署設定已經存在
                    ↓
            不需要重新設定專案
                    ↓
            不需要重新設定域名
                    ↓
            部署風險最小化
```

#### 優點 3：分支管理靈活
```
創建 goss-v4.1 分支進行開發
         ↓
    測試成功才合併回 main
         ↓
    隨時可以切換回 main
         ↓
    不怕搞壞生產環境
```

#### 優點 4：數據遷移零成本
```
goss_v4.db 已經在正確位置
         ↓
    live_data.json 已經在正確位置
         ↓
    不需要複製/移動數據
         ↓
    數據連續性不間斷
```

### 5.3 推薦的 Git 工作流程（未來）

```
main 分支 ------------------------→ 生產環境（穩定）
     ↑
     │ 合併（測試通過後）
     │
goss-v4.1 分支 ------------------→ 開發分支（新功能/修復）
     ↑
     │ 推送進行測試
     │
你的本地開發 --------------------→ 本地修改
```

### 5.4 總結：修復 vs 打掉重練對比

| 項目 | 修復現有結構（推薦） | 打掉重練 goss4.1 |
|------|---------------------|------------------|
| **耗時** | 30-60 分鐘 | 2-4 小時 |
| **Git 歷史** | ✅ 保留完整 | ❌ 中斷 |
| **部署風險** | 🟢 低 | 🟡 中 |
| **數據連續性** | ✅ 不中斷 | ⚠️ 需遷移 |
| **未來除錯** | ✅ 容易 | ❌ 困難 |
| **學習價值** | ✅ 理解問題根因 | ❌ 逃避問題 |

---

## 📌 最後建議

> **第一步**：先跑 `git log --oneline --since="2026-04-10"` 看看 `df501198` 還在不在
> 
> **如果在**：直接 `git cherry-pick`，五分鐘搞定
> 
> **如果不在**：照著上面的步驟手動重建，也是一小時內完成
> 
> **絕對不要**：創建 goss4.1 資料夾打掉重練，那是捨近求遠

---

**文件建立時間**：2026-04-12  
**文件版本**：v1.0
