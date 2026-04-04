#!/usr/bin/env python3
"""
诊断和修复FR24数据传输问题
"""
import paramiko
import time

def diagnose_and_fix_fr24():
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
        
        print("🔍 开始诊断...")
        
        # 1. 检查所有Docker容器
        print("\n1. 检查所有Docker容器...")
        stdin, stdout, stderr = ssh.exec_command("docker ps -a")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 2. 检查Docker镜像
        print("\n2. 检查Docker镜像...")
        stdin, stdout, stderr = ssh.exec_command("docker images")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 3. 检查ultrafeeder的完整日志
        print("\n3. 检查ultrafeeder的完整日志...")
        stdin, stdout, stderr = ssh.exec_command("docker logs ultrafeeder 2>&1")
        logs = stdout.read().decode()
        print(logs[-2000:] if len(logs) > 2000 else logs)
        print(stderr.read().decode())
        
        # 4. 检查是否有之前的fr24feed相关配置或容器
        print("\n4. 检查历史容器和配置...")
        commands = [
            "docker ps -a --format '{{.Names}} {{.Image}}' | sort",
            "ls -la ~/ 2>/dev/null || true",
            "ls -la ~/adsb-stack/ 2>/dev/null || true"
        ]
        
        for cmd in commands:
            print(f"\n执行: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print(stdout.read().decode())
            print(stderr.read().decode())
        
        # 5. 尝试从Docker Hub拉取fr24feed镜像（如果ghcr.io不行）
        print("\n5. 尝试查找可用的fr24feed镜像...")
        
        # 先尝试使用sdr-enthusiasts的fr24feed
        print("\n尝试使用sdr-enthusiasts的fr24feed镜像...")
        
        # 先检查是否能访问ghcr.io
        stdin, stdout, stderr = ssh.exec_command("curl -s https://ghcr.io/v2/ | head -10")
        print("ghcr.io访问测试:")
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 尝试使用不同的镜像名称
        print("\n尝试各种可能的fr24feed镜像...")
        
        # 先检查是否有其他镜像源
        print("\n检查Docker Hub上的fr24feed镜像...")
        
        # 让我们先尝试一个更简单的方法 - 检查ultrafeeder容器是否真的有FR24支持
        print("\n6. 检查ultrafeeder容器内部的服务...")
        
        commands = [
            "docker exec ultrafeeder ls -la /etc/s6-overlay/s6-rc.d/ 2>/dev/null",
            "docker exec ultrafeeder find / -name '*fr24*' -o -name '*FR24*' 2>/dev/null | head -20"
        ]
        
        for cmd in commands:
            print(f"\n执行: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            print(stdout.read().decode())
            print(stderr.read().decode())
        
        # 关闭连接
        ssh.close()
        
        print("\n✅ 诊断完成！")
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_and_fix_fr24()
