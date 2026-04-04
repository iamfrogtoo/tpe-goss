import time
import subprocess
import os

# 确保在正确的目录下运行
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def run_fr24_fetch():
    """运行 FR24 抓取脚本"""
    print("\n=== 运行 FR24 抓取 ===")
    result = subprocess.run(['python', 'fetch_fr24_v4.py'], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("错误:", result.stderr)

def run_adsb_fetch():
    """运行天线数据抓取脚本"""
    print("\n=== 运行天线数据抓取 ===")
    # 检查是否存在天线数据抓取脚本
    if os.path.exists('fetch_adsb_v4.py'):
        result = subprocess.run(['python', 'fetch_adsb_v4.py'], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("错误:", result.stderr)
    else:
        print("天线数据抓取脚本不存在，使用模拟数据")
        # 模拟天线数据
        print("模拟天线数据:")
        print("- 航班号: CXA123")
        print("- 飞机代码: A320")
        print("- 高度: 1000 英尺")
        print("- 速度: 150 节")
        print("- 位置: 25.08, 121.23")

def main():
    """主函数"""
    print("开始数据抓取和比较...")
    
    # 运行 FR24 抓取
    run_fr24_fetch()
    
    # 运行天线数据抓取
    run_adsb_fetch()
    
    print("\n=== 数据比较完成 ===")
    print("请比较 FR24 数据和天线数据，查看覆盖范围差异")

if __name__ == "__main__":
    main()
