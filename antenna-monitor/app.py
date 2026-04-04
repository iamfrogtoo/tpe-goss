#!/usr/bin/env python3
"""
天线活动状态监控工具
"""
import os
import time
import json
import threading
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import sqlite3
from flask import Flask, render_template, jsonify, request
import configparser

class AntennaMonitor:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # 初始化数据库
        self.db_path = self.config.get('Database', 'db_path', fallback='antenna_monitor.db')
        self.init_database()
        
        # 初始化状态
        self.antenna_status = {'status': 'unknown', 'last_checked': None, 'signal_strength': 0}
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 告警设置
        self.alert_history = []
        self.alert_cooldown = self.config.getint('Alerts', 'cooldown_minutes', fallback=5)
        self.last_alert_time = 0
        
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建状态表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS antenna_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            status TEXT,
            signal_strength REAL,
            message TEXT
        )''')
        
        # 创建告警表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            alert_type TEXT,
            message TEXT,
            status TEXT DEFAULT 'unread'
        )''')
        
        conn.commit()
        conn.close()
    
    def check_antenna_status(self):
        """检查天线状态"""
        try:
            # 这里是模拟检查，实际项目中需要根据具体天线类型实现
            # 例如：通过网络请求、串口通信等方式检查天线状态
            
            # 模拟信号强度（0-100）
            import random
            signal_strength = random.uniform(0, 100)
            
            if signal_strength > 70:
                status = 'active'
                message = '天线工作正常'
            elif signal_strength > 30:
                status = 'weak'
                message = '信号强度较弱'
            else:
                status = 'inactive'
                message = '信号强度过低，天线可能异常'
            
            self.antenna_status = {
                'status': status,
                'last_checked': datetime.datetime.now().isoformat(),
                'signal_strength': signal_strength
            }
            
            # 记录到数据库
            self.log_status(status, signal_strength, message)
            
            # 检查是否需要告警
            if status in ['weak', 'inactive']:
                self.check_alert(status, message, signal_strength)
            
            return self.antenna_status
            
        except Exception as e:
            error_msg = f"检查天线状态时出错: {str(e)}"
            self.antenna_status = {
                'status': 'error',
                'last_checked': datetime.datetime.now().isoformat(),
                'signal_strength': 0
            }
            self.log_status('error', 0, error_msg)
            self.check_alert('error', error_msg, 0)
            return self.antenna_status
    
    def log_status(self, status, signal_strength, message):
        """记录状态到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO antenna_status (timestamp, status, signal_strength, message)
        VALUES (?, ?, ?, ?)
        ''', (datetime.datetime.now().isoformat(), status, signal_strength, message))
        
        conn.commit()
        conn.close()
    
    def check_alert(self, alert_type, message, signal_strength):
        """检查是否需要告警"""
        current_time = time.time()
        
        # 检查冷却时间
        if current_time - self.last_alert_time < self.alert_cooldown * 60:
            return
        
        alert_message = f"【天线告警】{alert_type.upper()}: {message} (信号强度: {signal_strength:.2f}%)"
        
        # 记录告警
        self.log_alert(alert_type, alert_message)
        
        # 发送告警
        self.send_alerts(alert_message, alert_type)
        
        self.last_alert_time = current_time
    
    def log_alert(self, alert_type, message):
        """记录告警到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO alerts (timestamp, alert_type, message)
        VALUES (?, ?, ?)
        ''', (datetime.datetime.now().isoformat(), alert_type, message))
        
        conn.commit()
        conn.close()
    
    def send_alerts(self, message, alert_type):
        """发送告警通知"""
        # 发送邮件
        if self.config.getboolean('Email', 'enabled', fallback=False):
            try:
                self.send_email_alert(message, alert_type)
            except Exception as e:
                print(f"发送邮件告警失败: {str(e)}")
        
        # 发送Webhook（如Discord、Slack等）
        if self.config.getboolean('Webhook', 'enabled', fallback=False):
            try:
                self.send_webhook_alert(message, alert_type)
            except Exception as e:
                print(f"发送Webhook告警失败: {str(e)}")
    
    def send_email_alert(self, message, alert_type):
        """发送邮件告警"""
        smtp_server = self.config.get('Email', 'smtp_server')
        smtp_port = self.config.getint('Email', 'smtp_port')
        smtp_user = self.config.get('Email', 'smtp_user')
        smtp_password = self.config.get('Email', 'smtp_password')
        from_email = self.config.get('Email', 'from_email')
        to_emails = self.config.get('Email', 'to_emails').split(',')
        
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = f"天线监控告警 - {alert_type.upper()}"
        
        body = f"""时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

告警类型: {alert_type.upper()}

告警信息: {message}

建议操作:
- 检查天线物理连接
- 检查信号强度
- 重启相关设备
"""
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
    
    def send_webhook_alert(self, message, alert_type):
        """发送Webhook告警"""
        webhook_url = self.config.get('Webhook', 'url')
        
        payload = {
            'content': f"**天线监控告警 - {alert_type.upper()}**\n{message}"
        }
        
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
    
    def start_monitoring(self, interval=60):
        """开始监控"""
        self.is_monitoring = True
        
        def monitor_loop():
            while self.is_monitoring:
                self.check_antenna_status()
                time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def get_status_history(self, hours=24):
        """获取历史状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 计算时间范围
        start_time = (datetime.datetime.now() - datetime.timedelta(hours=hours)).isoformat()
        
        cursor.execute('''
        SELECT timestamp, status, signal_strength, message
        FROM antenna_status
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
        ''', (start_time,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'timestamp': row[0],
            'status': row[1],
            'signal_strength': row[2],
            'message': row[3]
        } for row in results]
    
    def get_alerts(self, limit=50):
        """获取告警记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, timestamp, alert_type, message, status
        FROM alerts
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'timestamp': row[1],
            'alert_type': row[2],
            'message': row[3],
            'status': row[4]
        } for row in results]
    
    def mark_alert_as_read(self, alert_id):
        """标记告警为已读"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE alerts
        SET status = 'read'
        WHERE id = ?
        ''', (alert_id,))
        
        conn.commit()
        conn.close()

# 初始化Flask应用
app = Flask(__name__)
monitor = AntennaMonitor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    return jsonify(monitor.antenna_status)

@app.route('/api/check')
def check_status():
    status = monitor.check_antenna_status()
    return jsonify(status)

@app.route('/api/history')
def get_history():
    hours = request.args.get('hours', 24, type=int)
    history = monitor.get_status_history(hours)
    return jsonify(history)

@app.route('/api/alerts')
def get_alerts():
    alerts = monitor.get_alerts()
    return jsonify(alerts)

@app.route('/api/alert/read/<int:alert_id>')
def read_alert(alert_id):
    monitor.mark_alert_as_read(alert_id)
    return jsonify({'success': True})

@app.route('/api/start')
def start_monitoring():
    interval = request.args.get('interval', 60, type=int)
    monitor.start_monitoring(interval)
    return jsonify({'success': True, 'message': '监控已启动'})

@app.route('/api/stop')
def stop_monitoring():
    monitor.stop_monitoring()
    return jsonify({'success': True, 'message': '监控已停止'})

if __name__ == '__main__':
    # 启动监控
    monitor.start_monitoring()
    
    # 运行Flask应用
    app.run(host='0.0.0.0', port=5000, debug=True)
