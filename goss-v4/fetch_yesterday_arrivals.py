import requests
import json
from datetime import datetime, timedelta, timezone

API_KEY = "DCeSb4fyM1ohoH2EUTJiDqS2Gm9x6duw"
API_BASE_URL = "https://aeroapi.flightaware.com/aeroapi"
TPE_ICAO = "RCTP"

HEADERS = {"x-apikey": API_KEY}

def get_yesterday_range():
    """取得昨日 UTC 時間範圍（台灣時間 UTC+8）"""
    tw_now = datetime.now(timezone(timedelta(hours=8)))
    yesterday_tw = tw_now - timedelta(days=1)
    start_tw = yesterday_tw.replace(hour=0, minute=0, second=0, microsecond=0)
    end_tw = yesterday_tw.replace(hour=23, minute=59, second=59, microsecond=0)
    start_utc = start_tw.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_utc = end_tw.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return start_utc, end_utc

def fetch_all_arrivals_by_time_window(start, end, target=100):
    """
    用「時間視窗滑動」方式翻頁，每次往前拉一批，直到足夠 target 筆。
    FlightAware 每頁最多 15 筆（預設），但 max_pages 可繼續往回拉。
    """
    url = f"{API_BASE_URL}/airports/{TPE_ICAO}/flights/arrivals"
    all_flights = []

    current_end = end
    page = 1

    print(f"查詢時間範圍 (UTC): {start} → {end}")
    print(f"目標筆數: {target}\n")

    while len(all_flights) < target:
        params = {
            "start":     start,
            "end":       current_end,
            "max_pages": 1,
        }

        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=15)
            print(f"  [第{page}頁] HTTP {r.status_code}", end="")

            if r.status_code != 200:
                print(f" - 錯誤: {r.text[:300]}")
                break

            data = r.json()
        except Exception as e:
            print(f"\n連線錯誤: {e}")
            break

        flights = data.get("arrivals", data.get("flights", []))
        print(f" | 本頁筆數: {len(flights)} | 累計: {len(all_flights) + len(flights)}")

        if not flights:
            print("  → 無更多資料")
            break

        all_flights.extend(flights)

        # 用最後一筆的實際落地時間往前推，避免重複
        last_flight = flights[-1]
        last_time = (
            last_flight.get("actual_on")
            or last_flight.get("actual_in")
            or last_flight.get("scheduled_on")
            or last_flight.get("scheduled_in")
        )

        if not last_time:
            print("  → 最後一筆沒有時間欄位，停止翻頁")
            break

        # 把 end 設為最後一筆時間 - 1 秒，避免重複抓
        try:
            last_dt = datetime.fromisoformat(last_time.replace("Z", "+00:00"))
            new_end_dt = last_dt - timedelta(seconds=1)
            current_end = new_end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception as e:
            print(f"  → 時間解析失敗: {e}，停止翻頁")
            break

        if current_end <= start:
            print("  → 已到達查詢起始時間，停止")
            break

        page += 1

    # 去重（同一航班可能被重複抓到）
    seen = set()
    unique_flights = []
    for f in all_flights:
        key = f.get("ident", "") + str(f.get("actual_on") or f.get("scheduled_on", ""))
        if key not in seen:
            seen.add(key)
            unique_flights.append(f)

    return unique_flights[:target]

def print_flights(flights):
    """整齊印出航班資料"""
    print("\n" + "="*90)
    print(f"{'No.':<5} {'航班號':<12} {'起飛地':<8} {'實際落地時間(台灣)':<22} {'機型':<10} {'機號'}")
    print("-"*90)

    for i, f in enumerate(flights, 1):
        flight_no     = f.get("ident_iata") or f.get("ident", "")
        origin_obj    = f.get("origin") or {}
        origin        = origin_obj.get("code_iata") or origin_obj.get("code_icao") or ""

        # 實際落地時間 → 轉台灣時間
        actual_time_str = f.get("actual_on") or f.get("actual_in") or f.get("scheduled_on") or ""
        if actual_time_str:
            try:
                dt_utc = datetime.fromisoformat(actual_time_str.replace("Z", "+00:00"))
                dt_tw  = dt_utc.astimezone(timezone(timedelta(hours=8)))
                actual_tw = dt_tw.strftime("%Y-%m-%d %H:%M")
            except:
                actual_tw = actual_time_str
        else:
            actual_tw = ""

        aircraft_type = f.get("aircraft_type", "")
        reg           = f.get("registration", "")

        print(f"{i:<5} {flight_no:<12} {origin:<8} {actual_tw:<22} {aircraft_type:<10} {reg}")

    print("="*90)
    print(f"共 {len(flights)} 筆")

def save_to_json(flights, filename="yesterday_arrivals.json"):
    """存成 JSON 備查"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(flights, f, ensure_ascii=False, indent=2)
    print(f"原始資料已儲存至 {filename}")

if __name__ == "__main__":
    print("="*50)
    print("昨日桃園機場 (RCTP) 降落航班查詢")
    print("="*50 + "\n")

    start, end = get_yesterday_range()
    flights = fetch_all_arrivals_by_time_window(start, end, target=100)

    if flights:
        print_flights(flights)
        save_to_json(flights)
    else:
        print("❌ 未取得任何航班資料，請確認 API Key 是否有效")
