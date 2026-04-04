import math
from track_landing import determine_runway, get_runway_info, calculate_distance

# 测试轨迹数据
# 模拟降落05L跑道的轨迹
landing_trajectory_05L = [
    {'timestamp': '2026-04-03 12:00:00', 'latitude': 25.1000, 'longitude': 121.2000, 'altitude': 4000, 'vertical_rate': -800},
    {'timestamp': '2026-04-03 12:01:00', 'latitude': 25.0950, 'longitude': 121.2100, 'altitude': 3000, 'vertical_rate': -750},
    {'timestamp': '2026-04-03 12:02:00', 'latitude': 25.0900, 'longitude': 121.2200, 'altitude': 2000, 'vertical_rate': -700},
    {'timestamp': '2026-04-03 12:03:00', 'latitude': 25.0880, 'longitude': 121.2300, 'altitude': 1000, 'vertical_rate': -650},
    {'timestamp': '2026-04-03 12:04:00', 'latitude': 25.0875, 'longitude': 121.2400, 'altitude': 50, 'vertical_rate': -200}
]

# 模拟降落23R跑道的轨迹
landing_trajectory_23R = [
    {'timestamp': '2026-04-03 12:00:00', 'latitude': 25.0500, 'longitude': 121.2500, 'altitude': 4000, 'vertical_rate': -800},
    {'timestamp': '2026-04-03 12:01:00', 'latitude': 25.0550, 'longitude': 121.2450, 'altitude': 3000, 'vertical_rate': -750},
    {'timestamp': '2026-04-03 12:02:00', 'latitude': 25.0600, 'longitude': 121.2400, 'altitude': 2000, 'vertical_rate': -700},
    {'timestamp': '2026-04-03 12:03:00', 'latitude': 25.0650, 'longitude': 121.2350, 'altitude': 1000, 'vertical_rate': -650},
    {'timestamp': '2026-04-03 12:04:00', 'latitude': 25.0680, 'longitude': 121.2250, 'altitude': 50, 'vertical_rate': -200}
]

def test_runway_detection():
    """测试跑道判别算法"""
    print("测试跑道判别算法...")
    
    # 测试05L跑道的轨迹
    print("\n测试05L跑道的轨迹:")
    runway_05L = determine_runway(landing_trajectory_05L)
    print(f"判别结果: {runway_05L}")
    
    # 测试23R跑道的轨迹
    print("\n测试23R跑道的轨迹:")
    runway_23R = determine_runway(landing_trajectory_23R)
    print(f"判别结果: {runway_23R}")
    
    # 测试获取跑道信息
    print("\n获取跑道信息:")
    runways = get_runway_info()
    for runway in runways:
        print(f"跑道: {runway[0]}, 坐标: ({runway[1]}, {runway[2]}), 方向: {runway[3]}度")
    
    # 测试距离计算
    print("\n测试距离计算:")
    # 计算05L跑道入口到轨迹最后点的距离
    distance_05L = calculate_distance(25.0875, 121.2400, 25.0875, 121.2400)
    print(f"05L跑道入口到自身的距离: {distance_05L}米")
    
    # 计算23R跑道入口到轨迹最后点的距离
    distance_23R = calculate_distance(25.0680, 121.2250, 25.0680, 121.2250)
    print(f"23R跑道入口到自身的距离: {distance_23R}米")

if __name__ == "__main__":
    test_runway_detection()