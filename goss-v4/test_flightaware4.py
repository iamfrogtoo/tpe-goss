import requests
import json

FLIGHTAWARE_API_KEY = "DCeSb4fyM1ohoH2EUTJiDqS2Gm9x6duw"
FLIGHTAWARE_API_BASE_URL = "https://aeroapi.flightaware.com/aeroapi"
TPE_ICAO = "RCTP"

headers = {"x-apikey": FLIGHTAWARE_API_KEY}

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
        
        # 檢查航班資料結構
        if data.get('departures'):
            flight = data['departures'][0]
            print(f"\n航班資料完整結構:")
            print(json.dumps(flight, indent=2, ensure_ascii=False))
            
    else:
        print(f"錯誤訊息: {response.text}")
        
except Exception as e:
    print(f"API 請求失敗: {e}")