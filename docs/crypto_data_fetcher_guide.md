# 加密货币数据获取工具使用指南

## 概述

`crypto_data_fetcher.py` 是一个免费的加密货币数据获取工具，支持获取实时价格和历史K线数据。

## 支持的免费数据源

### 1. Binance API (推荐)
- ✅ **完全免费**，无需API密钥
- ✅ 数据质量高，延迟低
- ✅ 支持多种时间周期
- ✅ 最高1000条K线数据
- ⚠️ 有请求频率限制

### 2. CCXT 库
- ✅ 支持100+交易所
- ✅ 统一的API接口
- ✅ 公开数据无需密钥
- ✅ 易于切换不同交易所

### 3. CoinGecko API
- ✅ 完全免费
- ✅ 提供市值、交易量等额外数据
- ⚠️ 免费层级有速率限制
- ⚠️ 免费版不提供完整OHLC数据

## 安装依赖

### 方法1: 使用 uv (推荐 ⚡️)

[uv](https://github.com/astral-sh/uv) 是新一代 Python 包管理器，比 pip 快 10-100 倍！

```bash
# 安装所有依赖（自动创建虚拟环境）
uv sync

# 添加开发依赖
uv sync --dev
```

### 方法2: 使用传统 pip

```bash
pip install ccxt python-binance requests pandas

# 或使用 requirements.txt
pip install -r requirements.txt
```

## 快速开始

### 1. 获取实时价格

```python
from crypto_data_fetcher import CryptoDataFetcher

# 使用Binance数据源
fetcher = CryptoDataFetcher(data_source='binance')

# 获取BTC实时价格
price_data = fetcher.get_realtime_price('BTC/USDT')
print(f"BTC价格: ${price_data['price']:,.2f}")
```

### 2. 获取历史K线数据

```python
# 获取最近100天的日线数据
df = fetcher.get_historical_klines(
    symbol='BTC/USDT',
    timeframe='1d',
    limit=100
)

print(df.head())
```

### 3. 获取多个时间周期

```python
# 同时获取多个周期的数据
timeframes = ['1h', '4h', '1d']
multi_data = fetcher.get_multiple_timeframes(
    symbol='BTC/USDT',
    timeframes=timeframes,
    limit=100
)

for tf, data in multi_data.items():
    print(f"时间周期: {tf}, 数据条数: {len(data)}")
```

## 支持的时间周期

| 周期代码 | 说明 | Binance | CCXT | CoinGecko |
|---------|------|---------|------|-----------|
| `1m`    | 1分钟 | ✅ | ✅ | ✅ |
| `5m`    | 5分钟 | ✅ | ✅ | ✅ |
| `15m`   | 15分钟 | ✅ | ✅ | ✅ |
| `30m`   | 30分钟 | ✅ | ✅ | ✅ |
| `1h`    | 1小时 | ✅ | ✅ | ✅ |
| `4h`    | 4小时 | ✅ | ✅ | ✅ |
| `1d`    | 1天 | ✅ | ✅ | ✅ |
| `1w`    | 1周 | ✅ | ✅ | ✅ |

## 完整示例

### 示例1: 监控多个币种的价格

```python
from crypto_data_fetcher import CryptoDataFetcher
import time

fetcher = CryptoDataFetcher(data_source='binance')

symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT']

while True:
    print("\n实时价格:")
    print("-" * 50)
    for symbol in symbols:
        price_data = fetcher.get_realtime_price(symbol)
        if price_data:
            print(f"{symbol:12} ${price_data['price']:>12,.2f}")
    
    time.sleep(10)  # 每10秒更新一次
```

### 示例2: 分析历史价格趋势

```python
from crypto_data_fetcher import CryptoDataFetcher

fetcher = CryptoDataFetcher(data_source='binance')

# 获取BTC最近90天的日线数据
df = fetcher.get_historical_klines('BTC/USDT', '1d', limit=90)

# 计算简单统计
print(f"最高价: ${df['high'].max():,.2f}")
print(f"最低价: ${df['low'].min():,.2f}")
print(f"平均价: ${df['close'].mean():,.2f}")

# 计算收益率
df['returns'] = df['close'].pct_change()
print(f"平均日收益率: {df['returns'].mean()*100:.2f}%")
print(f"波动率: {df['returns'].std()*100:.2f}%")
```

### 示例3: 保存数据到CSV

```python
from crypto_data_fetcher import CryptoDataFetcher

fetcher = CryptoDataFetcher(data_source='binance')

# 获取数据
df = fetcher.get_historical_klines('BTC/USDT', '1h', limit=168)  # 最近一周的小时数据

# 保存到CSV
fetcher.save_to_csv(df, 'btc_hourly_1week.csv')

print("数据已保存到 btc_hourly_1week.csv")
```

### 示例4: 使用CoinGecko获取市场数据

```python
from crypto_data_fetcher import CryptoDataFetcher

fetcher = CryptoDataFetcher(data_source='coingecko')

# CoinGecko提供额外的市场数据
price_data = fetcher.get_realtime_price('BTC', 'USDT')

if price_data:
    print(f"价格: ${price_data['price']:,.2f}")
    print(f"24小时涨跌: {price_data['change_24h']:.2f}%")
    print(f"24小时成交量: ${price_data['volume_24h']:,.0f}")
```

### 示例5: 切换不同的交易所

```python
from crypto_data_fetcher import CryptoDataFetcher

# 使用CCXT可以轻松切换交易所
fetcher = CryptoDataFetcher(data_source='ccxt')

# CCXT的交易所可以在初始化后更改
# 例如切换到Coinbase
import ccxt
fetcher.ccxt_exchange = ccxt.coinbase()

price_data = fetcher.get_realtime_price('BTC/USD')
print(f"Coinbase BTC价格: ${price_data['price']:,.2f}")
```

## 数据格式说明

### 实时价格数据格式

```python
{
    'symbol': 'BTC/USDT',
    'price': 45000.50,
    'bid': 44999.00,
    'ask': 45002.00,
    'high_24h': 46000.00,
    'low_24h': 44000.00,
    'volume_24h': 12345.67,
    'timestamp': 1634567890000,
    'source': 'binance'
}
```

### 历史K线数据格式 (DataFrame)

| 列名 | 说明 | 类型 |
|-----|------|------|
| `timestamp` | 时间戳 | datetime |
| `open` | 开盘价 | float |
| `high` | 最高价 | float |
| `low` | 最低价 | float |
| `close` | 收盘价 | float |
| `volume` | 成交量 | float |

## 常见问题

### Q: 如何避免请求频率限制？

A: 在循环中添加适当的延迟：

```python
import time

for symbol in symbols:
    data = fetcher.get_historical_klines(symbol, '1d', 100)
    time.sleep(0.5)  # 每次请求后等待0.5秒
```

### Q: 支持哪些交易对？

A: 
- Binance: 支持所有Binance现货交易对
- CoinGecko: 支持主流币种（BTC, ETH, BNB, SOL等）
- CCXT: 取决于选择的交易所

### Q: 如何获取更多历史数据？

A: Binance API单次最多返回1000条，如需更多数据，可以使用 `start_time` 参数分批获取：

```python
# 获取更长时间的数据
import time
from datetime import datetime, timedelta

all_data = []
end = datetime.now()
start = end - timedelta(days=365)  # 获取一年的数据

while start < end:
    df = fetcher.get_historical_klines(
        'BTC/USDT',
        '1d',
        start_time=int(start.timestamp() * 1000),
        limit=1000
    )
    all_data.append(df)
    start += timedelta(days=1000)  # 移动时间窗口
    time.sleep(1)  # 避免频率限制

import pandas as pd
full_data = pd.concat(all_data, ignore_index=True)
```

### Q: 数据的准确性如何？

A: 
- Binance API: 直接来自交易所，实时准确
- CoinGecko: 聚合多个交易所，会有轻微延迟
- 建议使用Binance作为主要数据源

## 进阶用法

### 与现有项目集成

可以将此工具集成到现有的交易策略中：

```python
from crypto_data_fetcher import CryptoDataFetcher
from dip_hunter import run_strategy

# 在策略中使用数据获取工具
fetcher = CryptoDataFetcher(data_source='binance')

def get_price_trend(symbol, timeframe='1h', limit=24):
    """获取价格趋势"""
    df = fetcher.get_historical_klines(symbol, timeframe, limit)
    if df is not None:
        # 计算趋势指标
        df['sma'] = df['close'].rolling(window=7).mean()
        df['price_change'] = df['close'].pct_change()
        return df
    return None

# 在交易策略中使用
trend_data = get_price_trend('BTC/USDT')
if trend_data is not None:
    latest_change = trend_data['price_change'].iloc[-1]
    if latest_change < -0.05:  # 价格下跌5%
        print("检测到大幅下跌，触发买入信号")
```

## 注意事项

1. **速率限制**: 所有免费API都有请求频率限制，请适当控制请求频率
2. **数据延迟**: CoinGecko等聚合服务可能有1-2分钟的数据延迟
3. **网络稳定**: 建议添加重试机制以应对网络问题
4. **时区处理**: 所有时间戳默认为UTC时间

## 运行演示

直接运行文件查看完整演示：

```bash
python src/crypto_data_fetcher.py
```

## 相关资源

- [Binance API文档](https://binance-docs.github.io/apidocs/)
- [CoinGecko API文档](https://www.coingecko.com/en/api/documentation)
- [CCXT文档](https://docs.ccxt.com/)

