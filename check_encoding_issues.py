import sqlite3

# 連接資料庫
conn = sqlite3.connect('goss-v4/goss_v4.db')
cursor = conn.cursor()

print("檢查 flight_schedule 表狀態欄位:")
cursor.execute("SELECT DISTINCT status FROM flight_schedule LIMIT 20")
statuses = cursor.fetchall()

print("狀態值樣本:")
for i, status in enumerate(statuses):
    print(f"  {i+1}. {repr(status[0])}")

print("\n檢查 source_airport 表狀態欄位:")
cursor.execute("SELECT DISTINCT status FROM source_airport LIMIT 20")
statuses_airport = cursor.fetchall()

print("狀態值樣本:")
for i, status in enumerate(statuses_airport):
    print(f"  {i+1}. {repr(status[0])}")

# 檢查是否有亂碼
print("\n檢查可能的亂碼狀態:")
cursor.execute("SELECT status FROM flight_schedule WHERE status LIKE '%�%' OR status LIKE '%?%' LIMIT 10")
corrupted = cursor.fetchall()

if corrupted:
    print("發現亂碼狀態:")
    for i, status in enumerate(corrupted):
        print(f"  {i+1}. {repr(status[0])}")
else:
    print("未發現明顯亂碼")

conn.close()