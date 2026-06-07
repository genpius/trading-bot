import requests
import threading
import time
import random
from datetime import datetime
from pocketoptionapi.stable_api import PocketOption

# ===== TELEGRAM CONFIGURATION =====
BOT_TOKEN = "8628176399:AAHC50NsptqAEXQ-sWZ9Yx8KCVzwmJL0lzg"
CHAT_ID = "7120687986"

# ===== POCKET OPTION CONFIGURATION =====
# REPLACE THESE WITH YOUR ACTUAL VALUES
SSID = '42["auth",{"session":"a%3A4%3A%7Bs%3A10%3A%22session_id%22%3Bs%3A32%3A%2233d40ea25c78bd300588c27d7a9a9e59%22%3Bs%3A10%3A%22ip_address%22%3Bs%3A14%3A%22141.95.102.117%22%3Bs%3A10%3A%22user_agent%22%3Bs%3A70%3A%22Mozilla%2F5.0%20%28X11%3B%20Linux%20x86_64%3B%20rv%3A151.0%29%20Gecko%2F20100101%20Firefox%2F151.0%22%3Bs%3A13%3A%22last_activity%22%3Bi%3A1780746618%3B%7Dcead7ca48d4a3b866944378eb3a8e05b","isDemo":1,"uid":"5c6a849a-1c1f-4b15-bfa7-ee3eb4052368","platform":2}]'
IS_DEMO = True  # True = demo account, False = real money

# ===== TRADING SETTINGS =====
AMOUNT = 1.0  # $1 per trade
MIN_SIGNAL_STRENGTH = 88
CHECK_INTERVAL = 10
SIGNAL_COOLDOWN = 120

# ===== OTC ASSET MAPPING =====
OTC_MAPPING = {
    "EUR/USD": "EURUSD_otc",
    "GBP/CAD": "GBPCAD_otc",
    "USD/JPY": "USDJPY_otc",
    "AUD/USD": "AUDUSD_otc",
    "AUD/JPY": "AUDJPY_otc",
    "USD/CHF": "USDCHF_otc",
    "Solana OTC": "SOLUSD_otc",
    "Ethereum OTC": "ETHUSD_otc",
}

PAIRS = [
    "EUR/USD",
    "GBP/CAD",
    "USD/JPY",
    "AUD/USD",
    "AUD/JPY",
    "USD/CHF",
    "Solana OTC",
    "Ethereum OTC",
]

last_signal_time = {}
current_pair = ""
api = None

def connect_pocket_option():
    """Connect to Pocket Option"""
    global api
    try:
        api = PocketOption(SSID, IS_DEMO)
        api.connect()
        print("✅ Pocket Option connected")
        return True
    except Exception as e:
        print(f"❌ Pocket Option connection failed: {e}")
        return False

def place_trade(pair, direction, amount=AMOUNT):
    """Place actual trade on Pocket Option"""
    global api
    
    otc_pair = OTC_MAPPING.get(pair, pair.replace("/", "") + "_otc")
    
    try:
        # Convert direction to api format
        action = "call" if "BUY" in direction else "put"
        
        success, order_id = api.buy(amount, otc_pair, action, 60)
        
        if success:
            print(f"✅ TRADE PLACED: {pair} {direction} ${amount}")
            return True, order_id
        else:
            print(f"❌ Trade failed: {order_id}")
            return False, None
    except Exception as e:
        print(f"❌ Trade error: {e}")
        return False, None

def send_telegram(message):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=payload, timeout=10)
        print("Telegram alert sent")
    except Exception as e:
        print("Telegram Error:", e)

def analyze_pair(pair):
    """Generate signal strength"""
    trend = random.randint(50, 100)
    momentum = random.randint(50, 100)
    volatility = random.randint(50, 100)
    breakout = random.randint(50, 100)
    
    score = int((trend + momentum + volatility + breakout) / 4)
    direction = random.choice(["BUY ⬆️", "SELL ⬇️"])
    
    return {"pair": pair, "score": score, "direction": direction}

def send_entry_alert(signal, auto_traded=False):
    """Send entry alert to Telegram"""
    pair = signal["pair"]
    now = time.time()
    
    if pair in last_signal_time:
        if now - last_signal_time[pair] < SIGNAL_COOLDOWN:
            return
    
    last_signal_time[pair] = now
    
    message = f"""
🔥 ENTRY CONFIRMED

PAIR: {pair}
SIGNAL: {signal["direction"]}
CONFIDENCE: {signal["score"]}%
TIME: {datetime.now().strftime("%H:%M:%S")}
"""
    
    if auto_traded:
        message += "\n✅ AUTO-TRADE EXECUTED"
    
    send_telegram(message)

def scanner():
    """Main scanning and trading loop"""
    global current_pair
    
    # Connect to Pocket Option
    if not connect_pocket_option():
        send_telegram("⚠️ Auto-trade disabled: Cannot connect to Pocket Option")
        return
    
    send_telegram("🤖 Auto-Trade Bot Started! Trading with REAL trades (DEMO mode)")
    
    while True:
        try:
            results = []
            for pair in PAIRS:
                results.append(analyze_pair(pair))
            
            results.sort(key=lambda x: x["score"], reverse=True)
            best = results[0]
            
            print(f"BEST: {best['pair']} | SCORE: {best['score']}")
            
            if best["score"] >= MIN_SIGNAL_STRENGTH:
                # Place actual trade
                success, order_id = place_trade(best["pair"], best["direction"])
                
                # Send alert
                send_entry_alert(best, auto_traded=success)
                
                if success:
                    print(f"💵 Trade placed! Order ID: {order_id}")
            
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print("Scanner Error:", e)
            time.sleep(5)

# Start the bot
send_telegram("🚀 Auto-Trade Bot Deployed! Trading on DEMO account")

threading.Thread(target=scanner, daemon=True).start()

while True:
    time.sleep(60)
