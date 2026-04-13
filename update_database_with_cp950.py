import sqlite3
import requests
import urllib3
from datetime import datetime
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def update_database_with_cp950():
    """使用 cp950 編碼重新處理資料庫"""
    
    print("=== 使用 cp950 編碼重新處理資料庫 ===")
    
    # 資料庫路徑
    db_path = "goss-v4/goss_v4.db"
    
    # 桃園機場資料來源
    urls = {
        "passenger_arrival": "https://www.taoyuan-airport.com/uploads/flightx/a_flight_v4.txt",
        "passenger_departure": "https://www.taoyuan-airport.com/uploads/flightx/d_flight_v4.txt",
        "cargo_arrival": "https://www.taoyuan-airport.com/uploads/flightx/af_flight_v4.txt",
        "cargo_departure": "https://www.taoyuan-airport.com/uploads/flightx/df_flight_v4.txt"
    }
    
    headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" }
    
    # 連接資料庫
    try:
        conn = sqlite3.connect(db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        print("✅ 資料庫連接成功")
    except Exception as e:
        print(f"❌ 資料庫連接失敗: {e}")
        return
    
    total_updated = 0
    
    for flight_type, url in urls.items():
        print(f"\n=== 處理 {flight_type} 資料 ===")
        
        try:
            # 使用 cp950 編碼抓取資料
            response = requests.get(url, headers=headers, verify=False, timeout=15)
            
            # 使用 cp950 優先策略
            try:
                content = response.content.decode('cp950').strip()
                print(f"  ✅ cp950 解碼成功")
            except UnicodeDecodeError:
                content = response.content.decode('utf-8', errors='ignore').strip()
                print(f"  ⚠️ utf-8 備援解碼")
            
            # 清理資料格式
            clean_text = content.replace("['", "").replace("']", "").replace("','", "\n").replace("', '", "\n")
            lines = clean_text.splitlines()
            
            print(f"  總行數: {len(lines)}")
            
            # 處理每行資料
            for line_num, line in enumerate(lines):
                if not line.strip():
                    continue
                    
                fields = line.split(',')
                
                # 確保有足夠的欄位
                if len(fields) < 18:
                    continue
                
                try:
                    # 解析欄位（依據 v4 格式）
                    # 0: terminal, 1: direction, 2: airline_code, 4: flight_no,
                    # 5: gate, 6: scheduled_date, 7: scheduled_time,
                    # 8: estimated_date, 9: estimated_time, 10: route, 13: status, 14: ac_type,
                    # 19: carousel/counter
                    
                    direction = fields[1].strip()
                    airline_code = fields[2].strip()
                    flight_no = fields[4].strip()
                    
                    if not airline_code or not flight_no:
                        continue
                    
                    # 建立 flight_key
                    scheduled_date = fields[6].strip()
                    flight_key = f"{scheduled_date}_{direction}_{airline_code}{flight_no}"
                    
                    # 檢查是否已存在
                    cursor.execute("SELECT COUNT(*) FROM flight_schedule WHERE flight_key = ?", (flight_key,))
                    exists = cursor.fetchone()[0] > 0
                    
                    if exists:
                        # 更新現有記錄
                        cursor.execute("""
                            UPDATE flight_schedule SET 
                                terminal = ?, direction = ?, airline_code = ?, flight_no = ?,
                                scheduled_date = ?, scheduled_time = ?, estimated_date = ?, estimated_time = ?,
                                route = ?, status = ?, ac_type = ?, gate = ?, carousel = ?,
                                last_updated = datetime('now')
                            WHERE flight_key = ?
                        """, (
                            fields[0].strip(), direction, airline_code, flight_no,
                            scheduled_date, fields[7].strip(), fields[8].strip(), fields[9].strip(),
                            fields[10].strip(), fields[13].strip(), fields[14].strip(), fields[5].strip(),
                            fields[19].strip() if len(fields) > 19 else "",
                            flight_key
                        ))
                    else:
                        # 插入新記錄
                        cursor.execute("""
                            INSERT INTO flight_schedule (
                                flight_key, terminal, direction, airline_code, flight_no,
                                scheduled_date, scheduled_time, estimated_date, estimated_time,
                                route, status, ac_type, gate, carousel, last_updated
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                        """, (
                            flight_key, fields[0].strip(), direction, airline_code, flight_no,
                            scheduled_date, fields[7].strip(), fields[8].strip(), fields[9].strip(),
                            fields[10].strip(), fields[13].strip(), fields[14].strip(), fields[5].strip(),
                            fields[19].strip() if len(fields) > 19 else ""
                        ))
                    
                    total_updated += 1
                    
                    # 每100筆顯示進度
                    if total_updated % 100 == 0:
                        print(f"  已處理 {total_updated} 筆...")
                        
                except Exception as e:
                    print(f"  第 {line_num+1} 行處理失敗: {e}")
                    continue
            
            print(f"  ✅ {flight_type} 處理完成")
            
        except Exception as e:
            print(f"  ❌ {flight_type} 處理失敗: {e}")
    
    # 提交變更
    conn.commit()
    conn.close()
    
    print(f"\n=== 處理完成 ===")
    print(f"總共更新/插入: {total_updated} 筆記錄")
    
    # 驗證資料庫更新
    verify_database_update(db_path)

def verify_database_update(db_path):
    """驗證資料庫更新結果"""
    
    print("\n=== 驗證資料庫更新 ===")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查總記錄數
        cursor.execute("SELECT COUNT(*) FROM flight_schedule")
        total_records = cursor.fetchone()[0]
        print(f"總記錄數: {total_records}")
        
        # 檢查最新記錄
        cursor.execute("""
            SELECT flight_key, airline_code, flight_no, route, status, last_updated 
            FROM flight_schedule 
            ORDER BY last_updated DESC 
            LIMIT 5
        """)
        
        print("最新5筆記錄:")
        for row in cursor.fetchall():
            flight_key, airline_code, flight_no, route, status, last_updated = row
            print(f"  {flight_key}: {airline_code}{flight_no} -> {route} ({status}) - {last_updated}")
        
        # 檢查中文字段是否正確
        cursor.execute("""
            SELECT DISTINCT route, status 
            FROM flight_schedule 
            WHERE route LIKE '%川%' OR route LIKE '%空%' OR status LIKE '%到%'
            LIMIT 10
        """)
        
        print("\n中文字段樣本:")
        for row in cursor.fetchall():
            route, status = row
            print(f"  目的地: {route}, 狀態: {status}")
        
        conn.close()
        
    except Exception as e:
        print(f"驗證失敗: {e}")

if __name__ == "__main__":
    update_database_with_cp950()