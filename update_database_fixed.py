import sqlite3
import requests
import urllib3
from datetime import datetime
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def update_database_with_cp950():
    """使用 cp950 編碼重新處理資料庫（符合實際資料庫結構）"""
    
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
                    # 8: estimated_date, 9: estimated_time, 10: route, 13: status, 14: ac_type
                    
                    direction = fields[1].strip()
                    airline_code = fields[2].strip()
                    flight_no = fields[4].strip()
                    
                    if not airline_code or not flight_no:
                        continue
                    
                    # 建立完整的航班號碼（航空公司代碼 + 航班號）
                    full_flight_no = f"{airline_code}{flight_no}"
                    
                    # 判斷是否為貨機
                    is_cargo = 1 if flight_type.startswith("cargo") else 0
                    
                    # 檢查是否已存在
                    cursor.execute("SELECT COUNT(*) FROM flight_schedule WHERE flight_no = ?", (full_flight_no,))
                    exists = cursor.fetchone()[0] > 0
                    
                    if exists:
                        # 更新現有記錄
                        cursor.execute("""
                            UPDATE flight_schedule SET 
                                direction = ?, gate = ?, scheduled_time = ?, is_cargo = ?,
                                actual_time = ?, status = ?, updated_at = datetime('now')
                            WHERE flight_no = ?
                        """, (
                            direction, fields[5].strip(), fields[7].strip(), is_cargo,
                            fields[9].strip(), fields[13].strip(), full_flight_no
                        ))
                    else:
                        # 插入新記錄
                        cursor.execute("""
                            INSERT INTO flight_schedule (
                                flight_no, direction, gate, scheduled_time, is_cargo,
                                actual_time, status, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                        """, (
                            full_flight_no, direction, fields[5].strip(), fields[7].strip(), is_cargo,
                            fields[9].strip(), fields[13].strip()
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
            SELECT flight_no, direction, gate, scheduled_time, actual_time, status, updated_at 
            FROM flight_schedule 
            ORDER BY updated_at DESC 
            LIMIT 5
        """)
        
        print("最新5筆記錄:")
        for row in cursor.fetchall():
            flight_no, direction, gate, scheduled_time, actual_time, status, updated_at = row
            print(f"  {flight_no} ({direction}): 表定{scheduled_time} 實際{actual_time} - {status} - {updated_at}")
        
        # 檢查中文字段是否正確
        cursor.execute("""
            SELECT DISTINCT status 
            FROM flight_schedule 
            WHERE status LIKE '%到%' OR status LIKE '%誤%' OR status LIKE '%消%'
            LIMIT 10
        """)
        
        print("\n航班狀態樣本（中文字段）:")
        for row in cursor.fetchall():
            status = row[0]
            print(f"  {status}")
        
        # 檢查貨機和客機的分佈
        cursor.execute("SELECT is_cargo, COUNT(*) FROM flight_schedule GROUP BY is_cargo")
        
        print("\n航班類型分佈:")
        for row in cursor.fetchall():
            is_cargo, count = row
            flight_type = "貨機" if is_cargo else "客機"
            print(f"  {flight_type}: {count} 筆")
        
        conn.close()
        
    except Exception as e:
        print(f"驗證失敗: {e}")

if __name__ == "__main__":
    update_database_with_cp950()