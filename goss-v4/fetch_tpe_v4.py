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
                # 徹底修正：根據實際 TXT 檔案格式重新調整欄位索引
                # 0:航廈, 1:進出, 2:航空公司, 3:目的地城市, 4:航班號碼, 5:登機門, 6:日期, 7:時間...
                if len(p) < 10 or "航廈" in line:
                    continue
                
                terminal = p[0].strip()
                direction = p[1].strip() # A/D
                airline_iata = p[2].strip()  # IATA 代碼
                destination_city = p[3].strip()  # 目的地城市（中文）
                flight_number = p[4].strip()     # 航班號碼（第5欄）
                gate = p[5].strip()              # 登機門
                
                # 機型在第 14 欄（索引 13）
                aircraft_type = p[13].strip() if len(p) > 13 else ""
                
                # IATA 代碼轉換為 ICAO 代碼
                iata_to_icao = {
                    'BR': 'EVA',  # 長榮航空
                    'CI': 'CAL',  # 中華航空
                    'AE': 'MDA',  # 華信航空
                    'B7': 'UIA',  # 立榮航空
                    'JX': 'SJX',  # 星宇航空
                    'IT': 'TTW',  # 台灣虎航
                    'CA': 'CCA',  # 中國國際航空
                    'CZ': 'CSN',  # 中國南方航空
                    'MU': 'CES',  # 中國東方航空
                    'FM': 'CSH',  # 上海航空
                    'ZH': 'CSZ',  # 深圳航空
                    'MF': 'CXA',  # 廈門航空
                    'SC': 'CDG',  # 山東航空
                    'HU': 'CHH',  # 海南航空
                    'JD': 'CBJ',  # 首都航空
                    '9C': 'CQH',  # 春秋航空
                    'HO': 'DKH',  # 吉祥航空
                    '3U': 'CSC',  # 四川航空
                    'JL': 'JAL',  # 日本航空
                    'NH': 'ANA',  # 全日空
                    'MM': 'APJ',  # 樂桃航空
                    'GK': 'JJP',  # 捷星日本
                    'KZ': 'NCA',  # 日本貨運航空
                    '7G': 'SFJ',  # 星悅航空
                    'BC': 'SKY',  # 天馬航空
                    'KE': 'KAL',  # 大韓航空
                    'OZ': 'AAR',  # 韓亞航空
                    '7C': 'JJA',  # 濟州航空
                    'LJ': 'JNA',  # 真航空
                    'BX': 'ABL',  # 釜山航空
                    'TW': 'TWB',  # 德威航空
                    'ZE': 'ESR',  # 易斯達航空
                    'CX': 'CPA',  # 國泰航空
                    'UO': 'HKE',  # 香港快運
                    'HX': 'CRK',  # 香港航空
                    'HB': 'HGB',  # 香港航空
                    'NX': 'AMU',  # 澳門航空
                    'SQ': 'SIA',  # 新加坡航空
                    'TR': 'TGW',  # 酷航
                    'MH': 'MAS',  # 馬來西亞航空
                    'OD': 'MXD',  # 馬印航空
                    'D7': 'XAX',  # 亞洲航空
                    'AK': 'AXM',  # 亞洲航空
                    'TG': 'THA',  # 泰國航空
                    'SL': 'TLM',  # 泰國獅航
                    'VZ': 'TVJ',  # 泰國越捷航空
                    'FD': 'AIQ',  # 泰國亞洲航空
                    'WE': 'THD',  # 泰國微笑航空
                    'VN': 'HVN',  # 越南航空
                    'VJ': 'VJC',  # 越捷航空
                    'QH': 'BAV',  # 越南航空
                    'PR': 'PAL',  # 菲律賓航空
                    '5J': 'CEB',  # 宿霧太平洋航空
                    'Z2': 'APG',  # 菲律賓亞洲航空
                    'RW': 'RWA',  # 菲律賓航空
                    'BI': 'RBA',  # 汶萊皇家航空
                    'GA': 'GIA',  # 印尼鷹航
                    'UA': 'UAL',  # 聯合航空
                    'DL': 'DAL',  # 達美航空
                    'AC': 'ACA',  # 加拿大航空
                    'KL': 'KLM',  # 荷蘭皇家航空
                    'TK': 'THY',  # 土耳其航空
                    'NZ': 'ANZ',  # 紐西蘭航空
                    'EK': 'UAE',  # 阿聯酋航空
                    'EY': 'ETD',  # 阿提哈德航空
                    '5X': 'UPS',  # UPS航空
                    'FX': 'FDX',  # 聯邦快遞
                    'PO': 'PAC',  # 極地航空
                    'LD': 'AHK',  # 香港華民航空
                    'RH': 'HKC',  # 香港航空
                    'CV': 'CLX',  # 盧森堡貨運航空
                    'CK': 'CKK',  # 中國貨運航空
                    'IC': 'ICV',  # 印度航空
                    'KJ': 'AANA', # 亞洲航空
                    'O3': 'CSS',  # 順豐航空
                    'QV': 'LAO',  # 寮國航空
                    '8K': 'KMI',  # 馬耳他航空
                    'RF': 'EOK',  # 遠東航空
                    'K6': 'KHM',  # 柬埔寨航空
                    'QD': 'QDA'   # 青島航空
                }
                
                # 轉換為 ICAO 代碼
                airline_icao = iata_to_icao.get(airline_iata, airline_iata)
                
                # 組合完整的航班號碼（使用 ICAO 代碼）
                f_no = f"{airline_icao}{flight_number}"
                
                # 時間欄位修正
                scheduled_date = p[6].strip() if len(p) > 6 else ""
                scheduled_time = p[7].strip() if len(p) > 7 else "00:00"
                actual_date = p[8].strip() if len(p) > 8 else ""
                actual_time = p[9].strip() if len(p) > 9 else ""
                status = p[12].strip() if len(p) > 12 else ""  # 狀態在第 13 欄
                
                # 修正狀態欄位編碼問題
                if status:
                    # 更可靠的編碼處理
                    try:
                        # 先檢查是否為有效的 UTF-8
                        status.encode('utf-8')
                    except UnicodeEncodeError:
                        # 如果不是有效的 UTF-8，嘗試多種解碼方式
                        for encoding in ['big5', 'cp950', 'latin-1', 'gbk']:
                            try:
                                status = status.encode('latin-1').decode(encoding, errors='ignore')
                                break
                            except:
                                continue
                    
                    # 清理特殊字元和亂碼
                    status = status.replace('\x00', '').replace('\ufffd', '').strip()
                    
                    # 如果狀態仍然包含亂碼或為空，使用預設值
                    if not status or any(char in status for char in ['�', '\x00', '\ufffd', '\x80', '\x81', '\x82']):
                        if direction == 'A':
                            status = 'ON TIME'
                        else:
                            status = '準時'
                
                # 写入机场分区表
                cursor.execute('''
                    INSERT INTO source_airport 
                    (flight_no, direction, gate, scheduled_time, actual_time, status, is_cargo, terminal, airline, aircraft_type, date, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (f_no, direction, gate, scheduled_time, actual_time, status, is_cargo, terminal, airline_iata, aircraft_type, current_date))
                
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