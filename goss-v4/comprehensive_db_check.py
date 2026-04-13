import subprocess
import json
from datetime import datetime

def check_database_structure():
    """檢查資料庫結構和資料狀態"""
    
    print("=== 資料庫結構檢查 ===")
    
    # 1. 檢查表格結構
    commands = [
        "sqlite3 goss_v4.db \".tables\"",
        "sqlite3 goss_v4.db \"SELECT name FROM sqlite_master WHERE type='table'\"",
        "sqlite3 goss_v4.db \"PRAGMA table_info(live_traffic)\"",
        "sqlite3 goss_v4.db \"PRAGMA table_info(flight_schedule)\"",
        "sqlite3 goss_v4.db \"PRAGMA table_info(source_airport)\"",
        "sqlite3 goss_v4.db \"PRAGMA table_info(source_opensky)\"",
        "sqlite3 goss_v4.db \"PRAGMA table_info(source_antenna)\"",
        "sqlite3 goss_v4.db \"PRAGMA table_info(source_fr24)\"",
        "sqlite3 goss_v4.db \"PRAGMA table_info(source_calair)\""
    ]
    
    for cmd in commands:
        full_cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && {cmd}\""
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        print(f"\n{cmd}")
        print("結果:", result.stdout.strip() if result.stdout else "無結果")
        if result.stderr and "no such table" not in result.stderr:
            print("錯誤:", result.stderr)

def check_data_counts():
    """檢查各表格的資料量"""
    
    print("\n=== 資料量統計 ===")
    
    tables = ["live_traffic", "flight_schedule", "source_airport", "source_opensky", 
              "source_antenna", "source_fr24", "source_calair"]
    
    for table in tables:
        cmd = f"sqlite3 goss_v4.db \"SELECT COUNT(*) FROM {table}\""
        full_cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && {cmd}\""
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout and result.stdout.strip().isdigit():
            count = int(result.stdout.strip())
            print(f"{table}: {count} 筆資料")
        else:
            print(f"{table}: 無資料或表格不存在")

def check_data_samples():
    """檢查資料樣本"""
    
    print("\n=== 資料樣本檢查 ===")
    
    sample_queries = [
        # live_traffic 資料
        "SELECT hex, flight_no, gate, is_cargo, source, updated_at FROM live_traffic ORDER BY updated_at DESC LIMIT 5",
        
        # flight_schedule 狀態檢查
        "SELECT flight_no, direction, gate, scheduled_time, actual_time, status FROM flight_schedule WHERE status IS NOT NULL LIMIT 10",
        
        # source_airport 狀態檢查
        "SELECT flight_no, direction, gate, scheduled_time, actual_time, status FROM source_airport WHERE status IS NOT NULL LIMIT 10",
        
        # source_opensky 資料
        "SELECT icao24, callsign, origin, destination, updated_at FROM source_opensky ORDER BY updated_at DESC LIMIT 5",
        
        # source_antenna 資料
        "SELECT hex, flight, alt_baro, gs, updated_at FROM source_antenna ORDER BY updated_at DESC LIMIT 5"
    ]
    
    for i, sql in enumerate(sample_queries):
        cmd = f"sqlite3 goss_v4.db \"{sql}\""
        full_cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && {cmd}\""
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        
        print(f"\n樣本 {i+1}: {sql[:50]}...")
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
        else:
            print("  無資料")

def check_encoding_issues():
    """檢查亂碼問題"""
    
    print("\n=== 亂碼問題檢查 ===")
    
    encoding_checks = [
        "SELECT COUNT(*) FROM flight_schedule WHERE status LIKE '%�%' OR status LIKE '%?%'",
        "SELECT COUNT(*) FROM source_airport WHERE status LIKE '%�%' OR status LIKE '%?%'",
        "SELECT DISTINCT status FROM flight_schedule WHERE status LIKE '%�%' LIMIT 5",
        "SELECT DISTINCT status FROM source_airport WHERE status LIKE '%�%' LIMIT 5"
    ]
    
    for sql in encoding_checks:
        cmd = f"sqlite3 goss_v4.db \"{sql}\""
        full_cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && {cmd}\""
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        
        print(f"\n{sql}")
        print("結果:", result.stdout.strip() if result.stdout else "無結果")

def check_running_processes():
    """檢查運行的程式"""
    
    print("\n=== 運行程式檢查 ===")
    
    # 檢查 Python 程式
    cmd = "ps aux | grep python | grep -v grep"
    full_cmd = f"ssh xinzhi@192.168.31.19 \"{cmd}\""
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    
    print("運行的 Python 程式:")
    if result.stdout:
        for line in result.stdout.strip().split('\n'):
            print(f"  {line}")
    else:
        print("  無運行的 Python 程式")
    
    # 檢查 cron 任務
    cmd = "crontab -l"
    full_cmd = f"ssh xinzhi@192.168.31.19 \"{cmd}\""
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    
    print("\nCron 任務:")
    if result.stdout:
        for line in result.stdout.strip().split('\n'):
            print(f"  {line}")
    else:
        print("  無 cron 任務")

if __name__ == "__main__":
    print("開始全面資料庫檢查...")
    print(f"檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    check_database_structure()
    check_data_counts()
    check_data_samples()
    check_encoding_issues()
    check_running_processes()
    
    print("\n✅ 檢查完成")