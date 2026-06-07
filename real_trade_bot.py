from pocketoptionapi.stable_api import PocketOption
import asyncio
import requests
import time
import json
from datetime import datetime
from pocketoptionapi.stable_api import PocketOption

# ===== TELEGRAM CONFIGURATION =====
BOT_TOKEN = "8628176399:AAHC50NsptqAEXQ-sWZ9Yx8KCVzwmJL0lzg"
CHAT_ID = "7120687986"

# ===== POCKET OPTION CONFIGURATION =====
IS_DEMO = True  # True for demo account, False for real

# ===== TRADING SETTINGS =====
ASSETS = ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc", "AUDUSD_otc"]
AMOUNT = 1.0
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# ===== GLOBAL VARIABLES =====
api = None
last_trade_time = {}
trade_count = 0
price_history = {}

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

def main():
    global api, trade_count, price_history
    
    send_telegram("🤖 REAL TRADING BOT STARTED\nUsing RSI indicator on OTC assets")
    
    # Connect to Pocket Option (auto-login via webview will open on first run)
    print("Connecting to Pocket Option...")
    api = PocketOption("", IS_DEMO)  # Empty string triggers auto-login
    
    if not api.connect():
        send_telegram("❌ Failed to connect to Pocket Option")
        print("Connection failed")
        return
    
    # Get balance
    try:
        balance = api.get_balance()
        if balance is None or balance == 0:
            send_telegram("⚠️ Connected but balance is $0. Make sure you logged in correctly.")
            print(f"Balance returned: {balance}")
        else:
            send_telegram(f"✅ Connected!\nDemo Balance: ${balance:.2f}")
            print(f"Balance: ${balance:.2f}")
    except Exception as e:
        send_telegram(f"❌ Balance error: {e}")
        print(f"Balance error: {e}")
        return
    
    # Get all available pairs
    pairs = api.GetPairs()
    print(f"Available pairs: {len(pairs) if pairs else 0}")
    
    # Subscribe to selected assets
    for asset in ASSETS:
        status = api.ChangeSymbol(asset, 60)
        print(f"Subscribed to {asset}: {status}")
    
    print("Bot running. Scanning for signals...")
    send_telegram("🔍 Scanning OTC assets for RSI signals...")
    
    while True:
        try:
            current_time = time.time()
            
            for asset in ASSETS:
                # Check cooldown (2 minutes between trades on same asset)
                if asset in last_trade_time:
                    if current_time - last_trade_time[asset] < 120:
                        continue
                
                # Get ticks (real-time prices)
                ticks = api.GetTicks(asset)
                
                if ticks and len(ticks) >= RSI_PERIOD + 1:
                    # Store price history
                    if asset not in price_history:
                        price_history[asset] = []
                    
                    # Add latest close price
                    latest_price = float(ticks[-1]['close']) if isinstance(ticks[-1], dict) else float(ticks[-1])
                    price_history[asset].append(latest_price)
                    
                    # Keep only last 50 candles
                    if len(price_history[asset]) > 50:
                        price_history[asset] = price_history[asset][-50:]
                    
                    # Calculate RSI
                    if len(price_history[asset]) >= RSI_PERIOD + 1:
                        rsi = calculate_rsi(price_history[asset])
                        current_price = price_history[asset][-1]
                        
                        print(f"{asset} - RSI: {rsi}, Price: {current_price}")
                        
                        # Determine signal
                        signal = None
                        if rsi <= RSI_OVERSOLD:
                            signal = "call"
                            signal_display = "CALL 🟢"
                        elif rsi >= RSI_OVERBOUGHT:
                            signal = "put"
                            signal_display = "PUT 🔴"
                        
                        if signal:
                            trade_count += 1
                            
                            # Place trade
                            success, order_id = api.Buy(AMOUNT, asset, signal, 60)
                            
                            if success:
                                last_trade_time[asset] = current_time
                                message = f"""
🎯 REAL TRADE #{trade_count}

ASSET: {asset}
DIRECTION: {signal_display}
PRICE: {current_price}
RSI: {rsi}
AMOUNT: ${AMOUNT}
EXPIRY: 1 minute

✅ AUTO-TRADE EXECUTED
TIME: {datetime.now().strftime("%H:%M:%S")}
"""
                                send_telegram(message)
                                print(f"✅ Trade placed: {asset} {signal_display}")
                                
                                # Check trade result after expiry
                                time.sleep(65)
                                profit, status = api.CheckWin(order_id)
                                print(f"Trade result for {order_id}: Profit=${profit}, Status={status}")
                            else:
                                print(f"❌ Trade failed: {order_id}")
                                send_telegram(f"❌ Trade failed on {asset}: {order_id}")
                            
                            # Wait 5 seconds between trades
                            time.sleep(5)
            
            time.sleep(60)  # Main loop interval
            
        except Exception as e:
            print(f"Main loop error: {e}")
            send_telegram(f"⚠️ Bot error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
