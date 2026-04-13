import re
from datetime import datetime

def check_data_dates():
    """檢查資料的時間範圍"""
    
    print("=== 檢查最新資料的時間範圍 ===")
    
    # 讀取客機資料
    with open("客機_latest.txt", 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # 收集所有日期
    dates = set()
    
    for line in lines:
        if line.strip():
            # 尋找日期格式：2026/04/08
            date_matches = re.findall(r'\d{4}/\d{2}/\d{2}', line)
            for date_str in date_matches:
                dates.add(date_str)
    
    # 排序日期
    sorted_dates = sorted(dates)
    
    print(f"資料中包含的日期範圍: {len(sorted_dates)} 天")
    print("具體日期:")
    for date in sorted_dates:
        print(f"  {date}")
    
    if sorted_dates:
        earliest = sorted_dates[0]
        latest = sorted_dates[-1]
        print(f"\n最早日期: {earliest}")
        print(f"最晚日期: {latest}")
        
        # 計算日期跨度
        from datetime import datetime
        earliest_dt = datetime.strptime(earliest, '%Y/%m/%d')
        latest_dt = datetime.strptime(latest, '%Y/%m/%d')
        days_diff = (latest_dt - earliest_dt).days
        
        print(f"日期跨度: {days_diff + 1} 天")
    
    # 檢查每種日期的資料筆數
    print("\n=== 各日期資料筆數 ===")
    date_counts = {}
    
    for line in lines:
        if line.strip():
            date_matches = re.findall(r'\d{4}/\d{2}/\d{2}', line)
            if date_matches:
                date = date_matches[0]  # 取第一個日期
                if date not in date_counts:
                    date_counts[date] = 0
                date_counts[date] += 1
    
    for date, count in sorted(date_counts.items()):
        print(f"  {date}: {count} 筆")

if __name__ == "__main__":
    check_data_dates()