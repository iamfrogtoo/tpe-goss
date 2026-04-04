import requests
import sqlite3
import json
from datetime import datetime

# FlightAware AeroAPI 配置
API_KEY = "DCeSb4fyM1ohoH2EUTJiDqS2Gm9x6duw"
API_BASE_URL = "https://aeroapi.flightaware.com/aeroapi"

# 桃园机场 ICAO 代码
TPE_ICAO = "RCTP"

# 数据库连接函数
def get_db_connection():
    conn = sqlite3.connect('goss_v4.db')
    conn.row_factory = sqlite3.Row
    return conn

# 测试 API 连接
def test_api_connection():
    print("测试 FlightAware AeroAPI 连接...")
    headers = {
        "x-apikey": API_KEY
    }
    
    # 测试端点 - 获取机场信息
    url = f"{API_BASE_URL}/airports/{TPE_ICAO}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        print("API 连接成功！")
        print(f"机场: {data.get('name', '未知')} ({data.get('icao', '未知')})")
        print(f"位置: {data.get('latitude', '未知')}, {data.get('longitude', '未知')}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"API 连接失败: {e}")
        return False

# 获取到达桃园机场的航班
def fetch_arrivals():
    headers = {
        "x-apikey": API_KEY
    }
    
    # 获取当前时间和前后3小时的时间范围
    from datetime import timedelta
    now = datetime.utcnow()
    start_time = (now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_time = (now + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url = f"{API_BASE_URL}/airports/{TPE_ICAO}/flights/arrivals"
    params = {
        "start": start_time,
        "end": end_time,
        "max_pages": 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get('flights', [])
    except requests.exceptions.RequestException as e:
        print(f"获取到达航班失败: {e}")
        return []

# 获取从桃园机场出发的航班
def fetch_departures():
    headers = {
        "x-apikey": API_KEY
    }
    
    # 获取当前时间和前后3小时的时间范围
    from datetime import timedelta
    now = datetime.utcnow()
    start_time = (now - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_time = (now + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    url = f"{API_BASE_URL}/airports/{TPE_ICAO}/flights/departures"
    params = {
        "start": start_time,
        "end": end_time,
        "max_pages": 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get('flights', [])
    except requests.exceptions.RequestException as e:
        print(f"获取出发航班失败: {e}")
        return []

# 处理航班数据并存储到数据库
def process_flights(flights):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    processed_count = 0
    
    for flight in flights:
        try:
            # 提取航班信息
            flight_id = flight.get('identification', {}).get('id', '')
            flight_number = flight.get('identification', {}).get('number', '')
            
            # 获取飞机信息
            aircraft = flight.get('aircraft', {})
            aircraft_registration = aircraft.get('registration', '')
            aircraft_type = aircraft.get('type', {}).get('code', '')
            
            # 获取航线信息
            origin = flight.get('airport', {}).get('origin', {}).get('code', {}).get('icao', '')
            destination = flight.get('airport', {}).get('destination', {}).get('code', {}).get('icao', '')
            
            # 获取时间信息
            departure_time = flight.get('time', {}).get('scheduled', {}).get('departure', '')
            arrival_time = flight.get('time', {}).get('scheduled', {}).get('arrival', '')
            
            # 获取位置信息（如果有）
            position = flight.get('position', {})
            altitude = position.get('altitude', {}).get('feet', 0)
            ground_speed = position.get('speed', {}).get('ground', {}).get('knots', 0)
            heading = position.get('heading', {}).get('degrees_true', 0)
            latitude = position.get('latitude', 0)
            longitude = position.get('longitude', 0)
            
            # 插入或更新数据
            cursor.execute('''
                INSERT OR REPLACE INTO source_flightaware 
                (flight_id, flight_number, aircraft_registration, aircraft_type, 
                 origin, destination, departure_time, arrival_time, 
                 altitude, ground_speed, heading, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                flight_id, flight_number, aircraft_registration, aircraft_type,
                origin, destination, departure_time, arrival_time,
                altitude, ground_speed, heading, latitude, longitude
            ))
            
            processed_count += 1
            
        except Exception as e:
            print(f"处理航班 {flight_number} 失败: {e}")
            continue
    
    conn.commit()
    conn.close()
    return processed_count

# 主函数
def main():
    print("启动 FlightAware 数据获取...")
    
    # 测试 API 连接
    if not test_api_connection():
        print("API 连接失败，退出程序")
        return
    
    # 获取到达航班
    print("获取到达航班数据...")
    arrivals = fetch_arrivals()
    print(f"收到 {len(arrivals)} 个到达航班")
    
    # 获取出发航班
    print("获取出发航班数据...")
    departures = fetch_departures()
    print(f"收到 {len(departures)} 个出发航班")
    
    # 合并航班数据
    all_flights = arrivals + departures
    print(f"总共处理 {len(all_flights)} 个航班")
    
    # 处理并存储数据
    if all_flights:
        processed = process_flights(all_flights)
        print(f"成功处理并存储 {processed} 个航班到 source_flightaware 表")
    else:
        print("没有航班数据需要处理")
    
    print("FlightAware 数据获取完成！")

if __name__ == "__main__":
    main()
