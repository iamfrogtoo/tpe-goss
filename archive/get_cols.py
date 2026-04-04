import requests
import json
import urllib3
urllib3.disable_warnings()
headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" }
# a = inbound, af = outbound or cargo?
for url in ["https://www.taoyuan-airport.com/uploads/flightx/a_flight_v4.txt", "https://www.taoyuan-airport.com/uploads/flightx/d_flight_v4.txt"]:
    print(f"URL: {url}")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        lines = r.content.decode('utf-8', errors='ignore').splitlines()
        valid = [l for l in lines if len(l)>10][:3]
        for l in valid:
            parts = [p.replace("'", "").replace('"', "").strip() for p in l.split(',')]
            print(json.dumps({i: p for i, p in enumerate(parts)}, ensure_ascii=False))
            print("---")
    except Exception as e:
        print(f"Error: {e}")
