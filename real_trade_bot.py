import requests
import time
import threading
from datetime import datetime
from pocketoptionapi.stable_api import PocketOption

# ===== TELEGRAM CONFIGURATION =====
BOT_TOKEN = "8628176399:AAHC50NsptqAEXQ-sWZ9Yx8KCVzwmJL0lzg"
CHAT_ID = "7120687986"

# ===== POCKET OPTION CONFIGURATION =====
# REPLACE THESE WITH YOUR FRESH SSID VALUES FROM COOKIE-EDITOR
CI_SESSION = "a%3A4%3A%7Bs%3A10%3A%22session_id%22%3Bs%3A32%3A%2233d40ea25c78bd300588c27d7a9a9e59%22%3Bs%3A10%3A%22ip_address%22%3Bs%3A14%3A%22141.95.102.117%22%3Bs%3A10%3A%22user_agent%22%3Bs%3A70%3A%22Mozilla%2F5.0%20%28X11%3B%20Linux%20x86_64%3B%20rv%3A151.0%29%20Gecko%2F20100101%20Firefox%2F151.0%22%3Bs%3A13%3A%22last_activity%22%3Bi%3A1780746618%3B%7Dcead7ca48d4a3b866944378eb3a8e05b"
PO_UUID = "5c6a849a-1c1f-4b15-bfa7-ee3eb4052368"
# =======================================

# Build the SSID in the correct format
SSID = f'42["auth",{{"session":"{CI_SESSION}","isDemo":1,"uid":"{PO_UUID}","platform":2}}]'
IS_DEMO = True

# ===== TRADING SETTINGS =====
ASSETS = ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc", "AUDUSD_otc"]
AMOUNT = 1.0
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
CHECK_INTERVAL = 60

# ===== GLOBAL VARIABLES =====
api = None
last_trade_time = {}
trade_count = 0

def send_telegram(message):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=payload, timeout=10)
        print("✅ Telegram sent")
    except Exception as e:
        print(f"Telegram error: {e}")

def calculate_rsi(prices):
    """Calculate RSI from price list"""
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

def get_signal(asset):
    """Get real trading signal from market data"""
    global api
    
    try:
        # CORRECTED: Get real candles from Pocket Option
        # The method is GetCandles, not get_candles
        # Parameters: (active, period) not asset=
        candles = api.GetCandles(asset, 60)
        
        if not candles or len(candles) < 30:
            print(f"Not enough candles for {asset}: {len(candles) if candles else 0}")
            return None
        
        # Extract close prices
        close_prices = []
        for candle in candles:
            close_prices.append(float(candle['close']))
        
        # Calculate RSI
        rsi = calculate_rsi(close_prices)
        current_price = close_prices[-1]
        
        print(f"{asset} - RSI: {rsi}, Price: {current_price}")
        
        # Determine signal
        if rsi <= RSI_OVERSOLD:
            return {"direction": "CALL 🟢", "rsi": rsi, "price": current_price}
        elif rsi >= RSI_OVERBOUGHT:
            return {"direction": "PUT 🔴", "rsi": rsi, "price": current_price}
        else:
            return None
            
    except Exception as e:
        print(f"Signal error for {asset}: {e}")
        return None

def place_trade(asset, direction, price, rsi):
    """Place actual trade on Pocket Option"""
    global api, trade_count
    
    action = "call" if "CALL" in direction else "put"
    
    try:
        success, order_id = api.buy(AMOUNT, asset, action, 60)
        
        if success:
            trade_count += 1
            message = f"""
🎯 REAL TRADE #{trade_count}

ASSET: {asset}
DIRECTION: {direction}
PRICE: {price}
RSI: {rsi}
AMOUNT: ${AMOUNT}
EXPIRY: 1 minute

✅ AUTO-TRADE EXECUTED
TIME: {datetime.now().strftime("%H:%M:%S")}
"""
            send_telegram(message)
            print(f"✅ Trade placed: {asset} {direction}")
            return True
        else:
            print(f"❌ Trade failed: {order_id}")
            send_telegram(f"❌ Trade failed on {asset}: {order_id}")
            return False
            
    except Exception as e:
        print(f"Trade error: {e}")
        return False

def main():
    global api
    
    send_telegram("🤖 REAL TRADING BOT STARTED\nUsing RSI indicator on OTC assets")
    
    # Connect to Pocket Option
    print("Connecting to Pocket Option...")
    api = PocketOption(SSID, IS_DEMO)
    
    if not api.connect():
        send_telegram("❌ Failed to connect to Pocket Option")
        print("Connection failed")
        return
    
    # Get balance with error handling
    try:
        balance = api.get_balance()
        if balance is None or balance == 0:
            send_telegram("⚠️ Connected but balance is $0. Check if your SSID is correct and account has funds.")
            print(f"Balance returned: {balance}")
        else:
            send_telegram(f"✅ Connected!\nDemo Balance: ${balance:.2f}")
            print(f"Balance: ${balance:.2f}")
    except Exception as e:
        send_telegram(f"❌ Balance error: {e}")
        print(f"Balance error: {e}")
        return
    
    print("Bot running. Scanning for signals every 60 seconds...")
    send_telegram("🔍 Scanning OTC assets for RSI signals...")
    
    while True:
        try:
            current_time = time.time()
            
            for asset in ASSETS:
                # Check cooldown (2 minutes between trades on same asset)
                if asset in last_trade_time:
                    if current_time - last_trade_time[asset] < 120:
                        continue
                
                # Get real signal
                signal = get_signal(asset)
                
                if signal:
                    print(f"{datetime.now().strftime('%H:%M:%S')} - {asset} RSI: {signal['rsi']} -> {signal['direction']}")
                    
                    # Place trade
                    success = place_trade(asset, signal['direction'], signal['price'], signal['rsi'])
                    
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
