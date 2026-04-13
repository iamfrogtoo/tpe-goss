import subprocess
import sys

# 在伺服器上執行簡單的 SQLite 查詢
cmd = """
ssh xinzhi@192.168.31.19 "cd /home/xinzhi/goss-v4 && sqlite3 goss_v4.db '.tables'"
"""

result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print("伺服器資料庫表格:")
print(result.stdout)
if result.stderr:
    print("錯誤:", result.stderr)

# 檢查資料庫大小
cmd2 = """
ssh xinzhi@192.168.31.19 "cd /home/xinzhi/goss-v4 && ls -lh goss_v4.db"
"""

result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
print("\n資料庫檔案大小:")
print(result2.stdout)
if result2.stderr:
    print("錯誤:", result2.stderr)