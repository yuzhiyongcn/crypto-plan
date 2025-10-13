# market_signal_monitor_v2.py
# Enhanced Bitcoin market cycle detection with multi-indicator scoring system
# 增强版比特币市场周期检测系统，使用多指标评分机制

import sys
import os
import pandas as pd
import pandas_ta as ta
import schedule
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Import new data fetcher
from crypto_data_fetcher import CryptoDataFetcher

# Import notification and Glassnode config (optional)
try:
    from config import (
        GLASSNODE_API_KEY, 
        TELEGRAM_BOT_TOKEN, 
        TELEGRAM_CHAT_ID, 
        EMAIL_SENDER, 
        EMAIL_PASSWORD, 
        EMAIL_RECEIVER, 
        SMTP_SERVER, 
        SMTP_PORT
    )
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logging.warning("config.py not found. Notifications will be disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ============================================================================
# NOTIFICATION MODULE
# ============================================================================

def send_telegram_message(message: str) -> None:
    """Send message to Telegram"""
    if not CONFIG_AVAILABLE or not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        logging.info("Telegram not configured. Message:")
        logging.info(message)
        return
    
    import requests
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logging.info("Telegram message sent successfully")
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")


def send_email_alert(subject: str, content: str) -> None:
    """Send email alert (optional)"""
    if not CONFIG_AVAILABLE or not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
        logging.info("Email not configured. Alert:")
        logging.info(f"{subject}\n{content}")
        return
    
    import smtplib
    from email.message import EmailMessage
    
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
            logging.info("Email sent successfully")
    except Exception as e:
        logging.error(f"Error sending email: {e}")


# ============================================================================
# DATA FETCHING MODULE
# ============================================================================

def get_price_data(symbol: str = 'BTC/USDT', timeframe: str = '1w', limit: int = 200) -> Optional[pd.DataFrame]:
    """
    Fetch price data using CryptoDataFetcher
    
    Args:
        symbol: Trading pair (default: 'BTC/USDT')
        timeframe: Timeframe for klines (default: '1w' for weekly)
        limit: Number of candles to fetch
        
    Returns:
        DataFrame with OHLCV data, or None if failed
    """
    try:
        fetcher = CryptoDataFetcher(data_source='binance')
        df = fetcher.get_historical_klines(symbol, timeframe, limit)
        
        if df is None or df.empty:
            logging.error(f"Failed to fetch data for {symbol} {timeframe}")
            return None
        
        # Rename columns to match expected format
        df.rename(columns={
            'timestamp': 'time',
            'open': 'o',
            'high': 'h',
            'low': 'l',
            'close': 'c',
            'volume': 'v'
        }, inplace=True)
        
        df.set_index('time', inplace=True)
        
        logging.info(f"Successfully fetched {len(df)} candles for {symbol} {timeframe}")
        return df
        
    except Exception as e:
        logging.error(f"Error fetching price data: {e}")
        return None


def get_glassnode_data(url: str, asset: str = 'BTC', resolution: str = '1w') -> Optional[pd.DataFrame]:
    """
    Fetch data from Glassnode API (optional, requires API key)
    
    Args:
        url: Glassnode API endpoint
        asset: Asset symbol
        resolution: Data resolution
        
    Returns:
        DataFrame with Glassnode data, or None if failed/unavailable
    """
    if not CONFIG_AVAILABLE or not GLASSNODE_API_KEY or GLASSNODE_API_KEY == 'YOUR_GLASSNODE_API_KEY':
        logging.info("Glassnode API key not configured. Skipping chain data.")
        return None
    
    import requests
    params = {'a': asset, 'i': resolution, 'api_key': GLASSNODE_API_KEY}
    
    try:
        res = requests.get(url, params=params, timeout=30)
        res.raise_for_status()
        df = pd.read_json(res.text, convert_dates=['t'])
        df.rename(columns={'t': 'time', 'v': 'value'}, inplace=True)
        df.set_index('time', inplace=True)
        logging.info(f"Successfully fetched Glassnode data from {url}")
        return df
    except Exception as e:
        logging.error(f"Error fetching Glassnode data: {e}")
        return None


# ============================================================================
# TECHNICAL INDICATORS CALCULATION
# ============================================================================

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all technical indicators needed for signal detection
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with added indicator columns
    """
    logging.info("Calculating technical indicators...")
    
    # EMA (Exponential Moving Averages)
    df['EMA_20'] = ta.ema(df['c'], length=20)
    df['EMA_50'] = ta.ema(df['c'], length=50)
    df['EMA_200'] = ta.ema(df['c'], length=200)
    
    # RSI (Relative Strength Index)
    df['RSI_14'] = ta.rsi(df['c'], length=14)
    
    # MACD (Moving Average Convergence Divergence)
    macd = ta.macd(df['c'], fast=12, slow=26, signal=9)
    if macd is not None and not macd.empty:
        macd_cols = macd.columns.tolist()
        if len(macd_cols) >= 3:
            df['MACD'] = macd.iloc[:, 0]         # MACD line
            df['MACD_hist'] = macd.iloc[:, 1]    # Histogram
            df['MACD_signal'] = macd.iloc[:, 2]  # Signal line
    
    # Bollinger Bands
    bbands = ta.bbands(df['c'], length=20, std=2)
    if bbands is not None and not bbands.empty:
        # Column names may vary, try to find them
        bb_cols = bbands.columns.tolist()
        if len(bb_cols) >= 3:
            df['BB_lower'] = bbands.iloc[:, 0]   # First column is lower band
            df['BB_middle'] = bbands.iloc[:, 1]  # Second column is middle band
            df['BB_upper'] = bbands.iloc[:, 2]   # Third column is upper band
    
    # Volume indicators
    df['Volume_MA'] = df['v'].rolling(window=20).mean()
    
    # OBV (On-Balance Volume)
    df['OBV'] = ta.obv(df['c'], df['v'])
    
    # ATR (Average True Range)
    df['ATR'] = ta.atr(df['h'], df['l'], df['c'], length=14)
    
    logging.info("Technical indicators calculated successfully")
    return df


# ============================================================================
# SIGNAL SCORING SYSTEM
# ============================================================================

def calculate_bear_signal_score(df: pd.DataFrame, chain_data: Optional[Dict] = None) -> Tuple[int, Dict[str, str]]:
    """
    Calculate bear signal score (0-100)
    
    Args:
        df: DataFrame with price and indicator data
        chain_data: Optional dictionary with chain data (MVRV, aSOPR)
        
    Returns:
        Tuple of (score, reasons_dict)
    """
    score = 0
    reasons = {}
    
    latest = df.iloc[-1]
    prev1 = df.iloc[-2]
    prev2 = df.iloc[-3] if len(df) >= 3 else prev1
    
    # === PRIMARY CONDITIONS (40 points) ===
    
    # Price below 20-week EMA (20 points)
    if pd.notna(latest['EMA_20']) and latest['c'] < latest['EMA_20']:
        if pd.notna(prev1['EMA_20']) and prev1['c'] < prev1['EMA_20']:
            score += 20
            reasons['EMA_20'] = "✅ [20分] 价格连续2周低于20周EMA"
        else:
            score += 10
            reasons['EMA_20'] = "🟡 [10分] 价格低于20周EMA（仅1周）"
    else:
        reasons['EMA_20'] = "❌ [0分] 价格高于20周EMA"
    
    # Price below 50-week EMA (10 points)
    if pd.notna(latest['EMA_50']) and latest['c'] < latest['EMA_50']:
        score += 10
        reasons['EMA_50'] = "✅ [10分] 价格低于50周EMA"
    else:
        reasons['EMA_50'] = "❌ [0分] 价格高于50周EMA"
    
    # Death Cross: 50 EMA < 200 EMA (10 points)
    if pd.notna(latest['EMA_50']) and pd.notna(latest['EMA_200']):
        if latest['EMA_50'] < latest['EMA_200']:
            score += 10
            reasons['Death_Cross'] = "✅ [10分] 死亡交叉（50EMA < 200EMA）"
        else:
            reasons['Death_Cross'] = "❌ [0分] 无死亡交叉"
    
    # === PRICE ACTION CONFIRMATION (25 points) ===
    
    # Lower Low (10 points)
    if latest['l'] < prev1['l']:
        score += 10
        reasons['Lower_Low'] = f"✅ [10分] 创新低 (${latest['l']:,.0f} < ${prev1['l']:,.0f})"
    else:
        reasons['Lower_Low'] = "❌ [0分] 未创新低"
    
    # Breaking support (8 points) - using recent lows
    recent_support = df['l'].tail(20).min()
    if latest['c'] < recent_support * 0.98:  # 2% below support
        score += 8
        reasons['Support'] = f"✅ [8分] 跌破关键支撑 (${recent_support:,.0f})"
    else:
        reasons['Support'] = "❌ [0分] 未跌破关键支撑"
    
    # Bollinger Band breakdown (7 points)
    if pd.notna(latest['BB_lower']) and latest['c'] < latest['BB_lower']:
        score += 7
        reasons['BB_Breakdown'] = "✅ [7分] 跌破布林带下轨"
    else:
        reasons['BB_Breakdown'] = "❌ [0分] 未跌破布林带下轨"
    
    # === MOMENTUM CONFIRMATION (20 points) ===
    
    # RSI from overbought (8 points)
    if pd.notna(latest['RSI_14']) and pd.notna(prev1['RSI_14']):
        rsi_was_overbought = df['RSI_14'].tail(10).max() > 70
        if rsi_was_overbought and latest['RSI_14'] < prev1['RSI_14']:
            score += 8
            reasons['RSI'] = f"✅ [8分] RSI从超买回落 (当前:{latest['RSI_14']:.1f})"
        elif latest['RSI_14'] < 30:
            score += 4
            reasons['RSI'] = f"🟡 [4分] RSI超卖 ({latest['RSI_14']:.1f})"
        else:
            reasons['RSI'] = f"❌ [0分] RSI中性 ({latest['RSI_14']:.1f})"
    
    # MACD Death Cross (7 points)
    if all(pd.notna(x) for x in [latest.get('MACD'), latest.get('MACD_signal'), 
                                   prev1.get('MACD'), prev1.get('MACD_signal')]):
        if latest['MACD'] < latest['MACD_signal'] and prev1['MACD'] >= prev1['MACD_signal']:
            score += 7
            reasons['MACD'] = "✅ [7分] MACD死叉"
        elif latest['MACD'] < latest['MACD_signal']:
            score += 3
            reasons['MACD'] = "🟡 [3分] MACD负值"
        else:
            reasons['MACD'] = "❌ [0分] MACD正向"
    
    # Bearish divergence (5 points) - price higher high but RSI lower high
    if len(df) >= 10:
        recent_price_high = df['h'].tail(10).max()
        recent_rsi_high = df['RSI_14'].tail(10).max()
        if latest['h'] >= recent_price_high * 0.98 and latest['RSI_14'] < recent_rsi_high * 0.95:
            score += 5
            reasons['Divergence'] = "✅ [5分] 检测到熊背离"
        else:
            reasons['Divergence'] = "❌ [0分] 无背离"
    
    # === VOLUME CONFIRMATION (10 points) ===
    
    # Declining with volume (5 points)
    if pd.notna(latest.get('Volume_MA')) and latest['v'] > latest['Volume_MA']:
        if latest['c'] < prev1['c']:
            score += 5
            reasons['Volume'] = "✅ [5分] 下跌放量"
        else:
            reasons['Volume'] = "🟡 [2分] 成交量放大但价格未下跌"
            score += 2
    else:
        reasons['Volume'] = "❌ [0分] 下跌缩量"
    
    # OBV declining (5 points)
    if pd.notna(latest.get('OBV')) and pd.notna(prev1.get('OBV')):
        if latest['OBV'] < prev1['OBV']:
            score += 5
            reasons['OBV'] = "✅ [5分] OBV下降"
        else:
            reasons['OBV'] = "❌ [0分] OBV上升"
    
    # === CHAIN DATA CONFIRMATION (5 points, optional) ===
    if chain_data:
        # MVRV Z-Score > 5.0 and declining (3 points)
        mvrv = chain_data.get('mvrv_z_score')
        if mvrv and mvrv > 5.0:
            score += 3
            reasons['MVRV'] = f"✅ [3分] MVRV过热 ({mvrv:.2f})"
        else:
            reasons['MVRV'] = f"❌ [0分] MVRV正常 ({mvrv:.2f if mvrv else 'N/A'})"
        
        # aSOPR < 1.0 (2 points)
        sopr = chain_data.get('sopr')
        if sopr and sopr < 1.0:
            score += 2
            reasons['SOPR'] = f"✅ [2分] aSOPR<1.0 ({sopr:.3f})"
        else:
            reasons['SOPR'] = f"❌ [0分] aSOPR>=1.0 ({sopr:.3f if sopr else 'N/A'})"
    else:
        reasons['Chain_Data'] = "ℹ️ [0分] 链上数据不可用"
    
    return score, reasons


def calculate_bull_signal_score(df: pd.DataFrame, chain_data: Optional[Dict] = None) -> Tuple[int, Dict[str, str]]:
    """
    Calculate bull signal score (0-100)
    
    Args:
        df: DataFrame with price and indicator data
        chain_data: Optional dictionary with chain data
        
    Returns:
        Tuple of (score, reasons_dict)
    """
    score = 0
    reasons = {}
    
    latest = df.iloc[-1]
    prev1 = df.iloc[-2]
    prev2 = df.iloc[-3] if len(df) >= 3 else prev1
    
    # === PRIMARY CONDITIONS (40 points) ===
    
    # Price above 20-week EMA for 3 weeks (20 points)
    if all(pd.notna(x.get('EMA_20')) for x in [latest, prev1, prev2]):
        weeks_above = sum([
            latest['c'] > latest['EMA_20'],
            prev1['c'] > prev1['EMA_20'],
            prev2['c'] > prev2['EMA_20']
        ])
        if weeks_above >= 3:
            score += 20
            reasons['EMA_20'] = "✅ [20分] 价格连续3周高于20周EMA"
        elif weeks_above == 2:
            score += 12
            reasons['EMA_20'] = "🟡 [12分] 价格连续2周高于20周EMA"
        elif weeks_above == 1:
            score += 6
            reasons['EMA_20'] = "🟡 [6分] 价格高于20周EMA（仅1周）"
        else:
            reasons['EMA_20'] = "❌ [0分] 价格低于20周EMA"
    
    # Price above 50-week EMA (10 points)
    if pd.notna(latest['EMA_50']) and latest['c'] > latest['EMA_50']:
        score += 10
        reasons['EMA_50'] = "✅ [10分] 价格高于50周EMA"
    else:
        reasons['EMA_50'] = "❌ [0分] 价格低于50周EMA"
    
    # Golden Cross: 50 EMA > 200 EMA (10 points)
    if pd.notna(latest['EMA_50']) and pd.notna(latest['EMA_200']):
        if latest['EMA_50'] > latest['EMA_200']:
            score += 10
            reasons['Golden_Cross'] = "✅ [10分] 黄金交叉（50EMA > 200EMA）"
        else:
            reasons['Golden_Cross'] = "❌ [0分] 无黄金交叉"
    
    # === PRICE ACTION CONFIRMATION (25 points) ===
    
    # Higher High (10 points)
    if latest['h'] > prev1['h']:
        score += 10
        reasons['Higher_High'] = f"✅ [10分] 创新高 (${latest['h']:,.0f} > ${prev1['h']:,.0f})"
    else:
        reasons['Higher_High'] = "❌ [0分] 未创新高"
    
    # Breaking resistance (8 points)
    recent_resistance = df['h'].tail(20).max()
    if latest['c'] > recent_resistance * 1.02:  # 2% above resistance
        score += 8
        reasons['Resistance'] = f"✅ [8分] 突破关键阻力 (${recent_resistance:,.0f})"
    else:
        reasons['Resistance'] = "❌ [0分] 未突破关键阻力"
    
    # Bollinger Band breakout (7 points)
    if pd.notna(latest['BB_upper']) and latest['c'] > latest['BB_upper']:
        score += 7
        reasons['BB_Breakout'] = "✅ [7分] 突破布林带上轨"
    else:
        reasons['BB_Breakout'] = "❌ [0分] 未突破布林带上轨"
    
    # === MOMENTUM CONFIRMATION (20 points) ===
    
    # RSI from oversold (8 points)
    if pd.notna(latest['RSI_14']) and pd.notna(prev1['RSI_14']):
        rsi_was_oversold = df['RSI_14'].tail(10).min() < 30
        if rsi_was_oversold and latest['RSI_14'] > prev1['RSI_14']:
            score += 8
            reasons['RSI'] = f"✅ [8分] RSI从超卖反弹 (当前:{latest['RSI_14']:.1f})"
        elif latest['RSI_14'] > 70:
            score += 4
            reasons['RSI'] = f"🟡 [4分] RSI超买 ({latest['RSI_14']:.1f})"
        else:
            reasons['RSI'] = f"❌ [0分] RSI中性 ({latest['RSI_14']:.1f})"
    
    # MACD Golden Cross (7 points)
    if all(pd.notna(x) for x in [latest.get('MACD'), latest.get('MACD_signal'),
                                   prev1.get('MACD'), prev1.get('MACD_signal')]):
        if latest['MACD'] > latest['MACD_signal'] and prev1['MACD'] <= prev1['MACD_signal']:
            score += 7
            reasons['MACD'] = "✅ [7分] MACD金叉"
        elif latest['MACD'] > latest['MACD_signal']:
            score += 3
            reasons['MACD'] = "🟡 [3分] MACD正值"
        else:
            reasons['MACD'] = "❌ [0分] MACD负向"
    
    # Bullish divergence (5 points)
    if len(df) >= 10:
        recent_price_low = df['l'].tail(10).min()
        recent_rsi_low = df['RSI_14'].tail(10).min()
        if latest['l'] <= recent_price_low * 1.02 and latest['RSI_14'] > recent_rsi_low * 1.05:
            score += 5
            reasons['Divergence'] = "✅ [5分] 检测到牛背离"
        else:
            reasons['Divergence'] = "❌ [0分] 无背离"
    
    # === VOLUME CONFIRMATION (10 points) ===
    
    # Rising with volume (5 points)
    if pd.notna(latest.get('Volume_MA')) and latest['v'] > latest['Volume_MA']:
        if latest['c'] > prev1['c']:
            score += 5
            reasons['Volume'] = "✅ [5分] 上涨放量"
        else:
            reasons['Volume'] = "🟡 [2分] 成交量放大但价格未上涨"
            score += 2
    else:
        reasons['Volume'] = "❌ [0分] 上涨缩量"
    
    # OBV rising (5 points)
    if pd.notna(latest.get('OBV')) and pd.notna(prev1.get('OBV')):
        if latest['OBV'] > prev1['OBV']:
            score += 5
            reasons['OBV'] = "✅ [5分] OBV上升"
        else:
            reasons['OBV'] = "❌ [0分] OBV下降"
    
    # === CHAIN DATA CONFIRMATION (5 points, optional) ===
    if chain_data:
        # MVRV Z-Score rising from bottom (3 points)
        mvrv = chain_data.get('mvrv_z_score')
        if mvrv and 0.5 < mvrv < 2.0:
            score += 3
            reasons['MVRV'] = f"✅ [3分] MVRV健康区间 ({mvrv:.2f})"
        else:
            reasons['MVRV'] = f"❌ [0分] MVRV非健康区间 ({mvrv:.2f if mvrv else 'N/A'})"
        
        # aSOPR > 1.0 (2 points)
        sopr = chain_data.get('sopr')
        if sopr and sopr > 1.0:
            score += 2
            reasons['SOPR'] = f"✅ [2分] aSOPR>1.0 ({sopr:.3f})"
        else:
            reasons['SOPR'] = f"❌ [0分] aSOPR<=1.0 ({sopr:.3f if sopr else 'N/A'})"
    else:
        reasons['Chain_Data'] = "ℹ️ [0分] 链上数据不可用"
    
    return score, reasons


# ============================================================================
# MAIN SIGNAL DETECTION
# ============================================================================

def check_market_signals():
    """Main function to check market signals"""
    logging.info(f"\n{'='*80}")
    logging.info(f"运行市场信号检测 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"{'='*80}\n")
    
    # Fetch weekly price data
    df_week = get_price_data('BTC/USDT', '1w', 200)
    if df_week is None or len(df_week) < 50:
        logging.error("无法获取足够的周线数据，终止检测")
        return
    
    # Calculate indicators
    df_week = calculate_indicators(df_week)
    df_week = df_week.dropna(subset=['EMA_20'])
    
    # Optionally fetch Glassnode chain data
    chain_data = None
    if CONFIG_AVAILABLE and GLASSNODE_API_KEY and GLASSNODE_API_KEY != 'YOUR_GLASSNODE_API_KEY':
        logging.info("尝试获取链上数据...")
        mvrv_df = get_glassnode_data('https://api.glassnode.com/v1/metrics/indicators/mvrv_z_score')
        sopr_df = get_glassnode_data('https://api.glassnode.com/v1/metrics/indicators/sopr_adjusted')
        
        if mvrv_df is not None and sopr_df is not None:
            latest_mvrv = mvrv_df['value'].iloc[-1] if len(mvrv_df) > 0 else None
            latest_sopr = sopr_df['value'].iloc[-1] if len(sopr_df) > 0 else None
            chain_data = {
                'mvrv_z_score': latest_mvrv,
                'sopr': latest_sopr
            }
            logging.info(f"链上数据: MVRV={latest_mvrv:.2f if latest_mvrv else 'N/A'}, aSOPR={latest_sopr:.3f if latest_sopr else 'N/A'}")
    
    # Calculate signal scores
    bear_score, bear_reasons = calculate_bear_signal_score(df_week, chain_data)
    bull_score, bull_reasons = calculate_bull_signal_score(df_week, chain_data)
    
    # Get latest data
    latest = df_week.iloc[-1]
    
    # Print results
    print(f"\n{'='*80}")
    print(f"BTC 市场信号检测结果")
    print(f"{'='*80}")
    print(f"当前价格: ${latest['c']:,.2f}")
    print(f"检测时间: {latest.name.strftime('%Y-%m-%d')}\n")
    
    print(f"[熊] 熊市信号评分: {bear_score}/100")
    print(f"[牛] 牛市信号评分: {bull_score}/100\n")
    
    # Determine signal strength and action
    alert_message = ""
    alert_subject = ""
    priority = "low"
    
    if bear_score >= 90:
        alert_subject = "🚨 强烈看跌信号！牛转熊高度确认"
        priority = "high"
        alert_message = generate_alert_message("STRONG_BEAR", bear_score, bear_reasons, latest)
    elif bear_score >= 70:
        alert_subject = "🔴 看跌信号！牛转熊确认"
        priority = "medium"
        alert_message = generate_alert_message("BEAR", bear_score, bear_reasons, latest)
    elif bear_score >= 50:
        alert_subject = "🟡 谨慎看跌信号"
        priority = "low"
        print(f"[!] 检测到谨慎看跌信号 ({bear_score}分)，建议观察\n")
    
    if bull_score >= 90:
        alert_subject = "🎉 强烈看涨信号！熊转牛高度确认"
        priority = "high"
        alert_message = generate_alert_message("STRONG_BULL", bull_score, bull_reasons, latest)
    elif bull_score >= 70:
        alert_subject = "🟢 看涨信号！熊转牛确认"
        priority = "medium"
        alert_message = generate_alert_message("BULL", bull_score, bull_reasons, latest)
    elif bull_score >= 50 and not alert_message:
        alert_subject = "🟡 谨慎看涨信号"
        priority = "low"
        print(f"[!] 检测到谨慎看涨信号 ({bull_score}分)，建议观察\n")
    
    # Print detailed reasons
    print(f"{'='*80}")
    print(f"[熊] 熊市信号详细分析:")
    print(f"{'='*80}")
    for key, reason in bear_reasons.items():
        print(f"  {reason}")
    
    print(f"\n{'='*80}")
    print(f"[牛] 牛市信号详细分析:")
    print(f"{'='*80}")
    for key, reason in bull_reasons.items():
        print(f"  {reason}")
    print(f"{'='*80}\n")
    
    # Send alerts if significant signal
    if alert_message:
        print(f"\n{'!'*80}")
        print(f"!!! {alert_subject} !!!")
        print(f"{'!'*80}\n")
        send_telegram_message(alert_message)
        if priority == "high":
            send_email_alert(alert_subject, alert_message)
    else:
        print("[OK] 当前市场状态中性，继续观察\n")


def generate_alert_message(signal_type: str, score: int, reasons: Dict, latest_data) -> str:
    """Generate formatted alert message"""
    
    emoji_map = {
        "STRONG_BEAR": "🚨🔴",
        "BEAR": "🔴",
        "STRONG_BULL": "🎉🟢",
        "BULL": "🟢"
    }
    
    title_map = {
        "STRONG_BEAR": "强烈看跌信号 - 牛转熊高度确认",
        "BEAR": "看跌信号 - 牛转熊确认",
        "STRONG_BULL": "强烈看涨信号 - 熊转牛高度确认",
        "BULL": "看涨信号 - 熊转牛确认"
    }
    
    recommendation_map = {
        "STRONG_BEAR": "**强烈建议**: 立即开始战略性减仓，降低风险敞口50-100%",
        "BEAR": "**建议**: 分批减仓，降低风险敞口25-50%",
        "STRONG_BULL": "**强烈建议**: 积极建仓或加仓，提升风险敞口50-100%",
        "BULL": "**建议**: 分批建仓或加仓，提升风险敞口25-50%"
    }
    
    emoji = emoji_map.get(signal_type, "")
    title = title_map.get(signal_type, "市场信号")
    recommendation = recommendation_map.get(signal_type, "建议观察")
    
    message = f"""{emoji} **{title}** {emoji}

**检测时间**: {latest_data.name.strftime('%Y-%m-%d')}
**BTC 价格**: ${latest_data['c']:,.2f}
**信号评分**: {score}/100

**指标详情**:
"""
    
    for key, reason in reasons.items():
        message += f"{reason}\n"
    
    message += f"\n{recommendation}\n"
    message += f"\n_本信号由增强版市场周期检测系统自动生成_"
    
    return message


# ============================================================================
# SCHEDULER
# ============================================================================

if __name__ == "__main__":
    print("启动增强版市场信号监控系统...")
    print("数据源: Binance (免费)")
    print("链上数据: Glassnode (可选)\n")
    
    # Run immediately
    check_market_signals()
    
    # Schedule weekly checks (Monday 2 AM)
    schedule.every().monday.at("02:00").do(check_market_signals)
    
    # Optional: daily check for more frequent monitoring
    # schedule.every().day.at("09:00").do(check_market_signals)
    
    print("\n调度器已启动，等待下次检测...")
    print("下次检测时间: 每周一凌晨2点")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

