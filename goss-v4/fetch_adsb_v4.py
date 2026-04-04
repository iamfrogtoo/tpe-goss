import requests
import sqlite3

# 這是範例，如果你有 RapidAPI Key 或官方 Key 請替換
API_KEY = "YOUR_API_KEY"
URL = "https://adsbexchange-com1.p.rapidapi.com/v2/lat/25.079/lon/121.234/dist/200/"

def fetch_adsbx():
    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "adsbexchange-com1.p.rapidapi.com"
    }
    # 邏輯：抓取 TPE 方圓 200km 的所有飛機
    # 寫入 goss_v4.db 的 aircraft_live 表
    pass