import requests
import sqlite3

FLIGHTAWARE_API_KEY = "DCeSb4fyM1ohoH2EUTJiDqS2Gm9x6duw"
FLIGHTAWARE_API_BASE_URL = "https://aeroapi.flightaware.com/aeroapi"
TPE_ICAO = "RCTP"
DB_PATH = "goss_v4.db"

headers = {"x-apikey": FLIGHTAWARE_API_KEY}

# 連接資料庫
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 獲取所有航班列表
cursor.execute("SELECT flight_no FROM flight_schedule")
all_scheduled_flights = [row[0] for row in cursor.fetchall()]

# 測試獲取桃園機場的航班信息
url = f"{FLIGHTAWARE_API_BASE_URL}/airports/{TPE_ICAO}/flights"
params = {"type": "departure"}

try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"離港航班數量: {len(data.get('departures', []))}")
        print(f"到港航班數量: {len(data.get('arrivals', []))}")
        
        # 檢查 FlightAware 航班與資料庫的匹配情況
        all_fa_flights = data.get('departures', []) + data.get('arrivals', [])
        
        print(f"\nFlightAware 航班與資料庫匹配情況:")
        matched_count = 0
        
        for flight in all_fa_flights:
            # 提取航班信息
            operator_icao = flight.get('operator_icao', '')
            flight_number_raw = flight.get('flight_number', '')
            
            # 組合完整的航班號碼
            if operator_icao and flight_number_raw:
                flight_number = f"{operator_icao}{flight_number_raw}"
            else:
                flight_number = flight.get('ident_icao', '') or flight.get('ident', '')
            
            flight_number = flight_number.strip()
            
            # 檢查是否在資料庫中
            if flight_number in all_scheduled_flights:
                print(f"✅ 匹配成功: {flight_number}")
                matched_count += 1
            else:
                print(f"❌ 匹配失敗: {flight_number}")
        
        print(f"\n匹配結果: {matched_count}/{len(all_fa_flights)} 個航班匹配成功")
        
    elif response.status_code == 429:
        print("FlightAware API 配額限制，但會繼續計費")
        print(f"錯誤訊息: {response.text}")
    else:
        print(f"錯誤訊息: {response.text}")
        
except Exception as e:
    print(f"API 請求失敗: {e}")

conn.close()