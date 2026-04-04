import traceback
try:
    from datetime import datetime
    import requests
    import urllib3
    urllib3.disable_warnings()
    url_a = 'https://www.taoyuan-airport.com/uploads/flightx/a_flight_v4.txt'
    resp = requests.get(url_a, verify=False)
    raw_text = resp.content.decode('utf-8', errors='ignore')
    clean_text = raw_text.replace("['", "").replace("']", "").replace("','", "\n").replace("', '", "\n")
    lines = clean_text.splitlines()

    print(f"Total lines: {len(lines)}")
    flights = []
    # Find IT201 or TTW201
    for line in lines:
        parts = [p.replace("'", "").replace('"', "").strip() for p in line.split(",")]
        if len(parts) > 7 and '201' in parts[4]:
            check_date = parts[6].strip()
            check_time = parts[7].strip()
            t_str = f"{check_time}:00" if check_time.count(":") == 1 else check_time
            dt_str = f"{check_date} {t_str}"
            try:
                flight_dt = datetime.strptime(dt_str, "%Y/%m/%d %H:%M:%S")
                ts = flight_dt.timestamp()
            except Exception as e:
                ts = -1
            print("Flight:", parts[2], parts[4], "dt:", dt_str, "ts:", ts)
except Exception as e:
    traceback.print_exc()
