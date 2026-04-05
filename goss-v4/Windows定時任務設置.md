# Windows 定時任務設置指南

## 方法一：使用循環腳本（最簡單，推薦）

直接雙擊運行 `run_pull_loop.bat`，它會每 30 秒自動執行一次。

優點：
- 最簡單，無需設置
- 可以隨時查看運行狀態
- 按 Ctrl+C 可以停止

## 方法二：使用 Windows 任務計劃程序

### 步驟：

1. 打開「任務計劃程序」（搜尋 taskschd.msc）
2. 右鍵「任務計劃程序庫」→ 「創建基本任務」
3. 名稱輸入：TPE GOSS 數據同步
4. 觸發器選擇：「每天」，開始時間設置為當前時間
5. 操作選擇：「啟動程序」
6. 程序或腳本：輸入 python.exe 的完整路徑
   - 例如：`C:\Users\Xin_Zhi\Desktop\google_ai\tpe-goss\.venv\Scripts\python.exe`
7. 參數：`pull_from_server.py`
8. 起始於：`C:\Users\Xin_Zhi\Desktop\google_ai\tpe-goss\goss-v4`
9. 完成後，雙擊新任務，進入「觸發器」標籤
10. 編輯觸發器，勾選「重複任務間隔」，設置為 1 分鐘
11. 持續時間選擇：「無限期」

## 方法三：使用 Python 循環（開機自動啟動）

創建一個快捷方式到「啟動」資料夾：

1. 按 Win+R，輸入 `shell:startup` 打開啟動資料夾
2. 右鍵 → 新建 → 快捷方式
3. 位置輸入：`cmd /k "cd /d C:\Users\Xin_Zhi\Desktop\google_ai\tpe-goss\goss-v4 && run_pull_loop.bat"`
4. 名稱輸入：TPE GOSS 數據同步
5. 完成

這樣開機就會自動運行了！

## 監控日誌

如果需要記錄日誌，可以修改 `run_pull_loop.bat`：

```batch
@echo off
chcp 65001 >nul
cd /d "%~dp0"

:loop
echo [%date% %time%] 開始執行 >> pull.log
python pull_from_server.py >> pull.log 2>&1
echo [%date% %time%] 執行完成 >> pull.log
timeout /t 30 /nobreak >nul
goto loop
```

## 當前狀態

✅ `pull_from_server.py` 測試成功
✅ 已從伺服器下載數據庫
✅ 已導出 116 架航班數據
✅ 已成功推送到 GitHub

現在只需要保持 `run_pull_loop.bat` 運行即可！
