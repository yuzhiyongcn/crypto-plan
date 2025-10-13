"""
自动化“下跌猎手”策略
Pionex Automated Dip Hunter Strategy.

本脚本实现了投资计划中定义的“下跌猎手”策略。
它监控BTC和ETH的价格，在大幅下跌时买入，并设置止盈订单。
"""
import os
import time
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 假设已安装pionex-python-sdk
# pip install pionex-python-sdk
from pionex import Pionex

# --- 配置日志 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 策略核心参数 ---
# 您可以在这里调整策略的行为
# 交易对和触发条件
TARGETS = {
    "BTC_USDT": {"dip_percentage": -10.0}, # BTC 24小时跌幅超过10%触发
    "ETH_USDT": {"dip_percentage": -12.0}, # ETH 24小时跌幅超过12%触发
}
BUY_AMOUNT_USDT = 2500.0  # 每次买入的金额 (USDT)
TAKE_PROFIT_PERCENTAGE = 1.15 # 止盈点 (+15%)
COOLDOWN_PERIOD_SECONDS = 24 * 60 * 60  # 冷却时间 (24小时)
LOOP_SLEEP_SECONDS = 5 * 60 # 循环间隔 (5分钟)


def get_pionex_client() -> Optional[Pionex]:
    """
    初始化并返回Pionex API客户端。

    通过环境变量加载API密钥。为了安全，请不要将密钥直接写入代码。
    请设置环境变量:
    - PIONEX_API_KEY
    - PIONEX_API_SECRET

    返回:
        一个配置好的Pionex客户端对象，如果密钥不存在则返回None。
    """
    # 从.env文件加载环境变量
    load_dotenv()
    
    api_key = os.getenv("PIONEX_API_KEY")
    api_secret = os.getenv("PIONEX_API_SECRET")

    if not api_key or not api_secret or api_key == "YOUR_PIONEX_API_KEY_HERE":
        logging.error("错误：请确保在.env文件中正确配置了PIONEX_API_KEY和PIONEX_API_SECRET。")
        return None
    
    logging.info("正在初始化Pionex客户端...")
    return Pionex(api_key, api_secret)


def get_market_data(client: Pionex, symbol: str) -> Optional[Dict[str, Any]]:
    """
    获取指定交易对的最新24小时行情数据。

    Args:
        client: Pionex客户端对象。
        symbol: 交易对 (例如, 'BTC_USDT')。

    Returns:
        包含行情数据的字典，例如24小时变动百分比。失败则返回None。
    """
    try:
        tickers = client.market.tickers(symbols=[symbol])
        # SDK返回的数据结构可能需要适配
        if tickers and 'tickers' in tickers and tickers['tickers']:
            return tickers['tickers'][0]
        return None
    except Exception as e:
        logging.error(f"获取 {symbol} 行情数据时出错: {e}")
        return None


def place_buy_order(client: Pionex, symbol: str, amount_usdt: float) -> Optional[Dict[str, Any]]:
    """
    下一个现货市价买单。

    Args:
        client: Pionex客户端对象。
        symbol: 要购买的交易对。
        amount_usdt: 花费的USDT金额。

    Returns:
        包含订单确认详情的字典。失败则返回None。
    """
    try:
        logging.info(f"准备为 {symbol} 下一个市价买单，金额约 {amount_usdt} USDT...")
        order_response = client.trade.place_order(
            symbol=symbol,
            side='BUY',
            order_type='MARKET',
            quote_order_quantity=str(amount_usdt) # 市价单使用购买金额
        )
        logging.info(f"成功下达买单: {order_response}")
        return order_response
    except Exception as e:
        logging.error(f"为 {symbol} 下买单时出错: {e}")
        return None

def place_sell_order(client: Pionex, symbol: str, quantity: str, price: str) -> Optional[Dict[str, Any]]:
    """
    下一个现货限价卖单 (用于止盈)。

    Args:
        client: Pionex客户端对象。
        symbol: 要卖出的交易对。
        quantity: 要卖出的资产数量。
        price: 卖出价格。

    Returns:
        包含订单确认详情的字典。失败则返回None。
    """
    try:
        logging.info(f"准备为 {symbol} 下一个限价卖单，数量 {quantity}，价格 {price}...")
        order_response = client.trade.place_order(
            symbol=symbol,
            side='SELL',
            order_type='LIMIT',
            quantity=quantity,
            price=price
        )
        logging.info(f"成功下达卖单: {order_response}")
        return order_response
    except Exception as e:
        logging.error(f"为 {symbol} 下卖单时出错: {e}")
        return None


def run_strategy() -> None:
    """
    运行“下跌猎手”策略循环的主函数。
    """
    logging.info("启动“下跌猎手”策略...")
    client = get_pionex_client()
    if not client:
        logging.critical("客户端初始化失败，策略退出。")
        return

    # 用于跟踪每个币种的上次购买时间，以实现冷却机制
    last_buy_times: Dict[str, float] = {}

    while True:
        logging.info("开始新一轮策略检查...")
        for symbol, params in TARGETS.items():
            dip_percentage_trigger = params['dip_percentage']

            # 1. 检查冷却时间
            current_time = time.time()
            if symbol in last_buy_times and current_time - last_buy_times[symbol] < COOLDOWN_PERIOD_SECONDS:
                logging.info(f"{symbol} 处于冷却期，跳过。")
                continue

            # 2. 获取行情数据
            market_data = get_market_data(client, symbol)
            if not market_data:
                continue
            
            # 派网API返回的涨跌幅是'change24h'字段，且是字符串形式，例如 "0.05" 代表 +5%
            change_24h_str = market_data.get('change24h', "0.0")
            try:
                change_24h = float(change_24h_str) * 100
            except ValueError:
                logging.warning(f"无法解析 {symbol} 的24小时变动数据: '{change_24h_str}'")
                continue

            logging.info(f"{symbol} 当前24小时变动: {change_24h:.2f}% (触发条件: < {dip_percentage_trigger}%)")

            # 3. 检查是否满足触发条件
            if change_24h < dip_percentage_trigger:
                logging.warning(f"!!! 触发 {symbol} 的买入条件 !!!")
                
                # 4. 执行买入
                buy_order = place_buy_order(client, symbol, BUY_AMOUNT_USDT)
                
                if buy_order and buy_order.get('orderId'):
                    # 5. 买入成功后，下止盈单
                    # 我们需要获取买入的实际成交数量和均价来计算卖出参数
                    # 为简化草稿，我们假设立即成交并能获取信息
                    # 注意：真实的成交可能需要轮询订单状态
                    time.sleep(2) # 等待订单成交
                    try:
                        order_details = client.trade.get_order(symbol=symbol, order_id=buy_order['orderId'])
                        filled_quantity = order_details.get('executedQuantity')
                        avg_price_str = order_details.get('avgPrice')

                        if filled_quantity and avg_price_str:
                            avg_price = float(avg_price_str)
                            take_profit_price = avg_price * TAKE_PROFIT_PERCENTAGE
                            
                            # 格式化以满足API精度要求 (需要查询具体交易对的精度规则)
                            # 此处为草稿简化
                            price_str = f"{take_profit_price:.2f}" 

                            place_sell_order(client, symbol, filled_quantity, price_str)

                            # 6. 更新购买时间戳
                            last_buy_times[symbol] = current_time
                        else:
                            logging.error(f"无法获取买单 {buy_order['orderId']} 的成交详情。")

                    except Exception as e:
                        logging.error(f"处理买单后续操作时出错: {e}")

                else:
                    logging.error(f"为 {symbol} 下买单失败或未返回订单ID。")

        logging.info(f"本轮检查结束，休眠 {LOOP_SLEEP_SECONDS / 60} 分钟...")
        time.sleep(LOOP_SLEEP_SECONDS)


if __name__ == "__main__":
    run_strategy()
