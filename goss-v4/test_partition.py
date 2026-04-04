import sqlite3
import time

def test_database_structure():
    """测试数据库结构是否正确创建"""
    conn = sqlite3.connect('goss_v4.db')
    cursor = conn.cursor()
    
    # 检查所有表是否存在
    tables = ['live_traffic', 'flight_schedule', 'source_airport', 'source_opensky', 'source_antenna', 'source_fr24', 'source_flightaware', 'source_calair']
    
    print("📋 检查数据库表结构...")
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
        result = cursor.fetchone()
        if result:
            print(f"✅ {table} 表存在")
        else:
            print(f"❌ {table} 表不存在")
    
    # 检查索引是否存在
    print("\n🔍 检查索引...")
    indexes = [
        'idx_live_traffic_flight',
        'idx_flight_schedule_flight',
        'idx_source_airport_flight',
        'idx_source_opensky_callsign',
        'idx_source_antenna_flight',
        'idx_source_fr24_flight',
        'idx_source_flightaware_flight',
        'idx_source_calair_flight'
    ]
    
    for idx in indexes:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{idx}';")
        result = cursor.fetchone()
        if result:
            print(f"✅ {idx} 索引存在")
        else:
            print(f"❌ {idx} 索引不存在")
    
    conn.close()

def test_data_insertion():
    """测试数据插入功能"""
    conn = sqlite3.connect('goss_v4.db')
    cursor = conn.cursor()
    
    print("\n📊 测试数据插入...")
    
    # 测试插入机场数据
    try:
        cursor.execute('''
            INSERT INTO source_airport 
            (flight_no, direction, gate, scheduled_time, is_cargo, terminal, airline, aircraft_type, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('CI001', 'A', 'A1', '12:00', 0, 'T1', 'CI', 'A320', '2026-03-29'))
        print("✅ 机场数据插入成功")
    except Exception as e:
        print(f"❌ 机场数据插入失败: {e}")
    
    # 测试插入OpenSky数据
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO source_opensky 
            (icao24, callsign, baro_altitude, velocity, latitude, longitude, heading, vertical_rate, squawk)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('A12345', 'CI001', 30000, 450, 25.079, 121.234, 90, 0, '1234'))
        print("✅ OpenSky数据插入成功")
    except Exception as e:
        print(f"❌ OpenSky数据插入失败: {e}")
    
    # 测试插入天线数据
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO source_antenna 
            (hex, flight, alt_baro, gs, lat, lon, track, vertical_rate, squawk, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('A12345', 'CI001', 30000, 450, 25.079, 121.234, 90, 0, '1234', 'A3'))
        print("✅ 天线数据插入成功")
    except Exception as e:
        print(f"❌ 天线数据插入失败: {e}")
    
    # 测试插入FR24数据
    try:
        cursor.execute('''
            INSERT INTO source_fr24 
            (flight_number, aircraft_code, airline, altitude, ground_speed, heading, latitude, longitude, vertical_speed, squawk, registration, origin, destination, aircraft_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('CI001', 'A320', 'China Airlines', 30000, 450, 90, 25.079, 121.234, 0, '1234', 'B-1234', 'TPE', 'HKG', 'A320'))
        print("✅ FR24数据插入成功")
    except Exception as e:
        print(f"❌ FR24数据插入失败: {e}")
    
    conn.commit()
    conn.close()

def test_data_query():
    """测试数据查询功能"""
    conn = sqlite3.connect('goss_v4.db')
    cursor = conn.cursor()
    
    print("\n🔎 测试数据查询...")
    
    # 测试查询机场数据
    cursor.execute("SELECT * FROM source_airport LIMIT 5;")
    airport_data = cursor.fetchall()
    print(f"✅ 机场数据: {len(airport_data)} 条")
    
    # 测试查询OpenSky数据
    cursor.execute("SELECT * FROM source_opensky LIMIT 5;")
    opensky_data = cursor.fetchall()
    print(f"✅ OpenSky数据: {len(opensky_data)} 条")
    
    # 测试查询天线数据
    cursor.execute("SELECT * FROM source_antenna LIMIT 5;")
    antenna_data = cursor.fetchall()
    print(f"✅ 天线数据: {len(antenna_data)} 条")
    
    # 测试查询FR24数据
    cursor.execute("SELECT * FROM source_fr24 LIMIT 5;")
    fr24_data = cursor.fetchall()
    print(f"✅ FR24数据: {len(fr24_data)} 条")
    
    # 测试查询实时交通数据
    cursor.execute("SELECT * FROM live_traffic LIMIT 5;")
    live_data = cursor.fetchall()
    print(f"✅ 实时交通数据: {len(live_data)} 条")
    
    # 测试查询航班计划数据
    cursor.execute("SELECT * FROM flight_schedule LIMIT 5;")
    schedule_data = cursor.fetchall()
    print(f"✅ 航班计划数据: {len(schedule_data)} 条")
    
    conn.close()

def test_data_integration():
    """测试数据整合功能"""
    conn = sqlite3.connect('goss_v4.db')
    cursor = conn.cursor()
    
    print("\n🔄 测试数据整合...")
    
    # 测试通过航班号关联不同数据源
    cursor.execute('''
        SELECT a.flight_no, a.gate, a.scheduled_time, 
               o.icao24, o.baro_altitude, o.velocity,
               ant.alt_baro, ant.gs
        FROM source_airport a
        LEFT JOIN source_opensky o ON a.flight_no = o.callsign
        LEFT JOIN source_antenna ant ON o.icao24 = ant.hex
        LIMIT 5;
    ''')
    integration_data = cursor.fetchall()
    print(f"✅ 数据整合结果: {len(integration_data)} 条")
    
    conn.close()

if __name__ == "__main__":
    print("🚀 开始测试分区式数据库架构...")
    
    # 首先初始化数据库
    import init_db
    init_db.init_db()
    
    # 测试数据库结构
    test_database_structure()
    
    # 测试数据插入
    test_data_insertion()
    
    # 测试数据查询
    test_data_query()
    
    # 测试数据整合
    test_data_integration()
    
    print("\n✅ 所有测试完成！")
