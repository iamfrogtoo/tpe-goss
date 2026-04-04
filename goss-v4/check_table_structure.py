import sqlite3

# 连接数据库
conn = sqlite3.connect('goss_v4.db')
cursor = conn.cursor()

# 查看 live_traffic 表结构
try:
    cursor.execute('PRAGMA table_info(live_traffic)')
    columns = cursor.fetchall()
    print('live_traffic 表结构:')
    for column in columns:
        print(f'列名: {column[1]}, 类型: {column[2]}')
    
    # 查看 source_antenna 表结构
    cursor.execute('PRAGMA table_info(source_antenna)')
    columns = cursor.fetchall()
    print('\nsource_antenna 表结构:')
    for column in columns:
        print(f'列名: {column[1]}, 类型: {column[2]}')
        
    # 查看最新的 source_antenna 数据
    cursor.execute('SELECT * FROM source_antenna ORDER BY updated_at DESC LIMIT 5')
    rows = cursor.fetchall()
    print('\n最新的 source_antenna 数据:')
    for row in rows:
        print(row)
        
except Exception as e:
    print(f'查询错误: {e}')
finally:
    conn.close()