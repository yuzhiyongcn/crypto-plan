# 加密货币数据获取工具 🚀

免费获取加密货币实时价格和历史K线数据的Python工具

## ✨ 特性

- 🆓 **完全免费** - 无需API密钥即可获取公开数据
- 📊 **多数据源** - 支持Binance、CoinGecko、CCXT等多个数据源
- ⏱️ **实时价格** - 获取加密货币的实时价格信息
- 📈 **历史K线** - 支持多种时间周期的历史K线数据
- 🔄 **多周期支持** - 1分钟、5分钟、15分钟、1小时、4小时、日线、周线等
- 💾 **数据导出** - 轻松保存数据到CSV文件
- 🐍 **易于使用** - 简洁的API接口，几行代码即可开始

## 🎯 支持的数据源

| 数据源 | 优点 | 是否免费 | 需要API密钥 |
|--------|------|----------|------------|
| **Binance** | 数据质量高，延迟低 | ✅ | ❌ |
| **CoinGecko** | 提供市场数据 | ✅ | ❌ |
| **CCXT** | 支持100+交易所 | ✅ | ❌ |

## 📦 安装

### 方法1: 使用 uv (推荐 ⚡️)

[uv](https://github.com/astral-sh/uv) 是一个超快的 Python 包管理器，比 pip 快 10-100 倍！

```bash
# 一键安装所有依赖（自动创建虚拟环境）
uv sync

# 运行项目
uv run python src/crypto_data_fetcher.py
```

### 方法2: 使用传统 pip

```bash
pip install -r requirements.txt

# 或者手动安装
pip install ccxt python-binance requests pandas
```

### 验证安装

```bash
# 使用 uv
uv run python src/crypto_data_fetcher.py

# 或使用 pip
python src/crypto_data_fetcher.py
```

## 🚀 快速开始

### 获取实时价格

```python
from crypto_data_fetcher import CryptoDataFetcher

# 初始化（使用Binance数据源）
fetcher = CryptoDataFetcher(data_source='binance')

# 获取BTC实时价格
price_data = fetcher.get_realtime_price('BTC/USDT')
print(f"BTC价格: ${price_data['price']:,.2f}")
```

### 获取历史K线数据

```python
# 获取BTC最近100天的日线数据
df = fetcher.get_historical_klines(
    symbol='BTC/USDT',
    timeframe='1d',  # 日线
    limit=100
)

print(df.head())
```

### 获取多个时间周期

```python
# 同时获取多个周期的数据
timeframes = ['1h', '4h', '1d']
multi_data = fetcher.get_multiple_timeframes(
    symbol='BTC/USDT',
    timeframes=timeframes,
    limit=100
)

for tf, data in multi_data.items():
    print(f"{tf}: {len(data)} 条数据")
```

## 📖 使用示例

### 示例1: 监控多个币种价格

```python
symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']

for symbol in symbols:
    price_data = fetcher.get_realtime_price(symbol)
    print(f"{symbol}: ${price_data['price']:,.2f}")
```

**输出:**
```
BTC/USDT: $45,234.50
ETH/USDT: $3,456.78
BNB/USDT: $567.89
```

### 示例2: 分析价格趋势

```python
# 获取最近30天的数据
df = fetcher.get_historical_klines('BTC/USDT', '1d', limit=30)

# 计算统计数据
print(f"最高价: ${df['high'].max():,.2f}")
print(f"最低价: ${df['low'].min():,.2f}")
print(f"平均价: ${df['close'].mean():,.2f}")

# 计算收益率
df['returns'] = df['close'].pct_change()
print(f"平均日收益率: {df['returns'].mean()*100:.2f}%")
```

### 示例3: 保存数据到CSV

```python
# 获取数据
df = fetcher.get_historical_klines('BTC/USDT', '1h', limit=168)

# 保存到CSV
fetcher.save_to_csv(df, 'btc_hourly_data.csv')
```

## 📊 支持的时间周期

| 代码 | 说明 | 示例用途 |
|------|------|----------|
| `1m` | 1分钟 | 超短线交易 |
| `5m` | 5分钟 | 日内交易 |
| `15m` | 15分钟 | 日内交易 |
| `30m` | 30分钟 | 短线交易 |
| `1h` | 1小时 | 短线交易 |
| `4h` | 4小时 | 波段交易 |
| `1d` | 1天 | 中长线投资 |
| `1w` | 1周 | 长线投资 |

## 🔧 完整示例程序

运行示例程序查看所有功能：

```bash
python examples/fetch_crypto_example.py
```

该示例包括：
- ✅ 获取实时价格
- ✅ 获取历史K线数据
- ✅ 获取多个时间周期数据
- ✅ 保存数据到CSV
- ✅ 使用CoinGecko API

## 📚 详细文档

查看完整使用指南：[crypto_data_fetcher_guide.md](docs/crypto_data_fetcher_guide.md)

## 🔍 数据格式

### 实时价格数据

```python
{
    'symbol': 'BTC/USDT',
    'price': 45000.50,
    'timestamp': 1634567890000,
    'source': 'binance'
}
```

### 历史K线数据 (DataFrame)

| timestamp | open | high | low | close | volume |
|-----------|------|------|-----|-------|--------|
| 2024-01-01 | 42000 | 43000 | 41500 | 42500 | 1234.56 |
| 2024-01-02 | 42500 | 44000 | 42000 | 43500 | 2345.67 |

## ⚠️ 注意事项

1. **速率限制**: 所有免费API都有请求频率限制，建议在循环中添加延迟
2. **网络要求**: 需要稳定的网络连接访问API
3. **时区**: 所有时间戳默认为UTC时间
4. **数据精度**: 不同数据源的精度可能略有差异

## 💡 高级用法

### 自定义数据源

```python
import ccxt

# 使用不同的交易所
fetcher = CryptoDataFetcher(data_source='ccxt')
fetcher.ccxt_exchange = ccxt.okx()  # 切换到OKX交易所

price = fetcher.get_realtime_price('BTC/USDT')
```

### 错误处理

```python
try:
    price_data = fetcher.get_realtime_price('BTC/USDT')
    if price_data:
        print(f"价格: ${price_data['price']}")
    else:
        print("获取价格失败")
except Exception as e:
    print(f"错误: {e}")
```

### 添加重试机制

```python
import time

def fetch_with_retry(fetcher, symbol, max_retries=3):
    for i in range(max_retries):
        try:
            data = fetcher.get_realtime_price(symbol)
            if data:
                return data
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(2 ** i)  # 指数退避
                continue
            raise e
    return None
```

## 🤝 集成到现有项目

该工具可以轻松集成到你的交易机器人或分析系统中：

```python
# 在你的交易策略中使用
from crypto_data_fetcher import CryptoDataFetcher

class TradingStrategy:
    def __init__(self):
        self.fetcher = CryptoDataFetcher(data_source='binance')
    
    def check_entry_signal(self, symbol):
        # 获取最新数据
        df = self.fetcher.get_historical_klines(symbol, '1h', limit=24)
        
        # 你的策略逻辑
        if df['close'].iloc[-1] < df['close'].mean():
            return True  # 买入信号
        return False
```

## 🛠️ 故障排除

### 问题：无法安装依赖

**解决方案:**
```bash
# 尝试更新pip
python -m pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题：网络连接超时

**解决方案:**
- 检查网络连接
- 尝试使用代理
- 切换到其他数据源

### 问题：数据获取失败

**解决方案:**
- 检查交易对格式是否正确（如 'BTC/USDT'）
- 确认该交易对在数据源中存在
- 查看日志获取详细错误信息

## 📞 相关资源

- [Binance API文档](https://binance-docs.github.io/apidocs/)
- [CoinGecko API文档](https://www.coingecko.com/en/api/documentation)
- [CCXT文档](https://docs.ccxt.com/)
- [Pandas文档](https://pandas.pydata.org/docs/)

## 📝 许可证

本项目仅供学习和研究使用。使用时请遵守各数据提供商的服务条款。

## ⭐ 项目结构

```
虚拟货币投资计划/
├── src/
│   ├── crypto_data_fetcher.py    # 主工具文件
│   ├── config.py                  # 配置文件
│   ├── dip_hunter.py              # 下跌猎手策略
│   └── market_signal_monitor.py   # 市场信号监控
├── examples/
│   └── fetch_crypto_example.py    # 使用示例
├── docs/
│   ├── crypto_data_fetcher_guide.md  # 详细使用指南
│   ├── market_signal_technical_guide.md
│   └── pionex_investment_plan.md
├── requirements.txt               # 依赖列表
└── README_CRYPTO_FETCHER.md      # 本文档
```

## 🎉 开始使用

1. **克隆或下载项目**
2. **安装依赖**: `pip install -r requirements.txt`
3. **运行示例**: `python examples/fetch_crypto_example.py`
4. **查看文档**: 阅读 `docs/crypto_data_fetcher_guide.md`
5. **集成到你的项目**: 按照上述示例集成

---

**祝你投资顺利！** 📈💰

如有问题或建议，欢迎提出 Issue 或 PR。

