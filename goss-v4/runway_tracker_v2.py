import sqlite3
import time
from datetime import datetime
import math

DB_PATH = "goss_v4.db"

# 桃园机场跑道坐标
RUNWAYS = {
    "05L": {"start": (25.0777, 121.2328), "end": (25.0877, 121.2528), "heading": 50},
    "05R": {"start": (25.0767, 121.2318), "end": (25.0867, 121.2518), "heading": 50},
    "23L": {"start": (25.0877, 121.2528), "end": (25.0777, 121.2328), "heading": 230},
    "23R": {"start": (25.0867, 121.2518), "end": (25.0767, 121.2318), "heading": 230}
}

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
            runway TEXT,
            distance_to_runway REAL,
            timestamp TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        self.conn.commit()
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """计算两点之间的距离（公里）"""
        R = 6371  # 地球半径
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        return distance
    
    def identify_runway(self, latitude, longitude, heading):
        """识别航班正在接近的跑道"""
        closest_runway = None
        min_distance = None
        
        for runway, data in RUNWAYS.items():
            # 计算到跑道起点的距离
            distance = self.calculate_distance(latitude, longitude, data["start"][0], data["start"][1])
            
            # 检查航向是否匹配
            heading_diff = abs(heading - data["heading"])
            if heading_diff > 180:
                heading_diff = 360 - heading_diff
            
            # 如果距离小于3公里且航向差小于30度，认为是在接近该跑道
            if distance < 3 and heading_diff < 30:
                if min_distance is None or distance < min_distance:
                    min_distance = distance
                    closest_runway = runway
        
        return closest_runway, min_distance
    
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
            if latitude and longitude and heading:
                # 识别跑道
                runway_result = self.identify_runway(latitude, longitude, heading)
                runway = str(runway_result[0]) if runway_result[0] else None
                distance_to_runway = float(runway_result[1]) if runway_result[1] and runway_result[1] != float('inf') else None
                
                # 插入或更新跑道轨迹数据
                self.cursor.execute('''
                INSERT OR REPLACE INTO runway_tracks 
                (hex, flight, altitude, ground_speed, latitude, longitude, heading, vertical_rate, runway, distance_to_runway, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    hex_code or '',
                    flight or '',
                    altitude or None,
                    ground_speed or None,
                    latitude or None,
                    longitude or None,
                    heading or None,
                    vertical_rate or None,
                    runway,
                    distance_to_runway,
                    datetime.now().isoformat()
                ))
        
        self.conn.commit()
        return len(flights)
    
    def get_runway_tracks(self, limit=100):
        """获取跑道轨迹数据"""
        self.cursor.execute('''
        SELECT id, hex, flight, altitude, ground_speed, latitude, longitude, heading, vertical_rate, runway, distance_to_runway, timestamp
        FROM runway_tracks
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        rows = self.cursor.fetchall()
        return rows
    
    def get_flight_track(self, flight):
        """获取特定航班的轨迹"""
        self.cursor.execute('''
        SELECT id, hex, flight, altitude, ground_speed, latitude, longitude, heading, vertical_rate, runway, distance_to_runway, timestamp
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
        print("id, hex, flight, altitude, ground_speed, latitude, longitude, heading, vertical_rate, runway, distance_to_runway, timestamp")
        
        tracks = tracker.get_runway_tracks(10)
        for track in tracks:
            print(",".join(str(col) for col in track))
            
    finally:
        tracker.close()