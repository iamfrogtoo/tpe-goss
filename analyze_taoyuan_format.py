import re
from datetime import datetime

def analyze_taoyuan_format():
    """分析桃園機場資料格式和亂碼問題"""
    
    print("=== 分析桃園機場資料格式 ===")
    
    # 讀取客機資料
    with open("客機_latest.txt", 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    print(f"總行數: {len(lines)}")
    
    # 分析前5行的結構
    print("\n=== 資料結構分析 ===")
    for i, line in enumerate(lines[:5]):
        if line.strip():
            print(f"\n行 {i+1}:")
            
            # 分割欄位
            fields = line.split(',')
            print(f"  欄位數: {len(fields)}")
            
            # 顯示每個欄位
            for j, field in enumerate(fields):
                cleaned_field = field.strip()
                if cleaned_field:
                    print(f"  欄位 {j}: {repr(cleaned_field)}")
    
    # 分析亂碼模式
    print("\n=== 亂碼模式分析 ===")
    
    # 收集常見的亂碼模式
    garbage_patterns = {}
    
    for line in lines[:20]:
        if line.strip():
            fields = line.split(',')
            
            # 檢查航空公司欄位（索引2）
            if len(fields) > 2:
                airline = fields[2].strip()
                if airline and len(airline) > 0:
                    if airline not in garbage_patterns:
                        garbage_patterns[airline] = 0
                    garbage_patterns[airline] += 1
            
            # 檢查目的地欄位（索引9）
            if len(fields) > 9:
                destination = fields[9].strip()
                if destination and len(destination) > 0:
                    if destination not in garbage_patterns:
                        garbage_patterns[destination] = 0
                    garbage_patterns[destination] += 1
    
    print("常見的亂碼模式:")
    for pattern, count in sorted(garbage_patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {repr(pattern)}: 出現 {count} 次")
    
    # 嘗試推測正確的航空公司名稱
    print("\n=== 航空公司推測 ===")
    airline_mapping = {
        'LJ': '大韓航空 (Korean Air)',
        'KE': '韓亞航空 (Asiana Airlines)', 
        'ZE': '易斯達航空 (Eastar Jet)',
        'TW': '德威航空 (Tway Air)',
        'CX': '國泰航空 (Cathay Pacific)',
        'TR': '酷航 (Scoot)',
        'SQ': '新加坡航空 (Singapore Airlines)',
        'MM': '樂桃航空 (Peach Aviation)',
        'HB': '香港快運航空 (HK Express)',
        'Z2': '亞洲航空 (AirAsia Zest)',
        'GK': '捷星日本航空 (Jetstar Japan)',
        '5J': '宿霧太平洋航空 (Cebu Pacific)',
        'IT': '台灣虎航 (Tigerair Taiwan)',
        'BR': '長榮航空 (EVA Air)',
        'UA': '聯合航空 (United Airlines)',
        'JX': '星宇航空 (Starlux Airlines)',
        'AC': '加拿大航空 (Air Canada)',
        'TG': '泰國航空 (Thai Airways)',
        'CI': '中華航空 (China Airlines)',
        'DL': '達美航空 (Delta Air Lines)',
        'VN': '越南航空 (Vietnam Airlines)',
        'TK': '土耳其航空 (Turkish Airlines)',
        'AV': '哥倫比亞航空 (Avianca)',
        'CM': '巴拿馬航空 (Copa Airlines)'
    }
    
    # 顯示前10個航班的航空公司
    print("前10個航班的航空公司:")
    for i, line in enumerate(lines[:10]):
        if line.strip():
            fields = line.split(',')
            if len(fields) > 2:
                airline_code = fields[2].strip()
                airline_name = airline_mapping.get(airline_code, '未知航空公司')
                print(f"  {airline_code}: {airline_name}")

def create_fixed_taoyuan_data():
    """建立修正後的桃園機場資料"""
    
    print("\n=== 建立修正版資料 ===")
    
    # 讀取原始資料
    with open("客機_latest.txt", 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # 航空公司代碼對照表
    airline_mapping = {
        'LJ': '大韓航空', 'KE': '韓亞航空', 'ZE': '易斯達航空',
        'TW': '德威航空', 'CX': '國泰航空', 'TR': '酷航',
        'SQ': '新加坡航空', 'MM': '樂桃航空', 'HB': '香港快運航空',
        'Z2': '亞洲航空', 'GK': '捷星日本航空', '5J': '宿霧太平洋航空',
        'IT': '台灣虎航', 'BR': '長榮航空', 'UA': '聯合航空',
        'JX': '星宇航空', 'AC': '加拿大航空', 'TG': '泰國航空',
        'CI': '中華航空', 'DL': '達美航空', 'VN': '越南航空',
        'TK': '土耳其航空', 'AV': '哥倫比亞航空', 'CM': '巴拿馬航空'
    }
    
    # 建立修正後的資料
    fixed_lines = []
    
    for line in lines:
        if line.strip():
            fields = line.split(',')
            
            # 修正航空公司名稱（如果可能）
            if len(fields) > 2:
                airline_code = fields[2].strip()
                if airline_code in airline_mapping:
                    # 在原始資料中保留航空公司代碼，但添加註解
                    fixed_line = line.replace(airline_code, f"{airline_code}({airline_mapping[airline_code]})")
                    fixed_lines.append(fixed_line)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
    
    # 儲存修正版
    with open("客機_fixed.txt", 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print("✅ 已建立修正版資料: 客機_fixed.txt")
    
    # 顯示修正後的樣本
    print("\n修正後的前3行樣本:")
    for i, line in enumerate(fixed_lines[:3]):
        print(f"  {i+1}. {line}")

if __name__ == "__main__":
    analyze_taoyuan_format()
    create_fixed_taoyuan_data()