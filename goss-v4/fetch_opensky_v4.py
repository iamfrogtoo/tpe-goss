import requests
import sqlite3
import time
import os
import json

# TPE 座標範圍 (桃園機場周邊約 200km 矩形)
LAMIN, LAMAX = 24.0, 26.0
LOMIN, LOMAX = 120.0, 122.5
DB_PATH = "goss_v4.db"

# OpenSky OAuth2 認證設定
CREDENTIALS_FILE = 'credentials.json'
CURRENT_TOKEN = None
TOKEN_EXPIRY = 0

# 追踪API调用频率，避免超过OpenSky的限制
LAST_API_CALL = 0
API_CALL_INTERVAL = 10  # 秒

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
            print(f"      [OAuth2] 取得 token 失敗: {r.status_code}")
    except Exception as e:
        print(f"      [OAuth2] 連線錯誤: {e}")
    return None, 0

def get_opensky_data():
    """使用 OAuth2 Bearer Token 抓取 OpenSky 資料 """
    global CURRENT_TOKEN, TOKEN_EXPIRY, LAST_API_CALL

    # 控制API调用频率
    current_time = time.time()
    if current_time - LAST_API_CALL < API_CALL_INTERVAL:
        time.sleep(API_CALL_INTERVAL - (current_time - LAST_API_CALL))
    LAST_API_CALL = time.time()

    client_id, client_secret = load_opensky_creds()

    url = f"https://opensky-network.org/api/states/all?lamin={LAMIN}&lomin={LOMIN}&lamax={LAMAX}&lomax={LOMAX}"

    # 檢查 token 是否過期或不存在
    if CURRENT_TOKEN is None or time.time() > TOKEN_EXPIRY:
        if client_id and client_secret:
            CURRENT_TOKEN, expires_in = get_access_token(client_id, client_secret)
            TOKEN_EXPIRY = time.time() + expires_in - 30  # 提前30秒過期
            if CURRENT_TOKEN:
                print(f"🔑 OpenSky OAuth2 認證成功")
        else:
            print("👤 使用匿名模式 (建議設定 credentials.json 以獲得更高額度)")

    headers = {'Authorization': f'Bearer {CURRENT_TOKEN}'} if CURRENT_TOKEN else {}

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json().get('states', [])
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

def fetch_opensky():
    try:
        states = get_opensky_data()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 確保分區表存在
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS source_opensky (
                icao24 TEXT PRIMARY KEY,
                callsign TEXT,
                baro_altitude REAL,
                velocity REAL,
                latitude REAL,
                longitude REAL,
                heading REAL,
                vertical_rate REAL,
                squawk TEXT,
                origin TEXT,
                destination TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 創建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_opensky_callsign ON source_opensky(callsign)')

        for s in states:
            # OpenSky 欄位：0:icao24, 1:callsign, 5:lon, 6:lat, 7:baro_alt, 9:velocity, 10:heading, 11:vertical_rate, 14:squawk
            icao = s[0]
            callsign = s[1].strip() if s[1] else ""
            squawk = s[14] if len(s) > 14 else None

            cursor.execute('''
                INSERT OR REPLACE INTO source_opensky
                (icao24, callsign, baro_altitude, velocity, latitude, longitude, heading, vertical_rate, squawk, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                icao,
                callsign,
                s[7],
                s[9],
                s[6],
                s[5],
                s[10],
                s[11],
                squawk
            ))

        # 清理過期的OpenSky數據（超過2小時）
        cursor.execute("DELETE FROM source_opensky WHERE updated_at < datetime('now', '-2 hours')")
        
        conn.commit()
        conn.close()
        print(f"✅ OpenSky 同步完成: {len(states)} 架飛機")

    except Exception as e:
        print(f"❌ OpenSky 失敗: {e}")

if __name__ == "__main__":
    fetch_opensky()
