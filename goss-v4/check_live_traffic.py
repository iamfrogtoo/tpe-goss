import sqlite3

# 连接数据库
conn = sqlite3.connect('goss_v4.db')
cursor = conn.cursor()

# 查询最新的实时交通数据
try:
    cursor.execute('SELECT flight, updated_at FROM live_traffic ORDER BY updated_at DESC LIMIT 10')
    rows = cursor.fetchall()
    
    print('最新的实时交通数据:')
    for row in rows:
        print(row)
    
    # 检查 CPA450 的最新数据
    cursor.execute('SELECT flight, updated_at, alt, gs, lat, lon FROM live_traffic WHERE flight = ?', ('CPA450',))
    cpa450_data = cursor.fetchone()
    if cpa450_data:
        print('\nCPA450 的最新数据:')
        print(f'航班: {cpa450_data[0]}')
        print(f'更新时间: {cpa450_data[1]}')
        print(f'高度: {cpa450_data[2]}')
        print(f'速度: {cpa450_data[3]}')
        print(f'纬度: {cpa450_data[4]}')
        print(f'经度: {cpa450_data[5]}')
    else:
        print('\nCPA450 没有最新数据')
        
    # 统计数据量
    cursor.execute('SELECT COUNT(*) FROM live_traffic')
    count = cursor.fetchone()[0]
    print(f'\n总实时交通数据量: {count}')
    
except Exception as e:
    print(f'查询错误: {e}')
finally:
    conn.close()