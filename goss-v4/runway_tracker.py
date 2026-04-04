import sqlite3
import time
from datetime import datetime

DB_PATH = "goss_v4.db"

class RunwayTracker:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.init_runway_table()
    
    def init_runway_table(self):
        """初始化跑道轨迹表"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS runway_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hex TEXT,
            flight TEXT,
            altitude INTEGER,
            ground_speed REAL,
            latitude REAL,
            longitude REAL,
            heading REAL,
            vertical_rate INTEGER,
            timestamp TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        self.conn.commit()
    
    def track_approach_flights(self):
        """追踪4000英尺以下的航班"""
        # 从source_antenna表中获取4000英尺以下的航班数据
        self.cursor.execute('''
        SELECT hex, flight, alt_baro, gs, lat, lon, track, vertical_rate
        FROM source_antenna
        WHERE alt_baro IS NOT NULL AND alt_baro < 4000
        AND lat IS NOT NULL AND lon IS NOT NULL
        ''')
        
        flights = self.cursor.fetchall()
        
        for flight_data in flights:
            hex_code, flight, altitude, ground_speed, latitude, longitude, heading, vertical_rate = flight_data
            
            # 确保数据有效
            if latitude and longitude:
                # 插入或更新跑道轨迹数据
                self.cursor.execute('''
                INSERT OR REPLACE INTO runway_tracks 
                (hex, flight, altitude, ground_speed, latitude, longitude, heading, vertical_rate, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    hex_code,
                    flight,
                    altitude,
                    ground_speed,
                    latitude,
                    longitude,
                    heading,
                    vertical_rate,
                    datetime.now().isoformat()
                ))
        
        self.conn.commit()
        return len(flights)
    
    def get_runway_tracks(self, limit=100):
        """获取跑道轨迹数据"""
        self.cursor.execute('''
        SELECT id, hex, flight, altitude, ground_speed, latitude, longitude, heading, vertical_rate, timestamp
        FROM runway_tracks
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        rows = self.cursor.fetchall()
        return rows
    
    def get_flight_track(self, flight):
        """获取特定航班的轨迹"""
        self.cursor.execute('''
        SELECT id, hex, flight, altitude, ground_speed, latitude, longitude, heading, vertical_rate, timestamp
        FROM runway_tracks
        WHERE flight = ?
        ORDER BY timestamp
        ''', (flight,))
        
        rows = self.cursor.fetchall()
        return rows
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == "__main__":
    tracker = RunwayTracker()
    
    try:
        # 追踪当前4000英尺以下的航班
        tracked_count = tracker.track_approach_flights()
        print(f"已追踪 {tracked_count} 个4000英尺以下的航班")
        
        # 显示最近的跑道轨迹数据
        print("\n最近的跑道轨迹数据:")
        print("id, hex, flight, altitude, ground_speed, latitude, longitude, heading, vertical_rate, timestamp")
        
        tracks = tracker.get_runway_tracks(10)
        for track in tracks:
            print(",".join(str(col) for col in track))
            
    finally:
        tracker.close()