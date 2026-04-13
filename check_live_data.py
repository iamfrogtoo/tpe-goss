import sqlite3
from datetime import datetime, timedelta

def check_live_traffic():
    """檢查即時航班資料"""
    
    try:
        conn = sqlite3.connect('goss-v4/goss_v4.db')
        cursor = conn.cursor()
        
        print("檢查 live_traffic 表資料:")
        
        # 檢查資料總數
        cursor.execute("SELECT COUNT(*) FROM live_traffic")
        total_count = cursor.fetchone()[0]
        print(f"live_traffic 總資料筆數: {total_count}")
        
        # 檢查最近5分鐘的資料
        five_minutes_ago = (datetime.now() - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT COUNT(*) FROM live_traffic WHERE updated_at > ?", (five_minutes_ago,))
        recent_count = cursor.fetchone()[0]
        print(f"最近5分鐘內的資料筆數: {recent_count}")
        
        # 檢查資料樣本
        cursor.execute("SELECT hex, flight_no, alt, gate, updated_at FROM live_traffic ORDER BY updated_at DESC LIMIT 10")
        recent_flights = cursor.fetchall()
        
        print("\n最近的10筆航班資料:")
        for flight in recent_flights:
            hex_code, flight_no, alt, gate, updated_at = flight
            print(f"  {flight_no} ({hex_code}): 高度 {alt}, 登機門 {gate}, 更新時間 {updated_at}")
        
        # 檢查與航班計畫表的關聯
        print("\n檢查與航班計畫表的關聯:")
        cursor.execute('''
            SELECT COUNT(*) 
            FROM live_traffic lt
            INNER JOIN flight_schedule fs ON lt.flight_no = fs.flight_no
            WHERE lt.updated_at > ?
        ''', (five_minutes_ago,))
        matched_count = cursor.fetchone()[0]
        print(f"最近5分鐘內有航班計畫匹配的資料筆數: {matched_count}")
        
        if matched_count == 0 and recent_count > 0:
            print("\n⚠️ 警告: 有即時航班資料但沒有匹配的航班計畫")
            
            # 檢查哪些航班沒有匹配
            cursor.execute('''
                SELECT lt.flight_no, lt.updated_at
                FROM live_traffic lt
                LEFT JOIN flight_schedule fs ON lt.flight_no = fs.flight_no
                WHERE lt.updated_at > ? AND fs.flight_no IS NULL
            ''', (five_minutes_ago,))
            unmatched_flights = cursor.fetchall()
            
            if unmatched_flights:
                print("未匹配的航班:")
                for flight_no, updated_at in unmatched_flights:
                    print(f"  {flight_no} (更新於 {updated_at})")
        
        conn.close()
        
    except Exception as e:
        print(f"檢查失敗: {e}")

if __name__ == "__main__":
    check_live_traffic()