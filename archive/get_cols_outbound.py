import requests
import json
import urllib3
urllib3.disable_warnings()
headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" }
url = "https://www.taoyuan-airport.com/uploads/flightx/a_flight_v4.txt"
r = requests.get(url, headers=headers, verify=False, timeout=10)
lines = r.content.decode('utf-8', errors='ignore').splitlines()
valid_d = [l for l in lines if len(l)>10 and "D" in l.split(',')[1].upper()][:3]
for l in valid_d:
    parts = [p.replace("'", "").replace('"', "").strip() for p in l.split(',')]
    print(json.dumps({i: p for i, p in enumerate(parts)}, ensure_ascii=False))
