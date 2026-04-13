import requests
import os
from datetime import datetime

def fetch_latest_taoyuan_data():
    """從桃園機場官網抓取最新資料"""
    
    # 桃園機場資料來源
    urls = {
        "客機": "https://www.taoyuan-airport.com/uploads/flightx/a_flight_v4.txt",
        "貨機": "https://www.taoyuan-airport.com/uploads/flightx/af_flight_v4.txt"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for flight_type, url in urls.items():
        print(f"\n=== 抓取 {flight_type} 資料 ===")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                content = response.text.strip()
                lines = content.split('\n')
                
                print(f"✅ 成功抓取 {len(lines)} 行資料")
                
                # 顯示前5行資料
                print("前5行資料樣本:")
                for i, line in enumerate(lines[:5]):
                    print(f"  {i+1}. {line}")
                
                # 檢查資料時間
                if lines and len(lines) > 1:
                    first_line = lines[1]  # 跳過標題行
                    if ',' in first_line:
                        fields = first_line.split(',')
                        if len(fields) >= 8:
                            date_field = fields[7] if len(fields) > 7 else fields[6]
                            print(f"資料日期: {date_field}")
                
                # 儲存到本地檔案
                filename = f"{flight_type}_latest.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"📁 已儲存到: {filename}")
                
            else:
                print(f"❌ 抓取失敗，狀態碼: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 抓取錯誤: {e}")

if __name__ == "__main__":
    print("開始從桃園機場官網抓取最新資料...")
    fetch_latest_taoyuan_data()