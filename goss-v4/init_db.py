import sqlite3

def init_db():
    conn = sqlite3.connect('goss_v4.db')
    cursor = conn.cursor()
    
    # 核心表 - 实时交通
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_traffic (
            hex TEXT PRIMARY KEY,
            flight_no TEXT,
            alt TEXT,
            gs REAL,
            gate TEXT,
            is_cargo INTEGER,
            source TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 核心表 - 航班计划
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flight_schedule (
            flight_no TEXT PRIMARY KEY,
            direction TEXT,
            gate TEXT,
            scheduled_time TEXT,
            actual_time TEXT,
            status TEXT,
            is_cargo INTEGER,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 分区表 - 机场数据
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS source_airport (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_no TEXT,
            direction TEXT,
            gate TEXT,
            scheduled_time TEXT,
            actual_time TEXT,
            status TEXT,
            is_cargo INTEGER,
            terminal TEXT,
            airline TEXT,
            aircraft_type TEXT,
            date TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 分区表 - OpenSky 数据
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS source_opensky (
            icao24 TEXT PRIMARY KEY,
            callsign TEXT,
            baro_altitude REAL,
            velocity REAL,
            latitude REAL,
            longitude REAL,
            heading REAL,
            vertical_rate REAL,
            squawk TEXT,
            origin TEXT,
            destination TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 分区表 - 天线数据（本地 ADS-B）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS source_antenna (
            hex TEXT PRIMARY KEY,
            flight TEXT,
            alt_baro INTEGER,
            gs REAL,
            lat REAL,
            lon REAL,
            track REAL,
            vertical_rate INTEGER,
            squawk TEXT,
            category TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 分区表 - FR24 数据
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS source_fr24 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_number TEXT,
            aircraft_code TEXT,
            airline TEXT,
            altitude INTEGER,
            ground_speed INTEGER,
            heading INTEGER,
            latitude REAL,
            longitude REAL,
            vertical_speed INTEGER,
            squawk TEXT,
            registration TEXT,
            origin TEXT,
            destination TEXT,
            aircraft_type TEXT,
            fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 分区表 - FlightAware 数据
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS source_flightaware (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id TEXT,
            flight_number TEXT,
            aircraft_registration TEXT,
            aircraft_type TEXT,
            origin TEXT,
            destination TEXT,
            departure_time TEXT,
            arrival_time TEXT,
            altitude INTEGER,
            ground_speed INTEGER,
            heading INTEGER,
            latitude REAL,
            longitude REAL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 分区表 - 华航邮件数据
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS source_calair (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_no TEXT,
            flight_date TEXT,
            departure_time TEXT,
            arrival_time TEXT,
            origin TEXT,
            destination TEXT,
            aircraft_type TEXT,
            gate TEXT,
            status TEXT,
            remarks TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 分区表 - 轨迹数据
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flight_trajectory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_no TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            latitude REAL,
            longitude REAL,
            altitude INTEGER,
            ground_speed REAL,
            heading REAL,
            vertical_rate INTEGER,
            source TEXT,
            runway TEXT,
            is_landing INTEGER DEFAULT 0,
            landing_time DATETIME
        )
    ''')
    
    # 分区表 - 跑道信息
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS runway_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            runway_code TEXT,
            threshold_lat REAL,
            threshold_lon REAL,
            direction REAL,
            length REAL,
            width REAL,
            elevation REAL
        )
    ''')
    
    # 初始化桃园机场跑道信息
    runways = [
        ('05L', 25.0875, 121.2400, 50, 3800, 60, 30),
        ('05R', 25.0880, 121.2450, 50, 3800, 60, 30),
        ('23L', 25.0675, 121.2300, 230, 3800, 60, 30),
        ('23R', 25.0680, 121.2250, 230, 3800, 60, 30)
    ]
    
    for runway in runways:
        cursor.execute('''
            INSERT OR IGNORE INTO runway_info 
            (runway_code, threshold_lat, threshold_lon, direction, length, width, elevation)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', runway)
    
    # 创建索引以提高查询性能
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_live_traffic_flight ON live_traffic(flight_no)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_flight_schedule_flight ON flight_schedule(flight_no)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_airport_flight ON source_airport(flight_no)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_opensky_callsign ON source_opensky(callsign)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_antenna_flight ON source_antenna(flight)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_fr24_flight ON source_fr24(flight_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_flightaware_flight ON source_flightaware(flight_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_calair_flight ON source_calair(flight_no)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_flight_trajectory_flight ON flight_trajectory(flight_no)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_flight_trajectory_landing ON flight_trajectory(is_landing)')
    
    conn.commit()
    conn.close()
    print("goss_v4.db 分区架构初始化完成！")

if __name__ == "__main__":
    init_db()