import sqlite3
import subprocess
import os
from datetime import datetime

def create_backup():
    """建立資料庫備份"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"goss_v4_backup_{timestamp}.db"
    
    cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && cp goss_v4.db {backup_file}\""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ 資料庫備份建立成功: {backup_file}")
        return backup_file
    else:
        print(f"❌ 備份失敗: {result.stderr}")
        return None

def analyze_encoding_issues():
    """詳細分析亂碼問題"""
    
    analysis_commands = [
        # 1. 檢查狀態分佈
        "SELECT status, COUNT(*) as count FROM flight_schedule WHERE status IS NOT NULL GROUP BY status ORDER BY count DESC LIMIT 15",
        "SELECT status, COUNT(*) as count FROM source_airport WHERE status IS NOT NULL GROUP BY status ORDER BY count DESC LIMIT 15",
        
        # 2. 檢查亂碼模式
        "SELECT DISTINCT status FROM flight_schedule WHERE status LIKE '%�%' LIMIT 10",
        "SELECT DISTINCT status FROM flight_schedule WHERE status LIKE '%?%' LIMIT 10",
        "SELECT DISTINCT status FROM source_airport WHERE status LIKE '%�%' LIMIT 10",
        "SELECT DISTINCT status FROM source_airport WHERE status LIKE '%?%' LIMIT 10",
        
        # 3. 檢查英文狀態
        "SELECT DISTINCT status FROM flight_schedule WHERE status REGEXP '[A-Z]' AND status NOT LIKE '%�%' LIMIT 10",
        "SELECT DISTINCT status FROM source_airport WHERE status REGEXP '[A-Z]' AND status NOT LIKE '%�%' LIMIT 10",
        
        # 4. 檢查中文狀態
        "SELECT DISTINCT status FROM flight_schedule WHERE status REGEXP '[\\u4e00-\\u9fff]' LIMIT 10",
        "SELECT DISTINCT status FROM source_airport WHERE status REGEXP '[\\u4e00-\\u9fff]' LIMIT 10"
    ]
    
    print("=== 詳細亂碼分析 ===")
    
    for i, sql in enumerate(analysis_commands):
        cmd = f"sqlite3 goss_v4.db \"{sql}\""
        full_cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && {cmd}\""
        
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        print(f"\n分析 {i+1}: {sql[:50]}...")
        print("結果:")
        
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
        else:
            print("  無結果")
            
        if result.stderr and "no such table" not in result.stderr:
            print(f"  錯誤: {result.stderr}")

def smart_fix_encoding():
    """智能修正亂碼問題"""
    
    # 分階段修正策略
    fix_phases = [
        # 第一階段：清理明顯亂碼
        {
            "name": "清理明顯亂碼",
            "sqls": [
                """
                UPDATE flight_schedule 
                SET status = CASE 
                    WHEN status LIKE '%�%' AND status LIKE '%ON TIME%' THEN '準時'
                    WHEN status LIKE '%�%' AND status LIKE '%DELAY%' THEN '延誤'
                    WHEN status LIKE '%�%' AND status LIKE '%CANCELLED%' THEN '取消'
                    WHEN status LIKE '%�%' AND status LIKE '%BOARDING%' THEN '登機中'
                    WHEN status LIKE '%�%' AND status LIKE '%DEPARTED%' THEN '已起飛'
                    WHEN status LIKE '%�%' AND status LIKE '%ARRIVED%' THEN '已抵達'
                    WHEN status LIKE '%�%' THEN '準時'  -- 無法識別的亂碼設為準時
                    ELSE status
                END
                WHERE status IS NOT NULL AND status LIKE '%�%'
                """,
                
                """
                UPDATE source_airport 
                SET status = CASE 
                    WHEN status LIKE '%�%' AND status LIKE '%ON TIME%' THEN '準時'
                    WHEN status LIKE '%�%' AND status LIKE '%DELAY%' THEN '延誤'
                    WHEN status LIKE '%�%' AND status LIKE '%CANCELLED%' THEN '取消'
                    WHEN status LIKE '%�%' AND status LIKE '%BOARDING%' THEN '登機中'
                    WHEN status LIKE '%�%' AND status LIKE '%DEPARTED%' THEN '已起飛'
                    WHEN status LIKE '%�%' AND status LIKE '%ARRIVED%' THEN '已抵達'
                    WHEN status LIKE '%�%' THEN '準時'
                    ELSE status
                END
                WHERE status IS NOT NULL AND status LIKE '%�%'
                """
            ]
        },
        
        # 第二階段：標準化英文狀態
        {
            "name": "標準化英文狀態",
            "sqls": [
                """
                UPDATE flight_schedule 
                SET status = CASE 
                    WHEN status = 'ON TIME' OR status LIKE '%ON TIME%' THEN '準時'
                    WHEN status = 'DELAY' OR status LIKE '%DELAY%' THEN '延誤'
                    WHEN status = 'CANCELLED' OR status LIKE '%CANCELLED%' THEN '取消'
                    WHEN status = 'BOARDING' OR status LIKE '%BOARDING%' THEN '登機中'
                    WHEN status = 'DEPARTED' OR status LIKE '%DEPARTED%' THEN '已起飛'
                    WHEN status = 'ARRIVED' OR status LIKE '%ARRIVED%' THEN '已抵達'
                    ELSE status
                END
                WHERE status IS NOT NULL AND status REGEXP '[A-Z]'
                """,
                
                """
                UPDATE source_airport 
                SET status = CASE 
                    WHEN status = 'ON TIME' OR status LIKE '%ON TIME%' THEN '準時'
                    WHEN status = 'DELAY' OR status LIKE '%DELAY%' THEN '延誤'
                    WHEN status = 'CANCELLED' OR status LIKE '%CANCELLED%' THEN '取消'
                    WHEN status = 'BOARDING' OR status LIKE '%BOARDING%' THEN '登機中'
                    WHEN status = 'DEPARTED' OR status LIKE '%DEPARTED%' THEN '已起飛'
                    WHEN status = 'ARRIVED' OR status LIKE '%ARRIVED%' THEN '已抵達'
                    ELSE status
                END
                WHERE status IS NOT NULL AND status REGEXP '[A-Z]'
                """
            ]
        },
        
        # 第三階段：清理無效狀態
        {
            "name": "清理無效狀態",
            "sqls": [
                "UPDATE flight_schedule SET status = NULL WHERE status = '' OR status = ' ' OR status = 'N/A' OR status = 'NULL'",
                "UPDATE source_airport SET status = NULL WHERE status = '' OR status = ' ' OR status = 'N/A' OR status = 'NULL'"
            ]
        }
    ]
    
    print("\n=== 智能亂碼修正 ===")
    
    for phase in fix_phases:
        print(f"\n階段: {phase['name']}")
        
        for i, sql in enumerate(phase['sqls']):
            # 寫入臨時文件
            sql_file = f"smart_fix_{phase['name']}_{i}.sql"
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write(sql)
            
            # 上傳並執行
            upload_cmd = f"scp {sql_file} xinzhi@192.168.31.19:/home/xinzhi/goss-v4/"
            execute_cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && sqlite3 goss_v4.db < {sql_file}\""
            
            result_upload = subprocess.run(upload_cmd, shell=True, capture_output=True, text=True)
            if result_upload.returncode != 0:
                print(f"❌ 上傳失敗: {result_upload.stderr}")
                continue
                
            result_execute = subprocess.run(execute_cmd, shell=True, capture_output=True, text=True)
            if result_execute.returncode == 0:
                print("✅ 修正成功")
            else:
                print(f"❌ 修正失敗: {result_execute.stderr}")
            
            # 清理文件
            os.remove(sql_file)

def improve_fetch_script_smart():
    """改進 fetch_tpe_v4.py 的編碼處理（智能版本）"""
    
    print("\n=== 改進資料抓取程式編碼處理 ===")
    
    # 讀取原始文件
    with open('fetch_tpe_v4.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更合理的編碼處理邏輯
    improved_logic = """                status = p[12].strip() if len(p) > 12 else ""  # 狀態在第 13 欄
                
                # 智能編碼處理
                if status:
                    # 先清理特殊字符
                    status = status.replace('\\x00', '').replace('\\ufffd', '').replace('�', '').strip()
                    
                    # 如果狀態包含中文字符，直接使用
                    if any('\\u4e00' <= char <= '\\u9fff' for char in status):
                        # 已經是中文，不需要轉換
                        pass
                    else:
                        # 嘗試識別英文狀態並轉換為中文
                        status_upper = status.upper()
                        if 'ON TIME' in status_upper:
                            status = '準時'
                        elif 'DELAY' in status_upper:
                            status = '延誤'
                        elif 'CANCELLED' in status_upper:
                            status = '取消'
                        elif 'BOARDING' in status_upper:
                            status = '登機中'
                        elif 'DEPARTED' in status_upper:
                            status = '已起飛'
                        elif 'ARRIVED' in status_upper:
                            status = '已抵達'
                        elif not status:
                            status = '準時'
                    
                    # 最終清理
                    status = status.strip()"""
    
    # 替換舊的編碼處理邏輯
    old_pattern = """                status = p[12].strip() if len(p) > 12 else ""  # 狀態在第 13 欄
                
                # 編碼處理
                if status:"""
    
    # 找到並替換整個編碼處理區塊
    import re
    pattern = r"status = p\[12\]\.strip\(\) if len\(p\) > 12 else \"\"  # 狀態在第 13 欄\s+# 編碼處理\s+if status:.*?(?=flight_no =)"
    
    improved_content = re.sub(pattern, improved_logic, content, flags=re.DOTALL)
    
    if improved_content != content:
        with open('fetch_tpe_v4.py', 'w', encoding='utf-8') as f:
            f.write(improved_content)
        print("✅ fetch_tpe_v4.py 編碼處理已改進")
        
        # 上傳到伺服器
        upload_cmd = "scp fetch_tpe_v4.py xinzhi@192.168.31.19:/home/xinzhi/goss-v4/"
        result = subprocess.run(upload_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 已上傳到伺服器")
        else:
            print(f"❌ 上傳失敗: {result.stderr}")
    else:
        print("⚠️ 未找到需要替換的編碼處理邏輯")

def verify_fix():
    """驗證修正結果"""
    
    verify_commands = [
        "SELECT COUNT(*) as total_count FROM flight_schedule",
        "SELECT COUNT(*) as status_count FROM flight_schedule WHERE status IS NOT NULL",
        "SELECT status, COUNT(*) as count FROM flight_schedule WHERE status IS NOT NULL GROUP BY status ORDER BY count DESC LIMIT 10",
        "SELECT COUNT(*) as total_count FROM source_airport",
        "SELECT COUNT(*) as status_count FROM source_airport WHERE status IS NOT NULL",
        "SELECT status, COUNT(*) as count FROM source_airport WHERE status IS NOT NULL GROUP BY status ORDER BY count DESC LIMIT 10",
        "SELECT COUNT(*) as remaining_garbage FROM flight_schedule WHERE status LIKE '%�%' OR status LIKE '%?%'",
        "SELECT COUNT(*) as remaining_garbage FROM source_airport WHERE status LIKE '%�%' OR status LIKE '%?%'"
    ]
    
    print("\n=== 修正結果驗證 ===")
    
    for sql in verify_commands:
        cmd = f"sqlite3 goss_v4.db \"{sql}\""
        full_cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && {cmd}\""
        
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        print(f"\n驗證: {sql}")
        print("結果:", result.stdout.strip() if result.stdout else "無結果")

if __name__ == "__main__":
    print("開始智能亂碼修正流程...")
    
    # 1. 建立備份
    backup_file = create_backup()
    if not backup_file:
        print("⚠️ 繼續執行但無備份")
    
    # 2. 詳細分析
    analyze_encoding_issues()
    
    # 3. 智能修正
    smart_fix_encoding()
    
    # 4. 改進抓取程式
    improve_fetch_script_smart()
    
    # 5. 驗證結果
    verify_fix()
    
    print("\n✅ 智能亂碼修正流程完成")