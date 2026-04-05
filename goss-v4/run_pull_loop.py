import time
import os
import sys
from datetime import datetime

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 導入 pull_from_server 的函數
from pull_from_server import download_db_from_server, export_live_data, push_to_github

def main():
    print("=" * 60)
    print("TPE GOSS 數據同步循環腳本")
    print("=" * 60)
    print()
    
    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 開始執行...")
            
            success = False
            if download_db_from_server():
                if export_live_data():
                    push_to_github()
                    success = True
            
            if success:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 執行成功")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 執行失敗")
                
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 發生錯誤: {e}")
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 等待 30 秒...")
        print("-" * 60)
        time.sleep(30)

if __name__ == "__main__":
    main()
