import os
import csv
import math

# 跑道信息
RUNWAYS = {
    '05L': {'name': '05L', 'threshold_lat': 25.076, 'threshold_lon': 121.234, 'heading': 50},
    '05R': {'name': '05R', 'threshold_lat': 25.076, 'threshold_lon': 121.242, 'heading': 50},
    '23L': {'name': '23L', 'threshold_lat': 25.084, 'threshold_lon': 121.187, 'heading': 230},
    '23R': {'name': '23R', 'threshold_lat': 25.084, 'threshold_lon': 121.179, 'heading': 230}
}

# 计算两点之间的距离（单位：公里）
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # 地球半径
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

# 基于规则的跑道预测
def predict_runway_rule_based(trajectory):
    # 提取降落阶段数据（高度低于10000英尺）
    landing_phase = [point for point in trajectory if point['altitude'] < 10000]
    
    if len(landing_phase) < 5:
        return "无法预测"
    
    # 获取最终降落点
    final_point = landing_phase[-1]
    final_lat, final_lon = map(float, final_point['position'].split(','))
    final_direction = final_point['direction']
    
    # 计算与各跑道的距离
    runway_distances = {}
    for runway_name, runway_info in RUNWAYS.items():
        distance = calculate_distance(final_lat, final_lon, runway_info['threshold_lat'], runway_info['threshold_lon'])
        runway_distances[runway_name] = distance
    
    # 计算方向差异
    runway_direction_diffs = {}
    for runway_name, runway_info in RUNWAYS.items():
        diff = abs(final_direction - runway_info['heading'])
        if diff > 180:
            diff = 360 - diff
        runway_direction_diffs[runway_name] = diff
    
    # 综合评分：距离权重0.7，方向权重0.3
    scores = {}
    for runway_name in RUNWAYS.keys():
        distance_score = 1.0 / (runway_distances[runway_name] + 0.001)  # 距离越近分数越高
        direction_score = 1.0 / (runway_direction_diffs[runway_name] + 0.001)  # 方向越接近分数越高
        scores[runway_name] = distance_score * 0.7 + direction_score * 0.3
    
    # 选择分数最高的跑道
    best_runway = max(scores, key=scores.get)
    
    # 额外规则：检查轨迹的整体方向趋势
    if len(landing_phase) > 10:
        # 计算平均方向
        directions = [point['direction'] for point in landing_phase[-10:]]
        avg_direction = sum(directions) / len(directions)
        
        # 检查方向是否与跑道方向一致
        best_runway_info = RUNWAYS[best_runway]
        direction_diff = abs(avg_direction - best_runway_info['heading'])
        if direction_diff > 90:
            # 如果方向差异太大，重新选择
            sorted_runways = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            for runway_name, _ in sorted_runways[1:]:
                runway_info = RUNWAYS[runway_name]
                direction_diff = abs(avg_direction - runway_info['heading'])
                if direction_diff <= 90:
                    best_runway = runway_name
                    break
    
    return best_runway

# 加载轨迹数据
def load_trajectory(file_path):
    trajectory = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            point = {
                'timestamp': int(row['Timestamp']),
                'utc': row['UTC'],
                'callsign': row['Callsign'],
                'position': row['Position'].strip('"'),
                'altitude': int(row['Altitude']),
                'speed': int(row['Speed']),
                'direction': int(row['Direction'])
            }
            trajectory.append(point)
    return trajectory

# 主函数
def main():
    data_dir = "C:\\Users\\Xin_Zhi\\Desktop\\google_ai\\tpe-goss\\goss-v4\\飛行軌跡"
    
    print("测试基于规则的跑道分类器:")
    
    correct_predictions = 0
    total_predictions = 0
    
    for runway in RUNWAYS.keys():
        runway_dir = os.path.join(data_dir, runway)
        if not os.path.exists(runway_dir):
            continue
        
        for file in os.listdir(runway_dir):
            if file.endswith('.csv'):
                file_path = os.path.join(runway_dir, file)
                trajectory = load_trajectory(file_path)
                prediction = predict_runway_rule_based(trajectory)
                
                is_correct = prediction == runway
                if is_correct:
                    correct_predictions += 1
                total_predictions += 1
                
                status = "正确" if is_correct else "错误"
                print(f"{status} 文件: {file} (实际跑道: {runway}) -> 预测跑道: {prediction}")
    
    if total_predictions > 0:
        accuracy = correct_predictions / total_predictions
        print(f"\n准确率: {accuracy:.2f}")
    else:
        print("没有找到测试数据")

if __name__ == "__main__":
    main()