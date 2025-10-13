# 快速开始指南 🚀

## 安装 (一行命令)

### 🚀 推荐：使用 uv (超快！)

```bash
uv sync
```

### 或使用传统 pip

```bash
pip install ccxt python-binance requests pandas
```

## 使用示例 (复制即用)

### 1️⃣ 获取实时价格

```python
# 使用 uv: 在项目根目录运行
# uv run python -c "from src.crypto_data_fetcher import CryptoDataFetcher; ..."

from crypto_data_fetcher import CryptoDataFetcher

fetcher = CryptoDataFetcher(data_source='binance')
price = fetcher.get_realtime_price('BTC/USDT')
print(f"BTC: ${price['price']:,.2f}")
```

### 2️⃣ 获取历史K线

```python
# 获取最近100天日线
df = fetcher.get_historical_klines('BTC/USDT', '1d', limit=100)
print(df.head())
```

### 3️⃣ 多个时间周期

```python
# 同时获取1小时、4小时、日线数据
data = fetcher.get_multiple_timeframes('BTC/USDT', ['1h', '4h', '1d'], limit=50)
```

### 4️⃣ 保存到CSV

```python
df = fetcher.get_historical_klines('BTC/USDT', '1h', limit=168)
fetcher.save_to_csv(df, 'btc_data.csv')
```

## 支持的时间周期

`1m` `5m` `15m` `30m` `1h` `4h` `1d` `1w`

## 测试运行

### 使用 uv (推荐)

```bash
# 运行完整演示
uv run python src/crypto_data_fetcher.py

# 运行示例程序
uv run python examples/fetch_crypto_example.py
```

### 使用传统方式

```bash
# 运行完整演示
python src/crypto_data_fetcher.py

# 运行示例程序
python examples/fetch_crypto_example.py
```

## 主要特点

✅ 完全免费 - 无需API密钥  
✅ 实时数据 - 延迟极低  
✅ 多数据源 - Binance/CoinGecko/CCXT  
✅ 易于使用 - 几行代码搞定  
✅ 数据导出 - 支持CSV格式  

## 常用币种

| 代码 | 名称 | 交易对 |
|------|------|--------|
| BTC | 比特币 | BTC/USDT |
| ETH | 以太坊 | ETH/USDT |
| BNB | 币安币 | BNB/USDT |
| SOL | Solana | SOL/USDT |
| XRP | 瑞波币 | XRP/USDT |

## 完整文档

📖 详细文档: `docs/crypto_data_fetcher_guide.md`  
📘 完整说明: `README_CRYPTO_FETCHER.md`

---

**就这么简单！开始你的加密货币数据分析之旅吧！** 🎉

