import sqlite3

# 连接数据库
conn = sqlite3.connect('goss_v4.db')
cursor = conn.cursor()

# 查询 source_antenna 表
try:
    cursor.execute('SELECT * FROM source_antenna LIMIT 10')
    rows = cursor.fetchall()
    
    print('天线航班数据:')
    print('hex, flight, alt_baro, gs, lat, lon, track, vertical_rate, squawk, category')
    for row in rows:
        print(','.join(str(col) for col in row))
    
    # 统计数据量
    cursor.execute('SELECT COUNT(*) FROM source_antenna')
    count = cursor.fetchone()[0]
    print(f'\n总记录数: {count}')
    
except Exception as e:
    print(f'查询错误: {e}')
finally:
    conn.close()