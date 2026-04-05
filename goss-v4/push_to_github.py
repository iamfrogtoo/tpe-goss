import sqlite3
import json
import os
import subprocess
from datetime import datetime

# 使用绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "goss_v4.db")
# 將數據輸出到項目根目錄的 public 文件夾，這樣可以直接通過 GitHub Pages 訪問
PROJECT_ROOT = SCRIPT_DIR  # 現在腳本就在項目根目錄
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "public")
OUTPUT_PATH = os.path.join(PUBLIC_DIR, "live_data.json")

def export_live_data():
    """导出实时数据到 JSON 文件"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取实时交通数据，并与航班计划表关联获取更多信息
        cursor.execute('''
            SELECT 
                lt.hex,
                lt.flight_no,
                lt.alt,
                lt.gs,
                lt.gate,
                lt.is_cargo,
                lt.source,
                lt.updated_at,
                fs.direction,
                fs.scheduled_time,
                fs.actual_time,
                fs.status,
                sa.terminal,
                sa.airline,
                sa.aircraft_type
            FROM live_traffic lt
            LEFT JOIN flight_schedule fs ON lt.flight_no = fs.flight_no
            LEFT JOIN (
                SELECT flight_no, terminal, airline, aircraft_type, MAX(updated_at) as latest_update
                FROM source_airport
                GROUP BY flight_no
            ) sa ON lt.flight_no = sa.flight_no
            WHERE lt.updated_at > datetime('now', '-5 minutes')
            ORDER BY CAST(lt.alt AS INTEGER) ASC
        ''')
        
        rows = cursor.fetchall()
        
        flights = []
        for row in rows:
            alt_value = row[2]
            if alt_value == "ground" or alt_value == "None" or not alt_value:
                alt_value = "0"
            flight = {
                "hex": row[0],
                "code": row[1] or "",
                "alt": str(alt_value),
                "gs": row[3] or 0,
                "gate": row[4] or "",
                "is_cargo": bool(row[5]),
                "source": row[6] or "",
                "updated_at": row[7],
                "direction": row[8] or "A",
                "scheduled_time": row[9] or "",
                "actual_time": row[10] or "",
                "status": row[11] or "",
                "terminal": row[12] or "-",
                "airline": row[13] or "",
                "actype": row[14] or "",
                "reg": "",
                "baggage": ""
            }
            
            # 只保留進場航班（direction == 'A' 或沒有 direction 資訊）
            if flight["direction"] == "A" or not flight["direction"]:
                flights.append(flight)
        
        # 确保 public 目录存在
        os.makedirs(PUBLIC_DIR, exist_ok=True)
        
        # 导出为 JSON
        result = {
            "timestamp": datetime.now().isoformat(),
            "flights": flights
        }
        
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 成功导出 {len(flights)} 架航班数据")
        return True
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 导出失败: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def push_to_github():
    """将数据推送到 GitHub"""
    try:
        # 切换到项目根目录
        os.chdir(PROJECT_ROOT)
        
        # 添加文件
        subprocess.run(['git', 'add', 'public/live_data.json'], check=True, capture_output=True)
        
        # 提交
        commit_msg = f"chore: 更新实时航班数据 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True, capture_output=True)
        
        # 推送
        subprocess.run(['git', 'push', 'origin', 'main'], check=True, capture_output=True)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 成功推送到 GitHub")
        return True
        
    except subprocess.CalledProcessError as e:
        # 如果沒有變更，git commit 會失敗，這是正常的
        if "nothing to commit" in str(e.stderr) or "nothing to commit" in str(e.stdout):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ℹ️  沒有數據變更，跳過提交")
            return True
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Git 操作失敗: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 推送到 GitHub 失敗: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print(f"開始執行: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if export_live_data():
        push_to_github()
    
    print("=" * 60)
    print(f"執行完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
