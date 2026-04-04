#!/usr/bin/env python3
"""
设置FR24Feed容器 - 版本2
"""
import paramiko
import time

def setup_fr24feed_v2():
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
        
        # 1. 停止并移除现有FR24Feed容器
        print("🔧 停止并移除现有FR24Feed容器...")
        commands = [
            "docker stop fr24feed 2>/dev/null || true",
            "docker rm fr24feed 2>/dev/null || true"
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print(f"执行: {cmd}")
            print(stdout.read().decode())
            print(stderr.read().decode())
        
        # 2. 检查ultrafeeder容器是否在运行
        print("🔍 检查ultrafeeder容器状态...")
        stdin, stdout, stderr = ssh.exec_command("docker ps --filter name=ultrafeeder --format '{{.Names}}'")
        ultrafeeder_status = stdout.read().decode().strip()
        if not ultrafeeder_status:
            print("❌ ultrafeeder容器未运行！")
            return
        
        print(f"✅ ultrafeeder容器正在运行")
        
        # 3. 创建新的FR24Feed容器，连接到ultrafeeder的网络
        print("🔧 创建新的FR24Feed容器...")
        docker_run_command = '''
docker run -d \\
  --name fr24feed \\
  --restart always \\
  --network container:ultrafeeder \\
  -e TZ=Asia/Taipei \\
  -e BEASTHOST=127.0.0.1 \\
  -e BEASTPORT=30005 \\
  -e FR24KEY=de528ed33a3c9b26 \\
  ghcr.io/sdr-enthusiasts/docker-fr24feed:latest
'''
        
        stdin, stdout, stderr = ssh.exec_command(docker_run_command)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 4. 等待容器启动
        print("⏳ 等待容器启动...")
        time.sleep(90)
        
        # 5. 检查容器状态
        print("🔍 检查容器状态...")
        stdin, stdout, stderr = ssh.exec_command("docker ps -a | grep fr24feed")
        print(stdout.read().decode())
        
        # 6. 检查容器日志
        print("🔍 检查FR24Feed日志...")
        stdin, stdout, stderr = ssh.exec_command("docker logs fr24feed 2>&1 | tail -150")
        print(stdout.read().decode())
        
        # 关闭连接
        ssh.close()
        
        print("\n✅ FR24Feed配置完成！")
        
    except Exception as e:
        print(f"❌ 配置失败: {e}")

if __name__ == "__main__":
    setup_fr24feed_v2()
