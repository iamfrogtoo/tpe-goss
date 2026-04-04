import os
import csv
import math

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

# 分析轨迹数据的降落点
def analyze_landing_points(data_dir):
    landing_points = {}
    
    for runway in ['05L', '05R', '23L', '23R']:
        runway_dir = os.path.join(data_dir, runway)
        if not os.path.exists(runway_dir):
            continue
        
        runway_points = []
        for file in os.listdir(runway_dir):
            if file.endswith('.csv'):
                file_path = os.path.join(runway_dir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    trajectory = []
                    for row in reader:
                        point = {
                            'position': row['Position'].strip('"'),
                            'altitude': int(row['Altitude'])
                        }
                        trajectory.append(point)
                
                # 找到降落点（高度为0的点）
                landing_point = None
                for point in reversed(trajectory):
                    if point['altitude'] == 0:
                        landing_point = point
                        break
                
                if landing_point:
                    lat, lon = map(float, landing_point['position'].split(','))
                    runway_points.append((lat, lon))
        
        if runway_points:
            landing_points[runway] = runway_points
    
    return landing_points

# 计算跑道的平均降落点
def calculate_average_landing_point(points):
    if not points:
        return None
    
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    avg_lat = sum(lats) / len(lats)
    avg_lon = sum(lons) / len(lons)
    
    return (avg_lat, avg_lon)

# 主函数
def main():
    data_dir = "C:\\Users\\Xin_Zhi\\Desktop\\google_ai\\tpe-goss\\goss-v4\\飛行軌跡"
    
    print("分析降落点数据:")
    landing_points = analyze_landing_points(data_dir)
    
    for runway, points in landing_points.items():
        print(f"\n跑道 {runway}:")
        print(f"降落点数量: {len(points)}")
        
        avg_point = calculate_average_landing_point(points)
        if avg_point:
            print(f"平均降落点: {avg_point[0]:.6f}, {avg_point[1]:.6f}")
        
        # 打印前几个降落点
        print("前5个降落点:")
        for i, (lat, lon) in enumerate(points[:5]):
            print(f"  {i+1}: {lat:.6f}, {lon:.6f}")

if __name__ == "__main__":
    main()