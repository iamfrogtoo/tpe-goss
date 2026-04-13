import requests
import sqlite3
import time
import os
import json
from datetime import datetime, timedelta
from io import StringIO
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 資料庫連接配置
DB_TIMEOUT = 30  # 30秒超時
DB_RETRY_COUNT = 3  # 重試次數
DB_RETRY_DELAY = 5  # 重試間隔秒數

DB_PATH = "goss_v4.db"

class TaoyuanDataProcessor:
    """桃園機場資料處理器（整合 v2 版本邏輯）"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self.taoyuan_urls = {
            "passenger_arrival": "https://www.taoyuan-airport.com/uploads/flightx/a_flight_v4.txt",
            "passenger_departure": "https://www.taoyuan-airport.com/uploads/flightx/d_flight_v4.txt",
            "cargo_arrival": "https://www.taoyuan-airport.com/uploads/flightx/af_flight_v4.txt",
            "cargo_departure": "https://www.taoyuan-airport.com/uploads/flightx/df_flight_v4.txt"
        }
    
    def get_db_connection(self):
        """獲取安全的資料庫連接（包含重試機制）"""
        for attempt in range(DB_RETRY_COUNT):
            try:
                conn = sqlite3.connect(self.db_path, timeout=DB_TIMEOUT)
                # 啟用 WAL 模式，支援多讀一寫
                conn.execute("PRAGMA journal_mode=WAL;")
                return conn
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < DB_RETRY_COUNT - 1:
                    print(f"[資料庫] 第{attempt+1}次重試，等待{DB_RETRY_DELAY}秒...")
                    time.sleep(DB_RETRY_DELAY)
                else:
                    raise e
        return None
    
    def fetch_taoyuan_txt(self, url):
        """從桃園機場抓取 txt 資料並解析（使用 cp950 編碼策略）"""
        
        # 先檢查是否有本地檔案
        local_filename = None
        if "a_flight_v4.txt" in url:
            local_filename = "a_flight_v4.txt"
        elif "d_flight_v4.txt" in url:
            local_filename = "d_flight_v4.txt"
        elif "af_flight_v4.txt" in url:
            local_filename = "af_flight_v4.txt"
        elif "df_flight_v4.txt" in url:
            local_filename = "df_flight_v4.txt"
        
        # 優先讀取本地檔案
        if local_filename and os.path.exists(local_filename):
            try:
                # 使用 cp950 編碼讀取本地檔案
                with open(local_filename, 'r', encoding='cp950') as f:
                    content = f.read().strip()
                print(f"[本地檔案] 使用 {local_filename} (cp950)")
            except Exception as e:
                print(f"[錯誤] 讀取本地檔案 {local_filename} 失敗: {e}")
                content = ""
        else:
            # 從官網抓取（使用 cp950 編碼策略）
            headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" }
            try:
                response = requests.get(url, headers=headers, verify=False, timeout=15)
                
                # 使用 v2 版本的 cp950 優先編碼策略
                try:
                    content = response.content.decode('cp950').strip()
                    print(f"[官網] 抓取 {url} (cp950 解碼成功)")
                except UnicodeDecodeError:
                    # cp950 失敗時使用 utf-8 備援
                    content = response.content.decode('utf-8', errors='ignore').strip()
                    print(f"[官網] 抓取 {url} (utf-8 備援解碼)")
                    
            except Exception as e:
                print(f"[錯誤] 抓取 {url} 失敗: {e}")
                return []
        
        # 清理並分割行（v2 版本邏輯）
        clean_text = content.replace("['", "").replace("']", "").replace("','", "\n").replace("', '", "\n")
        lines = clean_text.splitlines()
        
        flights = []
        for line in lines:
            if line.strip():
                # 解析每行資料
                fields = line.split(',')
                flights.append(fields)
        
        return flights
    
    def get_operational_day_window(self):
        """以凌晨03:00為分隔，取得今天的運營日起訖時間（v2 版本邏輯）"""
        now = datetime.now()
        cutoff = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if now >= cutoff:
            day_start = cutoff
            day_end   = cutoff + timedelta(days=1) - timedelta(seconds=1)
        else:
            day_start = cutoff - timedelta(days=1)
            day_end   = cutoff - timedelta(seconds=1)
        return day_start, day_end
    
    def is_in_daily_window(self, date_str, time_str):
        """判斷航班是否在今日運營日內（v2 版本邏輯）"""
        try:
            if not date_str or not time_str: return False, 0
            t_str = f"{time_str}:00" if time_str.count(":") == 1 else time_str
            flight_dt = datetime.strptime(f"{date_str} {t_str}", "%Y/%m/%d %H:%M:%S")
            day_start, day_end = self.get_operational_day_window()
            return day_start <= flight_dt <= day_end, flight_dt.timestamp()
        except: return False, 0
    
    def update_flight_schedule_from_taoyuan(self):
        """從桃園機場更新航班班表（即時離場/班表）"""
        print("=== 更新桃園機場航班班表 ===")
        
        total_upserted = 0
        
        # 使用安全的資料庫連接
        conn = self.get_db_connection()
        if not conn:
            print("[錯誤] 無法建立資料庫連接")
            return 0
            
        cursor = conn.cursor()
        
        try:
            for flight_type, url in self.taoyuan_urls.items():
                print(f"[班表] 處理 {flight_type} 資料...")
                taoyuan_data = self.fetch_taoyuan_txt(url)
                
                for f in taoyuan_data:
                    try:
                        # 欄位映射 (v4 格式)
                        # 0: terminal, 1: direction, 2: airline_code, 4: flight_no,
                        # 5: gate, 6: scheduled_date, 7: scheduled_time,
                        # 8: estimated_date, 9: estimated_time, 10: route, 13: status, 14: ac_type
                        
                        direction = f[1].strip().upper()
                        air_code = f[2].strip()
                        fno = f[4].strip()
                        
                        if not air_code or not fno: continue
                        
                        # 檢查是否在運營日內
                        s_date = f[6].strip()
                        s_time = f[7].strip()
                        in_daily, _ = self.is_in_daily_window(s_date, s_time)
                        if not in_daily: continue
                        
                        # 處理狀態
                        status_raw = f[13].upper() if len(f) > 13 else ""
                        status = self.parse_status(status_raw)
                        
                        # 判斷是否為貨機
                        is_cargo = 1 if flight_type.startswith("cargo") else 0
                        
                        # 插入或更新航班資料到 source_airport 表
                        cursor.execute('''
                            INSERT OR REPLACE INTO source_airport 
                            (flight_no, direction, gate, scheduled_time, is_cargo, 
                             terminal, airline, aircraft_type, date, updated_at, 
                             actual_time, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                        ''', (
                            fno, direction, f[5].strip(), s_time, is_cargo,
                            f[0].strip(), air_code, f[14].strip() if len(f) > 14 else "",
                            s_date, f[9].strip() if len(f) > 9 else "", status
                        ))
                        
                        # 同時更新 flight_schedule 表
                        cursor.execute('''
                            INSERT OR REPLACE INTO flight_schedule 
                            (flight_no, direction, gate, scheduled_time, is_cargo, 
                             updated_at, actual_time, status)
                            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                        ''', (
                            fno, direction, f[5].strip(), s_time, is_cargo,
                            f[9].strip() if len(f) > 9 else "", status
                        ))
                        
                        total_upserted += 1
                        
                    except Exception as e:
                        print(f"[錯誤] 處理航班資料失敗: {e}")
                        continue
            
            conn.commit()
            
        except Exception as e:
            print(f"[嚴重錯誤] 資料庫操作失敗: {e}")
        finally:
            conn.close()
        
        print(f"[完成] 班表更新完成: {total_upserted} 筆航班")
        return total_upserted
    
    def parse_status(self, status_raw):
        """解析航班狀態（v2 版本邏輯）"""
        status_raw = status_raw.upper()
        if "ARRIVED" in status_raw or "已到" in status_raw: 
            return "已抵達"
        elif "DEPARTED" in status_raw or "已飛" in status_raw: 
            return "已起飛"
        elif "CANCEL" in status_raw or "取消" in status_raw: 
            return "取消"
        elif "DELAY" in status_raw or "延誤" in status_raw: 
            return "延誤"
        elif "BOARDING" in status_raw or "登機" in status_raw: 
            return "登機中"
        else:
            return "準時"
    
    def update_gate_map(self):
        """更新機坪地圖資料"""
        print("=== 更新機坪地圖資料 ===")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 獲取當前活躍航班（從 source_airport 表獲取完整資訊）
        cursor.execute('''
            SELECT flight_no, direction, gate, terminal, scheduled_time, status, airline, aircraft_type
            FROM source_airport 
            WHERE status NOT IN ('已抵達', '已起飛', '取消')
            AND gate IS NOT NULL AND gate != ''
            ORDER BY scheduled_time
        ''')
        
        active_flights = cursor.fetchall()
        
        # 顯示機坪分配資訊
        gate_count = 0
        print("[機坪分配] 當前活躍航班機坪分配:")
        for flight in active_flights:
            flight_no, direction, gate, terminal, scheduled_time, status, airline, aircraft_type = flight
            
            print(f"  {airline}{flight_no} {direction} -> 機坪: {gate}, 航廈: {terminal}, 時間: {scheduled_time}")
            gate_count += 1
        
        conn.close()
        
        print(f"[完成] 機坪地圖更新: {gate_count} 筆機坪分配")
        return gate_count
    
    def get_real_time_departures(self):
        """獲取即時離場航班"""
        print("=== 獲取即時離場航班 ===")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 獲取即將離場的航班（未來2小時內）
        cursor.execute('''
            SELECT flight_no, airline, gate, terminal, scheduled_time, actual_time, status
            FROM source_airport 
            WHERE direction = 'D' 
            AND status NOT IN ('已起飛', '取消')
            AND scheduled_time > datetime('now')
            AND scheduled_time < datetime('now', '+2 hours')
            ORDER BY scheduled_time
        ''')
        
        departures = cursor.fetchall()
        
        # 顯示即時離場航班
        print("[即時離場] 未來2小時內離場航班:")
        for flight in departures[:10]:  # 只顯示前10筆
            flight_no, airline, gate, terminal, s_time, a_time, status = flight
            print(f"  {airline}{flight_no} -> 機坪:{gate} 時間:{s_time} 狀態:{status}")
        
        conn.close()
        
        print(f"[完成] 即時離場航班: {len(departures)} 筆")
        return departures
    
    def search_flights(self, query):
        """航班查詢功能"""
        print(f"=== 航班查詢: {query} ===")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 支援航班號、航空公司查詢
        cursor.execute('''
            SELECT flight_no, airline, direction, gate, terminal, 
                   scheduled_time, actual_time, status, aircraft_type
            FROM source_airport 
            WHERE flight_no LIKE ? OR airline LIKE ?
            ORDER BY scheduled_time
        ''', (f"%{query}%", f"%{query}%"))
        
        results = cursor.fetchall()
        conn.close()
        
        print(f"[完成] 查詢結果: {len(results)} 筆")
        return results
    
    def process_all_data(self):
        """一次處理所有桃園機場資料"""
        print("=== 開始處理桃園機場所有資料 ===")
        
        # 1. 更新航班班表
        schedule_count = self.update_flight_schedule_from_taoyuan()
        
        # 2. 更新機坪地圖
        gate_count = self.update_gate_map()
        
        # 3. 獲取即時離場航班
        departure_count = len(self.get_real_time_departures())
        
        print("\n=== 處理完成 ===")
        print(f"班表更新: {schedule_count} 筆")
        print(f"機坪分配: {gate_count} 筆")
        print(f"即時離場: {departure_count} 筆")
        
        return {
            "schedule_count": schedule_count,
            "gate_count": gate_count,
            "departure_count": departure_count
        }


def main():
    """主函數 - 單次執行版本"""
    processor = TaoyuanDataProcessor()
    
    # 一次處理所有資料
    results = processor.process_all_data()
    
    # 示範航班查詢
    print("\n=== 航班查詢示範 ===")
    search_results = processor.search_flights("CI")
    
    print("\n前5筆查詢結果:")
    for i, flight in enumerate(search_results[:5]):
        flight_no, airline, direction, gate, terminal, s_time, e_time, status, aircraft_type = flight
        print(f"{i+1}. {airline}{flight_no} {direction} 機坪:{gate} 航廈:{terminal} {s_time} {status}")


def main_loop():
    """主循環函數 - 自動10分鐘執行一次"""
    print("=== TPE GOSS 桃園機場資料處理系統 (自動循環版) ===")
    print("✅ 執行間隔: 10分鐘")
    print("✅ 功能: 即時離場/機坪地圖/班表/航班查詢")
    print("✅ 啟動時間:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    processor = TaoyuanDataProcessor()
    iteration = 0
    
    while True:
        iteration += 1
        print(f"\n=== 第 {iteration} 次執行 ===")
        print("時間:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        try:
            # 一次處理所有資料
            results = processor.process_all_data()
            
            print(f"✅ 處理完成: 班表{results['schedule_count']}筆, 機坪{results['gate_count']}筆, 離場{results['departure_count']}筆")
            
        except Exception as e:
            print(f"❌ 處理錯誤: {e}")
        
        # 等待10分鐘後再次執行
        print("⏰ 等待10分鐘後再次執行...")
        time.sleep(600)  # 10分鐘 = 600秒


if __name__ == "__main__":
    # 使用循環版本
    main_loop()