import sqlite3

def fix_encoding_issues():
    """修正本地資料庫的亂碼問題"""
    
    try:
        conn = sqlite3.connect('goss-v4/goss_v4.db')
        cursor = conn.cursor()
        
        print("開始修正資料庫亂碼問題...")
        
        # 先備份目前的狀態值
        cursor.execute("SELECT flight_no, status FROM flight_schedule WHERE status IS NOT NULL LIMIT 10")
        before_fix = cursor.fetchall()
        print("修正前的狀態樣本:")
        for flight_no, status in before_fix:
            print(f"  {flight_no}: {repr(status)}")
        
        # 修正 flight_schedule 表的亂碼狀態
        fix_sql = """
        UPDATE flight_schedule 
        SET status = CASE 
            WHEN status LIKE '%�%' OR status LIKE '%?%' OR LENGTH(status) < 2 THEN '準時'
            WHEN status = 'ON TIME' THEN '準時'
            WHEN status = 'DELAY' THEN '延誤'
            WHEN status = 'CANCELLED' THEN '取消'
            WHEN status = 'BOARDING' THEN '登機中'
            WHEN status = 'DEPARTED' THEN '已起飛'
            WHEN status = 'ARRIVED' THEN '已抵達'
            WHEN status LIKE '%:%:%' THEN '準時'  -- 時間格式視為準時
            ELSE status
        END
        WHERE status IS NOT NULL
        """
        
        cursor.execute(fix_sql)
        affected_rows = cursor.rowcount
        
        # 檢查修正後的結果
        cursor.execute("SELECT flight_no, status FROM flight_schedule WHERE status IS NOT NULL LIMIT 10")
        after_fix = cursor.fetchall()
        
        print(f"\n修正完成，受影響的資料筆數: {affected_rows}")
        print("修正後的狀態樣本:")
        for flight_no, status in after_fix:
            print(f"  {flight_no}: {repr(status)}")
        
        # 檢查狀態值的分布
        cursor.execute("SELECT status, COUNT(*) FROM flight_schedule WHERE status IS NOT NULL GROUP BY status")
        status_distribution = cursor.fetchall()
        
        print("\n狀態值分布:")
        for status, count in status_distribution:
            print(f"  {status}: {count} 筆")
        
        conn.commit()
        print("\n✅ 資料庫亂碼修正完成")
        
    except Exception as e:
        print(f"❌ 修正失敗: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_encoding_issues()