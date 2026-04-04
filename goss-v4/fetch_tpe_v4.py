import requests
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "goss_v4.db"
# 使用你剛發現的正確 flightx 路徑
URLS = {
    "passenger": "https://www.taoyuan-airport.com/uploads/flightx/a_flight_v4.txt",
    "cargo": "https://www.taoyuan-airport.com/uploads/flightx/af_flight_v4.txt"
}

def update_schedules():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 获取当前日期
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    for category, url in URLS.items():
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            if res.status_code != 200:
                print(f"❌ {category} 抓取失敗: {res.status_code}")
                continue
                
            lines = res.text.strip().splitlines()
            is_cargo = 1 if category == "cargo" else 0
            count = 0
            
            for line in lines:
                p = line.split(',')
                # 4.0 核心修正：不管是 18 還是 20 欄，前 6 欄位置是固定的
                # 0:航廈, 1:進出, 2:航空公司, 3:機型, 4:班號, 5:機坪
                if len(p) < 6 or "航廈" in line:
                    continue
                
                terminal = p[0].strip()
                direction = p[1].strip() # A/D
                airline = p[2].strip()
                aircraft_type = p[3].strip()
                flight_number = p[4].strip()
                gate = p[5].strip()
                scheduled_time = p[7].strip() if len(p) > 7 else "00:00"
                actual_time = p[8].strip() if len(p) > 8 else ""
                status = p[9].strip() if len(p) > 9 else ""
                f_no = f"{airline}{flight_number}"
                
                # 写入机场分区表
                cursor.execute('''
                    INSERT INTO source_airport 
                    (flight_no, direction, gate, scheduled_time, actual_time, status, is_cargo, terminal, airline, aircraft_type, date, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (f_no, direction, gate, scheduled_time, actual_time, status, is_cargo, terminal, airline, aircraft_type, current_date))
                
                # 更新航班计划表
                cursor.execute('''
                    INSERT INTO flight_schedule (flight_no, direction, gate, scheduled_time, actual_time, status, is_cargo, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(flight_no) DO UPDATE SET
                        direction=excluded.direction,
                        gate=excluded.gate,
                        scheduled_time=excluded.scheduled_time,
                        actual_time=excluded.actual_time,
                        status=excluded.status,
                        is_cargo=excluded.is_cargo,
                        updated_at=CURRENT_TIMESTAMP
                ''', (f_no, direction, gate, scheduled_time, actual_time, status, is_cargo))
                count += 1
            
            conn.commit()
            print(f"{category} 同步成功: {count} 筆 (含貨機專用機坪)")
            
        except Exception as e:
            print(f"{category} 異常: {e}")
    
    # 处理延误航班，确保延误超过4小时的航班不会被遗漏
    try:
        # 获取当前时间
        now = datetime.now()
        # 计算时间范围：前4小时到后8小时
        start_time = now - timedelta(hours=4)
        end_time = now + timedelta(hours=8)
        
        # 查询可能延误的入境航班
        cursor.execute('''
            SELECT flight_no, scheduled_time, actual_time, status 
            FROM flight_schedule 
            WHERE direction = 'A' 
            AND updated_at > datetime('now', '-24 hours')
        ''')
        
        delayed_flights = 0
        for row in cursor.fetchall():
            flight_no, scheduled_time, actual_time, status = row
            
            # 检查是否有延误信息
            if status and ('延誤' in status or 'DELAY' in status):
                # 对于延误航班，确保它们仍然在追踪范围内
                cursor.execute('''
                    UPDATE flight_schedule 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE flight_no = ?
                ''', (flight_no,))
                delayed_flights += 1
        
        if delayed_flights > 0:
            conn.commit()
            print(f"✅ 處理延誤航班: {delayed_flights} 筆")
            
    except Exception as e:
        print(f"❌ 處理延誤航班異常: {e}")
    
    conn.close()

if __name__ == "__main__":
    update_schedules()