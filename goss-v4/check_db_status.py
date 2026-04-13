import sqlite3
import sys

def check_db_status():
    conn = sqlite3.connect('goss_v4.db')
    cursor = conn.cursor()
    
    # 查看所有表格
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('資料庫中的表格:')
    for table in tables:
        print(f'- {table[0]}')
    
    # 檢查 flight_schedule 表的狀態欄位
    print('\n檢查 flight_schedule 表狀態欄位:')
    try:
        cursor.execute("SELECT flight_number, status FROM flight_schedule WHERE status IS NOT NULL LIMIT 10")
        rows = cursor.fetchall()
        print(f'找到 {len(rows)} 筆有狀態的航班:')
        for row in rows:
            flight_num, status = row
            print(f'航班: {flight_num}, 狀態: {repr(status)}')
    except Exception as e:
        print(f'查詢 flight_schedule 狀態錯誤: {e}')
    
    # 檢查 source_airport 表的狀態欄位
    print('\n檢查 source_airport 表狀態欄位:')
    try:
        cursor.execute("SELECT flight_number, status FROM source_airport WHERE status IS NOT NULL LIMIT 10")
        rows = cursor.fetchall()
        print(f'找到 {len(rows)} 筆有狀態的航班:')
        for row in rows:
            flight_num, status = row
            print(f'航班: {flight_num}, 狀態: {repr(status)}')
    except Exception as e:
        print(f'查詢 source_airport 狀態錯誤: {e}')
    
    # 檢查亂碼問題
    print('\n檢查可能的亂碼狀態:')
    try:
        cursor.execute("SELECT flight_number, status FROM flight_schedule WHERE status LIKE '%�%' OR status LIKE '%?%' LIMIT 10")
        rows = cursor.fetchall()
        print(f'找到 {len(rows)} 筆可能有亂碼的狀態:')
        for row in rows:
            flight_num, status = row
            print(f'航班: {flight_num}, 狀態: {repr(status)}')
    except Exception as e:
        print(f'查詢亂碼狀態錯誤: {e}')
    
    conn.close()

if __name__ == "__main__":
    check_db_status()