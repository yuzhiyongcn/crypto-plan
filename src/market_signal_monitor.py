# market_signal_monitor.py
# This script acts as a strategic radar for detecting Bitcoin market cycle shifts based on a multi-indicator model.

import requests
import pandas as pd
import pandas_ta as ta
import schedule
import time
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

# Import credentials from the config file
from config import GLASSNODE_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER, SMTP_SERVER, SMTP_PORT

# --- 1. NOTIFICATION MODULE ---
def send_telegram_message(message):
    """Sends a message to the configured Telegram chat."""
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        print("Telegram credentials not configured. Skipping message.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("Successfully sent Telegram message.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")

def send_email_alert(subject, content):
    """Sends an email alert (optional)."""
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER, SMTP_SERVER, SMTP_PORT]):
        print("Email credentials not fully configured. Skipping email alert.")
        return
        
    msg = EmailMessage()
    msg.set_content(content)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            print("Successfully sent email alert.")
    except Exception as e:
        print(f"Error sending email: {e}")

# --- 2. DATA FETCHING MODULE ---
def get_glassnode_data(url, asset='BTC', resolution='1w'):
    """Fetches data from the Glassnode API."""
    params = {'a': asset, 'i': resolution, 'api_key': GLASSNODE_API_KEY}
    try:
        res = requests.get(url, params=params, timeout=30)
        res.raise_for_status()
        df = pd.read_json(res.text, convert_dates=['t'])
        df.rename(columns={'t': 'time', 'v': 'value'}, inplace=True)
        df.set_index('time', inplace=True)
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Glassnode data from {url}: {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f"Error parsing Glassnode data from {url}: {e}")
        return None

# --- 3. INDICATOR CALCULATION & SIGNAL LOGIC ---
def check_market_signals():
    """Main function to fetch, calculate, and check for market signals."""
    print(f"\n--- Running market signal check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    # 3.1 Fetch all necessary data
    print("Fetching data from Glassnode...")
    price_df = get_glassnode_data('https://api.glassnode.com/v1/metrics/market/price_ohlc')
    mvrv_df = get_glassnode_data('https://api.glassnode.com/v1/metrics/indicators/mvrv_z_score')
    sopr_df = get_glassnode_data('https://api.glassnode.com/v1/metrics/indicators/sopr_adjusted')
    
    if price_df is None or mvrv_df is None or sopr_df is None:
        print("Failed to fetch critical data. Aborting check.")
        return

    # 3.2 Combine and prepare data
    df = price_df.copy()
    df['mvrv_z_score'] = mvrv_df['value']
    df['sopr'] = sopr_df['value']
    df = df[df.index > datetime.now() - timedelta(days=4*365)].dropna()

    # 3.3 Calculate indicators
    print("Calculating indicators...")
    df.ta.ema(length=20, append=True, col_names=('EMA_20',))
    df.ta.rsi(length=14, append=True, col_names=('RSI_14',))
    
    # Ensure we have enough data to work with
    if len(df) < 10:
        print("Not enough data for analysis. Aborting.")
        return
        
    # --- 3.4 The Dashboard Logic ---
    print("Analyzing signals...")
    
    latest = df.iloc[-1]
    prev1 = df.iloc[-2]
    prev2 = df.iloc[-3]

    # --- Bull-to-Bear Logic ---
    # Primary Condition
    bull_to_bear_primary = latest['c'] < latest['EMA_20'] and prev1['c'] < prev1['EMA_20']
    
    # Secondary Conditions
    bearish_confirmations = 0
    bearish_reasons = []

    # 1. Market Structure
    if latest['l'] < prev1['l']:
        bearish_confirmations += 1
        bearish_reasons.append("✅ Market Structure: Lower Low")
    else:
        bearish_reasons.append("❌ Market Structure: No Lower Low")

    # 2. MVRV Z-Score
    if latest['mvrv_z_score'] > 5.0 and latest['mvrv_z_score'] < prev1['mvrv_z_score']:
        bearish_confirmations += 1
        bearish_reasons.append(f"✅ MVRV Z-Score: High & Falling ({latest['mvrv_z_score']:.2f})")
    else:
        bearish_reasons.append(f"❌ MVRV Z-Score: Not High & Falling ({latest['mvrv_z_score']:.2f})")
        
    # 3. aSOPR
    if latest['sopr'] < 1.0:
        bearish_confirmations += 1
        bearish_reasons.append(f"✅ aSOPR: Below 1.0 ({latest['sopr']:.2f})")
    else:
        bearish_reasons.append(f"❌ aSOPR: Above 1.0 ({latest['sopr']:.2f})")
        
    # 4. RSI
    rsi_was_overbought = df['RSI_14'].rolling(4).max().iloc[-2] > 70
    if rsi_was_overbought and latest['RSI_14'] < prev1['RSI_14']:
        bearish_confirmations += 1
        bearish_reasons.append(f"✅ RSI: Falling from Overbought ({latest['RSI_14']:.2f})")
    else:
        bearish_reasons.append(f"❌ RSI: Not Falling from Overbought ({latest['RSI_14']:.2f})")

    # --- Bear-to-Bull Logic ---
    # Primary Condition
    bear_to_bull_primary = latest['c'] > latest['EMA_20'] and prev1['c'] > prev1['EMA_20'] and prev2['c'] > prev2['EMA_20']
    
    # Secondary Conditions
    bullish_confirmations = 0
    bullish_reasons = []
    
    # 1. Market Structure
    if latest['h'] > prev1['h']:
        bullish_confirmations += 1
        bullish_reasons.append("✅ Market Structure: Higher High")
    else:
        bullish_reasons.append("❌ Market Structure: No Higher High")

    # 2. MVRV Z-Score
    if latest['mvrv_z_score'] > 0.5 and latest['mvrv_z_score'] > prev1['mvrv_z_score']:
        bullish_confirmations += 1
        bullish_reasons.append(f"✅ MVRV Z-Score: Rising from Bottom ({latest['mvrv_z_score']:.2f})")
    else:
        bullish_reasons.append(f"❌ MVRV Z-Score: Not Rising from Bottom ({latest['mvrv_z_score']:.2f})")

    # 3. aSOPR
    if latest['sopr'] > 1.0:
        bullish_confirmations += 1
        bullish_reasons.append(f"✅ aSOPR: Above 1.0 ({latest['sopr']:.2f})")
    else:
        bullish_reasons.append(f"❌ aSOPR: Below 1.0 ({latest['sopr']:.2f})")
        
    # 4. RSI
    rsi_was_oversold = df['RSI_14'].rolling(8).min().iloc[-2] < 30
    if rsi_was_oversold and latest['RSI_14'] > prev1['RSI_14']:
        bullish_confirmations += 1
        bullish_reasons.append(f"✅ RSI: Rising from Oversold ({latest['RSI_14']:.2f})")
    else:
        bullish_reasons.append(f"❌ RSI: Not Rising from Oversold ({latest['RSI_14']:.2f})")


    # --- 3.5 Final Decision Engine ---
    alert_message = ""
    alert_subject = ""

    if bull_to_bear_primary and bearish_confirmations >= 2:
        alert_subject = "STRATEGIC ALERT: Bull-to-Bear Signal DETECTED!"
        alert_message = (
            f"🚨 **{alert_subject}** 🚨\n\n"
            f"**Date:** {latest.name.strftime('%Y-%m-%d')}\n"
            f"**BTC Price:** ${latest['c']:.2f}\n\n"
            f"**Primary Condition Met:**\n✅ Price has closed below the 20-Week EMA for 2 consecutive weeks.\n\n"
            f"**Confirmation Indicators ({bearish_confirmations}/4 Met):**\n" + "\n".join(bearish_reasons) +
            f"\n\n**Recommendation:**\nInitiate 'Strategic Contraction' phase as per the investment plan."
        )
    elif bear_to_bull_primary and bullish_confirmations >= 2:
        alert_subject = "STRATEGIC ALERT: Bear-to-Bull Signal DETECTED!"
        alert_message = (
            f"✅ **{alert_subject}** ✅\n\n"
            f"**Date:** {latest.name.strftime('%Y-%m-%d')}\n"
            f"**BTC Price:** ${latest['c']:.2f}\n\n"
            f"**Primary Condition Met:**\n✅ Price has closed above the 20-Week EMA for 3 consecutive weeks.\n\n"
            f"**Confirmation Indicators ({bullish_confirmations}/4 Met):**\n" + "\n".join(bullish_reasons) +
            f"\n\n**Recommendation:**\nInitiate 'Strategic Trend Deployment' phase as per the investment plan."
        )

    if alert_message:
        print(f"!!! {alert_subject} !!!")
        send_telegram_message(alert_message)
        send_email_alert(alert_subject, alert_message)
    else:
        print("No definitive signal detected. Market state is neutral or consolidating. All clear.")


# --- 4. SCHEDULER ---
if __name__ == "__main__":
    print("Starting the Market Signal Monitor.")
    check_market_signals()
    
    # Best practice: run on Monday morning to get the finalized weekly candle data from the previous week.
    schedule.every().monday.at("02:00").do(check_market_signals)
    
    print("Scheduler is running. Waiting for the next scheduled check...")
    while True:
        schedule.run_pending()
        time.sleep(60)
