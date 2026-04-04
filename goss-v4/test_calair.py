import sqlite3

def test_calair_table():
    """测试华航邮件数据表是否正确创建"""
    try:
        conn = sqlite3.connect('goss_v4.db')
        cursor = conn.cursor()
        
        # 检查 source_calair 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='source_calair'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("[OK] source_calair 表已存在")
            
            # 检查表结构
            cursor.execute("PRAGMA table_info(source_calair)")
            columns = cursor.fetchall()
            print("表结构：")
            for column in columns:
                print(f"  - {column[1]}: {column[2]}")
            
            # 测试插入一条测试数据
            test_data = (
                'CI123',  # flight_no
                '2026-04-01',  # flight_date
                '08:00',  # departure_time
                '10:30',  # arrival_time
                'TPE',  # origin
                'HKG',  # destination
                'A320',  # aircraft_type
                'A12',  # gate
                'ON TIME',  # status
                '测试数据'  # remarks
            )
            
            cursor.execute('''
                INSERT INTO source_calair 
                (flight_no, flight_date, departure_time, arrival_time, 
                 origin, destination, aircraft_type, gate, status, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', test_data)
            
            conn.commit()
            print("[OK] 测试数据插入成功")
            
            # 测试查询数据
            cursor.execute('SELECT * FROM source_calair WHERE flight_no = ?', ('CI123',))
            result = cursor.fetchone()
            if result:
                print("[OK] 测试数据查询成功")
                print(f"  航班号: {result[1]}")
                print(f"  日期: {result[2]}")
                print(f"  出发时间: {result[3]}")
                print(f"  到达时间: {result[4]}")
                print(f"  出发地: {result[5]}")
                print(f"  目的地: {result[6]}")
                print(f"  机型: {result[7]}")
                print(f"  登机门: {result[8]}")
                print(f"  状态: {result[9]}")
                print(f"  备注: {result[10]}")
            else:
                print("[ERROR] 测试数据查询失败")
            
            # 清理测试数据
            cursor.execute('DELETE FROM source_calair WHERE flight_no = ?', ('CI123',))
            conn.commit()
            print("[OK] 测试数据清理成功")
        else:
            print("[ERROR] source_calair 表不存在")
        
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("测试华航邮件数据表...")
    test_calair_table()
    print("测试完成！")
