import os
import csv
import math
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier

# 跑道信息
RUNWAYS = {
    '05L': {'name': '05L', 'heading': 50},
    '05R': {'name': '05R', 'heading': 50},
    '23L': {'name': '23L', 'heading': 230},
    '23R': {'name': '23R', 'heading': 230}
}

# 提取降落阶段数据
def extract_landing_phase(trajectory):
    # 按时间排序
    sorted_trajectory = sorted(trajectory, key=lambda x: x['timestamp'])
    
    # 找到高度开始持续下降的点
    landing_phase = []
    max_altitude = 0
    descent_started = False
    
    for point in sorted_trajectory:
        if point['altitude'] > max_altitude:
            max_altitude = point['altitude']
        elif point['altitude'] < max_altitude * 0.9:  # 高度开始下降超过10%
            descent_started = True
        
        if descent_started and point['altitude'] > 0:
            landing_phase.append(point)
    
    # 确保有足够的数据点
    if len(landing_phase) < 10:
        return None
    
    return landing_phase

# 提取特征
def extract_features(landing_phase):
    features = []
    
    # 1. 方向特征
    directions = [point['direction'] for point in landing_phase]
    avg_direction = sum(directions) / len(directions)
    direction_std = np.std(directions)
    
    # 2. 高度变化特征
    altitudes = [point['altitude'] for point in landing_phase]
    altitude_changes = [altitudes[i] - altitudes[i+1] for i in range(len(altitudes)-1)]
    avg_descent_rate = sum(altitude_changes) / len(altitude_changes) if altitude_changes else 0
    
    # 3. 速度变化特征
    speeds = [point['speed'] for point in landing_phase]
    avg_speed = sum(speeds) / len(speeds)
    
    # 4. 与跑道方向的差异
    runway_direction_diffs = []
    for runway in RUNWAYS.values():
        diff = abs(avg_direction - runway['heading'])
        if diff > 180:
            diff = 360 - diff
        runway_direction_diffs.append(diff)
    
    features.extend([avg_direction, direction_std])
    features.append(avg_descent_rate)
    features.append(avg_speed)
    features.extend(runway_direction_diffs)
    
    return features

# 批量处理文件
def process_files_in_batches(data_dir, batch_size=15):
    all_files = []
    
    # 收集所有文件路径
    for runway in RUNWAYS.keys():
        runway_dir = os.path.join(data_dir, runway)
        if os.path.exists(runway_dir):
            for file in os.listdir(runway_dir):
                if file.endswith('.csv'):
                    all_files.append((runway, os.path.join(runway_dir, file)))
    
    # 分批处理
    for i in range(0, len(all_files), batch_size):
        batch_files = all_files[i:i+batch_size]
        X_batch = []
        y_batch = []
        
        for runway, file_path in batch_files:
            # 读取文件
            trajectory = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    point = {
                        'timestamp': int(row['Timestamp']),
                        'position': row['Position'].strip('"'),
                        'altitude': int(row['Altitude']),
                        'speed': int(row['Speed']),
                        'direction': int(row['Direction'])
                    }
                    trajectory.append(point)
            
            # 提取降落阶段
            landing_phase = extract_landing_phase(trajectory)
            if landing_phase:
                # 提取特征
                features = extract_features(landing_phase)
                if features:
                    X_batch.append(features)
                    y_batch.append(runway)
        
        yield np.array(X_batch), np.array(y_batch)

# 主函数
def main():
    data_dir = "C:\\Users\\Xin_Zhi\\Desktop\\google_ai\\tpe-goss\\goss-v4\\飛行軌跡"
    
    # 分批处理数据
    all_X = []
    all_y = []
    
    for X_batch, y_batch in process_files_in_batches(data_dir, batch_size=15):
        if len(X_batch) > 0:
            all_X.extend(X_batch)
            all_y.extend(y_batch)
    
    X = np.array(all_X)
    y = np.array(all_y)
    
    print(f"处理了 {len(X)} 条降落轨迹")
    
    if len(X) > 0:
        # 训练模型
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        model = KNeighborsClassifier(n_neighbors=min(5, len(X)))
        model.fit(X_scaled, y)
        
        print("模型训练完成")

if __name__ == "__main__":
    main()