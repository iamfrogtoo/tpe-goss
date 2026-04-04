#!/usr/bin/env python3
"""
设置PiAware容器并获取Feeder ID
"""
import paramiko
import time

def setup_piaware():
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
        
        # 1. 停止并移除现有PiAware容器
        print("🔧 停止并移除现有PiAware容器...")
        commands = [
            "docker stop piaware",
            "docker rm piaware"
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print(f"执行: {cmd}")
            print(stdout.read().decode())
            print(stderr.read().decode())
        
        # 2. 创建新的PiAware容器
        print("🔧 创建新的PiAware容器...")
        docker_run_command = '''
docker run -d \
  --name piaware \
  --restart always \
  --privileged \
  -e TZ=Asia/Taipei \
  -e BEASTHOST=ultrafeeder \
  -e BEASTPORT=30005 \
  -p 8081:80 \
  ghcr.io/sdr-enthusiasts/docker-piaware:latest
'''
        
        stdin, stdout, stderr = ssh.exec_command(docker_run_command)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 3. 等待容器启动
        print("⏳ 等待容器启动...")
        time.sleep(60)
        
        # 4. 检查容器状态
        print("🔍 检查容器状态...")
        stdin, stdout, stderr = ssh.exec_command("docker ps -a | grep piaware")
        print(stdout.read().decode())
        
        # 5. 获取Feeder ID
        print("🔍 获取Feeder ID...")
        stdin, stdout, stderr = ssh.exec_command("docker logs piaware 2>&1 | grep -E 'feeder id|Feeder ID' | head -10")
        feeder_id_output = stdout.read().decode()
        print(feeder_id_output)
        
        # 6. 检查PiAware网页界面
        print("🔍 检查PiAware网页界面...")
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8081 | head -20")
        print(stdout.read().decode())
        
        # 7. 检查数据传输状态
        print("🔍 检查数据传输状态...")
        stdin, stdout, stderr = ssh.exec_command("docker logs piaware 2>&1 | tail -50")
        print(stdout.read().decode())
        
        # 关闭连接
        ssh.close()
        
        print("\n✅ PiAware配置完成！")
        print("\n📋 FlightAware账号配对步骤：")
        print("1. 访问 FlightAware 网站：https://flightaware.com/account/join")
        print("2. 注册或登录您的账号")
        print("3. 访问：https://flightaware.com/adsb/piaware/claim")
        print("4. 输入上面获取的 Feeder ID")
        print("5. 按照提示完成配对过程")
        print("\n⚠️ 注意：配对完成后，您将获得 Enterprise 会员权限！")
        
    except Exception as e:
        print(f"❌ 配置失败: {e}")

if __name__ == "__main__":
    setup_piaware()