import subprocess
import json
from datetime import datetime

def check_database_structure():
    """檢查資料庫結構和資料狀態"""
    
    print("=== 資料庫結構檢查 ===")
    
    # 使用正確的語法
    commands = [
        "sqlite3 goss_v4.db '.tables'",
        "sqlite3 goss_v4.db \"SELECT name FROM sqlite_master WHERE type='table'\"",
        "sqlite3 goss_v4.db '.schema live_traffic'",
        "sqlite3 goss_v4.db '.schema flight_schedule'",
        "sqlite3 goss_v4.db '.schema source_airport'",
        "sqlite3 goss_v4.db '.schema source_opensky'",
        "sqlite3 goss_v4.db '.schema source_antenna'"
    ]
    
    for cmd in commands:
        full_cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && {cmd}\""
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        print(f"\n{cmd}")
        if result.stdout:
            print("結果:", result.stdout.strip())
        else:
            print("結果: 無結果")
        if result.stderr:
            print("錯誤:", result.stderr)

def check_data_counts():
    """檢查各表格的資料量"""
    
    print("\n=== 資料量統計 ===")
    
    # 先獲取所有表格名稱
    cmd = "sqlite3 goss_v4.db \"SELECT name FROM sqlite_master WHERE type='table'\""
    full_cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && {cmd}\""
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
    
    if result.stdout:
        tables = result.stdout.strip().split('\n')
        print(f"找到 {len(tables)} 個表格: {tables}")
        
        for table in tables:
            if table.strip():
                cmd = f"sqlite3 goss_v4.db \"SELECT COUNT(*) FROM {table.strip()}\""
                full_cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && {cmd}\""
                result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
                
                if result.stdout and result.stdout.strip().isdigit():
                    count = int(result.stdout.strip())
                    print(f"{table.strip()}: {count} 筆資料")
                else:
                    print(f"{table.strip()}: 無資料")
    else:
        print("無表格存在")

def check_actual_data():
    """檢查實際資料內容"""
    
    print("\n=== 實際資料檢查 ===")
    
    # 檢查是否有航班資料
    queries = [
        "SELECT * FROM flight_schedule LIMIT 3",
        "SELECT * FROM source_airport LIMIT 3",
        "SELECT * FROM live_traffic LIMIT 3",
        "SELECT * FROM source_antenna LIMIT 3"
    ]
    
    for sql in queries:
        cmd = f"sqlite3 goss_v4.db \"{sql}\""
        full_cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && {cmd}\""
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        
        print(f"\n{sql}")
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines[:3]:  # 只顯示前3行
                print(f"  {line}")
            if len(lines) > 3:
                print(f"  ... (還有 {len(lines)-3} 行)")
        else:
            print("  無資料")

def check_script_files():
    """檢查腳本檔案狀態"""
    
    print("\n=== 腳本檔案檢查 ===")
    
    scripts = ["bridge_v4.py", "fetch_tpe_v4.py", "fetch_opensky_v4.py", "fetch_adsb_v4.py", "api_server.py"]
    
    for script in scripts:
        cmd = f"ls -la {script}"
        full_cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && {cmd}\""
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print(f"✅ {script}: 存在")
        else:
            print(f"❌ {script}: 不存在")

if __name__ == "__main__":
    print("開始修正後的資料庫檢查...")
    print(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_database_structure()
    check_data_counts()
    check_actual_data()
    check_script_files()
    
    print("\n✅ 檢查完成")