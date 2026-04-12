import requests
import sqlite3
import time
import os
import json
from datetime import datetime, timedelta

DB_PATH = "goss_v4.db"
LOCAL_URL = "http://192.168.31.221:8080/data/aircraft.json"
# ===== 改造：加大 OpenSky 範圍 =====
# 原範圍：24.0-26.0, 120.0-122.5 (約 200km x 200km)
# 新範圍：23.0-26.5, 119.0-123.0 (約 400km x 400km)
OPENSKY_URL = "https://opensky-network.org/api/states/all?lamin=23.0&lomin=119.0&lamax=26.5&lomax=123.0"

# FlightAware AeroAPI 配置
FLIGHTAWARE_API_KEY = "DCeSb4fyM1ohoH2EUTJiDqS2Gm9x6duw"
FLIGHTAWARE_API_BASE_URL = "https://aeroapi.flightaware.com/aeroapi"
TPE_ICAO = "RCTP"

# OpenSky OAuth2 認證設定
CREDENTIALS_FILE = 'credentials.json'
CURRENT_TOKEN = None
TOKEN_EXPIRY = 0

# ===== 改造：控制請求頻率 =====
LAST_OPENSKY_CALL = 0
OPENSKY_CALL_INTERVAL = 30  # 30秒一次，避免超額

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
    """使用 OAuth2 Bearer Token 抓取 OpenSky 資料（改造版本）"""
    global CURRENT_TOKEN, TOKEN_EXPIRY, LAST_OPENSKY_CALL

    # ===== 改造：控制請求頻率 =====
    current_time = time.time()
    time_since_last_call = current_time - LAST_OPENSKY_CALL
    
    if time_since_last_call < OPENSKY_CALL_INTERVAL:
        wait_time = OPENSKY_CALL_INTERVAL - time_since_last_call
        print(f"[OpenSky] 等待 {wait_time:.1f} 秒後再請求（避免超額）")
        time.sleep(wait_time)
    
    LAST_OPENSKY_CALL = time.time()

    client_id, client_secret = load_opensky_creds()

    # 檢查 token 是否過期或不存在
    if CURRENT_TOKEN is None or time.time() > TOKEN_EXPIRY:
        if client_id and client_secret:
            CURRENT_TOKEN, expires_in = get_access_token(client_id, client_secret)
            TOKEN_EXPIRY = time.time() + expires_in - 30  # 提前30秒過期
            if CURRENT_TOKEN:
                print("🔑 OpenSky OAuth2 認證成功")
        else:
            print("👤 使用匿名模式 (建議設定 credentials.json 以獲得更高額度)")

    headers = {'Authorization': f'Bearer {CURRENT_TOKEN}'} if CURRENT_TOKEN else {}

    try:
        print(f"[OpenSky] 請求範圍: 23.0-26.5°N, 119.0-123.0°E (約400km x 400km)")
        r = requests.get(OPENSKY_URL, headers=headers, timeout=15)
        
        if r.status_code == 200:
            states = r.json().get('states', [])
            print(f"[OpenSky] 成功取得 {len(states)} 筆航班資料")
            
            # ===== 改造：新增入境航班過濾 =====
            arrival_states = filter_arrival_flights(states)
            print(f"[OpenSky] 過濾後入境航班: {len(arrival_states)} 筆")
            return arrival_states
            
        elif r.status_code == 401:
            # Token 過期，重新取得
            print("🔄 OpenSky Token 過期，重新取得...")
            CURRENT_TOKEN = None
            return get_opensky_data()  # 遞迴重試
            
        elif r.status_code == 429:
            print(f"❌ OpenSky 請求過於頻繁 (429)，暫停60秒")
            time.sleep(60)
            return []
            
        else:
            print(f"❌ OpenSky 連線失敗: {r.status_code}")
            
    except Exception as e:
        print(f"❌ OpenSky 連線錯誤: {e}")
    
    return []

def get_flightaware_data():
    """抓取 FlightAware 資料 """
    headers = {
        "x-apikey": FLIGHTAWARE_API_KEY
    }
    
    all_flights = []
    
    # 获取桃园机场的航班信息
    try:
        url = f"{FLIGHTAWARE_API_BASE_URL}/airports/{TPE_ICAO}/flights"
        params = {
            "type": "departure"  # 获取离港航班
        }
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # 合并离港和到港航班
            departures = data.get('departures', [])
            arrivals = data.get('arrivals', [])
            all_flights = departures + arrivals
        elif response.status_code == 429:
            print("FlightAware API 请求过于频繁，暂时跳过")
            return []
    except Exception as e:
        print(f"获取FlightAware航班失败: {e}")
    
    return all_flights

def is_within_antenna_range(lat, lon):
    """檢查飛機是否在天線範圍內"""
    return ADJUSTED_LAMIN <= lat <= LAMAX and LOMIN <= lon <= LOMAX

def filter_arrival_flights(states):
    """過濾入境航班（移植 v2 版本邏輯）"""
    arrival_states = []
    
    for state in states:
        if not state or len(state) < 2:
            continue
            
        callsign = state[1] if state[1] else ""
        
        # 檢查是否為入境航班
        if is_arrival_flight(callsign.strip()):
            arrival_states.append(state)
    
    return arrival_states


def is_arrival_flight(flight_no):
    """檢查是否為入境航班（移植 v2 版本邏輯）"""
    if not flight_no:
        return False
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT direction FROM flight_schedule WHERE flight_no = ?", (flight_no,))
        result = cursor.fetchone()
        
        if result:
            direction = result[0]
            return direction == 'A'  # A 表示入境航班
        
        # 如果航班表中找不到，檢查航班號碼格式
        # 入境航班通常是國際航班，有較長的航班號
        if len(flight_no) >= 6 and flight_no[:2].isalpha():
            # 可能是國際航班，暫時視為入境
            return True
            
    except Exception as e:
        print(f"[入境檢查] 錯誤: {e}")
    finally:
        conn.close()
    
    return False

def fusion_engine():
    global flight_last_seen
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 抓取本地天線數據 (優先)
    local_count = 0
    try:
        res = requests.get(LOCAL_URL, timeout=1).json()
        aircraft_list = res.get('aircraft', [])
        print(f"[天線] 原始資料: {len(aircraft_list)} 筆")
        
        # ===== 改造：過濾入境航班 =====
        arrival_aircraft = []
        for ac in aircraft_list:
            flight = ac.get('flight', '').strip()
            if flight and is_arrival_flight(flight):
                arrival_aircraft.append(ac)
        
        print(f"[天線] 過濾後入境航班: {len(arrival_aircraft)} 筆")
        
        for ac in arrival_aircraft:
            hex_code = ac.get('hex')
            flight = ac.get('flight', '').strip()

            # 檢查是否在天線範圍內
            lat = ac.get('lat')
            lon = ac.get('lon')
            if lat and lon and not is_within_antenna_range(lat, lon):
                # 不在範圍內的飛機，跳過
                continue

            # 寫入天線分區表（記錄所有範圍內的飛機）
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

            # 嚴格檢查航班計畫：只納入有桃園機場航班計畫的航班
            # 修正：先去除航班號碼中的空格，再進行航空公司代碼轉換
            clean_flight = flight.strip()
            
            # 航空公司代碼轉換：本地天線代碼 -> 資料庫代碼
            airline_mapping = {
                'EVA': 'BR',  # 長榮航空
                'CAL': 'CI',  # 中華航空
                'CHINA': 'CI', # 中華航空
                'UNI': 'B7',  # 立榮航空
                'TNA': 'GE',  # 復興航空
                'MDA': 'AE',  # 華信航空
                'FAT': 'EF',  # 遠東航空
                'TBA': 'IT',  # 台灣虎航
                'JJA': '7C',  # 濟州航空
                'CPA': 'CX',  # 國泰航空
                'SIA': 'SQ',  # 新加坡航空
                'ANA': 'NH',  # 全日空
                'JAL': 'JL',  # 日本航空
                'KAL': 'KE',  # 大韓航空
                'THA': 'TG',  # 泰國航空
                'MAS': 'MH',  # 馬來西亞航空
                'AFR': 'AF',  # 法國航空
                'DLH': 'LH',  # 漢莎航空
                'BAW': 'BA',  # 英國航空
                'UAL': 'UA',  # 聯合航空
                'AAL': 'AA',  # 美國航空
                'DAL': 'DL',  # 達美航空
                'KLM': 'KL',  # 荷蘭皇家航空
                'QTR': 'QR',  # 卡達航空
                'UAE': 'EK',  # 阿聯酋航空
                'SVA': 'SV',  # 沙烏地阿拉伯航空
                'FIN': 'AY',  # 芬蘭航空
                'SWR': 'LX',  # 瑞士航空
                'VIR': 'VS',  # 維珍航空
                'QFA': 'QF',  # 澳洲航空
                'ANZ': 'NZ',  # 紐西蘭航空
                'SAS': 'SK',  # 北歐航空
                'IBE': 'IB',  # 西班牙航空
                'AZA': 'AZ',  # 義大利航空
                'BER': 'AB',  # 柏林航空
                'RYR': 'FR',  # 瑞安航空
                'EZY': 'U2',  # 易捷航空
                'WZZ': 'W6',  # 威茲航空
                'VLG': 'VY',  # 伏林航空
                'TAP': 'TP',  # 葡萄牙航空
                'AIC': 'AI',  # 印度航空
                'THY': 'TK',  # 土耳其航空
                'RAM': 'AT',  # 摩洛哥皇家航空
                'ETH': 'ET',  # 衣索比亞航空
                'KAC': 'KU',  # 科威特航空
                'MEA': 'ME',  # 中東航空
                'PIA': 'PK',  # 巴基斯坦航空
                'SAA': 'SA',  # 南非航空
                'LAN': 'LA',  # 智利航空
                'TAM': 'JJ',  # 巴西天馬航空
                'GLO': 'G3',  # 高爾航空
                'AVA': 'AV',  # 哥倫比亞航空
                'AEA': 'UX',  # 西班牙航空
                'AUA': 'OS',  # 奧地利航空
                'BEL': 'SN',  # 布魯塞爾航空
                'CFG': 'DE',  # 神鷹航空
                'CMP': 'CM',  # 巴拿馬航空
                'CUB': 'CU',  # 古巴航空
                'DTA': 'DT',  # 安哥拉航空
                'ELY': 'LY',  # 以色列航空
                'ETD': 'EY',  # 阿提哈德航空
                'GFA': 'GF',  # 海灣航空
                'IRA': 'IR',  # 伊朗航空
                'JAF': 'TB',  # 捷特航空
                'KMI': 'KM',  # 馬耳他航空
                'LOT': 'LO',  # 波蘭航空
                'MAU': 'MK',  # 毛里求斯航空
                'MSR': 'MS',  # 埃及航空
                'MXA': 'MX',  # 墨西哥航空
                'PAL': 'PR',  # 菲律賓航空
                'RAM': 'AT',  # 摩洛哥皇家航空
                'ROT': 'RO',  # 羅馬尼亞航空
                'SAS': 'SK',  # 北歐航空
                'SVA': 'SV',  # 沙烏地阿拉伯航空
                'TAM': 'JJ',  # 巴西天馬航空
                'TAP': 'TP',  # 葡萄牙航空
                'THY': 'TK',  # 土耳其航空
                'TUN': 'TU',  # 突尼西亞航空
                'UAE': 'EK',  # 阿聯酋航空
                'VIR': 'VS',  # 維珍航空
                'VLG': 'VY',  # 伏林航空
                'WZZ': 'W6'   # 威茲航空
            }
            
            # 嘗試轉換航空公司代碼
            converted_flight = clean_flight
            for local_code, db_code in airline_mapping.items():
                if clean_flight.startswith(local_code):
                    # 轉換航空公司代碼
                    flight_number = clean_flight[len(local_code):].strip()
                    converted_flight = db_code + flight_number
                    break
            
            # 使用模糊匹配查詢資料庫（支援航班號碼格式不匹配問題）
            # 先嘗試精確匹配
            cursor.execute("SELECT gate, is_cargo FROM flight_schedule WHERE flight_no = ?", (converted_flight,))
            sch = cursor.fetchone()
            
            # 如果精確匹配失敗，嘗試模糊匹配（前綴匹配）
            if not sch and len(converted_flight) >= 4:
                # 嘗試匹配前3位數的航班號碼
                prefix_match = converted_flight[:3]
                cursor.execute("SELECT gate, is_cargo FROM flight_schedule WHERE flight_no LIKE ?", (prefix_match + '%',))
                sch = cursor.fetchone()
            
            # 如果前綴匹配失敗，嘗試航空公司代碼匹配
            if not sch and len(converted_flight) >= 3:
                # 只匹配航空公司代碼
                airline_match = converted_flight[:3]
                cursor.execute("SELECT gate, is_cargo FROM flight_schedule WHERE flight_no LIKE ? LIMIT 1", (airline_match + '%',))
                sch = cursor.fetchone()
            
            # 如果航空公司代碼匹配失敗，嘗試反向匹配（資料庫航班號碼較長的情況）
            if not sch and len(converted_flight) >= 3:
                # 嘗試匹配資料庫中較長的航班號碼
                cursor.execute("SELECT gate, is_cargo FROM flight_schedule WHERE flight_no LIKE ? LIMIT 1", (converted_flight + '%',))
                sch = cursor.fetchone()
            
            if sch:  # 只有當航班有航班計畫時才納入 live_traffic
                gate, is_cargo = sch[0], sch[1]

                # 更新到實時交通表（使用去除空格的航班號碼）
                cursor.execute('''
                    INSERT OR REPLACE INTO live_traffic
                    (hex, flight_no, alt, gs, gate, is_cargo, source, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 'LOCAL', CURRENT_TIMESTAMP)
                ''', (
                    hex_code,
                    clean_flight,  # 使用去除空格的航班號碼
                    str(ac.get('alt_baro')),
                    ac.get('gs'),
                    gate,
                    is_cargo
                ))
                
                # 更新航班最後看見時間
                if flight:
                    flight_last_seen[flight] = time.time()
                    
                local_count += 1
            else:
                # 記錄跳過的過境航班（用於調試）
                print(f"跳過過境航班: {flight} (無桃園機場航班計畫)")
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
                
                # 寫入OpenSky分區表（記錄所有範圍內的飛機）
                squawk_value = s[14] if len(s) > 14 else None
                cursor.execute('INSERT OR REPLACE INTO source_opensky (icao24, callsign, baro_altitude, velocity, latitude, longitude, heading, vertical_rate, squawk) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (icao, callsign, s[7], s[9], s[6], s[5], s[10], s[11], squawk_value))

                # 嚴格檢查航班計畫：只納入有桃園機場航班計畫的航班
                cursor.execute("SELECT gate, is_cargo FROM flight_schedule WHERE flight_no = ?", (callsign,))
                sch = cursor.fetchone()
                
                if sch:  # 只有當航班有航班計畫時才納入 live_traffic
                    gate, is_cargo = sch[0], sch[1]

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
                else:
                    # 記錄跳過的過境航班（用於調試）
                    print(f"跳過過境航班: {callsign} (無桃園機場航班計畫)")

    # 3. 抓取FlightAware數據 (補位)
    fa_count = 0
    # [V4調整] 啟用 FlightAware 抓取，免費額度10美元，超額計費
    fa_flights = get_flightaware_data()

    if fa_flights:
        # 获取本地所有航班列表（包含入境和离港）
        cursor.execute("SELECT flight_no FROM flight_schedule")
        all_scheduled_flights = [row[0] for row in cursor.fetchall()]
        
        for flight in fa_flights:
            try:
                # 提取航班信息
                flight_id = flight.get('identification', {}).get('id', '')
                
                # 修正航班号码提取逻辑 - FlightAware 格式
                operator_icao = flight.get('operator_icao', '')
                flight_number_raw = flight.get('flight_number', '')
                
                # 组合完整的航班号码 (航空公司代码 + 航班号码)
                if operator_icao and flight_number_raw:
                    flight_number = f"{operator_icao}{flight_number_raw}"
                else:
                    flight_number = flight.get('ident_icao', '') or flight.get('ident', '')
                
                flight_number = flight_number.strip()
                
                # 只处理有航班计划的航班
                if flight_number not in all_scheduled_flights:
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
                    # 写入FlightAware分區表（即使没有位置信息也记录）
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

                    # 更新到實時交通表（即使没有位置信息也记录）
                    cursor.execute('''
                        INSERT OR REPLACE INTO live_traffic
                        (hex, flight_no, alt, gs, gate, is_cargo, source, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'FLIGHTAWARE', CURRENT_TIMESTAMP)
                    ''', (
                        f"FA_{flight_number}",  # 使用航班号作为hex的替代
                        flight_number,
                        str(altitude) if altitude else "0",
                        ground_speed if ground_speed else 0,
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
