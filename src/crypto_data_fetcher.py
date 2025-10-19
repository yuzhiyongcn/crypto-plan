"""
加密货币数据获取工具
免费获取加密货币实时价格和历史K线数据的工具

支持多个免费数据源：
- Binance API (公开数据无需API密钥)
- CoinGecko API (免费层级有速率限制)
- CCXT 库 (统一的多交易所接口)

使用方法:
    from crypto_data_fetcher import CryptoDataFetcher
    
    fetcher = CryptoDataFetcher()
    
    # 获取实时价格
    price = fetcher.get_realtime_price("BTC/USDT")
    
    # 获取历史K线数据
    klines = fetcher.get_historical_klines("BTC/USDT", "1d", limit=100)
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

# 第三方库（安装命令：pip install ccxt requests python-binance 或 uv add ccxt python-binance requests）
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    print("警告：ccxt 未安装。安装命令：pip install ccxt 或 uv add ccxt")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("警告：requests 未安装。安装命令：pip install requests 或 uv add requests")

try:
    from binance.client import Client as BinanceClient
    BINANCE_AVAILABLE = True
except ImportError:
    BINANCE_AVAILABLE = False
    print("警告：python-binance 未安装。安装命令：pip install python-binance 或 uv add python-binance")

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class CryptoDataFetcher:
    """
    从多个免费数据源获取加密货币数据的主类
    """
    
    # 支持的时间周期映射
    TIMEFRAME_MAP = {
        '1m': {'binance': '1m', 'ccxt': '1m', 'coingecko': 'minutely'},
        '5m': {'binance': '5m', 'ccxt': '5m', 'coingecko': 'minutely'},
        '15m': {'binance': '15m', 'ccxt': '15m', 'coingecko': 'minutely'},
        '30m': {'binance': '30m', 'ccxt': '30m', 'coingecko': 'minutely'},
        '1h': {'binance': '1h', 'ccxt': '1h', 'coingecko': 'hourly'},
        '4h': {'binance': '4h', 'ccxt': '4h', 'coingecko': 'hourly'},
        '1d': {'binance': '1d', 'ccxt': '1d', 'coingecko': 'daily'},
        '1w': {'binance': '1w', 'ccxt': '1w', 'coingecko': 'daily'},
    }
    
    def __init__(self, data_source: str = 'binance'):
        """
        初始化数据获取器
        
        参数:
            data_source: 数据源选择 ('binance', 'coingecko', 或 'ccxt')
        """
        self.data_source = data_source
        self.binance_client = None
        self.ccxt_exchange = None
        
        # 根据可用的库初始化客户端
        if data_source == 'binance' and BINANCE_AVAILABLE:
            self.binance_client = BinanceClient()
            logging.info("已初始化 Binance 客户端")
        elif data_source == 'ccxt' and CCXT_AVAILABLE:
            self.ccxt_exchange = ccxt.binance()
            logging.info("已初始化 CCXT Binance 交易所")
        elif data_source == 'coingecko' and REQUESTS_AVAILABLE:
            logging.info("使用 CoinGecko API")
        else:
            logging.warning(f"数据源 '{data_source}' 不可用。请检查依赖。")
    
    def get_realtime_price(self, symbol: str, vs_currency: str = 'USDT') -> Optional[Dict[str, Any]]:
        """
        获取加密货币的实时价格
        
        参数:
            symbol: 交易对符号 (例如: 'BTC/USDT', 'ETH/USDT')
            vs_currency: 计价货币 (默认: 'USDT')
            
        返回:
            包含价格信息的字典，失败则返回 None。返回的数据结构因数据源而异：
            - Binance: {'symbol', 'price', 'timestamp', 'source'}
            - CCXT: {'symbol', 'price', 'bid', 'ask', 'high_24h', 'low_24h', 'volume_24h', 'timestamp', 'source'}
            - CoinGecko: {'symbol', 'price', 'change_24h', 'volume_24h', 'last_updated', 'source'}
        """
        try:
            if self.data_source == 'binance' and self.binance_client:
                return self._get_price_binance(symbol)
            elif self.data_source == 'ccxt' and self.ccxt_exchange:
                return self._get_price_ccxt(symbol)
            elif self.data_source == 'coingecko':
                return self._get_price_coingecko(symbol.split('/')[0], vs_currency.lower())
            else:
                logging.error("没有可用的数据源")
                return None
        except Exception as e:
            logging.error(f"获取实时价格时出错: {e}")
            return None
    
    def _get_price_binance(self, symbol: str) -> Optional[Dict[str, Any]]:
        """从 Binance API 获取价格"""
        symbol_formatted = symbol.replace('/', '')
        ticker = self.binance_client.get_symbol_ticker(symbol=symbol_formatted)
        
        if ticker:
            return {
                'symbol': symbol,
                'price': float(ticker['price']),
                'timestamp': int(time.time() * 1000),
                'source': 'binance'
            }
        return None
    
    def _get_price_ccxt(self, symbol: str) -> Optional[Dict[str, Any]]:
        """从 CCXT 获取价格"""
        ticker = self.ccxt_exchange.fetch_ticker(symbol)
        
        if ticker:
            return {
                'symbol': symbol,
                'price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'high_24h': ticker['high'],
                'low_24h': ticker['low'],
                'volume_24h': ticker['baseVolume'],
                'timestamp': ticker['timestamp'],
                'source': 'ccxt'
            }
        return None
    
    def _get_price_coingecko(self, coin_id: str, vs_currency: str = 'usd') -> Optional[Dict[str, Any]]:
        """从 CoinGecko API 获取价格"""
        # 将常见符号映射到 CoinGecko ID
        coin_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'ADA': 'cardano',
            'XRP': 'ripple',
            'DOT': 'polkadot',
            'DOGE': 'dogecoin',
            'AVAX': 'avalanche-2',
            'MATIC': 'matic-network',
        }
        
        coin_id_mapped = coin_map.get(coin_id.upper(), coin_id.lower())
        
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coin_id_mapped,
            'vs_currencies': vs_currency,
            'include_24hr_change': 'true',
            'include_24hr_vol': 'true',
            'include_last_updated_at': 'true'
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if coin_id_mapped in data:
            coin_data = data[coin_id_mapped]
            return {
                'symbol': f"{coin_id}/{vs_currency.upper()}",
                'price': coin_data[vs_currency],
                'change_24h': coin_data.get(f'{vs_currency}_24h_change', 0),
                'volume_24h': coin_data.get(f'{vs_currency}_24h_vol', 0),
                'last_updated': coin_data.get('last_updated_at', 0),
                'source': 'coingecko'
            }
        return None
    
    def get_historical_klines(
        self, 
        symbol: str, 
        timeframe: str = '1d', 
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> Optional[pd.DataFrame]:
        """
        获取历史K线/蜡烛图数据
        
        参数:
            symbol: 交易对符号 (例如: 'BTC/USDT')
            timeframe: K线时间周期 ('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w')
            limit: 获取K线数量 (默认: 100, 最大: 1000)
            start_time: 开始时间戳（毫秒）（可选）
            end_time: 结束时间戳（毫秒）（可选）
            
        返回:
            包含K线数据的 pandas.DataFrame，失败则返回 None。
            DataFrame 包含以下列:
            - timestamp (datetime): K线开盘时间
            - open (float): 开盘价
            - high (float): 最高价
            - low (float): 最低价
            - close (float): 收盘价
            - volume (float): 成交量
        """
        try:
            if self.data_source == 'binance' and self.binance_client:
                return self._get_klines_binance(symbol, timeframe, limit, start_time, end_time)
            elif self.data_source == 'ccxt' and self.ccxt_exchange:
                return self._get_klines_ccxt(symbol, timeframe, limit, start_time)
            elif self.data_source == 'coingecko':
                return self._get_klines_coingecko(symbol.split('/')[0], limit)
            else:
                logging.error("没有可用的数据源")
                return None
        except Exception as e:
            logging.error(f"获取历史K线数据时出错: {e}")
            return None
    
    def _get_klines_binance(
        self, 
        symbol: str, 
        timeframe: str, 
        limit: int,
        start_time: Optional[int],
        end_time: Optional[int]
    ) -> pd.DataFrame:
        """从 Binance API 获取K线数据"""
        symbol_formatted = symbol.replace('/', '')
        interval = self.TIMEFRAME_MAP[timeframe]['binance']
        
        # 构建参数
        kwargs = {
            'symbol': symbol_formatted,
            'interval': interval,
            'limit': min(limit, 1000)  # Binance 最大限制是 1000
        }
        
        if start_time:
            kwargs['start_str'] = str(start_time)
        if end_time:
            kwargs['end_str'] = str(end_time)
        
        klines = self.binance_client.get_klines(**kwargs)
        
        # 转换为 DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        # 只保留必要的列并转换类型
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        
        return df
    
    def _get_klines_ccxt(
        self, 
        symbol: str, 
        timeframe: str, 
        limit: int,
        start_time: Optional[int]
    ) -> pd.DataFrame:
        """从 CCXT 获取K线数据"""
        timeframe_ccxt = self.TIMEFRAME_MAP[timeframe]['ccxt']
        
        # 获取 OHLCV 数据
        ohlcv = self.ccxt_exchange.fetch_ohlcv(
            symbol, 
            timeframe_ccxt, 
            since=start_time,
            limit=limit
        )
        
        # 转换为 DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df
    
    def _get_klines_coingecko(self, coin_id: str, days: int) -> pd.DataFrame:
        """从 CoinGecko API 获取历史数据"""
        # 将常见符号映射到 CoinGecko ID
        coin_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'ADA': 'cardano',
            'XRP': 'ripple',
            'DOT': 'polkadot',
            'DOGE': 'dogecoin',
            'AVAX': 'avalanche-2',
            'MATIC': 'matic-network',
        }
        
        coin_id_mapped = coin_map.get(coin_id.upper(), coin_id.lower())
        
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id_mapped}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily' if days > 90 else 'hourly'
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'prices' in data:
            df = pd.DataFrame(data['prices'], columns=['timestamp', 'close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # CoinGecko 的免费层级不提供 OHLC 数据，只有收盘价
            df['open'] = df['close']
            df['high'] = df['close']
            df['low'] = df['close']
            df['volume'] = 0  # 简单端点中不可用
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        return pd.DataFrame()
    
    def get_multiple_timeframes(
        self, 
        symbol: str, 
        timeframes: List[str], 
        limit: int = 100
    ) -> Dict[str, pd.DataFrame]:
        """
        一次性获取多个时间周期的历史K线数据
        
        参数:
            symbol: 交易对符号
            timeframes: 要获取的时间周期列表
            limit: 每个时间周期的K线数量
            
        返回:
            一个字典，键是时间周期 (str)，值是包含K线数据的 pandas.DataFrame。
            每个 DataFrame 的结构与 get_historical_klines 返回的相同。
        """
        results = {}
        
        for tf in timeframes:
            logging.info(f"正在获取 {symbol} 的 {tf} 周期数据...")
            df = self.get_historical_klines(symbol, tf, limit)
            if df is not None and not df.empty:
                results[tf] = df
                time.sleep(0.1)  # 小延迟以避免速率限制
            else:
                logging.warning(f"获取 {tf} 周期数据失败")
        
        return results
    
    def save_to_csv(self, df: pd.DataFrame, filename: str) -> None:
        """
        将 DataFrame 保存到 CSV 文件
        
        参数:
            df: 要保存的 DataFrame
            filename: 输出文件名
        """
        df.to_csv(filename, index=False)
        logging.info(f"数据已保存到 {filename}")
    
    def print_summary(self, df: pd.DataFrame) -> None:
        """
        打印K线数据的摘要信息
        
        参数:
            df: 包含K线数据的 DataFrame
        """
        if df is None or df.empty:
            print("没有数据可显示")
            return
        
        print("\n" + "="*80)
        print(f"数据摘要")
        print("="*80)
        print(f"总记录数: {len(df)}")
        print(f"时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
        print(f"\n前 5 条记录:")
        print(df.head())
        print(f"\n后 5 条记录:")
        print(df.tail())
        print(f"\n价格统计:")
        print(df[['open', 'high', 'low', 'close', 'volume']].describe())
        print("="*80 + "\n")


def demo_usage():
    """
    演示如何使用 CryptoDataFetcher
    """
    print("加密货币数据获取工具 - 演示\n")
    
    # 示例 1: 使用 Binance 获取实时价格
    print("=" * 80)
    print("示例 1: 获取实时价格")
    print("=" * 80)
    
    fetcher = CryptoDataFetcher(data_source='binance')
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    for symbol in symbols:
        price_data = fetcher.get_realtime_price(symbol)
        if price_data:
            print(f"{symbol}: ${price_data['price']:,.2f}")
    
    # 示例 2: 获取历史K线数据
    print("\n" + "=" * 80)
    print("示例 2: 获取历史K线数据 (日线, 最近30天)")
    print("=" * 80)
    
    df = fetcher.get_historical_klines('BTC/USDT', timeframe='1d', limit=30)
    if df is not None:
        fetcher.print_summary(df)
        # 可选：保存到 CSV
        # fetcher.save_to_csv(df, 'btc_daily_30days.csv')
    
    # 示例 3: 获取多个时间周期
    print("\n" + "=" * 80)
    print("示例 3: 获取多个时间周期")
    print("=" * 80)
    
    timeframes = ['1h', '4h', '1d']
    multi_data = fetcher.get_multiple_timeframes('BTC/USDT', timeframes, limit=20)
    
    for tf, data in multi_data.items():
        print(f"\n时间周期: {tf}")
        print(f"记录数: {len(data)}")
        print(f"最新价格: ${data['close'].iloc[-1]:,.2f}")
        print(f"价格区间: ${data['low'].min():,.2f} - ${data['high'].max():,.2f}")
    
    # 示例 4: 使用 CoinGecko
    print("\n" + "=" * 80)
    print("示例 4: 使用 CoinGecko API")
    print("=" * 80)
    
    cg_fetcher = CryptoDataFetcher(data_source='coingecko')
    price_data = cg_fetcher.get_realtime_price('BTC', 'usd')  # CoinGecko 使用小写 'usd'
    if price_data:
        print(f"BTC 价格: ${price_data['price']:,.2f}")
        print(f"24小时涨跌: {price_data['change_24h']:.2f}%")
        print(f"24小时成交量: ${price_data['volume_24h']:,.0f}")


if __name__ == "__main__":
    demo_usage()
