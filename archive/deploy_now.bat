@echo off
chcp 65001 >nul
color 0A

echo ============================================
echo  TPE GOSS 部署 tracker_schedule.py (全日班表版)
echo  Daily_Schedule + Schedule_Arr + Schedule_Dep
echo ============================================
echo.
echo [步驟 1] SCP 上傳
echo.
scp "C:\Users\Xin_Zhi\Desktop\google_ai\tpe-goss\Flight_Project\tracker_schedule.py" xinzhi@192.168.31.19:/home/xinzhi/goss-system/tracker_schedule.py
echo.
echo [步驟 2] SSH 重啟 tracker
echo.
ssh xinzhi@192.168.31.19 "pkill -f tracker_schedule 2>/dev/null; sleep 1; cd /home/xinzhi/goss-system && nohup python3 -u tracker_schedule.py >> schedule.log 2>&1 & echo '[OK] tracker 已重啟（全日班表版）'"
echo.
echo [步驟 3] 確認 log
ssh xinzhi@192.168.31.19 "tail -20 /home/xinzhi/goss-system/schedule.log"
echo.
echo ============================================
echo  [OK] 請等 10 分鐘讓 tracker 完成第一次更新
echo  更新後 Google Sheets 會有:
echo    Daily_Schedule (全日彙總)
echo    Schedule_Arr   (入境)
echo    Schedule_Dep   (出境)
echo  確認 log 應看到「寫入 Daily_Schedule」字樣
echo ============================================
pause
