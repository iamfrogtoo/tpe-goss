import requests

FLIGHTAWARE_API_KEY = "DCeSb4fyM1ohoH2EUTJiDqS2Gm9x6duw"
FLIGHTAWARE_API_BASE_URL = "https://aeroapi.flightaware.com/aeroapi"

headers = {"x-apikey": FLIGHTAWARE_API_KEY}
url = f"{FLIGHTAWARE_API_BASE_URL}/flights/position"
params = {
    "min_lat": 24.0,
    "max_lat": 26.0,
    "min_lon": 120.0,
    "max_lon": 122.5,
    "max_pages": 1
}

try:
    response = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        flights = data.get("flights", [])
        print(f"航班數量: {len(flights)}")
        
        if flights:
            print("前5個航班:")
            for i, flight in enumerate(flights[:5]):
                flight_id = flight.get("identification", {}).get("id", "")
                flight_number = flight.get("identification", {}).get("number", {}).get("default", "")
                print(f"  {i+1}. {flight_id} - {flight_number}")
    else:
        print(f"錯誤訊息: {response.text}")
        
except Exception as e:
    print(f"API 請求失敗: {e}")