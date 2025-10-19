# Telegram 通知工具使用指南

## 工具简介

`src/telegram_notifier.py` 提供发送 Telegram 消息的独立工具，可在命令行直接调用，也能在策略脚本中导入 `send_telegram_message` 函数，实现交易信号的实时推送。

## 环境准备

- Python >= 3.9
- 已安装依赖：`requests`、`python-dotenv`
- Telegram 机器人（通过 BotFather 创建）

如果尚未安装依赖，可执行：

```bash
pip install requests python-dotenv
```

## 配置凭证

1. 在项目根目录创建 `.env` 文件。
2. 写入以下内容，将占位符替换为实际凭证：

```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

> 若项目已存在 `src/config.py` 并包含同名常量，工具也会回退读取该文件的配置。

## 命令行快速使用

发送固定文本：

```bash
python src/telegram_notifier.py "BTC bullish signal detected"
```

通过管道发送动态内容：

```bash
echo "Buy signal triggered at $65k" | python src/telegram_notifier.py
```

可选参数：

- `--token`：临时覆盖 `.env` 中的机器人 token。
- `--chat-id`：临时覆盖默认 chat id。
- `--parse-mode`：Telegram 消息解析模式（默认 `Markdown`）。
- `--timeout`：HTTP 请求超时秒数（默认 10）。

示例（自定义解析模式）：

```bash
python src/telegram_notifier.py "<b>BTC alert</b>" --parse-mode HTML
```

## 作为模块导入

```python
from telegram_notifier import send_telegram_message

send_telegram_message("BTC buy signal at $65k")
```

如需在代码内覆盖凭证：

```python
from telegram_notifier import send_telegram_message

send_telegram_message(
    "Strategy alert: position opened",
    token="my_custom_token",
    chat_id="12345678",
)
```

## 集成到策略脚本

以下示例展示如何在检测到买入信号时发送提醒：

```python
from telegram_notifier import send_telegram_message

def handle_signal(price: float) -> None:
    send_telegram_message(f"BTC buy signal triggered at ${price:,.2f}")

# 在策略主循环中调用 handle_signal
```

## 常见问题

### 消息发送失败怎么办？

- 确认 `.env` 中 token 和 chat id 是否正确。
- 检查机器人是否已加入目标群组并拥有发送权限。
- 保证网络可访问 `https://api.telegram.org`。

### 如何获取 chat id？

1. 与机器人对话发送任意消息。
2. 在浏览器打开 `https://api.telegram.org/bot<你的token>/getUpdates`。
3. 在返回的 JSON 中查找 `chat` 字段的 `id`。

### 能否禁用 Markdown？

可以通过 `--parse-mode plain` 或在函数调用时传入 `parse_mode="MarkdownV2"`、`"HTML"` 或 `None` 来控制格式。

