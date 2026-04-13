import http.server
import socketserver
import threading
import time
import os
import json
from datetime import datetime

# 使用絕對路徑
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "goss_v4.db")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "live_data.json")

PORT = 8001
EXPORT_INTERVAL = 10  # 每10秒導出一次資料

def export_live_data():
    """導出實時資料到 JSON 檔案（修正版本）"""
    import sqlite3

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 修正：整合即時雷達資料與航班時刻表，只顯示桃園機場入境航班
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
            INNER JOIN flight_schedule fs ON lt.flight_no = fs.flight_no
            LEFT JOIN (
                SELECT flight_no, terminal, airline, aircraft_type, MAX(updated_at) as latest_update
                FROM source_airport
                GROUP BY flight_no
            ) sa ON lt.flight_no = sa.flight_no
            WHERE fs.direction = 'A'  -- 只顯示入境航班
            AND lt.updated_at > datetime('now', '-10 minutes')  -- 只顯示最近10分鐘的資料
            ORDER BY CAST(lt.alt AS INTEGER) DESC
            LIMIT 50
        ''')

        rows = cursor.fetchall()

        flights = []
        for row in rows:
            # 修正編碼問題：確保中文字段正確處理
            status_text = row[11] or ""
            # 嘗試解碼中文字段
            try:
                # 如果 status 是 bytes 類型，解碼為字串
                if isinstance(status_text, bytes):
                    status_text = status_text.decode('cp950', errors='ignore')
            except:
                pass
                
            flight = {
                "hex": row[0] or "",
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
                "status": status_text,  # 修正編碼處理
                "terminal": row[12] or "-",
                "airline": row[13] or (row[1][:2] if len(row[1]) > 2 else row[1]),
                "actype": row[14] or "",
                "reg": "",
                "baggage": ""
            }
            flights.append(flight)
        
        # 如果沒有即時資料，回退到航班時刻表
        if len(flights) == 0:
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
                WHERE direction = 'A'  -- 只顯示入境航班
                AND scheduled_time IS NOT NULL 
                ORDER BY scheduled_time
                LIMIT 50
            ''')
            
            rows = cursor.fetchall()
            for row in rows:
                status_text = row[5] or ""
                try:
                    if isinstance(status_text, bytes):
                        status_text = status_text.decode('cp950', errors='ignore')
                except:
                    pass
                    
                flight = {
                    "hex": "",
                    "code": row[0] or "",
                    "alt": "0",
                    "gs": 0,
                    "gate": row[2] or "",
                    "is_cargo": bool(row[6]),
                    "source": "schedule",
                    "updated_at": row[7],
                    "direction": row[1] or "A",
                    "scheduled_time": row[3] or "",
                    "actual_time": row[4] or "",
                    "status": status_text,
                    "terminal": "-",
                    "airline": row[0][:2] if len(row[0]) > 2 else row[0],
                    "actype": "",
                    "reg": "",
                    "baggage": ""
                }
                flights.append(flight)

        # 導出為 JSON（修正編碼問題）
        result = {
            "timestamp": datetime.now().isoformat(),
            "flights": flights
        }

        # 修正 JSON 輸出，確保所有字串都是有效的 Unicode
        def safe_string_encoder(obj):
            if isinstance(obj, str):
                # 確保字串是有效的 UTF-8
                try:
                    # 先嘗試解碼為 cp950（資料庫編碼），再編碼為 UTF-8
                    if any(ord(c) > 127 for c in obj):
                        # 如果包含非 ASCII 字符，嘗試解碼
                        try:
                            decoded = obj.encode('cp950').decode('utf-8', errors='ignore')
                        except:
                            decoded = obj.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
                        # 確保解碼後的字串是有效的
                        obj = decoded
                except:
                    pass
                
                # 移除所有可能導致 JSON 解析失敗的特殊字符
                # 只保留 ASCII 可打印字符和基本控制字符
                cleaned = ''.join(c for c in obj if 32 <= ord(c) <= 126 or c in '\n\r\t')
                
                # 確保字串不包含未配對的引號
                cleaned = cleaned.replace('"', '').replace('\'', '')
                
                # 如果字串為空，使用預設值
                if not cleaned:
                    cleaned = "N/A"
                    
                return cleaned
            return str(obj)

        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=safe_string_encoder)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 成功導出 {len(flights)} 筆航班資料")
        return True

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 導出失敗: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def export_thread():
    """定時導出資料的執行緒"""
    while True:
        export_live_data()
        time.sleep(EXPORT_INTERVAL)

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_GET(self):
        if self.path == '/api/flights':
            # 直接從檔案讀取資料
            try:
                with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
                    data = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data.encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_msg = json.dumps({"error": str(e)})
                self.wfile.write(error_msg.encode('utf-8'))
        else:
            super().do_GET()

def start_server():
    """啟動伺服器"""
    # 先導出一次資料
    export_live_data()
    
    # 啟動定時導出執行緒
    thread = threading.Thread(target=export_thread, daemon=True)
    thread.start()
    print("資料導出執行緒已啟動，每 10 秒導出一次")
    
    # 啟動 HTTP 伺服器
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"API 伺服器啟動在端口 {PORT}")
        print(f"API 端點: http://localhost:{PORT}/api/flights")
        print(f"資料檔案: {OUTPUT_PATH}")
        httpd.serve_forever()

if __name__ == "__main__":
    start_server()