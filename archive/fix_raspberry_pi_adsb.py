#!/usr/bin/env python3
"""
树莓派ADS-B配置修复脚本
"""
import paramiko
import time

def fix_raspberry_pi_adsb():
    # 树莓派信息
    host = "192.168.31.221"
    port = 22
    username = "xinzhi"
    password = "zhi52401314"
    
    try:
        # 建立SSH连接
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port, username, password)
        
        # 1. 停止并移除现有容器
        print("🔧 停止并移除现有容器...")
        commands = [
            "docker-compose -f ~/adsb-stack/docker-compose.yml down",
            "docker volume prune -f",
            "docker network prune -f"
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print(stdout.read().decode())
            print(stderr.read().decode())
        
        # 2. 更新docker-compose.yml
        print("🔧 更新docker-compose.yml配置...")
        docker_compose_content = "services:\n  ultrafeeder:\n    image: ghcr.io/sdr-enthusiasts/docker-adsb-ultrafeeder:latest\n    container_name: ultrafeeder\n    restart: always\n    privileged: true\n    environment:\n      - TZ=Asia/Taipei\n      - READSB_DEVICE_TYPE=rtlsdr\n      - READSB_RTLSDR_DEVICE=0\n      - READSB_GAIN=49.6\n      - READSB_LAT=25.07\n      - READSB_LON=121.23\n      - READSB_WRITE_JSON=/run/readsb\n      - ENABLE_FR24=true\n      - FR24KEY=de528ed33a3c9b26\n      - ENABLE_PIAWARE=true\n      - ENABLE_RADARBOX=true\n      - ENABLE_ADSBEXCHANGE=true\n      - ENABLE_PLANEFINDER=true\n    volumes:\n      - ~/adsb-stack/data:/run/readsb\n    ports:\n      - \"8080:80\"\n      - \"30005:30005\"\n    networks:\n      - adsb_network\n\nnetworks:\n  adsb_network:\n    name: adsb_network"
        
        # 写入配置文件
        stdin, stdout, stderr = ssh.exec_command('echo "' + docker_compose_content.replace('"', '\\"') + '" > ~/adsb-stack/docker-compose.yml')
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 3. 重新启动容器
        print("🔧 重新启动容器...")
        stdin, stdout, stderr = ssh.exec_command("docker-compose -f ~/adsb-stack/docker-compose.yml up -d")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 4. 等待容器启动
        print("⏳ 等待容器启动...")
        time.sleep(30)
        
        # 5. 检查状态
        print("🔍 检查容器状态...")
        stdin, stdout, stderr = ssh.exec_command("docker ps -a")
        print(stdout.read().decode())
        
        print("🔍 检查数据生成...")
        stdin, stdout, stderr = ssh.exec_command("ls -la ~/adsb-stack/data/")
        print(stdout.read().decode())
        
        # 6. 检查各平台连接状态
        print("🔍 检查各平台连接状态...")
        stdin, stdout, stderr = ssh.exec_command("docker logs ultrafeeder 2>&1 | tail -100")
        logs = stdout.read().decode()
        print(logs)
        
        # 关闭连接
        ssh.close()
        
        print("\n✅ 树莓派ADS-B配置修复完成！")
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")

if __name__ == "__main__":
    fix_raspberry_pi_adsb()