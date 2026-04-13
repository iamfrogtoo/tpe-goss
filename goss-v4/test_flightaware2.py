import requests

FLIGHTAWARE_API_KEY = "DCeSb4fyM1ohoH2EUTJiDqS2Gm9x6duw"
FLIGHTAWARE_API_BASE_URL = "https://aeroapi.flightaware.com/aeroapi"

headers = {"x-apikey": FLIGHTAWARE_API_KEY}

# 測試不同的 API 端點和參數格式
test_endpoints = [
    "/flights/search",
    "/airports/RCTP/flights",
    "/flights"
]

for endpoint in test_endpoints:
    url = f"{FLIGHTAWARE_API_BASE_URL}{endpoint}"
    print(f"\n測試端點: {endpoint}")
    
    try:
        if endpoint == "/airports/RCTP/flights":
            params = {"type": "departure"}
        else:
            params = {}
            
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"回應格式: {type(data)}")
            if isinstance(data, dict):
                print(f"回應鍵值: {list(data.keys())}")
        else:
            print(f"錯誤訊息: {response.text[:200]}")
            
    except Exception as e:
        print(f"API 請求失敗: {e}")