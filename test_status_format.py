import re

# 模拟从CSV文件中读取的状态文本
# 根据用户提供的信息，实际格式可能是"乱码+英文状态"
status_examples = [
    '�Ǯ�ON TIME',  # 乱码 + ON TIME
    '�ɶ����SCHEDULE CHANGE',  # 乱码 + SCHEDULE CHANGE
    'ON TIME',  # 纯英文
    'SCHEDULE CHANGE',  # 纯英文
    'DELAYED',  # 纯英文
    'CANCELLED',  # 纯英文
    'BOARDING',  # 纯英文
    'DEPARTED'  # 纯英文
]

# 状态文本映射为中文
status_map = {
    'ON TIME': '準時',
    'SCHEDULE CHANGE': '時間更改',
    'DELAYED': '延誤',
    'CANCELLED': '取消',
    'BOARDING': '登機中',
    'DEPARTED': '已起飛'
}

# 测试正则表达式
print("测试状态文本处理:")
for status in status_examples:
    # 匹配英文状态文本，忽略前面的乱码
    match = re.search(r'(ON TIME|SCHEDULE CHANGE|DELAYED|CANCELLED|BOARDING|DEPARTED)', status)
    if match:
        english_status = match.group(0)
        chinese_status = status_map.get(english_status, english_status)
        print(f"原始状态: '{status}' -> 英文状态: '{english_status}' -> 中文状态: '{chinese_status}'")
    else:
        print(f"原始状态: '{status}' -> 未匹配到状态")
