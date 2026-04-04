import os
import csv

# 跑道列表
RUNWAYS = ['05L', '05R', '23L', '23R']

# 提取降落阶段数据
def extract_landing_phase(trajectory):
    # 按时间排序
    sorted_trajectory = sorted(trajectory, key=lambda x: int(x['Timestamp']))
    
    # 找到高度开始持续下降的点
    max_altitude = 0
    descent_start_index = 0
    
    # 找到最大高度
    for i, point in enumerate(sorted_trajectory):
        altitude = int(point['Altitude'])
        if altitude > max_altitude:
            max_altitude = altitude
            descent_start_index = i
    
    # 从最大高度开始，找到持续下降的部分
    landing_phase = []
    in_descent = False
    previous_altitude = max_altitude
    
    for i in range(descent_start_index, len(sorted_trajectory)):
        point = sorted_trajectory[i]
        altitude = int(point['Altitude'])
        
        # 如果高度开始下降，标记为进入降落阶段
        if altitude < previous_altitude * 0.95:
            in_descent = True
        
        # 如果在降落阶段，添加数据点
        if in_descent and altitude > 0:
            landing_phase.append(point)
        
        previous_altitude = altitude
    
    # 确保有足够的数据点
    if len(landing_phase) < 10:
        return None
    
    return landing_phase

# 处理单个文件
def process_file(input_path, output_path):
    # 读取原始数据
    trajectory = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            trajectory.append(row)
    
    # 提取降落阶段
    landing_phase = extract_landing_phase(trajectory)
    
    if landing_phase:
        # 保存处理后的数据
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(landing_phase)
        return len(landing_phase)
    
    return 0

# 主函数
def main():
    data_dir = "C:\\Users\\Xin_Zhi\\Desktop\\google_ai\\tpe-goss\\goss-v4\\飛行軌跡"
    
    total_files = 0
    total_lines_before = 0
    total_lines_after = 0
    
    print("开始处理飞行轨迹数据...")
    
    for runway in RUNWAYS:
        runway_dir = os.path.join(data_dir, runway)
        if not os.path.exists(runway_dir):
            continue
        
        print(f"\n处理跑道 {runway}:")
        
        for file in os.listdir(runway_dir):
            if file.endswith('.csv'):
                input_path = os.path.join(runway_dir, file)
                
                # 统计原始行数
                with open(input_path, 'r', encoding='utf-8') as f:
                    lines_before = sum(1 for _ in f) - 1  # 减去表头
                
                # 处理文件
                lines_after = process_file(input_path, input_path)
                
                if lines_after > 0:
                    total_files += 1
                    total_lines_before += lines_before
                    total_lines_after += lines_after
                    reduction = (1 - lines_after / lines_before) * 100
                    print(f"  {file}: {lines_before} 行 -> {lines_after} 行 (减少 {reduction:.1f}%)")
    
    print(f"\n处理完成:")
    print(f"总文件数: {total_files}")
    print(f"原始总行数: {total_lines_before}")
    print(f"处理后总行数: {total_lines_after}")
    print(f"总减少比例: {(1 - total_lines_after / total_lines_before) * 100:.1f}%")

if __name__ == "__main__":
    main()