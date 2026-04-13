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
        
        # 檢查第一個離港航班的完整結構
        if data.get('departures'):
            flight = data['departures'][0]
            print(f"\n第一個離港航班完整結構:")
            print(json.dumps(flight, indent=2, ensure_ascii=False))
            
            # 檢查航班號碼的實際結構
            print(f"\n航班號碼相關欄位:")
            print(f"flight.keys(): {list(flight.keys())}")
            
            # 檢查可能的航班號碼欄位
            for key in flight.keys():
                if 'flight' in key.lower() or 'number' in key.lower():
                    print(f"{key}: {flight.get(key)}")
                    
    elif response.status_code == 429:
        print("FlightAware API 配額限制，但會繼續計費")
        print(f"錯誤訊息: {response.text}")
    else:
        print(f"錯誤訊息: {response.text}")
        
except Exception as e:
    print(f"API 請求失敗: {e}")