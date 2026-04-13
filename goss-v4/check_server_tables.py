import subprocess

# 檢查伺服器資料庫的表格結構和資料
commands = [
    "ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && sqlite3 goss_v4.db '.tables'\"",
    "ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && sqlite3 goss_v4.db \"SELECT name FROM sqlite_master WHERE type='table'\"\"",
    "ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && sqlite3 goss_v4.db \"PRAGMA table_info(flight_schedule)\"\"",
    "ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && sqlite3 goss_v4.db \"SELECT COUNT(*) FROM flight_schedule\"\"",
    "ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && sqlite3 goss_v4.db \"SELECT flight_no, status FROM flight_schedule WHERE status IS NOT NULL LIMIT 10\"\"",
    "ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && sqlite3 goss_v4.db \"PRAGMA table_info(source_airport)\"\"",
    "ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && sqlite3 goss_v4.db \"SELECT COUNT(*) FROM source_airport\"\"",
    "ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && sqlite3 goss_v4.db \"SELECT flight_no, status FROM source_airport WHERE status IS NOT NULL LIMIT 10\"\""
]

for i, cmd in enumerate(commands):
    print(f"\n=== 執行命令 {i+1} ===")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("輸出:", result.stdout)
    if result.stderr:
        print("錯誤:", result.stderr)