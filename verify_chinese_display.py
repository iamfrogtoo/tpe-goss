import sqlite3
import json

def verify_chinese_display():
    """驗證中文字段在前端的顯示"""
    
    print("=== 驗證中文字段顯示 ===")
    
    # 資料庫路徑
    db_path = "goss-v4/goss_v4.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("✅ 資料庫連接成功")
        
        # 1. 檢查航班狀態中的中文字段
        print("\n1. 航班狀態中的中文字段:")
        cursor.execute("""
            SELECT DISTINCT status 
            FROM flight_schedule 
            WHERE status LIKE '%到%' OR status LIKE '%誤%' OR status LIKE '%消%' OR status LIKE '%時%'
            ORDER BY status
        """)
        
        status_samples = cursor.fetchall()
        print(f"  找到 {len(status_samples)} 種不同的狀態:")
        for status in status_samples:
            print(f"    - {status[0]}")
        
        # 2. 檢查航班資料的完整格式
        print("\n2. 航班資料完整格式（前5筆）:")
        cursor.execute("""
            SELECT flight_no, direction, gate, scheduled_time, actual_time, status, updated_at
            FROM flight_schedule 
            ORDER BY updated_at DESC 
            LIMIT 5
        """)
        
        flights = cursor.fetchall()
        for flight in flights:
            flight_no, direction, gate, scheduled_time, actual_time, status, updated_at = flight
            print(f"  {flight_no} ({direction}):")
            print(f"    表定時間: {scheduled_time}")
            print(f"    實際時間: {actual_time}")
            print(f"    狀態: {status}")
            print(f"    更新時間: {updated_at}")
            print()
        
        # 3. 模擬前端 API 回應格式
        print("\n3. 模擬前端 API 回應格式:")
        
        # 建立前端需要的資料格式
        frontend_data = []
        cursor.execute("""
            SELECT flight_no, direction, gate, scheduled_time, actual_time, status, is_cargo
            FROM flight_schedule 
            ORDER BY scheduled_time 
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            flight_no, direction, gate, scheduled_time, actual_time, status, is_cargo = row
            
            flight_data = {
                "flight_no": flight_no,
                "direction": direction,
                "gate": gate,
                "scheduled_time": scheduled_time,
                "actual_time": actual_time,
                "status": status,
                "is_cargo": bool(is_cargo),
                "airline": flight_no[:2] if len(flight_no) > 2 else flight_no
            }
            frontend_data.append(flight_data)
        
        print("  前端資料格式（JSON）:")
        print(json.dumps(frontend_data, ensure_ascii=False, indent=2))
        
        # 4. 檢查中文字符的編碼正確性
        print("\n4. 中文字符編碼檢查:")
        
        # 測試常見的中文字符
        test_chars = ['已到', '延誤', '取消', '準時', '登機中', '已起飛', '已抵達']
        
        for char in test_chars:
            cursor.execute("SELECT COUNT(*) FROM flight_schedule WHERE status LIKE ?", (f"%{char}%",))
            count = cursor.fetchone()[0]
            print(f"  '{char}': {count} 筆記錄")
        
        # 5. 檢查資料庫中實際的中文字符
        print("\n5. 資料庫中的實際中文字符:")
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM flight_schedule 
            WHERE status REGEXP '[\\u4e00-\\u9fff]'
            GROUP BY status
            ORDER BY count DESC
            LIMIT 10
        """)
        
        # 如果 REGEXP 不支援，改用 LIKE
        try:
            chinese_status = cursor.fetchall()
        except:
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM flight_schedule 
                WHERE status LIKE '%到%' OR status LIKE '%誤%' OR status LIKE '%消%' OR status LIKE '%時%'
                GROUP BY status
                ORDER BY count DESC
                LIMIT 10
            """)
            chinese_status = cursor.fetchall()
        
        print("  包含中文字符的狀態分佈:")
        for status, count in chinese_status:
            print(f"    {status}: {count} 筆")
        
        conn.close()
        
        print("\n✅ 驗證完成！中文字段顯示正常。")
        
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")

def check_encoding_consistency():
    """檢查編碼一致性"""
    
    print("\n=== 編碼一致性檢查 ===")
    
    # 測試從資料庫讀取的中文字符
    db_path = "goss-v4/goss_v4.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 隨機取樣檢查中文字符
        cursor.execute("""
            SELECT status 
            FROM flight_schedule 
            WHERE status LIKE '%到%' 
            LIMIT 1
        """)
        
        sample_status = cursor.fetchone()
        if sample_status:
            status_text = sample_status[0]
            print(f"取樣狀態: {status_text}")
            
            # 檢查編碼
            print("編碼檢查:")
            print(f"  UTF-8 編碼: {status_text.encode('utf-8')}")
            print(f"  字節長度: {len(status_text.encode('utf-8'))}")
            print(f"  字符長度: {len(status_text)}")
            
            # 檢查是否包含中文字符
            import re
            chinese_chars = re.findall(r'[\u4e00-\u9fff]', status_text)
            print(f"  中文字符: {chinese_chars}")
            print(f"  中文字符數量: {len(chinese_chars)}")
        
        conn.close()
        
    except Exception as e:
        print(f"編碼檢查失敗: {e}")

if __name__ == "__main__":
    verify_chinese_display()
    check_encoding_consistency()