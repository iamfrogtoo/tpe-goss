import paramiko
import sqlite3
import json
import os
import subprocess
from datetime import datetime
import shutil

# 配置
SERVER_HOST = "192.168.31.19"
SERVER_USER = "xinzhi"
SERVER_DB_PATH = "/home/xinzhi/goss-v4/goss_v4.db"

# 本地路徑
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
LOCAL_DB_PATH = os.path.join(SCRIPT_DIR, "goss_v4_server.db")
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "public")
OUTPUT_PATH = os.path.join(PUBLIC_DIR, "live_data.json")

def download_db_from_server():
    """從伺服器下載數據庫"""
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在從伺服器下載數據庫...")
        
        # 使用 paramiko SFTP 下載
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SERVER_HOST, username=SERVER_USER)
        
        sftp = ssh.open_sftp()
        sftp.get(SERVER_DB_PATH, LOCAL_DB_PATH)
        sftp.close()
        ssh.close()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 數據庫下載成功")
        return True
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 下載失敗: {e}")
        return False

def export_live_data():
    """從本地數據庫導出實時數據"""
    try:
        conn = sqlite3.connect(LOCAL_DB_PATH)
        cursor = conn.cursor()
        
        # 獲取實時交通數據，並與航班計劃表關聯獲取更多信息
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
            WHERE 1=1
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
        
        # 確保 public 目錄存在
        os.makedirs(PUBLIC_DIR, exist_ok=True)
        
        # 導出為 JSON
        result = {
            "timestamp": datetime.now().isoformat(),
            "flights": flights
        }
        
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 成功導出 {len(flights)} 架航班數據")
        return True
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 導出失敗: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def push_to_github():
    """將數據推送到 GitHub"""
    try:
        # 切換到項目根目錄
        os.chdir(PROJECT_ROOT)
        
        # 添加文件
        subprocess.run(['git', 'add', 'public/live_data.json'], check=True, capture_output=True)
        
        # 提交
        commit_msg = f"chore: 更新實時航班數據 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True, capture_output=True)
        
        # 推送
        subprocess.run(['git', 'push', 'origin', 'main'], check=True, capture_output=True)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 成功推送到 GitHub")
        return True
        
    except subprocess.CalledProcessError as e:
        # 如果沒有變更，git commit 會失敗，這是正常的
        if "nothing to commit" in str(e.stderr) or "nothing to commit" in str(e.stdout):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 沒有數據變更，跳過提交")
            return True
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Git 操作失敗: {e}")
        return False
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 推送到 GitHub 失敗: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print(f"開始執行: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    success = False
    if download_db_from_server():
        if export_live_data():
            push_to_github()
            success = True
    
    print("=" * 60)
    print(f"執行完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
