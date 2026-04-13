import sqlite3

def check_real_tables():
    conn = sqlite3.connect('goss_v4.db')
    cursor = conn.cursor()
    
    # 查看所有表格
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('資料庫中的表格:')
    for table in tables:
        print(f'- {table[0]}')
    
    # 檢查每個表格的結構和內容
    for table in tables:
        table_name = table[0]
        print(f'\n=== {table_name} 表結構 ===')
        
        # 查看表格結構
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for column in columns:
            print(f'列名: {column[1]}, 類型: {column[2]}')
        
        # 查看前5筆資料
        print(f'\n=== {table_name} 前5筆資料 ===')
        try:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            for row in rows:
                print(row)
        except Exception as e:
            print(f'查詢錯誤: {e}')
    
    conn.close()

if __name__ == "__main__":
    check_real_tables()