import requests
import json
import time

CREDENTIALS_FILE = 'credentials.json'
TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
OPENSKY_URL = "https://opensky-network.org/api/states/all?lamin=24.0&lomin=120.0&lamax=26.0&lomax=122.5"

def load_creds():
    with open(CREDENTIALS_FILE, 'r') as f:
        c = json.load(f)
    return c.get('clientId'), c.get('clientSecret')

def get_token(client_id, client_secret):
    print(f"[1] 嘗試取得 OAuth2 Token...")
    print(f"    clientId: {client_id}")
    try:
        r = requests.post(TOKEN_URL, data={'grant_type': 'client_credentials'},
                          auth=(client_id, client_secret), timeout=10)
        print(f"    Token 回應狀態: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            token = data.get('access_token')
            expires_in = data.get('expires_in', 0)
            print(f"    ✅ Token 取得成功！有效期: {expires_in} 秒")
            print(f"    Token 前30字: {token[:30]}...")
            return token
        else:
            print(f"    ❌ 取得 Token 失敗: {r.text}")
            return None
    except Exception as e:
        print(f"    ❌ 連線錯誤: {e}")
        return None

def test_api(token=None):
    print(f"\n[2] 測試 OpenSky API...")
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    mode = "認證模式" if token else "匿名模式"
    print(f"    模式: {mode}")
    try:
        r = requests.get(OPENSKY_URL, headers=headers, timeout=10)
        print(f"    API 回應狀態: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            states = data.get('states', [])
            print(f"    ✅ 成功！取得航班數量: {len(states)} 架")
            if states:
                print(f"    第一筆資料 (ICAO, Callsign): {states[0][0]}, {states[0][1]}")
        elif r.status_code == 429:
            print(f"    ❌ 429 Too Many Requests - 請求頻率超限")
            # 檢查回應 headers
            print(f"    回應 Headers:")
            for k, v in r.headers.items():
                if any(x in k.lower() for x in ['retry', 'limit', 'remain', 'reset', 'x-rate']):
                    print(f"      {k}: {v}")
        elif r.status_code == 401:
            print(f"    ❌ 401 Unauthorized - Token 無效或過期")
        else:
            print(f"    ❌ 其他錯誤: {r.status_code} - {r.text[:200]}")
    except Exception as e:
        print(f"    ❌ 連線錯誤: {e}")

def test_anonymous():
    print(f"\n[3] 對比測試：匿名模式...")
    test_api(token=None)

if __name__ == "__main__":
    print("=" * 50)
    print("OpenSky Network 連線測試")
    print("=" * 50)

    client_id, client_secret = load_creds()
    token = get_token(client_id, client_secret)
    test_api(token)

    print("\n[等待 3 秒後測試匿名模式...]")
    time.sleep(3)
    test_anonymous()

    print("\n" + "=" * 50)
    print("測試完成")
