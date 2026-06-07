import requests
import threading
import time
import random
from datetime import datetime

BOT_TOKEN = "8628176399:AAHC50NsptqAEXQ-sWZ9Yx8KCVzwmJL0lzg"
CHAT_ID = "7120687986"

PAIRS = [
    "EUR/USD",
    "GBP/CAD",
    "USD/JPY",
    "AUD/USD",
    "AUD/JPY",
    "USD/CHF",
    "NZD/USD",
    "CAD/JPY",
    "CHF/JPY",
    "SGD/JPY",
    "Crypto IDX",
    "Ethereum OTC",
    "Solana OTC",
    "PancakeSwap OTC"
]

MIN_SIGNAL_STRENGTH = 88
PAIR_SWITCH_THRESHOLD = 75
CHECK_INTERVAL = 10
SIGNAL_COOLDOWN = 120

last_signal_time = {}
current_pair = ""

def send_telegram(message):

    try:

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }

        requests.post(url, data=payload, timeout=10)

        print("Telegram alert sent")

    except Exception as e:

        print("Telegram Error:", e)

def analyze_pair(pair):

    trend = random.randint(50, 100)
    momentum = random.randint(50, 100)
    volatility = random.randint(50, 100)
    breakout = random.randint(50, 100)

    score = int(
        (trend + momentum + volatility + breakout) / 4
    )

    direction = random.choice([
        "BUY ⬆️",
        "SELL ⬇️"
    ])

    return {
        "pair": pair,
        "score": score,
        "direction": direction
    }

def send_prepare_alert(pair, score):

    global current_pair

    if current_pair == pair:
        return

    current_pair = pair

    message = f"""
⚠️ PREPARE TO SWITCH

PAIR:
{pair}

MARKET ENERGY:
{score}%

ACTION:
Open chart now

TIME:
{datetime.now().strftime("%H:%M:%S")}
"""

    send_telegram(message)

def send_entry_alert(signal):

    pair = signal["pair"]

    now = time.time()

    if pair in last_signal_time:

        if now - last_signal_time[pair] < SIGNAL_COOLDOWN:
            return

    last_signal_time[pair] = now

    expiry = random.choice([
        "1 Minute",
        "3 Minutes"
    ])

    message = f"""
🔥 ENTRY CONFIRMED

PAIR:
{pair}

SIGNAL:
{signal["direction"]}

EXPIRY:
{expiry}

CONFIDENCE:
{signal["score"]}%

ENTER NOW

TIME:
{datetime.now().strftime("%H:%M:%S")}
"""

    send_telegram(message)

def scanner():

    while True:

        try:

            results = []

            for pair in PAIRS:

                result = analyze_pair(pair)

                results.append(result)

            results.sort(
                key=lambda x: x["score"],
                reverse=True
            )

            best = results[0]

            print(
                f"BEST: {best['pair']} | SCORE: {best['score']}"
            )

            if best["score"] >= PAIR_SWITCH_THRESHOLD:

                send_prepare_alert(
                    best["pair"],
                    best["score"]
                )

            if best["score"] >= MIN_SIGNAL_STRENGTH:

                send_entry_alert(best)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:

            print("Scanner Error:", e)

            time.sleep(5)

threading.Thread(
    target=scanner,
    daemon=True
).start()

send_telegram("🟢 Binomo Signal Bot Started")

while True:

    time.sleep(60)
