import sqlite3

def alter_db():
    conn = sqlite3.connect('goss_v4.db')
    cursor = conn.cursor()
    
    # 修改flight_schedule表，添加actual_time和status列
    try:
        cursor.execute('ALTER TABLE flight_schedule ADD COLUMN actual_time TEXT')
        print("✅ flight_schedule 表添加 actual_time 列成功")
    except Exception as e:
        print(f"⚠️ flight_schedule 表添加 actual_time 列失败: {e}")
    
    try:
        cursor.execute('ALTER TABLE flight_schedule ADD COLUMN status TEXT')
        print("✅ flight_schedule 表添加 status 列成功")
    except Exception as e:
        print(f"⚠️ flight_schedule 表添加 status 列失败: {e}")
    
    # 修改source_airport表，添加actual_time和status列
    try:
        cursor.execute('ALTER TABLE source_airport ADD COLUMN actual_time TEXT')
        print("✅ source_airport 表添加 actual_time 列成功")
    except Exception as e:
        print(f"⚠️ source_airport 表添加 actual_time 列失败: {e}")
    
    try:
        cursor.execute('ALTER TABLE source_airport ADD COLUMN status TEXT')
        print("✅ source_airport 表添加 status 列成功")
    except Exception as e:
        print(f"⚠️ source_airport 表添加 status 列失败: {e}")
    
    conn.commit()
    conn.close()
    print("✅ 数据库表结构修改完成！")

if __name__ == "__main__":
    alter_db()