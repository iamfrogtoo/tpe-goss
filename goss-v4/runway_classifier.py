import os
import csv
import math
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

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

# 提取轨迹特征
def extract_features(trajectory):
    features = []
    
    # 提取降落阶段数据（高度低于10000英尺）
    landing_phase = [point for point in trajectory if point['altitude'] < 10000]
    
    if len(landing_phase) < 10:
        return None
    
    # 1. 最终降落点坐标
    final_point = landing_phase[-1]
    final_lat, final_lon = map(float, final_point['position'].split(','))
    
    # 2. 降落前的高度变化率
    altitudes = [point['altitude'] for point in landing_phase]
    altitude_changes = [altitudes[i] - altitudes[i-1] for i in range(1, len(altitudes))]
    avg_altitude_descent = sum(altitude_changes) / len(altitude_changes) if altitude_changes else 0
    max_altitude_descent = min(altitude_changes) if altitude_changes else 0
    
    # 3. 降落前的速度变化
    speeds = [point['speed'] for point in landing_phase]
    speed_changes = [speeds[i] - speeds[i-1] for i in range(1, len(speeds))]
    avg_speed_change = sum(speed_changes) / len(speed_changes) if speed_changes else 0
    final_speed = speeds[-1]
    
    # 4. 降落前的方向变化
    directions = [point['direction'] for point in landing_phase]
    direction_changes = []
    for i in range(1, len(directions)):
        diff = directions[i] - directions[i-1]
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360
        direction_changes.append(diff)
    avg_direction_change = sum(direction_changes) / len(direction_changes) if direction_changes else 0
    final_direction = directions[-1]
    
    # 5. 与各跑道阈值的距离
    runway_distances = []
    for runway in RUNWAYS.values():
        distance = calculate_distance(final_lat, final_lon, runway['threshold_lat'], runway['threshold_lon'])
        runway_distances.append(distance)
    
    # 6. 最终方向与跑道方向的差异
    runway_direction_diff = []
    for runway in RUNWAYS.values():
        diff = abs(final_direction - runway['heading'])
        if diff > 180:
            diff = 360 - diff
        runway_direction_diff.append(diff)
    
    # 7. 降落轨迹的长度
    trajectory_length = 0
    for i in range(1, len(landing_phase)):
        lat1, lon1 = map(float, landing_phase[i-1]['position'].split(','))
        lat2, lon2 = map(float, landing_phase[i]['position'].split(','))
        trajectory_length += calculate_distance(lat1, lon1, lat2, lon2)
    
    # 8. 降落时间
    landing_time = landing_phase[-1]['timestamp'] - landing_phase[0]['timestamp']
    
    features.extend([final_lat, final_lon])
    features.append(avg_altitude_descent)
    features.append(max_altitude_descent)
    features.append(avg_speed_change)
    features.append(final_speed)
    features.append(avg_direction_change)
    features.append(final_direction)
    features.extend(runway_distances)
    features.extend(runway_direction_diff)
    features.append(trajectory_length)
    features.append(landing_time)
    
    return features

# 加载数据
def load_data(data_dir):
    X = []
    y = []
    
    for runway in RUNWAYS.keys():
        runway_dir = os.path.join(data_dir, runway)
        if not os.path.exists(runway_dir):
            continue
        
        for file in os.listdir(runway_dir):
            if file.endswith('.csv'):
                file_path = os.path.join(runway_dir, file)
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
                
                features = extract_features(trajectory)
                if features:
                    X.append(features)
                    y.append(runway)
    
    return np.array(X), np.array(y)

# 训练模型
def train_model(X, y):
    # 使用全部数据训练，因为数据量太少
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 尝试不同的模型
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.ensemble import RandomForestClassifier
    
    models = {
        'KNN (k=1)': KNeighborsClassifier(n_neighbors=1),
        'KNN (k=3)': KNeighborsClassifier(n_neighbors=3),
        'KNN (k=5)': KNeighborsClassifier(n_neighbors=5),
        'Decision Tree': DecisionTreeClassifier(random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42)
    }
    
    best_model = None
    best_accuracy = 0
    
    # 交叉验证
    from sklearn.model_selection import cross_val_score
    
    for name, model in models.items():
        scores = cross_val_score(model, X_scaled, y, cv=5)
        avg_accuracy = scores.mean()
        print(f"{name} 交叉验证准确率: {avg_accuracy:.2f}")
        
        if avg_accuracy > best_accuracy:
            best_accuracy = avg_accuracy
            best_model = model
    
    # 训练最佳模型
    best_model.fit(X_scaled, y)
    print(f"最佳模型: {best_model.__class__.__name__}")
    
    return best_model, scaler

# 预测跑道
def predict_runway(model, scaler, trajectory):
    features = extract_features(trajectory)
    if not features:
        return "无法预测"
    
    features_scaled = scaler.transform([features])
    prediction = model.predict(features_scaled)
    return prediction[0]

# 主函数
def main():
    data_dir = "C:\\Users\\Xin_Zhi\\Desktop\\google_ai\\tpe-goss\\goss-v4\\飛行軌跡"
    
    print("加载数据...")
    X, y = load_data(data_dir)
    print(f"加载了 {len(X)} 条轨迹数据")
    
    if len(X) == 0:
        print("没有找到有效数据")
        return
    
    print("训练模型...")
    model, scaler = train_model(X, y)
    
    # 测试模型
    print("\n测试模型:")
    test_dir = data_dir
    for runway in RUNWAYS.keys():
        runway_dir = os.path.join(test_dir, runway)
        if not os.path.exists(runway_dir):
            continue
        
        files = [f for f in os.listdir(runway_dir) if f.endswith('.csv')]
        if files:
            test_file = os.path.join(runway_dir, files[0])
            trajectory = []
            
            with open(test_file, 'r', encoding='utf-8') as f:
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
            
            prediction = predict_runway(model, scaler, trajectory)
            print(f"文件: {files[0]} (实际跑道: {runway}) -> 预测跑道: {prediction}")

if __name__ == "__main__":
    main()