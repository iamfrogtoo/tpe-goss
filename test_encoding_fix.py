import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_different_encodings():
    """測試不同編碼方式的效果"""
    
    url = "https://www.taoyuan-airport.com/uploads/flightx/a_flight_v4.txt"
    headers = { "User-Agent": "Mozilla/5.0" }
    
    print("=== 測試不同編碼方式 ===")
    
    # 方法1: v4 版本的方式 (utf-8)
    print("\n1. v4 版本方式 (utf-8):")
    r = requests.get(url, headers=headers, verify=False, timeout=15)
    r.encoding = 'utf-8'
    text_utf8 = r.text
    
    lines_utf8 = text_utf8.split('\n')[:3]
    for i, line in enumerate(lines_utf8):
        print(f"  行 {i+1}: {repr(line[:100])}")
    
    # 方法2: v2 版本的方式 (cp950 優先)
    print("\n2. v2 版本方式 (cp950 優先):")
    r = requests.get(url, headers=headers, verify=False, timeout=15)
    try:
        text_cp950 = r.content.decode('cp950')
        print("  ✅ cp950 解碼成功")
    except Exception as e:
        print(f"  ❌ cp950 解碼失敗: {e}")
        text_cp950 = r.content.decode('utf-8', errors='ignore')
        print("  ✅ utf-8 備援解碼成功")
    
    lines_cp950 = text_cp950.split('\n')[:3]
    for i, line in enumerate(lines_cp950):
        print(f"  行 {i+1}: {repr(line[:100])}")
    
    # 比較兩種方式的中文字符數量
    def count_chinese_chars(text):
        import re
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text[:1000])
        return len(chinese_chars)
    
    chinese_utf8 = count_chinese_chars(text_utf8)
    chinese_cp950 = count_chinese_chars(text_cp950)
    
    print(f"\n=== 中文字符數量比較 ===")
    print(f"utf-8 方式: {chinese_utf8} 個中文字符")
    print(f"cp950 方式: {chinese_cp950} 個中文字符")
    
    if chinese_cp950 > chinese_utf8:
        print("✅ cp950 編碼效果更好！")
        return text_cp950
    else:
        print("⚠️ utf-8 編碼效果較好")
        return text_utf8

def create_fixed_taoyuan_with_cp950():
    """使用 cp950 編碼重新抓取並修正資料"""
    
    print("\n=== 使用 cp950 編碼重新抓取資料 ===")
    
    urls = {
        "客機": "https://www.taoyuan-airport.com/uploads/flightx/a_flight_v4.txt",
        "貨機": "https://www.taoyuan-airport.com/uploads/flightx/af_flight_v4.txt"
    }
    
    headers = { "User-Agent": "Mozilla/5.0" }
    
    for flight_type, url in urls.items():
        print(f"\n處理 {flight_type} 資料...")
        
        r = requests.get(url, headers=headers, verify=False, timeout=15)
        
        # 使用 v2 版本的編碼策略
        try:
            text = r.content.decode('cp950')
            print(f"  ✅ cp950 解碼成功")
        except Exception as e:
            print(f"  ❌ cp950 解碼失敗: {e}")
            text = r.content.decode('utf-8', errors='ignore')
            print(f"  ✅ utf-8 備援解碼成功")
        
        # 清理資料格式 (v2 版本方式)
        clean_text = text.replace("['", "").replace("']", "").replace("','", "\n").replace("', '", "\n")
        
        # 儲存修正版
        filename = f"{flight_type}_fixed_cp950.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(clean_text)
        
        print(f"  📁 已儲存: {filename}")
        
        # 顯示修正後的樣本
        lines = clean_text.split('\n')[:3]
        print("  修正後的前3行樣本:")
        for i, line in enumerate(lines):
            print(f"    行 {i+1}: {line[:100]}")

if __name__ == "__main__":
    # 測試不同編碼方式
    best_text = test_different_encodings()
    
    # 使用最佳編碼重新抓取資料
    create_fixed_taoyuan_with_cp950()