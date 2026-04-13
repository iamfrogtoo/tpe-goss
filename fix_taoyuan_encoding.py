import requests
import chardet
from datetime import datetime

def detect_and_fix_encoding():
    """檢測並修正桃園機場資料的編碼問題"""
    
    # 讀取剛抓取的最新資料
    files = {
        "客機": "客機_latest.txt",
        "貨機": "貨機_latest.txt"
    }
    
    for flight_type, filename in files.items():
        print(f"\n=== 處理 {flight_type} 資料編碼 ===")
        
        try:
            # 讀取檔案並檢測編碼
            with open(filename, 'rb') as f:
                raw_data = f.read()
            
            # 檢測編碼
            encoding_result = chardet.detect(raw_data)
            detected_encoding = encoding_result['encoding']
            confidence = encoding_result['confidence']
            
            print(f"檢測到的編碼: {detected_encoding} (可信度: {confidence:.2f})")
            
            # 嘗試不同編碼讀取
            encodings_to_try = ['utf-8', 'big5', 'cp950', 'gbk', 'gb2312', 'latin1']
            
            for encoding in encodings_to_try:
                try:
                    content = raw_data.decode(encoding)
                    
                    # 檢查是否包含中文字符
                    chinese_chars = []
                    for char in content[:500]:  # 檢查前500個字符
                        if '\u4e00' <= char <= '\u9fff':
                            chinese_chars.append(char)
                    
                    if len(chinese_chars) > 10:  # 如果包含足夠的中文字符
                        print(f"✅ {encoding}: 包含 {len(chinese_chars)} 個中文字符")
                        
                        # 顯示修正後的中文樣本
                        lines = content.split('\n')[:3]
                        print("修正後的前3行樣本:")
                        for i, line in enumerate(lines[:3]):
                            print(f"  {i+1}. {line}")
                        
                        # 儲存修正後的檔案
                        fixed_filename = f"{flight_type}_fixed_{encoding}.txt"
                        with open(fixed_filename, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"📁 已儲存修正版: {fixed_filename}")
                        
                        break
                    else:
                        print(f"❌ {encoding}: 僅包含 {len(chinese_chars)} 個中文字符")
                        
                except UnicodeDecodeError:
                    print(f"❌ {encoding}: 解碼失敗")
                except Exception as e:
                    print(f"❌ {encoding}: 錯誤 - {e}")
            
        except Exception as e:
            print(f"❌ 處理 {filename} 失敗: {e}")

def analyze_encoding_patterns():
    """分析編碼模式"""
    
    print("\n=== 分析編碼模式 ===")
    
    # 讀取客機資料進行分析
    with open("客機_latest.txt", 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # 分析常見的亂碼模式
    lines = content.split('\n')[:10]
    
    print("前10行資料分析:")
    for i, line in enumerate(lines):
        if line.strip():
            # 分割欄位
            fields = line.split(',')
            if len(fields) >= 10:
                airline = fields[2].strip() if len(fields) > 2 else ""
                destination = fields[9].strip() if len(fields) > 9 else ""
                
                print(f"\n行 {i+1}:")
                print(f"  航空公司: {repr(airline)}")
                print(f"  目的地: {repr(destination)}")
                
                # 嘗試猜測正確的航空公司
                if '�u���' in airline:
                    print("  🔍 猜測: 大韓航空 (Korean Air)")
                elif '�j�����' in airline:
                    print("  🔍 猜測: 韓亞航空 (Asiana Airlines)")
                elif '�����F' in airline:
                    print("  🔍 猜測: 中華航空 (China Airlines)")

if __name__ == "__main__":
    print("開始修正桃園機場資料編碼問題...")
    detect_and_fix_encoding()
    analyze_encoding_patterns()