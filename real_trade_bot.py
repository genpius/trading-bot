import asyncio
import os
import time
import requests
from datetime import datetime
from pocket_option import PocketOptionClient
from pocket_option.constants import Regions
from pocket_option.models import AuthorizationData, DealAction

# ===== TELEGRAM CONFIGURATION =====
BOT_TOKEN = "8628176399:AAHC50NsptqAEXQ-sWZ9Yx8KCVzwmJL0lzg"
CHAT_ID = "7120687986"

# ===== POCKET OPTION CONFIGURATION =====
# REPLACE THESE WITH YOUR FRESH SSID VALUES FROM COOKIE-EDITOR
CI_SESSION = "a%3A4%3A%7Bs%3A10%3A%22session_id%22%3Bs%3A32%3A%2233d40ea25c78bd300588c27d7a9a9e59%22%3Bs%3A10%3A%22ip_address%22%3Bs%3A14%3A%22141.95.102.117%22%3Bs%3A10%3A%22user_agent%22%3Bs%3A70%3A%22Mozilla%2F5.0%20%28X11%3B%20Linux%20x86_64%3B%20rv%3A151.0%29%20Gecko%2F20100101%20Firefox%2F151.0%22%3Bs%3A13%3A%22last_activity%22%3Bi%3A1780746618%3B%7Dcead7ca48d4a3b866944378eb3a8e05b"
PO_UUID = "5c6a849a-1c1f-4b15-bfa7-ee3eb4052368"
# =======================================

ASSETS = ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc", "AUDUSD_otc"]
AMOUNT = 1.0
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

last_trade_time = {}
trade_count = 0
price_history = {}

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=payload, timeout=10)
        print("✅ Telegram sent")
    except Exception as e:
        print(f"Telegram error: {e}")

def calculate_rsi(prices):
    if len(prices) < RSI_PERIOD + 1:
        return 50
    
    gains, losses = [], []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains[-RSI_PERIOD:]) / RSI_PERIOD
    avg_loss = sum(losses[-RSI_PERIOD:]) / RSI_PERIOD
    
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

async def main():
    global trade_count, price_history
    
    send_telegram("🤖 REAL TRADING BOT STARTED\nUsing RSI indicator on OTC assets")
    
    client = PocketOptionClient()
    
    @client.on.connect
    async def on_connect(data):
        print("Connected to Pocket Option")
        await client.emit.auth(AuthorizationData(
            session=CI_SESSION,
            isDemo=1,
            uid=int(PO_UUID),
            platform=2
        ))
    
    @client.on.success_auth
    async def on_success_auth(data):
        print(f"✅ Authorized successfully")
        balance = await client.get_balance()
        send_telegram(f"✅ Connected!\nDemo Balance: ${balance:.2f}")
        print(f"Balance: ${balance:.2f}")
        
        for asset in ASSETS:
            await client.emit.subscribe_to_asset(asset)
            print(f"Subscribed to {asset}")
    
    @client.on.update_close_value
    async def on_update_close_value(assets):
        current_time = time.time()
        
        for asset_data in assets:
            asset_name = str(asset_data.asset)
            price = asset_data.close
            
            if asset_name not in price_history:
                price_history[asset_name] = []
            
            price_history[asset_name].append(price)
            
            if len(price_history[asset_name]) > 50:
                price_history[asset_name] = price_history[asset_name][-50:]
            
            if len(price_history[asset_name]) >= RSI_PERIOD + 1:
                rsi = calculate_rsi(price_history[asset_name])
                current_price = price_history[asset_name][-1]
                
                if asset_name in last_trade_time:
                    if current_time - last_trade_time[asset_name] < 120:
                        continue
                
                signal = None
                if rsi <= RSI_OVERSOLD:
                    signal = "CALL 🟢"
                elif rsi >= RSI_OVERBOUGHT:
                    signal = "PUT 🔴"
                
                if signal:
                    trade_count += 1
                    action = DealAction.CALL if "CALL" in signal else DealAction.PUT
                    
                    result = await client.emit.buy(
                        amount=AMOUNT,
                        asset=asset_name,
                        action=action,
                        duration=60,
                        is_demo=1
                    )
                    
                    if result and hasattr(result, 'id'):
                        last_trade_time[asset_name] = current_time
                        message = f"""
🎯 REAL TRADE #{trade_count}

ASSET: {asset_name}
DIRECTION: {signal}
PRICE: {current_price}
RSI: {rsi}
AMOUNT: ${AMOUNT}
EXPIRY: 1 minute

✅ AUTO-TRADE EXECUTED
TIME: {datetime.now().strftime("%H:%M:%S")}
"""
                        send_telegram(message)
                        print(f"✅ Trade placed: {asset_name} {signal}")
    
    await client.connect(Regions.DEMO)
    
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
