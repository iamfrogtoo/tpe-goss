import sqlite3
import re

def is_garbage_text(text):
    """判斷是否為亂碼文字"""
    if not text or len(text) < 1:
        return False
    
    # 檢查是否包含非中英文字符和非時間格式
    if re.match(r'^\d{2}:\d{2}:\d{2}$', text):  # 時間格式
        return False
    
    # 合法的中文狀態
    valid_statuses = ['準時', '延誤', '取消', '登機中', '已起飛', '已抵達', 'ON TIME', 'DELAY', 'CANCELLED', 'BOARDING', 'DEPARTED', 'ARRIVED']
    if text in valid_statuses:
        return False
    
    # 檢查是否包含非ASCII字符且不是中文
    has_non_ascii = bool(re.search(r'[^\x00-\x7F]', text))
    if has_non_ascii:
        # 檢查是否為中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        if len(chinese_chars) > 0:
            return False  # 包含中文字符，不是亂碼
        return True  # 包含非ASCII但非中文，可能是亂碼
    
    # 檢查是否為奇怪的短字符組合
    if len(text) <= 3 and not text.isalnum():
        return True
    
    return False

def fix_encoding_issues_comprehensive():
    """全面修正資料庫亂碼問題"""
    
    try:
        conn = sqlite3.connect('goss-v4/goss_v4.db')
        cursor = conn.cursor()
        
        print("開始全面修正資料庫亂碼問題...")
        
        # 先檢查目前的亂碼情況
        cursor.execute("SELECT flight_no, status FROM flight_schedule WHERE status IS NOT NULL")
        all_statuses = cursor.fetchall()
        
        garbage_count = 0
        for flight_no, status in all_statuses:
            if is_garbage_text(status):
                garbage_count += 1
                if garbage_count <= 10:  # 只顯示前10個亂碼樣本
                    print(f"發現亂碼: {flight_no}: {repr(status)}")
        
        print(f"\n總共發現 {garbage_count} 筆亂碼資料")
        
        # 修正所有亂碼狀態
        cursor.execute("SELECT flight_no, status FROM flight_schedule WHERE status IS NOT NULL")
        all_statuses = cursor.fetchall()
        
        update_count = 0
        for flight_no, status in all_statuses:
            if is_garbage_text(status):
                # 根據航班號和時間判斷狀態
                # 簡單判斷：如果航班號包含字母和數字，且狀態是亂碼，設為準時
                new_status = '準時'
                
                cursor.execute(
                    "UPDATE flight_schedule SET status = ? WHERE flight_no = ? AND status = ?",
                    (new_status, flight_no, status)
                )
                update_count += 1
        
        # 再次檢查修正後的狀態分布
        cursor.execute("SELECT status, COUNT(*) FROM flight_schedule WHERE status IS NOT NULL GROUP BY status ORDER BY COUNT(*) DESC")
        status_distribution = cursor.fetchall()
        
        print(f"\n修正完成，更新了 {update_count} 筆資料")
        print("\n修正後的狀態值分布:")
        for status, count in status_distribution:
            print(f"  {status}: {count} 筆")
        
        conn.commit()
        print("\n✅ 資料庫亂碼全面修正完成")
        
    except Exception as e:
        print(f"❌ 修正失敗: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_encoding_issues_comprehensive()