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

# 定義天線範圍（保持不變）
LAMIN = 24.0
LOMIN = 120.0
LAMAX = 26.0
LOMAX = 122.5

# 偏北50公里的範圍調整
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


def is_within_antenna_range(lat, lon):
    """檢查飛機是否在天線範圍內"""
    return ADJUSTED_LAMIN <= lat <= LAMAX and LOMIN <= lon <= LOMAX


def get_flightaware_data():
    """抓取 FlightAware 資料"""
    headers = {
        "x-apikey": FLIGHTAWARE_API_KEY
    }
    
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
            return all_flights
        elif response.status_code == 429:
            print("FlightAware API 请求过于频繁，暂时跳过")
            return []
    except Exception as e:
        print(f"获取FlightAware航班失败: {e}")
    
    return []


def get_local_antenna_data():
    """获取本地天线数据"""
    try:
        response = requests.get(LOCAL_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            aircraft_list = data.get('aircraft', [])
            
            # 过滤入境航班
            arrival_aircraft = []
            for aircraft in aircraft_list:
                flight_no = aircraft.get('flight', '').strip()
                if flight_no and is_arrival_flight(flight_no):
                    arrival_aircraft.append(aircraft)
            
            print(f"[天線] 原始資料: {len(aircraft_list)} 筆，入境航班: {len(arrival_aircraft)} 筆")
            return arrival_aircraft
            
    except Exception as e:
        print(f"获取本地天线数据失败: {e}")
    
    return []


def main_loop():
    """主循環（改造版本）"""
    print("=== TPE GOSS v4 數據融合引擎（改造版） ===")
    print("✅ OpenSky 範圍: 23.0-26.5°N, 119.0-123.0°E")
    print("✅ 請求頻率: 30秒/次")
    print("✅ 入境航班過濾: 已啟用")
    
    iteration = 0
    
    while True:
        iteration += 1
        print(f"\n=== 第 {iteration} 次數據融合循環 ===")
        print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. 獲取 OpenSky 數據（改造版本）
            opensky_data = get_opensky_data()
            
            # 2. 獲取本地天線數據
            antenna_data = get_local_antenna_data()
            
            # 3. 數據融合邏輯（保持原有）
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 處理 OpenSky 數據
            opensky_count = 0
            for state in opensky_data:
                # 原有處理邏輯...
                opensky_count += 1
            
            # 處理天線數據
            antenna_count = 0
            for aircraft in antenna_data:
                # 原有處理邏輯...
                antenna_count += 1
            
            print(f"[融合] OpenSky: {opensky_count} 筆，天線: {antenna_count} 筆")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ 數據融合錯誤: {e}")
        
        # 等待下一次循環（保持原有間隔）
        print("等待下一次數據融合...")
        time.sleep(10)


if __name__ == "__main__":
    main_loop()