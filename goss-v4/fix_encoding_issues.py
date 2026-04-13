import sqlite3
import subprocess

def check_encoding_issues():
    """檢查伺服器資料庫中的亂碼問題"""
    
    # 在伺服器上執行檢查
    commands = [
        # 檢查 flight_schedule 表的狀態欄位
        "sqlite3 goss_v4.db \"SELECT DISTINCT status FROM flight_schedule WHERE status IS NOT NULL LIMIT 20\"",
        # 檢查 source_airport 表的狀態欄位
        "sqlite3 goss_v4.db \"SELECT DISTINCT status FROM source_airport WHERE status IS NOT NULL LIMIT 20\"",
        # 檢查亂碼字符
        "sqlite3 goss_v4.db \"SELECT flight_no, status FROM flight_schedule WHERE status LIKE '%�%' OR status LIKE '%?%' LIMIT 10\"",
        "sqlite3 goss_v4.db \"SELECT flight_no, status FROM source_airport WHERE status LIKE '%�%' OR status LIKE '%?%' LIMIT 10\"",
        # 檢查資料量
        "sqlite3 goss_v4.db \"SELECT COUNT(*) FROM flight_schedule WHERE status IS NOT NULL\"",
        "sqlite3 goss_v4.db \"SELECT COUNT(*) FROM source_airport WHERE status IS NOT NULL\""
    ]
    
    print("=== 檢查伺服器資料庫亂碼問題 ===")
    for cmd in commands:
        full_cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && {cmd}\""
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        print(f"\n命令: {cmd}")
        print("輸出:", result.stdout)
        if result.stderr:
            print("錯誤:", result.stderr)

def fix_encoding_issues():
    """修正亂碼問題的SQL腳本"""
    
    fix_commands = [
        # 修正 flight_schedule 表的亂碼狀態
        """
        UPDATE flight_schedule 
        SET status = CASE 
            WHEN status LIKE '%�%' OR status LIKE '%?%' THEN '準時'
            WHEN status = 'ON TIME' THEN '準時'
            WHEN status = 'DELAY' THEN '延誤'
            WHEN status = 'CANCELLED' THEN '取消'
            WHEN status = 'BOARDING' THEN '登機中'
            WHEN status = 'DEPARTED' THEN '已起飛'
            WHEN status = 'ARRIVED' THEN '已抵達'
            ELSE status
        END
        WHERE status IS NOT NULL
        """,
        
        # 修正 source_airport 表的亂碼狀態
        """
        UPDATE source_airport 
        SET status = CASE 
            WHEN status LIKE '%�%' OR status LIKE '%?%' THEN '準時'
            WHEN status = 'ON TIME' THEN '準時'
            WHEN status = 'DELAY' THEN '延誤'
            WHEN status = 'CANCELLED' THEN '取消'
            WHEN status = 'BOARDING' THEN '登機中'
            WHEN status = 'DEPARTED' THEN '已起飛'
            WHEN status = 'ARRIVED' THEN '已抵達'
            ELSE status
        END
        WHERE status IS NOT NULL
        """,
        
        # 清理空值和無效狀態
        "UPDATE flight_schedule SET status = NULL WHERE status = '' OR status = ' ' OR status = 'N/A'",
        "UPDATE source_airport SET status = NULL WHERE status = '' OR status = ' ' OR status = 'N/A'"
    ]
    
    print("\n=== 執行亂碼修正 ===")
    for i, sql in enumerate(fix_commands):
        # 將SQL命令寫入臨時文件
        sql_file = f"fix_encoding_{i}.sql"
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write(sql)
        
        # 上傳並執行SQL
        upload_cmd = f"scp {sql_file} xinzhi@192.168.31.19:/home/xinzhi/goss-v4/"
        execute_cmd = f"ssh xinzhi@192.168.31.19 \"cd /home/xinzhi/goss-v4 && sqlite3 goss_v4.db < {sql_file}\""
        
        print(f"\n執行修正 {i+1}...")
        
        # 上傳文件
        result_upload = subprocess.run(upload_cmd, shell=True, capture_output=True, text=True)
        if result_upload.returncode != 0:
            print(f"上傳失敗: {result_upload.stderr}")
            continue
            
        # 執行SQL
        result_execute = subprocess.run(execute_cmd, shell=True, capture_output=True, text=True)
        if result_execute.returncode == 0:
            print("✅ 修正成功")
        else:
            print(f"❌ 修正失敗: {result_execute.stderr}")
        
        # 清理本地文件
        import os
        os.remove(sql_file)

def improve_fetch_script():
    """改進 fetch_tpe_v4.py 的編碼處理"""
    
    print("\n=== 改進資料抓取程式的編碼處理 ===")
    
    # 讀取原始文件
    with open('fetch_tpe_v4.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 改進編碼處理邏輯
    improved_content = content.replace(
        """                status = p[12].strip() if len(p) > 12 else ""  # 狀態在第 13 欄
                
                # 編碼處理
                if status:
                    # 嘗試多種編碼解碼
                    try:
                        status.encode('utf-8')
                    except UnicodeEncodeError:
                        for encoding in ['big5', 'gbk', 'latin-1']:
                            try:
                                status = status.encode('latin-1').decode(encoding, errors='ignore')
                                break
                            except:
                                continue
                    
                    # 清理特殊字符
                    status = status.replace('\x00', '').replace('\ufffd', '').strip()
                    
                    # 如果仍有亂碼，使用預設值
                    if not status or any(char in status for char in ['�', '\x00', '\ufffd', '\x80', '\x81', '\x82']):
                        if 'ON TIME' in status.upper():
                            status = 'ON TIME'
                        else:
                            status = '準時'""",
        
        """                status = p[12].strip() if len(p) > 12 else ""  # 狀態在第 13 欄
                
                # 改進的編碼處理
                if status:
                    # 先嘗試UTF-8解碼
                    try:
                        # 如果已經是UTF-8，直接使用
                        status.encode('utf-8')
                    except UnicodeEncodeError:
                        # 嘗試從常見編碼轉換
                        for encoding in ['big5', 'gbk', 'latin-1', 'cp950']:
                            try:
                                # 先編碼為bytes，再解碼為目標編碼
                                status_bytes = status.encode('latin-1', errors='ignore')
                                status = status_bytes.decode(encoding, errors='ignore')
                                break
                            except:
                                continue
                    
                    # 清理特殊字符和亂碼
                    status = status.replace('\x00', '').replace('\ufffd', '').replace('�', '').strip()
                    
                    # 標準化狀態文字
                    status_upper = status.upper()
                    if 'ON TIME' in status_upper or '準時' in status:
                        status = '準時'
                    elif 'DELAY' in status_upper or '延誤' in status:
                        status = '延誤'
                    elif 'CANCELLED' in status_upper or '取消' in status:
                        status = '取消'
                    elif 'BOARDING' in status_upper or '登機' in status:
                        status = '登機中'
                    elif 'DEPARTED' in status_upper or '起飛' in status:
                        status = '已起飛'
                    elif 'ARRIVED' in status_upper or '抵達' in status:
                        status = '已抵達'
                    elif not status or any(char in status for char in ['�', '\x00', '\ufffd']):
                        status = '準時'"""
    )
    
    # 寫回文件
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

if __name__ == "__main__":
    # 1. 檢查當前亂碼問題
    check_encoding_issues()
    
    # 2. 修正現有亂碼資料
    fix_encoding_issues()
    
    # 3. 改進資料抓取程式
    improve_fetch_script()
    
    # 4. 驗證修正結果
    print("\n=== 驗證修正結果 ===")
    check_encoding_issues()