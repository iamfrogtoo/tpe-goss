import requests
import sqlite3
import time
import logging
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='fr24_fetch.log'
)
logger = logging.getLogger('fr24_fetcher')

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect('goss_v4.db')
    cursor = conn.cursor()
    
    # 创建 FR24 航班表（分区表）
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
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_fr24_flight ON source_fr24(flight_number)')
    
    conn.commit()
    conn.close()

def fetch_fr24_data():
    """从 FR24 获取指定区域的航班数据"""
    try:
        # 定义桃园机场跑道附近区域的边界框
        # 基于桃园机场实际位置调整，确保覆盖跑道及其周围区域
        # 格式: min_lat, min_lon, max_lat, max_lon
        min_lat = 25.0
        min_lon = 121.15
        max_lat = 25.15
        max_lon = 121.3
        
        logger.info(f"开始抓取 FR24 数据，区域: {min_lat}, {min_lon}, {max_lat}, {max_lon}")
        print(f"开始抓取 FR24 数据，区域: {min_lat}, {min_lon}, {max_lat}, {max_lon}")
        
        # 尝试不同的 API 端点
        endpoints = [
            "https://data.flightradar24.com/zones/fcgi/feed.js",
            "https://www.flightradar24.com/static/legacy/feed.json"
        ]
        
        data = None
        for url in endpoints:
            print(f"尝试 API 端点: {url}")
            # 设置请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.flightradar24.com/'
            }
            
            try:
                # 发送请求
                response = requests.get(url, headers=headers, timeout=10)
                print(f"响应状态码: {response.status_code}")
                
                # 解析响应数据
                data = response.json()
                print(f"收到响应数据，包含 {len(data)} 个条目")
                break
            except Exception as e:
                print(f"使用端点 {url} 时出错: {str(e)}")
                continue
        
        if not data:
            print("所有 API 端点都失败了")
            logger.error("所有 API 端点都失败了")
            return
        
        # 处理航班数据
        flights = []
        for key, value in data.items():
            if key == 'full_count' or key == 'version':
                print(f"跳过非航班数据: {key} = {value}")
                continue
            
            # 提取航班信息
            flight_data = value
            if len(flight_data) >= 12:
                # 检查航班是否在指定区域内
                longitude = flight_data[1]
                latitude = flight_data[2]
                
                print(f"检查航班: {key} - 位置: {latitude}, {longitude}")
                
                if (latitude >= min_lat and latitude <= max_lat and
                    longitude >= min_lon and longitude <= max_lon):
                    
                    flight = {
                        'longitude': longitude,
                        'latitude': latitude,
                        'altitude': flight_data[4],
                        'ground_speed': flight_data[5],
                        'heading': flight_data[3],
                        'vertical_speed': flight_data[6],
                        'squawk': flight_data[7],
                        'aircraft_code': flight_data[8] if len(flight_data) > 8 else 'N/A',
                        'registration': flight_data[9] if len(flight_data) > 9 else 'N/A',
                        'origin': flight_data[10] if len(flight_data) > 10 else 'N/A',
                        'destination': flight_data[11] if len(flight_data) > 11 else 'N/A',
                        'airline': flight_data[12] if len(flight_data) > 12 else 'N/A',
                        'flight_number': flight_data[13] if len(flight_data) > 13 else 'N/A'
                    }
                    flights.append(flight)
                    print(f"添加航班: {flight['flight_number']}")
                else:
                    print(f"跳过区域外航班: {key} - 位置: {latitude}, {longitude}")
            else:
                print(f"跳过不完整的航班数据: {key} = {value}")
        
        logger.info(f"成功获取 {len(flights)} 个航班")
        print(f"成功获取 {len(flights)} 个航班")
        
        # 显示航班数据
        if flights:
            print("\n抓取到的航班数据:")
            print("-" * 80)
            for flight in flights:
                print(f"航班号: {flight['flight_number']}")
                print(f"飞机代码: {flight['aircraft_code']}")
                print(f"航空公司: {flight['airline']}")
                print(f"高度: {flight['altitude']} 英尺")
                print(f"速度: {flight['ground_speed']} 节")
                print(f"航向: {flight['heading']}°")
                print(f"位置: {flight['latitude']}, {flight['longitude']}")
                print(f"垂直速度: {flight['vertical_speed']}")
                print(f"应答机: {flight['squawk']}")
                print(f"注册号: {flight['registration']}")
                print(f"出发地: {flight['origin']}")
                print(f"目的地: {flight['destination']}")
                print("-" * 80)
        
        # 存储数据到数据库
        conn = sqlite3.connect('goss_v4.db')
        cursor = conn.cursor()
        
        for flight in flights:
            try:
                # 插入数据到分区表
                cursor.execute('''
                INSERT INTO source_fr24 (
                    flight_number, aircraft_code, airline, altitude, ground_speed, 
                    heading, latitude, longitude, vertical_speed, squawk, 
                    registration, origin, destination, aircraft_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    flight['flight_number'],
                    flight['aircraft_code'],
                    flight['airline'],
                    flight['altitude'],
                    flight['ground_speed'],
                    flight['heading'],
                    flight['latitude'],
                    flight['longitude'],
                    flight['vertical_speed'],
                    flight['squawk'],
                    flight['registration'],
                    flight['origin'],
                    flight['destination'],
                    flight['aircraft_code']  # 使用 aircraft_code 作为 aircraft_type
                ))
                
            except Exception as e:
                logger.error(f"处理航班 {flight['flight_number']} 时出错: {str(e)}")
                print(f"处理航班 {flight['flight_number']} 时出错: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        
        logger.info("数据存储完成")
        print("数据存储完成")
        
    except Exception as e:
        logger.error(f"抓取 FR24 数据时出错: {str(e)}")
        print(f"抓取 FR24 数据时出错: {str(e)}")

def main():
    """主函数"""
    print("初始化数据库...")
    init_db()
    print("开始抓取 FR24 数据...")
    fetch_fr24_data()
    print("抓取完成!")

if __name__ == "__main__":
    main()