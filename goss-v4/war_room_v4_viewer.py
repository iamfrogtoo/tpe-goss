import sqlite3
import os
import time

DB_PATH = "goss_v4.db"

def show_war_room():
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # 撈出最近 1 分鐘有更新的飛機，優先排顯示貨機
            cursor.execute('''
                SELECT flight_no, alt, gs, gate, is_cargo, source 
                FROM live_traffic 
                WHERE updated_at > datetime('now', '-1 minute')
                ORDER BY is_cargo DESC, flight_no ASC
            ''')
            rows = cursor.fetchall()
            conn.close()

            os.system('cls')
            print(f"=== TPE GOSS 4.0 戰情室 | 目前掌握: {len(rows)} 架 ===\n")
            print(f"{'班號':<10} {'機坪':<8} {'高度':<8} {'速度':<8} {'狀態':<8}")
            print("-" * 55)

            # 找到輸出循環的部分，修改如下：
            for r in rows:
                f_no, alt_raw, gs_raw, gate, is_cargo, src = r[0], r[1], r[2], r[3], r[4], r[5]
                tag = "⚠️貨機" if is_cargo == 1 else "客機"

                # 處理高度顯示 (如果是 ground、None、空字符串或 TBD 就顯示 GND)
                alt_display = "GND" if (alt_raw == "ground" or alt_raw is None or alt_raw == "None" or alt_raw == "TBD" or alt_raw == "") else f"{float(alt_raw):.0f}"
                # 處理速度顯示
                gs_display = "0" if (gs_raw is None or gs_raw == "None" or gs_raw == "") else f"{float(gs_raw):.0f}"

                print(f"{f_no:<10} {gate:<8} {alt_display:<8} {gs_display:<8} {tag:<8} ({src})")

        except Exception as e:
            print(f"等待同步中... {e}")
        
        time.sleep(2)

if __name__ == "__main__":
    show_war_room()