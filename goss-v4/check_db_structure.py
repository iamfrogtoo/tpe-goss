import sqlite3

def check_database_structure():
    """檢查資料庫結構"""
    conn = sqlite3.connect('goss_v4.db')
    cursor = conn.cursor()
    
    # 檢查所有表格
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("=== 資料庫表格列表 ===")
    for table in tables:
        table_name = table[0]
        print(f"\n表格: {table_name}")
        
        # 檢查表格欄位
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == "__main__":
    check_database_structure()