import sqlite3
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

DB_PATH = "goss_v4.db"

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a sample spreadsheet.
# 请替换为您实际的Google Sheets ID
SAMPLE_SPREADSHEET_ID = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSCuBrrJGhiA5xudlHKt2XXZJtp6MsUg1IJlpflqe5dHT3LTxwU6EmzSUghZwy6kmJ_e_J-63pveWjR/pub?output=csv"
SAMPLE_RANGE_NAME = "Sheet1!A1:J1"

def get_credentials():
    """获取Google API凭证"""
    creds = None
    
    # 检查credentials.json是否存在且格式正确
    if not os.path.exists("credentials.json"):
        print("错误: credentials.json 文件不存在")
        print("请从 Google Cloud Console 创建并下载正确的 Google API 客户端密钥文件")
        return None
    
    # 检查文件格式
    try:
        with open("credentials.json", "r") as f:
            import json
            client_config = json.load(f)
            if "installed" not in client_config and "web" not in client_config:
                print("错误: credentials.json 格式不正确")
                print("当前文件是 OpenSky API 凭证，不是 Google API 凭证")
                print("请从 Google Cloud Console 创建并下载正确的 Google API 客户端密钥文件")
                return None
    except Exception as e:
        print(f"读取 credentials.json 时出错: {e}")
        return None
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def get_trajectory_data():
    """从数据库获取轨迹数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT flight_no, timestamp, latitude, longitude, altitude, 
               ground_speed, heading, vertical_rate, runway, landing_time
        FROM flight_trajectory
        WHERE is_landing = 1
        ORDER BY timestamp DESC
        LIMIT 100
    ''')
    
    data = cursor.fetchall()
    conn.close()
    return data

def export_to_gsheets():
    """导出数据到Google Sheets"""
    # 检查Google Sheets ID格式
    import re
    spreadsheet_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', SAMPLE_SPREADSHEET_ID)
    if spreadsheet_id_match:
        spreadsheet_id = spreadsheet_id_match.group(1)
    else:
        # 如果不是URL格式，直接使用
        spreadsheet_id = SAMPLE_SPREADSHEET_ID
    
    # 获取凭证
    creds = get_credentials()
    if not creds:
        print("无法获取Google API凭证，导出失败")
        return
    
    try:
        service = build("sheets", "v4", credentials=creds)
        
        # 获取数据
        data = get_trajectory_data()
        
        if not data:
            print("没有轨迹数据可导出")
            return
        
        # 准备数据
        values = [
            ["航班号", "时间戳", "纬度", "经度", "高度(英尺)", "地速", "航向", "垂直速率", "降落跑道", "降落时间"]
        ]
        
        for row in data:
            flight_no, timestamp, latitude, longitude, altitude, ground_speed, heading, vertical_rate, runway, landing_time = row
            values.append([
                flight_no,
                timestamp,
                latitude,
                longitude,
                altitude,
                ground_speed if ground_speed else "",
                heading if heading else "",
                vertical_rate if vertical_rate else "",
                runway if runway else "未知",
                landing_time if landing_time else ""
            ])
        
        # 写入数据
        body = {
            "values": values
        }
        
        # 先清空现有数据
        clear_range = "Sheet1!A1:J1000"
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=clear_range
        ).execute()
        
        # 写入新数据
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=SAMPLE_RANGE_NAME,
            valueInputOption="RAW",
            body=body
        ).execute()
        
        print(f"成功导出 {result.get('updatedCells', 0)} 个单元格的数据到Google Sheets")
        
    except HttpError as err:
        print(f"导出到Google Sheets时出错: {err}")
    except Exception as e:
        print(f"导出过程中出错: {e}")

if __name__ == "__main__":
    export_to_gsheets()