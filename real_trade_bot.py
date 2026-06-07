import requests
import time
import json
from datetime import datetime
from pocketoptionapi.stable_api import PocketOption

# ===== TELEGRAM CONFIGURATION =====
BOT_TOKEN = "8628176399:AAHC50NsptqAEXQ-sWZ9Yx8KCVzwmJL0lzg"
CHAT_ID = "7120687986"

# ===== POCKET OPTION CONFIGURATION =====
# 🔻🔻🔻 REPLACE THIS WITH YOUR ACTUAL SSID 🔻🔻🔻
SSID = '42["auth",{"session":"a%3A4%3A%7Bs%3A10%3A%22session_id%22%3Bs%3A32%3A%2233d40ea25c78bd300588c27d7a9a9e59%22%3Bs%3A10%3A%22ip_address%22%3Bs%3A14%3A%22141.95.102.117%22%3Bs%3A10%3A%22user_agent%22%3Bs%3A70%3A%22Mozilla%2F5.0%20%28X11%3B%20Linux%20x86_64%3B%20rv%3A151.0%29%20Gecko%2F20100101%20Firefox%2F151.0%22%3Bs%3A13%3A%22last_activity%22%3Bi%3A1780746618%3B%7Dcead7ca48d4a3b866944378eb3a8e05b","isDemo":1,"uid":"5c6a849a-1c1f-4b15-bfa7-ee3eb4052368","platform":2}]'
# 🔺🔺🔺 REPLACE THIS WITH YOUR ACTUAL SSID 🔺🔺🔺

IS_DEMO = True

# ===== TRADING SETTINGS =====
ASSETS = ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc", "AUDUSD_otc"]
AMOUNT = 1.0
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
CHECK_INTERVAL = 60

# ===== GLOBAL VARIABLES =====
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
    
    gains = []
    losses = []
    
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
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def get_signal(asset, api):
    global price_history
    
    try:
        # Get real-time ticks
        ticks = api.GetTicks(asset)
        
        if not ticks or len(ticks) < 30:
            return None
        
        # Extract close prices
        close_prices = []
        for tick in ticks[-50:]:
            if isinstance(tick, dict):
                close_prices.append(float(tick['close']))
            else:
                close_prices.append(float(tick))
        
        if asset not in price_history:
            price_history[asset] = []
        
        price_history[asset].extend(close_prices)
        
        # Keep last 100 prices
        if len(price_history[asset]) > 100:
            price_history[asset] = price_history[asset][-100:]
        
        if len(price_history[asset]) >= RSI_PERIOD + 1:
            rsi = calculate_rsi(price_history[asset])
            current_price = price_history[asset][-1]
            
            print(f"{asset} - RSI: {rsi}, Price: {current_price}")
            
            if rsi <= RSI_OVERSOLD:
                return {"direction": "call", "display": "CALL 🟢", "rsi": rsi, "price": current_price}
            elif rsi >= RSI_OVERBOUGHT:
                return {"direction": "put", "display": "PUT 🔴", "rsi": rsi, "price": current_price}
        
        return None
        
    except Exception as e:
        print(f"Signal error for {asset}: {e}")
        return None

def place_trade(api, asset, signal, price, rsi):
    global trade_count
    
    try:
        success, order_id = api.buy(AMOUNT, asset, signal['direction'], 60)
        
        if success:
            trade_count += 1
            message = f"""
🎯 TRADE #{trade_count}

ASSET: {asset}
DIRECTION: {signal['display']}
PRICE: {price}
RSI: {rsi}
AMOUNT: ${AMOUNT}
EXPIRY: 1 minute

✅ AUTO-TRADE EXECUTED
TIME: {datetime.now().strftime('%H:%M:%S')}
"""
            send_telegram(message)
            print(f"✅ Trade placed: {asset} {signal['display']}")
            return True
        else:
            print(f"❌ Trade failed: {order_id}")
            return False
            
    except Exception as e:
        print(f"Trade error: {e}")
        return False

def main():
    global last_trade_time
    
    send_telegram("🤖 POCKET OPTION AUTO-TRADE BOT STARTED")
    
    print("Connecting to Pocket Option...")
    api = PocketOption(SSID, IS_DEMO)
    
    if not api.connect():
        send_telegram("❌ Failed to connect to Pocket Option")
        print("Connection failed")
        return
    
    balance = api.get_balance()
    if balance:
        send_telegram(f"✅ Connected!\nDemo Balance: ${balance:.2f}")
        print(f"Balance: ${balance:.2f}")
    else:
        send_telegram("⚠️ Connected but balance is None")
        print("Balance is None - SSID may be invalid")
        return
    
    # Subscribe to assets
    for asset in ASSETS:
        api.ChangeSymbol(asset, 60)
        print(f"Subscribed to {asset}")
    
    send_telegram(f"🔍 Scanning {len(ASSETS)} OTC assets for RSI signals...")
    print("Bot running. Scanning for signals...")
    
    while True:
        try:
            current_time = time.time()
            
            for asset in ASSETS:
                # Cooldown: 2 minutes between trades on same asset
                if asset in last_trade_time:
                    if current_time - last_trade_time[asset] < 120:
                        continue
                
                signal = get_signal(asset, api)
                
                if signal:
                    success = place_trade(api, asset, signal, signal['price'], signal['rsi'])
                    
                    if success:
                        last_trade_time[asset] = current_time
                    
                    # Wait 5 seconds between trades
                    time.sleep(5)
            
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print(f"Main loop error: {e}")
            send_telegram(f"⚠️ Bot error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
