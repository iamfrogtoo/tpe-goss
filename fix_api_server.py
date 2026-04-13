import sqlite3
import json
from datetime import datetime

def fix_api_server():
    """修復 API 伺服器，導出航班時刻表資料"""
    
    print("=== 修復 API 伺服器資料導出 ===")
    
    db_path = "goss-v4/goss_v4.db"
    output_path = "goss-v4/live_data.json"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查詢航班時刻表資料（而不是即時雷達資料）
        cursor.execute('''
            SELECT 
                flight_no,
                direction,
                gate,
                scheduled_time,
                actual_time,
                status,
                is_cargo,
                updated_at
            FROM flight_schedule 
            WHERE scheduled_time IS NOT NULL 
            ORDER BY scheduled_time
            LIMIT 100
        ''')
        
        rows = cursor.fetchall()
        
        flights = []
        for row in rows:
            flight = {
                "code": row[0] or "",
                "direction": row[1] or "A",
                "gate": row[2] or "",
                "scheduled_time": row[3] or "",
                "actual_time": row[4] or "",
                "status": row[5] or "",
                "is_cargo": bool(row[6]),
                "updated_at": row[7],
                "alt": "0",
                "gs": 0,
                "source": "schedule",
                "terminal": "-",
                "airline": row[0][:2] if len(row[0]) > 2 else row[0],
                "actype": "",
                "reg": "",
                "baggage": ""
            }
            flights.append(flight)
        
        # 導出為 JSON
        result = {
            "timestamp": datetime.now().isoformat(),
            "flights": flights
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 成功導出 {len(flights)} 筆航班資料")
        
        # 顯示前3筆資料
        print("前3筆航班資料:")
        for i, flight in enumerate(flights[:3]):
            print(f"  {i+1}. {flight['code']} ({flight['direction']}): {flight['scheduled_time']} - {flight['status']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 導出失敗: {e}")

def check_current_api_output():
    """檢查當前 API 輸出的資料"""
    
    print("\n=== 檢查當前 API 輸出 ===")
    
    output_path = "goss-v4/live_data.json"
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"資料時間戳: {data.get('timestamp', 'N/A')}")
        print(f"航班數量: {len(data.get('flights', []))}")
        
        if data.get('flights'):
            print("前3筆航班:")
            for i, flight in enumerate(data['flights'][:3]):
                print(f"  {i+1}. {flight.get('code', 'N/A')} - {flight.get('status', 'N/A')}")
        else:
            print("❌ 沒有航班資料")
            
    except Exception as e:
        print(f"❌ 讀取失敗: {e}")

if __name__ == "__main__":
    check_current_api_output()
    fix_api_server()