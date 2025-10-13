"""
Simple example script for using the CryptoDataFetcher
演示如何使用加密货币数据获取工具
"""

import sys
import os

# Add parent directory to path to import the module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from crypto_data_fetcher import CryptoDataFetcher


def example_realtime_price():
    """Example: Get real-time cryptocurrency prices"""
    print("\n" + "="*80)
    print("示例 1: 获取实时价格")
    print("="*80)
    
    fetcher = CryptoDataFetcher(data_source='binance')
    
    # Get prices for multiple cryptocurrencies
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT']
    
    print(f"\n{'交易对':<15} {'价格 (USDT)':<20}")
    print("-" * 40)
    
    for symbol in symbols:
        try:
            price_data = fetcher.get_realtime_price(symbol)
            if price_data:
                print(f"{symbol:<15} ${price_data['price']:>15,.2f}")
        except Exception as e:
            print(f"{symbol:<15} Error: {e}")


def example_historical_klines():
    """Example: Get historical kline data"""
    print("\n" + "="*80)
    print("示例 2: 获取历史K线数据 (BTC最近30天日线)")
    print("="*80)
    
    fetcher = CryptoDataFetcher(data_source='binance')
    
    # Get 30 days of daily klines for BTC
    df = fetcher.get_historical_klines(
        symbol='BTC/USDT',
        timeframe='1d',
        limit=30
    )
    
    if df is not None and not df.empty:
        print(f"\n成功获取 {len(df)} 条数据")
        print(f"时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
        print(f"\n最近5条数据:")
        print(df.tail())
        
        # Calculate some statistics
        print(f"\n价格统计:")
        print(f"最高价: ${df['high'].max():,.2f}")
        print(f"最低价: ${df['low'].min():,.2f}")
        print(f"平均价: ${df['close'].mean():,.2f}")
        print(f"当前价: ${df['close'].iloc[-1]:,.2f}")
        
        # Calculate price change
        price_change = ((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
        print(f"30天涨跌幅: {price_change:+.2f}%")
    else:
        print("获取数据失败")


def example_multiple_timeframes():
    """Example: Get data for multiple timeframes"""
    print("\n" + "="*80)
    print("示例 3: 获取多个时间周期的数据")
    print("="*80)
    
    fetcher = CryptoDataFetcher(data_source='binance')
    
    timeframes = ['1h', '4h', '1d']
    
    print(f"\n获取 ETH/USDT 的多个时间周期数据...")
    
    multi_data = fetcher.get_multiple_timeframes(
        symbol='ETH/USDT',
        timeframes=timeframes,
        limit=20
    )
    
    print(f"\n{'时间周期':<10} {'数据条数':<12} {'最新价格':<15} {'价格区间'}")
    print("-" * 70)
    
    for tf, data in multi_data.items():
        latest_price = data['close'].iloc[-1]
        min_price = data['low'].min()
        max_price = data['high'].max()
        
        print(f"{tf:<10} {len(data):<12} ${latest_price:>10,.2f}    "
              f"${min_price:,.2f} - ${max_price:,.2f}")


def example_save_to_csv():
    """Example: Save data to CSV file"""
    print("\n" + "="*80)
    print("示例 4: 保存数据到CSV文件")
    print("="*80)
    
    fetcher = CryptoDataFetcher(data_source='binance')
    
    # Get hourly data for the last 7 days
    print("\n正在获取 BTC/USDT 最近7天的小时数据...")
    df = fetcher.get_historical_klines(
        symbol='BTC/USDT',
        timeframe='1h',
        limit=168  # 7 days * 24 hours
    )
    
    if df is not None and not df.empty:
        filename = 'btc_hourly_7days.csv'
        fetcher.save_to_csv(df, filename)
        print(f"成功保存 {len(df)} 条数据到 {filename}")
    else:
        print("获取数据失败")


def example_coingecko():
    """Example: Using CoinGecko API"""
    print("\n" + "="*80)
    print("示例 5: 使用 CoinGecko API 获取数据")
    print("="*80)
    
    try:
        fetcher = CryptoDataFetcher(data_source='coingecko')
        
        coins = ['BTC', 'ETH', 'BNB', 'SOL']
        
        print(f"\n{'币种':<10} {'价格 (USD)':<15} {'24h涨跌':<12} {'24h成交量'}")
        print("-" * 70)
        
        for coin in coins:
            try:
                price_data = fetcher.get_realtime_price(coin, 'USD')
                if price_data:
                    print(f"{coin:<10} ${price_data['price']:>11,.2f}  "
                          f"{price_data['change_24h']:>+8.2f}%  "
                          f"${price_data['volume_24h']:>15,.0f}")
            except Exception as e:
                print(f"{coin:<10} Error: {e}")
    except Exception as e:
        print(f"CoinGecko API 示例失败: {e}")
        print("提示: CoinGecko 不需要安装额外库，只需要 requests 库")


def main():
    """Run all examples"""
    print("\n")
    print("#" * 80)
    print("#" + " " * 20 + "加密货币数据获取工具 - 示例演示" + " " * 21 + "#")
    print("#" * 80)
    
    try:
        # Run all examples
        example_realtime_price()
        example_historical_klines()
        example_multiple_timeframes()
        example_save_to_csv()
        example_coingecko()
        
        print("\n" + "="*80)
        print("所有示例运行完成!")
        print("="*80)
        print("\n提示:")
        print("- 使用前请确保已安装依赖: pip install -r requirements.txt")
        print("- 更多用法请参考: docs/crypto_data_fetcher_guide.md")
        print("- 如遇到网络问题，可以尝试使用代理或切换数据源")
        print("\n")
        
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n\n运行示例时出错: {e}")
        print("请确保已安装所需依赖: pip install ccxt python-binance requests pandas")


if __name__ == "__main__":
    main()

