import sqlite3
import json
import os
from datetime import datetime

# 使用绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "goss_v4.db")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "live_data.json")

def export_live_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 获取实时交通数据，并与航班计划表关联获取更多信息
        cursor.execute('''
            SELECT 
                lt.hex,
                lt.flight_no,
                lt.alt,
                lt.gs,
                lt.gate,
                lt.is_cargo,
                lt.source,
                lt.updated_at,
                fs.direction,
                fs.scheduled_time,
                fs.actual_time,
                fs.status,
                sa.terminal,
                sa.airline,
                sa.aircraft_type
            FROM live_traffic lt
            LEFT JOIN flight_schedule fs ON lt.flight_no = fs.flight_no
            LEFT JOIN (
                SELECT flight_no, terminal, airline, aircraft_type, MAX(updated_at) as latest_update
                FROM source_airport
                GROUP BY flight_no
            ) sa ON lt.flight_no = sa.flight_no
            WHERE lt.updated_at > datetime('now', '-5 minutes')
            ORDER BY CAST(lt.alt AS INTEGER) ASC
        ''')
        
        rows = cursor.fetchall()
        
        flights = []
        for row in rows:
            flight = {
                "hex": row[0],
                "code": row[1] or "",
                "alt": row[2] or "0",
                "gs": row[3] or 0,
                "gate": row[4] or "",
                "is_cargo": bool(row[5]),
                "source": row[6] or "",
                "updated_at": row[7],
                "direction": row[8] or "A",
                "scheduled_time": row[9] or "",
                "actual_time": row[10] or "",
                "status": row[11] or "",
                "terminal": row[12] or "-",
                "airline": row[13] or "",
                "actype": row[14] or "",
                "reg": ""  # 註冊編號後續可以添加
            }
            
            # 只保留進場航班（direction == 'A' 或沒有 direction 資訊）
            if flight["direction"] == "A" or not flight["direction"]:
                flights.append(flight)
        
        # 导出为 JSON
        result = {
            "timestamp": datetime.now().isoformat(),
            "flights": flights
        }
        
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 成功导出 {len(flights)} 架航班数据到 {OUTPUT_PATH}")
        return True
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    export_live_data()
