import sqlite3
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

DB_PATH = "goss_v4.db"
SERVICE_ACCOUNT_FILE = "google_service_account.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1aNXOaARvfu_08g5yjnxuQMIko6r1m5T8CW06oM365lc"

class RunwayTracksExporter:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
    
    def get_runway_tracks(self, limit=1000):
        """获取跑道轨迹数据"""
        self.cursor.execute('''
        SELECT id, hex, flight, altitude, ground_speed, latitude, longitude, heading, vertical_rate, runway, distance_to_runway, timestamp
        FROM runway_tracks
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        rows = self.cursor.fetchall()
        return rows
    
    def build_sheet_rows(self, tracks):
        """构建表格行数据"""
        rows = [[
            "序號", "航班號", "高度(呎)", "地速(節)", "緯度", "經度", 
            "航向(度)", "垂直速度", "跑道", "到跑道距離(公里)", "時間戳"
        ]]
        
        for i, track in enumerate(tracks, 1):
            id, hex_code, flight, altitude, ground_speed, latitude, longitude, heading, vertical_rate, runway, distance_to_runway, timestamp = track
            
            rows.append([
                i,
                flight if flight else hex_code,
                altitude or "",
                ground_speed or "",
                latitude or "",
                longitude or "",
                heading or "",
                vertical_rate or "",
                runway or "未知",
                distance_to_runway if distance_to_runway else "",
                timestamp
            ])
        
        return rows
    
    def get_service(self):
        """获取 Google Sheets 服务"""
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        return build("sheets", "v4", credentials=creds)
    
    def export(self):
        """导出数据到 Google Sheets"""
        print("读取跑道轨迹数据...")
        tracks = self.get_runway_tracks()
        print(f"  共 {len(tracks)} 条轨迹记录")
        
        if not tracks:
            print("  没有轨迹数据，跳过导出")
            return
        
        rows = self.build_sheet_rows(tracks)
        
        print("连接 Google Sheets...")
        service = self.get_service()
        sheet = service.spreadsheets()
        
        # 检查可用的工作表
        print("检查可用的工作表...")
        spreadsheet = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = spreadsheet.get('sheets', [])
        print(f"可用的工作表: {[s.get('properties', {}).get('title') for s in sheets]}")
        
        # 使用第一个工作表
        if sheets:
            sheet_title = sheets[0].get('properties', {}).get('title')
            print(f"使用工作表: {sheet_title}")
        else:
            sheet_title = "Sheet1"
            print(f"未找到工作表，使用默认值: {sheet_title}")
        
        # 清空工作表
        print("清空工作表...")
        sheet.values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_title}!A1:L1000"
        ).execute()
        
        # 写入数据
        print("写入数据...")
        result = sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_title}!A1",
            valueInputOption="RAW",
            body={"values": rows}
        ).execute()
        
        updated = result.get("updatedCells", 0)
        print(f"\n✅ 成功！已写入 {updated} 个单元格（{len(rows)-1} 条轨迹 + 标题列）")
        print(f"   试算表链接: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
        
        # 设置标题列样式
        try:
            sheet.batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={
                    "requests": [{
                        "repeatCell": {
                            "range": {
                                "sheetId": 1,  # 假设跑道轨迹是第二个工作表
                                "startRowIndex": 0,
                                "endRowIndex": 1
                            },
                            "cell": {
                                "userEnteredFormat": {
                                    "textFormat": {
                                        "bold": True,
                                        "foregroundColorStyle": {
                                            "rgbColor": {"red": 1.0, "green": 1.0, "blue": 1.0}
                                        }
                                    },
                                    "backgroundColorStyle": {
                                        "rgbColor": {"red": 0.27, "green": 0.51, "blue": 0.71}
                                    }
                                }
                            },
                            "fields": "userEnteredFormat(textFormat,backgroundColorStyle)"
                        }
                    }]
                }
            ).execute()
            print("   标题列样式已设置（蓝底白字粗体）")
        except Exception as e:
            print(f"   (标题样式设置失败，可忽略: {e})")
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

if __name__ == "__main__":
    exporter = RunwayTracksExporter()
    
    try:
        exporter.export()
    except HttpError as e:
        print(f"❌ Google API 错误: {e}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        raise
    finally:
        exporter.close()