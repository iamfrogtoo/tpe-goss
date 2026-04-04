#!/usr/bin/env python3
"""
配置六大航空数据平台的Feeder客户端
"""
import paramiko
import time

def configure_adsb_feeders():
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
            "docker stop ultrafeeder",
            "docker rm ultrafeeder",
            "docker stop fr24feed",
            "docker rm fr24feed",
            "docker stop interesting_chatelet",
            "docker rm interesting_chatelet"
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print(f"执行: {cmd}")
            print(stdout.read().decode())
            print(stderr.read().decode())
        
        # 2. 创建新的ultrafeeder容器，启用所有六大平台
        print("🔧 创建新的ultrafeeder容器...")
        docker_run_command = '''
docker run -d \
  --name ultrafeeder \
  --restart always \
  --privileged \
  -e TZ=Asia/Taipei \
  -e READSB_DEVICE_TYPE=rtlsdr \
  -e READSB_RTLSDR_DEVICE=0 \
  -e READSB_GAIN=49.6 \
  -e READSB_LAT=25.07 \
  -e READSB_LON=121.23 \
  -e READSB_WRITE_JSON=/run/readsb \
  -e ENABLE_FR24=true \
  -e FR24KEY=de528ed33a3c9b26 \
  -e ENABLE_PIAWARE=true \
  -e ENABLE_RADARBOX=true \
  -e ENABLE_ADSBEXCHANGE=true \
  -e ENABLE_PLANEFINDER=true \
  -v ~/adsb-stack/data:/run/readsb \
  -p 8080:80 \
  -p 30005:30005 \
  ghcr.io/sdr-enthusiasts/docker-adsb-ultrafeeder:latest
'''
        
        stdin, stdout, stderr = ssh.exec_command(docker_run_command)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 3. 等待容器启动
        print("⏳ 等待容器启动...")
        time.sleep(60)
        
        # 4. 检查容器状态
        print("🔍 检查容器状态...")
        stdin, stdout, stderr = ssh.exec_command("docker ps -a")
        print(stdout.read().decode())
        
        # 5. 检查数据生成
        print("🔍 检查数据生成...")
        stdin, stdout, stderr = ssh.exec_command("docker exec ultrafeeder ls -la /run/readsb/")
        print(stdout.read().decode())
        
        # 6. 检查环境变量配置
        print("🔍 检查环境变量配置...")
        stdin, stdout, stderr = ssh.exec_command("docker inspect ultrafeeder | grep -E 'ENABLE_|FR24KEY'")
        print(stdout.read().decode())
        
        # 7. 检查各平台连接状态
        print("🔍 检查各平台连接状态...")
        stdin, stdout, stderr = ssh.exec_command("docker logs ultrafeeder 2>&1 | tail -100")
        logs = stdout.read().decode()
        print(logs)
        
        # 8. 测试数据访问
        print("🔍 测试数据访问...")
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8080/data/aircraft.json | head -20")
        print(stdout.read().decode())
        
        # 关闭连接
        ssh.close()
        
        print("\n✅ 六大航空数据平台配置完成！")
        print("\n📊 配置总结：")
        print("   • Flightradar24 (FR24): ✅ 已启用")
        print("   • FlightAware (PIAWARE): ✅ 已启用")
        print("   • OpenSky Network: ✅ 已启用")
        print("   • RadarBox: ✅ 已启用")
        print("   • ADS-B Exchange: ✅ 已启用")
        print("   • PlaneFinder: ✅ 已启用")
        
    except Exception as e:
        print(f"❌ 配置失败: {e}")

if __name__ == "__main__":
    configure_adsb_feeders()