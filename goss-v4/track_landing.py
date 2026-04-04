import sqlite3
import time
import math
from datetime import datetime

DB_PATH = "goss_v4.db"

# 桃园机场坐标
TPE_LAT = 25.077731
TPE_LON = 121.232822

# 降落检测参数
MAX_ALTITUDE_FOR_LANDING = 5000  # 英尺
MIN_DESCENT_RATE = -500  # 英尺/分钟
LANDING_ALTITUDE_THRESHOLD = 100  # 英尺

# 航班状态跟踪
flight_states = {}

class FlightState:
    def __init__(self):
        self.trajectory = []
        self.is_landing = False
        self.landing_time = None
        self.runway = None
        self.last_altitude = None
        self.last_vertical_rate = None

def calculate_distance(lat1, lon1, lat2, lon2):
    """计算两点之间的距离（米）"""
    R = 6371000  # 地球半径（米）
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def get_runway_info():
    """获取跑道信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT runway_code, threshold_lat, threshold_lon, direction FROM runway_info")
    runways = cursor.fetchall()
    conn.close()
    return runways

def detect_landing(flight_no, altitude, vertical_rate, lat, lon):
    """检测航班是否正在降落"""
    if flight_no not in flight_states:
        flight_states[flight_no] = FlightState()
    
    state = flight_states[flight_no]
    
    # 记录轨迹点
    state.trajectory.append({
        'timestamp': datetime.now(),
        'latitude': lat,
        'longitude': lon,
        'altitude': altitude,
        'vertical_rate': vertical_rate
    })
    
    # 限制轨迹点数量，只保留最近的100个点
    if len(state.trajectory) > 100:
        state.trajectory = state.trajectory[-100:]
    
    # 检测降落条件
    if not state.is_landing:
        # 检查是否满足降落条件
        if (altitude is not None and altitude < MAX_ALTITUDE_FOR_LANDING and
            vertical_rate is not None and vertical_rate < MIN_DESCENT_RATE):
            # 可能正在降落
            state.is_landing = True
            print(f"航班 {flight_no} 可能正在降落，高度: {altitude} 英尺，下降率: {vertical_rate} 英尺/分钟")
    
    # 检测降落完成
    if state.is_landing and altitude is not None and altitude < LANDING_ALTITUDE_THRESHOLD:
        if state.landing_time is None:
            state.landing_time = datetime.now()
            print(f"航班 {flight_no} 已降落，时间: {state.landing_time}")
            # 判别跑道
            state.runway = determine_runway(state.trajectory)
            print(f"航班 {flight_no} 降落跑道: {state.runway}")
            # 保存轨迹数据
            save_trajectory(flight_no, state)
    
    # 更新状态
    state.last_altitude = altitude
    state.last_vertical_rate = vertical_rate

def determine_runway(trajectory):
    """基于轨迹数据判别降落跑道"""
    if not trajectory:
        return "未知"
    
    # 获取跑道信息
    runways = get_runway_info()
    
    # 找到轨迹中最低的点（最接近地面的点）
    lowest_point = min(trajectory, key=lambda x: x['altitude'] if x['altitude'] else float('inf'))
    
    # 分析轨迹的最后部分（降落阶段）
    landing_phase = trajectory[-20:] if len(trajectory) >= 20 else trajectory
    
    # 计算轨迹的平均航向
    avg_heading = None
    headings = []
    for i in range(1, len(landing_phase)):
        point = landing_phase[i]
        prev_point = landing_phase[i-1]
        if prev_point['latitude'] != point['latitude'] or prev_point['longitude'] != point['longitude']:
            # 计算两点之间的航向
            dy = point['latitude'] - prev_point['latitude']
            dx = point['longitude'] - prev_point['longitude']
            heading = math.degrees(math.atan2(dx, dy))
            if heading < 0:
                heading += 360
            headings.append(heading)
    
    if headings:
        avg_heading = sum(headings) / len(headings)
    
    # 计算每个跑道的得分
    runway_scores = {}
    for runway in runways:
        runway_code, threshold_lat, threshold_lon, runway_direction = runway
        
        # 计算距离得分（距离越近得分越高）
        distance = calculate_distance(lowest_point['latitude'], lowest_point['longitude'], threshold_lat, threshold_lon)
        distance_score = max(0, 100 - distance / 100)  # 每100米减1分
        
        # 计算航向匹配得分（航向越接近跑道方向得分越高）
        heading_score = 0
        if avg_heading is not None:
            # 计算航向差（考虑360度循环）
            heading_diff = min(abs(avg_heading - runway_direction), 360 - abs(avg_heading - runway_direction))
            heading_score = max(0, 100 - heading_diff * 2)  # 每度减2分
        
        # 计算高度变化得分（下降率越稳定得分越高）
        altitude_score = 0
        if len(landing_phase) >= 2:
            altitude_changes = []
            for i in range(1, len(landing_phase)):
                alt1 = landing_phase[i-1]['altitude']
                alt2 = landing_phase[i]['altitude']
                if alt1 and alt2:
                    altitude_changes.append(alt2 - alt1)
            if altitude_changes:
                avg_descent = sum(altitude_changes) / len(altitude_changes)
                # 理想的下降率在-500到-1000英尺/分钟之间
                if -1000 <= avg_descent <= -500:
                    altitude_score = 100
                elif -1500 <= avg_descent < -1000 or -500 < avg_descent <= -200:
                    altitude_score = 75
                elif -2000 <= avg_descent < -1500 or -200 < avg_descent <= 0:
                    altitude_score = 50
        
        # 综合得分
        total_score = distance_score * 0.5 + heading_score * 0.3 + altitude_score * 0.2
        runway_scores[runway_code] = total_score
    
    # 选择得分最高的跑道
    if runway_scores:
        best_runway = max(runway_scores, key=runway_scores.get)
        return best_runway
    
    return "未知"

def save_trajectory(flight_no, state):
    """保存轨迹数据到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for point in state.trajectory:
        cursor.execute('''
            INSERT INTO flight_trajectory 
            (flight_no, timestamp, latitude, longitude, altitude, ground_speed, heading, vertical_rate, source, runway, is_landing, landing_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            flight_no,
            point['timestamp'],
            point['latitude'],
            point['longitude'],
            point['altitude'],
            None,  # 暂时没有地速数据
            None,  # 暂时没有航向数据
            point['vertical_rate'],
            'SYSTEM',
            state.runway,
            1 if state.is_landing else 0,
            state.landing_time
        ))
    
    conn.commit()
    conn.close()
    print(f"已保存航班 {flight_no} 的轨迹数据")

def track_landing_process():
    """主追踪流程"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 获取所有入境航班的实时数据
        cursor.execute("""
            SELECT lt.flight_no, sa.lat, sa.lon, sa.alt_baro, sa.vertical_rate
            FROM live_traffic lt
            JOIN source_antenna sa ON lt.hex = sa.hex
            WHERE lt.source = 'LOCAL' AND lt.flight_no IS NOT NULL
        """)
        
        flights = cursor.fetchall()
        
        for flight in flights:
            flight_no, lat, lon, altitude, vertical_rate = flight
            if lat and lon and altitude is not None:
                detect_landing(flight_no, altitude, vertical_rate, lat, lon)
        
        # 处理OpenSky数据
        cursor.execute("""
            SELECT lt.flight_no, so.latitude, so.longitude, so.baro_altitude, so.vertical_rate
            FROM live_traffic lt
            JOIN source_opensky so ON lt.hex = so.icao24
            WHERE lt.source = 'OPENSKY' AND lt.flight_no IS NOT NULL AND lt.hex NOT IN (SELECT hex FROM source_antenna)
        """)
        
        os_flights = cursor.fetchall()
        
        for flight in os_flights:
            flight_no, lat, lon, altitude, vertical_rate = flight
            if lat and lon and altitude is not None:
                detect_landing(flight_no, altitude, vertical_rate, lat, lon)
                
    except Exception as e:
        print(f"追踪降落过程时出错: {e}")
    finally:
        conn.close()

def cleanup_old_states():
    """清理长时间无更新的航班状态"""
    current_time = time.time()
    to_remove = []
    
    for flight_no, state in flight_states.items():
        if state.trajectory:
            last_update = state.trajectory[-1]['timestamp'].timestamp()
            if current_time - last_update > 3600:  # 1小时无更新
                to_remove.append(flight_no)
    
    for flight_no in to_remove:
        del flight_states[flight_no]
        print(f"清理航班 {flight_no} 的状态")

if __name__ == "__main__":
    print("开始追踪航班降落过程...")
    
    while True:
        track_landing_process()
        cleanup_old_states()
        time.sleep(5)  # 每5秒检查一次