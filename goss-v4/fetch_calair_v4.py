import imaplib
import email
import sqlite3
import re
from email.header import decode_header
from datetime import datetime

class ChinaAirlinesEmailFetcher:
    def __init__(self, email_address, password, imap_server='imap.gmail.com'):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.conn = None
        self.cursor = None
    
    def connect_db(self):
        """连接到 SQLite 数据库"""
        self.conn = sqlite3.connect('goss_v4.db')
        self.cursor = self.conn.cursor()
    
    def disconnect_db(self):
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
    
    def connect_email(self):
        """连接到邮件服务器"""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.email_address, self.password)
            self.mail.select('inbox')
            print("✅ 成功连接到邮件服务器")
            return True
        except Exception as e:
            print(f"❌ 连接邮件服务器失败: {e}")
            return False
    
    def fetch_emails(self, search_criteria='(FROM "china-airlines" SUBJECT "flight")'):
        """抓取邮件"""
        try:
            status, messages = self.mail.search(None, search_criteria)
            message_ids = messages[0].split()
            print(f"找到 {len(message_ids)} 封华航邮件")
            
            for msg_id in message_ids:
                status, msg_data = self.mail.fetch(msg_id, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        self.process_email(msg)
            
            return True
        except Exception as e:
            print(f"❌ 抓取邮件失败: {e}")
            return False
    
    def process_email(self, msg):
        """处理邮件内容"""
        subject, encoding = decode_header(msg['Subject'])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or 'utf-8')
        
        print(f"处理邮件: {subject}")
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain' or content_type == 'text/html':
                    body = part.get_payload(decode=True).decode()
                    self.parse_email_body(body)
        else:
            content_type = msg.get_content_type()
            if content_type == 'text/plain' or content_type == 'text/html':
                body = msg.get_payload(decode=True).decode()
                self.parse_email_body(body)
    
    def parse_email_body(self, body):
        """解析邮件正文，提取航班信息"""
        # 这里需要根据实际的华航邮件格式进行调整
        # 以下是示例正则表达式，实际使用时需要根据邮件格式修改
        
        # 提取航班号
        flight_no_pattern = r'([A-Z]{2}\d{3,4})'
        flight_no_matches = re.findall(flight_no_pattern, body)
        
        # 提取日期
        date_pattern = r'(\d{4}/\d{2}/\d{2}|\d{2}/\d{2}/\d{4})'
        date_matches = re.findall(date_pattern, body)
        
        # 提取时间
        time_pattern = r'(\d{2}:\d{2})'
        time_matches = re.findall(time_pattern, body)
        
        # 提取出发地和目的地
        airport_pattern = r'([A-Z]{3})\s*->\s*([A-Z]{3})'
        airport_matches = re.findall(airport_pattern, body)
        
        # 提取机型
        aircraft_pattern = r'([A-Z]\d{3})'
        aircraft_matches = re.findall(aircraft_pattern, body)
        
        # 提取登机门
        gate_pattern = r'Gate\s*([A-Z]\d+|\d+)'
        gate_matches = re.findall(gate_pattern, body)
        
        # 提取状态
        status_pattern = r'Status:\s*(\w+)'
        status_matches = re.findall(status_pattern, body)
        
        # 提取备注
        remarks_pattern = r'Remarks:\s*(.*?)\n'
        remarks_matches = re.findall(remarks_pattern, body, re.DOTALL)
        
        # 处理提取的数据
        if flight_no_matches:
            flight_no = flight_no_matches[0]
            flight_date = date_matches[0] if date_matches else ''
            departure_time = time_matches[0] if len(time_matches) > 0 else ''
            arrival_time = time_matches[1] if len(time_matches) > 1 else ''
            origin = airport_matches[0][0] if airport_matches else ''
            destination = airport_matches[0][1] if airport_matches else ''
            aircraft_type = aircraft_matches[0] if aircraft_matches else ''
            gate = gate_matches[0] if gate_matches else ''
            status = status_matches[0] if status_matches else ''
            remarks = remarks_matches[0] if remarks_matches else ''
            
            self.save_flight_data(flight_no, flight_date, departure_time, arrival_time, 
                               origin, destination, aircraft_type, gate, status, remarks)
    
    def save_flight_data(self, flight_no, flight_date, departure_time, arrival_time, 
                       origin, destination, aircraft_type, gate, status, remarks):
        """将航班数据保存到数据库"""
        try:
            # 检查航班是否已存在
            self.cursor.execute('''
                SELECT id FROM source_calair 
                WHERE flight_no = ? AND flight_date = ?
            ''', (flight_no, flight_date))
            
            if self.cursor.fetchone():
                # 更新现有记录
                self.cursor.execute('''
                    UPDATE source_calair 
                    SET departure_time = ?, arrival_time = ?, origin = ?, 
                        destination = ?, aircraft_type = ?, gate = ?, 
                        status = ?, remarks = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE flight_no = ? AND flight_date = ?
                ''', (departure_time, arrival_time, origin, destination, 
                      aircraft_type, gate, status, remarks, flight_no, flight_date))
                print(f"✅ 更新航班: {flight_no} {flight_date}")
            else:
                # 插入新记录
                self.cursor.execute('''
                    INSERT INTO source_calair 
                    (flight_no, flight_date, departure_time, arrival_time, 
                     origin, destination, aircraft_type, gate, status, remarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (flight_no, flight_date, departure_time, arrival_time, 
                      origin, destination, aircraft_type, gate, status, remarks))
                print(f"✅ 新增航班: {flight_no} {flight_date}")
            
            self.conn.commit()
        except Exception as e:
            print(f"❌ 保存数据失败: {e}")
            self.conn.rollback()
    
    def run(self):
        """运行抓取过程"""
        print("🚀 启动华航邮件抓取...")
        
        # 连接数据库
        self.connect_db()
        
        # 连接邮件服务器
        if self.connect_email():
            # 抓取邮件
            self.fetch_emails()
            
            # 断开邮件连接
            self.mail.logout()
        
        # 断开数据库连接
        self.disconnect_db()
        
        print("✅ 华航邮件抓取完成！")

if __name__ == "__main__":
    # 这里需要填写实际的邮箱地址和密码
    # 注意：在生产环境中，应该使用环境变量或配置文件来存储敏感信息
    email_address = 'your_email@example.com'
    password = 'your_email_password'
    
    fetcher = ChinaAirlinesEmailFetcher(email_address, password)
    fetcher.run()
