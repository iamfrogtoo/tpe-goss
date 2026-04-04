#!/usr/bin/env python3
"""
验证FR24数据传输
"""
import paramiko

def verify_fr24():
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
        
        print("🔍 验证FR24数据传输...")
        
        # 1. 检查所有容器状态
        print("\n1. 检查所有容器状态...")
        stdin, stdout, stderr = ssh.exec_command("docker ps -a")
        print(stdout.read().decode())
        
        # 2. 检查flightradar24的最新日志
        print("\n2. 检查flightradar24的最新日志...")
        stdin, stdout, stderr = ssh.exec_command("docker logs flightradar24 2>&1 | tail -100")
        print(stdout.read().decode())
        
        # 3. 检查flightradar24的健康状态
        print("\n3. 检查flightradar24的健康状态...")
        stdin, stdout, stderr = ssh.exec_command("docker inspect flightradar24 --format='{{.State.Health.Status}}'")
        print(f"健康状态: {stdout.read().decode().strip()}")
        
        # 关闭连接
        ssh.close()
        
        print("\n✅ 验证完成！")
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_fr24()
