import http.server
import socketserver
import threading
import time
import os
import json
from datetime import datetime

# 使用绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "goss_v4.db")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "live_data.json")

PORT = 8001
EXPORT_INTERVAL = 10  # 每10秒导出一次数据

def export_live_data():
    """导出实时数据到 JSON 文件"""
    import sqlite3
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取实时交通数据，并与航班计划表关联获取更多信息
        # 修正：只获取有航班计划的航班（与 bridge_v4.py 筛选逻辑一致）
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
            INNER JOIN flight_schedule fs ON lt.flight_no = fs.flight_no  -- 只保留有航班计划的航班
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
                "reg": "",
                "baggage": ""
            }
            
            # 修正：保留所有有航班计划的航班（与 bridge_v4.py 筛选逻辑一致）
            # 不再限制只显示进场航班，让前端根据 direction 字段自行筛选
            flights.append(flight)
        
        # 导出为 JSON
        result = {
            "timestamp": datetime.now().isoformat(),
            "flights": flights
        }
        
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 成功导出 {len(flights)} 架航班数据")
        return True
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 导出失败: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def export_worker():
    """后台线程，定期导出数据"""
    while True:
        export_live_data()
        time.sleep(EXPORT_INTERVAL)

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """支持 CORS 的请求处理器"""
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        # 支援新舊端點
        if self.path == '/live_data.json' or self.path == '/' or self.path.startswith('/api/flights'):
            self.path = '/live_data.json'
        return super().do_GET()

def start_server():
    """启动 HTTP 服务器"""
    # 切换到脚本目录
    os.chdir(SCRIPT_DIR)
    
    # 启动后台导出线程
    export_thread = threading.Thread(target=export_worker, daemon=True)
    export_thread.start()
    print(f"✅ 数据导出线程已启动，每 {EXPORT_INTERVAL} 秒导出一次")
    
    # 启动 HTTP 服务器
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"🚀 API 服务器已启动在 http://localhost:{PORT}")
        print(f"📡 实时数据端点: http://localhost:{PORT}/live_data.json")
        print("=" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 服务器已停止")
            httpd.shutdown()

if __name__ == "__main__":
    start_server()
