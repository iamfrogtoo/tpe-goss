import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_ascii_encoding():
    """測試 ASCII 編碼方式"""
    
    url = "https://www.taoyuan-airport.com/uploads/flightx/a_flight_v4.txt"
    headers = { "User-Agent": "Mozilla/5.0" }
    
    print("=== 測試 ASCII 編碼方式 ===")
    
    r = requests.get(url, headers=headers, verify=False, timeout=15)
    
    # 方法1: 直接使用 ASCII 解碼
    print("\n1. ASCII 解碼:")
    try:
        text_ascii = r.content.decode('ascii')
        print("  ✅ ASCII 解碼成功")
        
        lines_ascii = text_ascii.split('\n')[:3]
        for i, line in enumerate(lines_ascii):
            print(f"  行 {i+1}: {repr(line[:100])}")
            
    except UnicodeDecodeError as e:
        print(f"  ❌ ASCII 解碼失敗: {e}")
        
        # 方法2: 使用 latin1 (ISO-8859-1) 解碼
        print("\n2. Latin1 (ISO-8859-1) 解碼:")
        try:
            text_latin1 = r.content.decode('latin1')
            print("  ✅ Latin1 解碼成功")
            
            lines_latin1 = text_latin1.split('\n')[:3]
            for i, line in enumerate(lines_latin1):
                print(f"  行 {i+1}: {repr(line[:100])}")
                
        except Exception as e2:
            print(f"  ❌ Latin1 解碼失敗: {e2}")
    
    # 方法3: 檢查原始位元組內容
    print("\n3. 原始位元組分析:")
    first_100_bytes = r.content[:100]
    print(f"  前100位元組: {first_100_bytes}")
    
    # 檢查是否包含中文字符的位元組模式
    print("  位元組值分析:")
    for i, byte in enumerate(first_100_bytes[:50]):
        if byte > 127:  # 大於127可能是中文字符
            print(f"    位置 {i}: 0x{byte:02x} (可能為中文字符)")
    
    # 方法4: 嘗試 Windows-1252 編碼
    print("\n4. Windows-1252 解碼:")
    try:
        text_1252 = r.content.decode('windows-1252')
        print("  ✅ Windows-1252 解碼成功")
        
        lines_1252 = text_1252.split('\n')[:3]
        for i, line in enumerate(lines_1252):
            print(f"  行 {i+1}: {repr(line[:100])}")
            
    except Exception as e:
        print(f"  ❌ Windows-1252 解碼失敗: {e}")

def check_actual_encoding():
    """檢查實際使用的編碼"""
    
    print("\n=== 檢查實際編碼 ===")
    
    url = "https://www.taoyuan-airport.com/uploads/flightx/a_flight_v4.txt"
    headers = { "User-Agent": "Mozilla/5.0" }
    
    r = requests.get(url, headers=headers, verify=False, timeout=15)
    
    # 檢查 HTTP 回應的編碼聲明
    print(f"HTTP Content-Type: {r.headers.get('Content-Type', '未指定')}")
    print(f"HTTP Content-Encoding: {r.headers.get('Content-Encoding', '未指定')}")
    
    # 檢查是否包含 BOM (Byte Order Mark)
    bom_utf8 = b'\xef\xbb\xbf'
    bom_utf16_le = b'\xff\xfe'
    bom_utf16_be = b'\xfe\xff'
    
    if r.content.startswith(bom_utf8):
        print("✅ 檢測到 UTF-8 BOM")
    elif r.content.startswith(bom_utf16_le):
        print("✅ 檢測到 UTF-16 LE BOM")
    elif r.content.startswith(bom_utf16_be):
        print("✅ 檢測到 UTF-16 BE BOM")
    else:
        print("❌ 未檢測到 BOM")
    
    # 測試最常見的編碼
    encodings_to_test = ['ascii', 'utf-8', 'cp950', 'big5', 'latin1', 'windows-1252', 'gbk', 'gb2312']
    
    print("\n=== 編碼測試結果 ===")
    for encoding in encodings_to_test:
        try:
            text = r.content.decode(encoding)
            # 檢查是否包含中文字符
            import re
            chinese_chars = re.findall(r'[\u4e00-\u9fff]', text[:500])
            
            if chinese_chars:
                print(f"✅ {encoding}: 包含 {len(chinese_chars)} 個中文字符")
                # 顯示第一個中文字符
                if chinese_chars:
                    print(f"    範例: {chinese_chars[:5]}")
            else:
                print(f"❌ {encoding}: 無中文字符")
                
        except UnicodeDecodeError as e:
            print(f"❌ {encoding}: 解碼失敗")
        except Exception as e:
            print(f"❌ {encoding}: 錯誤 - {e}")

if __name__ == "__main__":
    test_ascii_encoding()
    check_actual_encoding()