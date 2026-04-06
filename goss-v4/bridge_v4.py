import requests
import sqlite3
import time
import os
import json
from datetime import datetime, timedelta

DB_PATH = "goss_v4.db"
LOCAL_URL = "http://192.168.31.221:8080/data/aircraft.json"
# 調整OpenSky URL以符合指定的座標範圍
OPENSKY_URL = "https://opensky-network.org/api/states/all?lamin=24.0&lomin=120.0&lamax=26.0&lomax=122.5"

# FlightAware AeroAPI 配置
FLIGHTAWARE_API_KEY = "DCeSb4fyM1ohoH2EUTJiDqS2Gm9x6duw"
FLIGHTAWARE_API_BASE_URL = "https://aeroapi.flightaware.com/aeroapi"
TPE_ICAO = "RCTP"

# OpenSky OAuth2 認證設定
CREDENTIALS_FILE = 'credentials.json'
CURRENT_TOKEN = None
TOKEN_EXPIRY = 0

# 追踪航班的最後更新時間，用於處理OpenSky訊號暫時消失的情況
flight_last_seen = {}

# 定義天線範圍
LAMIN = 24.0
LOMIN = 120.0
LAMAX = 26.0
LOMAX = 122.5

# 偏北50公里的範圍調整
# 1度緯度約等於111公里，所以50公里約等於0.45度
ADJUSTED_LAMIN = LAMIN - 0.45


def load_opensky_creds():
    """讀取 credentials.json，支援 clientId/clientSecret (OAuth2) """
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                c = json.load(f)
                return c.get('clientId'), c.get('clientSecret')
        except:
            pass
    return None, None

def get_access_token(client_id, client_secret):
    """用 OAuth2 client credentials 取得 access token """
    token_url = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
    payload = {'grant_type': 'client_credentials'}
    try:
        r = requests.post(token_url, data=payload, auth=(client_id, client_secret), timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get('access_token'), data.get('expires_in', 300)
        else:
            print(f"[OAuth2] 取得 token 失敗: {r.status_code}")
    except Exception as e:
        print(f"[OAuth2] 連線錯誤: {e}")
    return None, 0

def get_opensky_data():
    """使用 OAuth2 Bearer Token 抓取 OpenSky 資料 """
    global CURRENT_TOKEN, TOKEN_EXPIRY

    client_id, client_secret = load_opensky_creds()

    # 檢查 token 是否過期或不存在
    if CURRENT_TOKEN is None or time.time() > TOKEN_EXPIRY:
        if client_id and client_secret:
            CURRENT_TOKEN, expires_in = get_access_token(client_id, client_secret)
            TOKEN_EXPIRY = time.time() + expires_in - 30  # 提前30秒過期
        else:
            print("使用匿名模式 (建議設定 credentials.json)")

    headers = {'Authorization': f'Bearer {CURRENT_TOKEN}'} if CURRENT_TOKEN else {}

    try:
        r = requests.get(OPENSKY_URL, headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json().get('states', [])
        elif r.status_code == 401:
            # Token 過期，重新取得
            print("OpenSky Token 過期，重新取得...")
            CURRENT_TOKEN = None
            return get_opensky_data()  # 遞迴重試
        elif r.status_code == 429:
            print(f"OpenSky 請求過於頻繁 (429)")
            return []
        else:
            print(f"OpenSky 連線失敗: {r.status_code}")
    except Exception as e:
        print(f"OpenSky 連線錯誤: {e}")
    return []

def get_flightaware_data():
    """抓取 FlightAware 資料 """
    headers = {
        "x-apikey": FLIGHTAWARE_API_KEY
    }
    
    # 桃园机场坐标和350公里范围
    tpe_lat = 25.077731
    tpe_lon = 121.232822
    radius_km = 350
    
    # 计算经纬度范围（1度纬度约111公里，1度经度在25度纬度约100公里）
    lat_range = radius_km / 111
    lon_range = radius_km / 100
    
    min_lat = tpe_lat - lat_range
    max_lat = tpe_lat + lat_range
    min_lon = tpe_lon - lon_range
    max_lon = tpe_lon + lon_range
    
    all_flights = []
    
    # 获取指定范围内的航班
    try:
        url = f"{FLIGHTAWARE_API_BASE_URL}/flights/position"
        params = {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon,
            "max_pages": 1
        }
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            all_flights = response.json().get('flights', [])
        elif response.status_code == 429:
            print("FlightAware API 请求过于频繁，暂时跳过")
            return []
    except Exception as e:
        print(f"获取FlightAware航班失败: {e}")
    
    return all_flights

def is_within_antenna_range(lat, lon):
    """檢查飛機是否在天線範圍內"""
    return ADJUSTED_LAMIN <= lat <= LAMAX and LOMIN <= lon <= LOMAX

def is_arrival_flight(flight_no):
    """檢查是否為入境航班"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT direction FROM flight_schedule WHERE flight_no = ?", (flight_no,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 'A'

def fusion_engine():
    global flight_last_seen
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 抓取本地天線數據 (優先)
    local_count = 0
    try:
        res = requests.get(LOCAL_URL, timeout=1).json()
        for ac in res.get('aircraft', []):
            hex_code = ac.get('hex')
            flight = ac.get('flight', '').strip()

            # 檢查是否在天線範圍內
            lat = ac.get('lat')
            lon = ac.get('lon')
            if lat and lon and not is_within_antenna_range(lat, lon):
                # 不在範圍內的飛機，跳過
                continue

            # 寫入天線分區表
            cursor.execute('''
                INSERT OR REPLACE INTO source_antenna
                (hex, flight, alt_baro, gs, lat, lon, track, vertical_rate, squawk, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                hex_code,
                flight,
                ac.get('alt_baro'),
                ac.get('gs'),
                ac.get('lat'),
                ac.get('lon'),
                ac.get('track'),
                ac.get('vert_rate'),
                ac.get('squawk'),
                ac.get('category')
            ))

            # 查班表
            cursor.execute("SELECT gate, is_cargo FROM flight_schedule WHERE flight_no = ?", (flight,))
            sch = cursor.fetchone()
            gate, is_cargo = (sch[0], sch[1]) if sch else ("TBD", 0)

            # 更新到實時交通表
            cursor.execute('''
                INSERT OR REPLACE INTO live_traffic
                (hex, flight_no, alt, gs, gate, is_cargo, source, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 'LOCAL', CURRENT_TIMESTAMP)
            ''', (
                hex_code,
                flight,
                str(ac.get('alt_baro')),
                ac.get('gs'),
                gate,
                is_cargo
            ))
            
            # 更新航班最後看見時間
            if flight:
                flight_last_seen[flight] = time.time()
                
            local_count += 1
    except Exception as e:
        print(f"本地天線數據抓取失敗: {e}")

    # 2. 抓取OpenSky數據 (補位)
    os_count = 0
    states = get_opensky_data()

    if states:
        for s in states:
            icao = s[0].upper()
            callsign = s[1].strip() if s[1] else ""
            
            # 檢查本地是否已有數據
            cursor.execute("SELECT source FROM live_traffic WHERE hex = ? AND source = 'LOCAL'", (icao,))
            if not cursor.fetchone():
                # 檢查是否在天線範圍內
                lat = s[6]
                lon = s[5]
                if lat and lon and not is_within_antenna_range(lat, lon):
                    # 不在範圍內的飛機，跳過
                    continue
                
                # 寫入OpenSky分區表
                squawk_value = s[14] if len(s) > 14 else None
                cursor.execute('INSERT OR REPLACE INTO source_opensky (icao24, callsign, baro_altitude, velocity, latitude, longitude, heading, vertical_rate, squawk) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (icao, callsign, s[7], s[9], s[6], s[5], s[10], s[11], squawk_value))

                # 查班表
                cursor.execute("SELECT gate, is_cargo FROM flight_schedule WHERE flight_no = ?", (callsign,))
                sch = cursor.fetchone()
                gate, is_cargo = (sch[0], sch[1]) if sch else ("TBD", 0)

                # 轉換單位：高度(公尺->英尺), 速度(公尺/秒->節)
                alt_ft = int(s[7] * 3.28084) if s[7] is not None else ""
                gs_kt = int(s[9] * 1.94384) if s[9] is not None else 0

                # 更新到實時交通表
                cursor.execute('''
                    INSERT OR REPLACE INTO live_traffic
                    (hex, flight_no, alt, gs, gate, is_cargo, source, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 'OPENSKY', CURRENT_TIMESTAMP)
                ''', (
                    icao,
                    callsign,
                    str(alt_ft) if alt_ft else "",
                    gs_kt,
                    gate,
                    is_cargo
                ))
                
                # 更新航班最後看見時間
                if callsign:
                    flight_last_seen[callsign] = time.time()
                    
                os_count += 1

    # 3. 抓取FlightAware數據 (補位)
    fa_count = 0
    # [V4調整] 暫時停用 FlightAware 抓取，做為本地天線故障時的備案
    fa_flights = [] # get_flightaware_data()

    if fa_flights:
        # 获取本地入境航班列表
        cursor.execute("SELECT flight_no FROM flight_schedule WHERE direction = 'A'")
        arrival_flights = [row[0] for row in cursor.fetchall()]
        
        for flight in fa_flights:
            try:
                # 提取航班信息
                flight_id = flight.get('identification', {}).get('id', '')
                flight_number = flight.get('identification', {}).get('number', '').strip()
                
                # 只处理入境航班列表中的航班
                if flight_number not in arrival_flights:
                    continue
                
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
                
                # 检查本地和OpenSky是否已有数据
                cursor.execute("SELECT source FROM live_traffic WHERE flight_no = ? AND (source = 'LOCAL' OR source = 'OPENSKY')", (flight_number,))
                if not cursor.fetchone() and flight_number:
                    # 检查是否在天线范围内
                    if latitude and longitude and is_within_antenna_range(latitude, longitude):
                        # 写入FlightAware分區表
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

                        # 查班表
                        cursor.execute("SELECT gate, is_cargo FROM flight_schedule WHERE flight_no = ?", (flight_number,))
                        sch = cursor.fetchone()
                        gate, is_cargo = (sch[0], sch[1]) if sch else ("TBD", 0)

                        # 更新到實時交通表
                        cursor.execute('''
                            INSERT OR REPLACE INTO live_traffic
                            (hex, flight_no, alt, gs, gate, is_cargo, source, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, 'FLIGHTAWARE', CURRENT_TIMESTAMP)
                        ''', (
                            f"FA_{flight_number}",  # 使用航班号作为hex的替代
                            flight_number,
                            str(altitude),
                            ground_speed,
                            gate,
                            is_cargo
                        ))
                        
                        # 更新航班最後看見時間
                        if flight_number:
                            flight_last_seen[flight_number] = time.time()
                            
                        fa_count += 1
            except Exception as e:
                print(f"处理FlightAware航班 {flight_number} 失败: {e}")
                continue

    # 4. 處理華航郵件數據 (貨機專用)
    calair_count = 0
    try:
        # 从source_calair表获取华航航班数据（优先处理最近30分钟更新的数据）
        cursor.execute('''
            SELECT flight_no, flight_date, departure_time, arrival_time, 
                   origin, destination, aircraft_type, gate, status, remarks 
            FROM source_calair 
            WHERE updated_at > datetime('now', '-30 minute')
            ORDER BY updated_at DESC
        ''')
        recent_calair_flights = cursor.fetchall()
        
        # 处理最近30分钟的华航邮件数据（半小時更新一次）
        for flight_data in recent_calair_flights:
            try:
                flight_no, flight_date, departure_time, arrival_time, origin, destination, aircraft_type, gate, status, remarks = flight_data
                
                # 检查是否为货机（华航货机通常是CI开头的航班）
                is_cargo = 1 if flight_no.startswith('CI') else 0
                
                # 提取遠端機坪信息（从remarks中提取）
                remote_gate = gate
                if remarks:
                    # 尝试从remarks中提取遠端機坪信息
                    import re
                    remote_gate_match = re.search(r'遠端機坪[:：]\s*(\w+)', remarks)
                    if remote_gate_match:
                        remote_gate = remote_gate_match.group(1)
                
                # 接飛與機號對照參考
                aircraft_registration = ""
                if remarks:
                    # 尝试从remarks中提取机号信息
                    reg_match = re.search(r'機號[:：]\s*([A-Z0-9-]+)', remarks)
                    if reg_match:
                        aircraft_registration = reg_match.group(1)
                
                # 更新flight_schedule表（华航邮件的遠端機坪信息优先）
                cursor.execute('''
                    INSERT OR REPLACE INTO flight_schedule 
                    (flight_no, direction, gate, scheduled_time, actual_time, status, is_cargo, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    flight_no,
                    'A' if destination == 'TPE' else 'D',  # 假设目的地为TPE的是入境航班
                    remote_gate,  # 使用遠端機坪信息
                    departure_time if origin == 'TPE' else arrival_time,  # 出境航班用起飞时间，入境航班用到达时间
                    arrival_time if origin == 'TPE' else departure_time,
                    status,
                    is_cargo
                ))
                
                # 检查是否已有实时数据
                cursor.execute("SELECT source FROM live_traffic WHERE flight_no = ?", (flight_no,))
                existing_data = cursor.fetchone()
                
                if not existing_data:
                    # 如果没有实时数据，基于华航邮件数据创建记录
                    cursor.execute('''
                        INSERT OR REPLACE INTO live_traffic
                        (hex, flight_no, alt, gs, gate, is_cargo, source, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'CALAIR', CURRENT_TIMESTAMP)
                    ''', (
                        f"CA_{flight_no}",  # 使用航班号作为hex的替代
                        flight_no,
                        "TBD",  # 华航邮件数据没有高度信息
                        0,      # 华航邮件数据没有速度信息
                        remote_gate,  # 使用遠端機坪信息
                        is_cargo
                    ))
                    
                    # 更新航班最後看見時間
                    flight_last_seen[flight_no] = time.time()
                else:
                    # 如果已有数据但来源不是LOCAL或OPENSKY，更新为华航数据（优先遠端機坪信息）
                    cursor.execute("SELECT source FROM live_traffic WHERE flight_no = ? AND (source = 'LOCAL' OR source = 'OPENSKY')", (flight_no,))
                    if not cursor.fetchone():
                        cursor.execute('''
                            UPDATE live_traffic
                            SET gate = ?, is_cargo = ?, source = 'CALAIR', updated_at = CURRENT_TIMESTAMP
                            WHERE flight_no = ?
                        ''', (remote_gate, is_cargo, flight_no))
                
                calair_count += 1
            except Exception as e:
                print(f"处理华航航班 {flight_no} 失败: {e}")
                continue
        
        # 处理24小时内的其他华航数据（作为补充）
        cursor.execute('''
            SELECT flight_no, flight_date, departure_time, arrival_time, 
                   origin, destination, aircraft_type, gate, status, remarks 
            FROM source_calair 
            WHERE updated_at > datetime('now', '-24 hour') AND updated_at <= datetime('now', '-30 minute')
        ''')
        other_calair_flights = cursor.fetchall()
        
        for flight_data in other_calair_flights:
            try:
                flight_no, flight_date, departure_time, arrival_time, origin, destination, aircraft_type, gate, status, remarks = flight_data
                
                # 检查是否为货机
                is_cargo = 1 if flight_no.startswith('CI') else 0
                
                # 提取遠端機坪信息
                remote_gate = gate
                if remarks:
                    import re
                    remote_gate_match = re.search(r'遠端機坪[:：]\s*(\w+)', remarks)
                    if remote_gate_match:
                        remote_gate = remote_gate_match.group(1)
                
                # 检查是否已有实时数据
                cursor.execute("SELECT source FROM live_traffic WHERE flight_no = ?", (flight_no,))
                existing_data = cursor.fetchone()
                
                if not existing_data:
                    # 检查flight_schedule中是否已有记录
                    cursor.execute("SELECT gate FROM flight_schedule WHERE flight_no = ?", (flight_no,))
                    existing_schedule = cursor.fetchone()
                    if not existing_schedule:
                        # 如果航班计划中也没有记录，创建记录
                        cursor.execute('''
                            INSERT OR REPLACE INTO flight_schedule 
                            (flight_no, direction, gate, scheduled_time, actual_time, status, is_cargo, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ''', (
                            flight_no,
                            'A' if destination == 'TPE' else 'D',
                            remote_gate,
                            departure_time if origin == 'TPE' else arrival_time,
                            arrival_time if origin == 'TPE' else departure_time,
                            status,
                            is_cargo
                        ))
                
            except Exception as e:
                print(f"处理华航航班 {flight_no} 失败: {e}")
                continue
                
    except Exception as e:
        print(f"华航邮件数据处理失败: {e}")

    # 4. 處理OpenSky訊號暫時消失的情況
    # 保留最近2分鐘內看見的航班
    current_time = time.time()
    expired_flights = [flight for flight, last_seen in flight_last_seen.items() if current_time - last_seen > 120]
    for flight in expired_flights:
        del flight_last_seen[flight]

    # 5. 清理過期的數據
    try:
        # 刪除超過1小時未更新的數據
        cursor.execute("DELETE FROM live_traffic WHERE updated_at < datetime('now', '-1 hour')")
        cursor.execute("DELETE FROM source_antenna WHERE hex NOT IN (SELECT hex FROM live_traffic)")
        cursor.execute("DELETE FROM source_opensky WHERE icao24 NOT IN (SELECT hex FROM live_traffic)")
        cursor.execute("DELETE FROM source_flightaware WHERE flight_number NOT IN (SELECT flight_no FROM live_traffic)")
        cursor.execute("DELETE FROM source_calair WHERE updated_at < datetime('now', '-7 day')")  # 保留7天的华航邮件数据
    except Exception as e:
        print(f"清理過期數據異常: {e}")

    conn.commit()
    conn.close()
    print(f"4.0 運行中 | 本地: {local_count} | 雲端補位: {os_count} | FlightAware: {fa_count} | 華航郵件: {calair_count}")

if __name__ == "__main__":
    while True:
        fusion_engine()
        time.sleep(2)
