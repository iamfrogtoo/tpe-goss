import json
from datetime import datetime, timedelta, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SERVICE_ACCOUNT_FILE = "google_service_account.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1aNXOaARvfu_08g5yjnxuQMIko6r1m5T8CW06oM365lc"
DATA_FILE = "yesterday_arrivals.json"

def get_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)

def load_flights():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def format_tw_time(utc_str):
    """UTC 時間字串轉台灣時間"""
    if not utc_str:
        return ""
    try:
        dt = datetime.fromisoformat(utc_str.replace("Z", "+00:00"))
        tw = dt.astimezone(timezone(timedelta(hours=8)))
        return tw.strftime("%Y-%m-%d %H:%M")
    except:
        return utc_str

def build_rows(flights):
    rows = [[
        "序號", "航班號(IATA)", "航班號(ICAO)", "起飛機場(IATA)", "起飛機場名稱",
        "實際落地(台灣時間)", "預定落地(台灣時間)", "機型", "機尾號", "航空公司"
    ]]
    for i, f in enumerate(flights, 1):
        ident_iata  = f.get("ident_iata", "")
        ident_icao  = f.get("ident", "")
        origin      = f.get("origin") or {}
        origin_iata = origin.get("code_iata", "")
        origin_name = origin.get("name", "")

        actual_on   = format_tw_time(f.get("actual_on") or f.get("actual_in", ""))
        sched_on    = format_tw_time(f.get("scheduled_on") or f.get("scheduled_in", ""))
        actype      = f.get("aircraft_type", "")
        reg         = f.get("registration", "")

        # 從 ICAO 航班號推航空公司（前3碼）
        airline_icao = ident_icao[:3] if len(ident_icao) >= 3 else ""

        rows.append([
            i, ident_iata, ident_icao, origin_iata, origin_name,
            actual_on, sched_on, actype, reg, airline_icao
        ])
    return rows

def export():
    print("讀取昨日航班資料...")
    flights = load_flights()
    print(f"  共 {len(flights)} 筆航班")

    rows = build_rows(flights)

    print("連接 Google Sheets...")
    service = get_service()
    sheet = service.spreadsheets()

    # 先清空 A1:J300
    print("清空試算表...")
    sheet.values().clear(
        spreadsheetId=SPREADSHEET_ID,
        range="工作表1!A1:J300"
    ).execute()

    # 寫入資料
    print("寫入資料...")
    result = sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range="工作表1!A1",
        valueInputOption="RAW",
        body={"values": rows}
    ).execute()

    updated = result.get("updatedCells", 0)
    print(f"\n✅ 成功！已寫入 {updated} 個儲存格（{len(rows)-1} 筆航班 + 標題列）")
    print(f"   試算表連結: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")

    # 設定標題列粗體
    try:
        sheet.batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={
                "requests": [{
                    "repeatCell": {
                        "range": {
                            "sheetId": 0,
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
        print("   標題列樣式已設定（藍底白字粗體）")
    except Exception as e:
        print(f"   (標題樣式設定失敗，可忽略: {e})")

if __name__ == "__main__":
    try:
        export()
    except HttpError as e:
        print(f"❌ Google API 錯誤: {e}")
    except FileNotFoundError as e:
        print(f"❌ 找不到檔案: {e}")
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        raise
