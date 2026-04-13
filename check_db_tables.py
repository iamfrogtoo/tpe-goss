import sqlite3

# 連接資料庫
conn = sqlite3.connect('goss-v4/goss_v4.db')
cursor = conn.cursor()

# 查詢所有表格
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()

print('資料庫中的表格:')
for table in tables:
    print(f'  - {table[0]}')
    
    # 檢查每個表格的結構
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print(f'    欄位結構:')
    for col in columns:
        print(f'      {col[1]} ({col[2]})')
    
    # 檢查每個表格的資料筆數
    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
    count = cursor.fetchone()[0]
    print(f'    資料筆數: {count}')
    print()

conn.close()