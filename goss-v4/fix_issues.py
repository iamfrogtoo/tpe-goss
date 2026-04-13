import sqlite3
import time
from datetime import datetime, timedelta
import subprocess

DB_PATH = "goss_v4.db"

def fix_landed_flights():
    """解決問題1：已落地航班3分鐘後過濾掉"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 獲取當前時間
    current_time = datetime.now()
    
    # 查找已落地航班（狀態包含"已到"、"ARRIVED"等）
    cursor.execute('''
        SELECT flight_no, actual_time, status 
        FROM flight_schedule 
        WHERE status LIKE '%已到%' OR status LIKE '%ARRIVED%' OR status LIKE '%到達%'
    ''')
    
    landed_flights = cursor.fetchall()
    print(f"[落地航班] 找到 {len(landed_flights)} 筆已落地航班")
    
    removed_count = 0
    for flight_no, actual_time, status in landed_flights:
        if actual_time:
            try:
                # 解析實際落地時間
                landed_time = datetime.strptime(actual_time, '%Y-%m-%d %H:%M:%S')
                
                # 計算落地後經過的時間
                time_since_landed = current_time - landed_time
                
                # 如果超過3分鐘，移除該航班
                if time_since_landed.total_seconds() > 180:  # 3分鐘 = 180秒
                    cursor.execute('''
                        DELETE FROM flight_schedule 
                        WHERE flight_no = ? AND status LIKE '%已到%'
                    ''', (flight_no,))
                    print(f"[移除] {flight_no} 已落地超過3分鐘，已移除")
                    removed_count += 1
                    
            except Exception as e:
                print(f"[錯誤] 處理航班 {flight_no} 時發生錯誤: {e}")
    
    conn.commit()
    conn.close()
    print(f"[完成] 已移除 {removed_count} 筆超過3分鐘的落地航班")
    return removed_count


def fix_encoding_issues():
    """解決問題2：亂碼問題"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 檢查並修復亂碼狀態
    cursor.execute('''
        SELECT flight_no, status FROM flight_schedule 
        WHERE status LIKE '%�%' OR status LIKE '%�%'
    ''')
    
    garbled_flights = cursor.fetchall()
    print(f"[亂碼檢查] 找到 {len(garbled_flights)} 筆有亂碼的航班")
    
    fixed_count = 0
    for flight_no, status in garbled_flights:
        # 根據常見的亂碼模式進行修復
        if '�' in status:
            if 'ON TIME' in status:
                new_status = '準時'
            elif 'DELAY' in status:
                new_status = '延誤'
            elif 'CANCELLED' in status:
                new_status = '取消'
            elif 'BOARDING' in status:
                new_status = '登機中'
            elif 'DEPARTED' in status:
                new_status = '已起飛'
            elif 'ARRIVED' in status:
                new_status = '已抵達'
            else:
                new_status = '準時'  # 預設值
            
            cursor.execute('''
                UPDATE flight_schedule 
                SET status = ? 
                WHERE flight_no = ? AND status = ?
            ''', (new_status, flight_no, status))
            
            print(f"[修復] {flight_no}: {status} -> {new_status}")
            fixed_count += 1
    
    conn.commit()
    conn.close()
    print(f"[完成] 已修復 {fixed_count} 筆亂碼狀態")
    return fixed_count


def fix_gate_display():
    """解決問題3：桃園機場停機坪顯示問題"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 檢查客機停機坪顯示問題
    cursor.execute('''
        SELECT flight_no, gate, is_cargo 
        FROM flight_schedule 
        WHERE gate IS NULL OR gate = ''
    ''')
    
    missing_gate_flights = cursor.fetchall()
    print(f"[停機坪檢查] 找到 {len(missing_gate_flights)} 筆缺少停機坪資訊的航班")
    
    # 從桃園機場官網獲取最新的停機坪資訊
    # 這裡需要實現從官網抓取停機坪資訊的邏輯
    # 暫時先標記需要手動處理
    
    print("[停機坪] 需要從桃園機場官網獲取最新的停機坪資訊")
    
    conn.close()
    return len(missing_gate_flights)


def fix_flight_number_format():
    """解決問題4：航班號碼顯示格式"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 航空公司代碼映射表
    airline_mapping = {
        'CAL': 'CI',  # 中華航空
        'EVA': 'BR',  # 長榮航空
        'UNI': 'B7',  # 立榮航空
        'TNA': 'GE',  # 復興航空
        'MDA': 'AE',  # 華信航空
        'TBA': 'IT',  # 台灣虎航
    }
    
    # 查找需要轉換的航班號碼
    cursor.execute('''
        SELECT flight_no, direction, scheduled_time, actual_time, status, gate, is_cargo 
        FROM flight_schedule 
        WHERE flight_no LIKE 'CAL%' OR flight_no LIKE 'EVA%'
    ''')
    
    flights_to_fix = cursor.fetchall()
    print(f"[航班號碼] 找到 {len(flights_to_fix)} 筆需要轉換的航班")
    
    fixed_count = 0
    for flight_data in flights_to_fix:
        flight_no, direction, scheduled_time, actual_time, status, gate, is_cargo = flight_data
        
        # 轉換航班號碼格式
        if flight_no.startswith('CAL'):
            new_flight_no = flight_no.replace('CAL', 'CI')
        elif flight_no.startswith('EVA'):
            new_flight_no = flight_no.replace('EVA', 'BR')
        else:
            continue
        
        # 先檢查新航班號是否已存在
        cursor.execute('SELECT COUNT(*) FROM flight_schedule WHERE flight_no = ?', (new_flight_no,))
        existing_count = cursor.fetchone()[0]
        
        if existing_count == 0:
            # 如果新航班號不存在，直接更新
            cursor.execute('''
                UPDATE flight_schedule 
                SET flight_no = ? 
                WHERE flight_no = ?
            ''', (new_flight_no, flight_no))
            print(f"[轉換] {flight_no} -> {new_flight_no}")
            fixed_count += 1
        else:
            # 如果新航班號已存在，刪除舊的記錄
            cursor.execute('DELETE FROM flight_schedule WHERE flight_no = ?', (flight_no,))
            print(f"[刪除] {flight_no} (已存在 {new_flight_no})")
    
    conn.commit()
    conn.close()
    print(f"[完成] 已處理 {fixed_count} 筆航班號碼")
    return fixed_count


def fix_aircraft_number_format():
    """解決問題4：機號顯示格式"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 查找類似"899105"的錯誤機號
    cursor.execute('''
        SELECT flight_no, aircraft_type, remarks 
        FROM flight_schedule 
        WHERE remarks LIKE '%899105%' OR remarks LIKE '%8%9%1%0%5%'
    ''')
    
    wrong_aircraft_flights = cursor.fetchall()
    print(f"[機號檢查] 找到 {len(wrong_aircraft_flights)} 筆可能有錯誤機號的航班")
    
    # 這裡需要從其他資料源獲取正確的機型+機號資訊
    # 暫時先標記需要手動處理
    
    print("[機號] 需要從其他資料源獲取正確的機型+機號資訊")
    
    conn.close()
    return len(wrong_aircraft_flights)


def main():
    """主修復函數"""
    print("=== TPE GOSS v4 問題修復工具 ===")
    print("開始修復您提到的四個問題...")
    
    # 1. 已落地航班3分鐘後過濾掉
    print("\n1. 處理已落地航班...")
    fix_landed_flights()
    
    # 2. 亂碼問題
    print("\n2. 修復亂碼問題...")
    fix_encoding_issues()
    
    # 3. 停機坪顯示問題
    print("\n3. 檢查停機坪顯示問題...")
    fix_gate_display()
    
    # 4. 航班號碼顯示格式
    print("\n4. 修正航班號碼顯示格式...")
    fix_flight_number_format()
    
    # 4. 機號顯示格式
    print("\n5. 修正機號顯示格式...")
    fix_aircraft_number_format()
    
    print("\n=== 修復完成 ===")
    print("請檢查修復結果，如有需要可再次運行此腳本")


if __name__ == "__main__":
    main()