import ccxt
import pandas as pd
import pandas_ta as ta
import telebot
import time
import threading
import os
from flask import Flask
from datetime import datetime

TOKEN = "8721237317:AAGzlu2c0q_pdJOazMhJ_tg_NcY_HfmtSNs"
CHAT_ID = "204224497"   # ←←← ОБЯЗАТЕЛЬНО ВСТАВЬ СВОЙ chat_id

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

monitored = ["FARTCOIN-USD", "ETH-USD", "KAS-USD", "SOL-USD", "MNT-USD", "BTC-USD"]

exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'future'}})

@app.route('/')
def home():
    return "Bot is running 24/7 ✅"

def get_ohlcv(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol.replace("-USD", "/USDT"), "1h", limit=300)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def add_indicators(df):
    df = df.copy()
    df['rsi'] = ta.rsi(df['close'], 14)
    bb = ta.bbands(df['close'], 20, 2)
    df['bb_lower'] = bb['BBL_20_2.0']
    df['bb_upper'] = bb['BBU_20_2.0']
    stoch = ta.stoch(df['high'], df['low'], df['close'], 14, 3, 3)
    df['stoch_k'] = stoch.iloc[:, 0]
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], 14)
    df['vol_ma'] = ta.sma(df['volume'], 20)
    return df

def signal_loop():
    while True:
        for symbol in monitored:
            try:
                df = add_indicators(get_ohlcv(symbol))
                close = df['close'].iloc[-1]
                rsi = df['rsi'].iloc[-1]
                stoch_k = df['stoch_k'].iloc[-1]
                stoch_prev = df['stoch_k'].iloc[-2]
                bb_lower = df['bb_lower'].iloc[-1]
                bb_upper = df['bb_upper'].iloc[-1]
                volume_ratio = df['volume'].iloc[-1] / df['vol_ma'].iloc[-1]
                atr = df['atr'].iloc[-1]

                # LONG
                if rsi < 33 and stoch_k > 20 and stoch_prev <= 20 and close <= bb_lower * 1.015 and volume_ratio >= 1.0:
                    sl = round(close - 1.5 * atr, 4)
                    tp1 = round(close + 2.5 * atr, 4)
                    tp2 = round(close + 5 * atr, 4)
                    bot.send_message(CHAT_ID, f"""
🚀 **LONG по {symbol}**
Вход от: {round(close,4)}$
Стоп: {sl}$
TP1: {tp1}$
TP2: {tp2}$
                    """)

                # SHORT
                elif rsi > 67 and stoch_k < 80 and stoch_prev >= 80 and close >= bb_upper * 0.985 and volume_ratio >= 1.0:
                    sl = round(close + 1.5 * atr, 4)
                    tp1 = round(close - 2.5 * atr, 4)
                    tp2 = round(close - 5 * atr, 4)
                    bot.send_message(CHAT_ID, f"""
🔻 **SHORT по {symbol}**
Вход от: {round(close,4)}$
Стоп: {sl}$
TP1: {tp1}$
TP2: {tp2}$
                    """)
            except:
                pass
        time.sleep(300)

threading.Thread(target=signal_loop, daemon=True).start()

bot.send_message(CHAT_ID, "✅ Бот запущен 24/7\nСледит за 6 монетами\nПиши add KASUSDT чтобы добавить новую")

port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)
