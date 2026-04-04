import os
import csv
import math
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import accuracy_score

# 跑道信息
RUNWAYS = {
    '05L': {'name': '05L', 'heading': 50},
    '05R': {'name': '05R', 'heading': 50},
    '23L': {'name': '23L', 'heading': 230},
    '23R': {'name': '23R', 'heading': 230}
}

# 计算两点之间的距离（单位：公里）
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
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

# 提取特征
def extract_features(trajectory):
    features = []
    
    if len(trajectory) < 10:
        return None
    
    # 1. 方向特征
    directions = [point['direction'] for point in trajectory]
    avg_direction = sum(directions) / len(directions)
    direction_std = np.std(directions)
    
    # 2. 高度变化特征
    altitudes = [point['altitude'] for point in trajectory]
    altitude_changes = [altitudes[i] - altitudes[i+1] for i in range(len(altitudes)-1)]
    avg_descent_rate = sum(altitude_changes) / len(altitude_changes) if altitude_changes else 0
    max_descent_rate = max(altitude_changes) if altitude_changes else 0
    
    # 3. 速度变化特征
    speeds = [point['speed'] for point in trajectory]
    avg_speed = sum(speeds) / len(speeds)
    speed_std = np.std(speeds)
    
    # 4. 与跑道方向的差异
    runway_direction_diffs = []
    for runway in RUNWAYS.values():
        diff = abs(avg_direction - runway['heading'])
        if diff > 180:
            diff = 360 - diff
        runway_direction_diffs.append(diff)
    
    # 5. 轨迹长度
    trajectory_length = 0
    for i in range(len(trajectory)-1):
        lat1, lon1 = trajectory[i]['lat'], trajectory[i]['lon']
        lat2, lon2 = trajectory[i+1]['lat'], trajectory[i+1]['lon']
        trajectory_length += calculate_distance(lat1, lon1, lat2, lon2)
    
    # 6. 降落时间
    timestamps = [point['timestamp'] for point in trajectory]
    landing_time = max(timestamps) - min(timestamps)
    
    # 7. 最终位置
    final_point = trajectory[-1]
    final_lat = final_point['lat']
    final_lon = final_point['lon']
    
    features.extend([avg_direction, direction_std])
    features.extend([avg_descent_rate, max_descent_rate])
    features.extend([avg_speed, speed_std])
    features.extend(runway_direction_diffs)
    features.extend([trajectory_length, landing_time])
    features.extend([final_lat, final_lon])
    
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
                        lat, lon = map(float, row['Position'].strip('"').split(','))
                        point = {
                            'timestamp': int(row['Timestamp']),
                            'lat': lat,
                            'lon': lon,
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
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 尝试不同的k值
    best_k = 1
    best_score = 0
    
    for k in range(1, min(10, len(X))):
        model = KNeighborsClassifier(n_neighbors=k)
        scores = cross_val_score(model, X_scaled, y, cv=min(5, len(X)))
        avg_score = scores.mean()
        if avg_score > best_score:
            best_score = avg_score
            best_k = k
    
    model = KNeighborsClassifier(n_neighbors=best_k)
    model.fit(X_scaled, y)
    
    print(f"最佳k值: {best_k}")
    print(f"交叉验证准确率: {best_score:.2f}")
    
    return model, scaler

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
    
    print("\n训练模型...")
    model, scaler = train_model(X, y)
    
    # 测试模型
    print("\n测试模型:")
    correct_predictions = 0
    total_predictions = 0
    
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
                        lat, lon = map(float, row['Position'].strip('"').split(','))
                        point = {
                            'timestamp': int(row['Timestamp']),
                            'lat': lat,
                            'lon': lon,
                            'altitude': int(row['Altitude']),
                            'speed': int(row['Speed']),
                            'direction': int(row['Direction'])
                        }
                        trajectory.append(point)
                
                prediction = predict_runway(model, scaler, trajectory)
                is_correct = prediction == runway
                if is_correct:
                    correct_predictions += 1
                total_predictions += 1
                
                status = "正确" if is_correct else "错误"
                print(f"{status} 文件: {file} (实际跑道: {runway}) -> 预测跑道: {prediction}")
    
    if total_predictions > 0:
        accuracy = correct_predictions / total_predictions
        print(f"\n测试准确率: {accuracy:.2f}")

if __name__ == "__main__":
    main()