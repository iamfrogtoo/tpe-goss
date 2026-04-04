import sqlite3

DB_PATH = "goss_v4.db"

def update_runway_table():
    """更新跑道轨迹表结构"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 添加 runway 列
        cursor.execute('ALTER TABLE runway_tracks ADD COLUMN runway TEXT')
        print("添加 runway 列成功")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("runway 列已存在")
        else:
            print(f"添加 runway 列失败: {e}")
    
    try:
        # 添加 distance_to_runway 列
        cursor.execute('ALTER TABLE runway_tracks ADD COLUMN distance_to_runway REAL')
        print("添加 distance_to_runway 列成功")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("distance_to_runway 列已存在")
        else:
            print(f"添加 distance_to_runway 列失败: {e}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_runway_table()