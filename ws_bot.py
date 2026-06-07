import websocket
import json
import requests
import time
import threading
from datetime import datetime

# ===== TELEGRAM CONFIG =====
BOT_TOKEN = "8628176399:AAHC50NsptqAEXQ-sWZ9Yx8KCVzwmJL0lzg"
CHAT_ID = "7120687986"

# ===== YOUR COOKIES FROM COOKIE-EDITOR =====
CI_SESSION = "a%3A4%3A%7Bs%3A10%3A%22session_id%22%3Bs%3A32%3A%2233d40ea25c78bd300588c27d7a9a9e59%22%3Bs%3A10%3A%22ip_address%22%3Bs%3A14%3A%22141.95.102.117%22%3Bs%3A10%3A%22user_agent%22%3Bs%3A70%3A%22Mozilla%2F5.0%20%28X11%3B%20Linux%20x86_64%3B%20rv%3A151.0%29%20Gecko%2F20100101%20Firefox%2F151.0%22%3Bs%3A13%3A%22last_activity%22%3Bi%3A1780746618%3B%7Dcead7ca48d4a3b866944378eb3a8e05b"
PO_UUID = "5c6a849a-1c1f-4b15-bfa7-ee3eb4052368"

# Build the auth message exactly as Pocket Option expects
AUTH_MSG = f'42["auth",{{"session":"{CI_SESSION}","isDemo":1,"uid":{PO_UUID},"platform":2}}]'

ASSETS = ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc"]
connected = False
authenticated = False

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except:
        pass

def on_message(ws, message):
    global authenticated
    print(f"📨 {message[:100]}")
    
    if '42["auth"' in message and '"status":true' in message:
        authenticated = True
        send_telegram("✅ Connected to Pocket Option!")
        print("✅ Authenticated!")
        
        # Subscribe to assets
        for asset in ASSETS:
            ws.send(f'42["subscribe",{{"name":"{asset}"}}]')
            print(f"Subscribed to {asset}")

def on_error(ws, error):
    print(f"❌ Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("🔌 Connection closed")
    send_telegram("⚠️ Connection lost")

def on_open(ws):
    print("🔌 WebSocket opened")
    ws.send(AUTH_MSG)
    print("📤 Auth sent")

# Try multiple endpoints
ENDPOINTS = [
    "wss://api.pocketoption.com/socket.io/?EIO=4&transport=websocket",
    "wss://ws.pocketoption.com/socket.io/?EIO=4&transport=websocket",
]

send_telegram("🤖 WebSocket Bot Starting...")

for endpoint in ENDPOINTS:
    print(f"\n🌐 Trying: {endpoint}")
    ws = websocket.WebSocketApp(endpoint,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    time.sleep(10)
    
    if authenticated:
        send_telegram("✅ Bot connected and running!")
        print("✅ Bot is running!")
        break
    else:
        print(f"❌ Failed on {endpoint}")
        ws.close()

if not authenticated:
    send_telegram("❌ Failed to connect to any endpoint")

# Keep running
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    print("Bot stopped")
