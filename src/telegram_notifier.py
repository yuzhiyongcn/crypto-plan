"""Utility for sending Telegram notifications.

This module exposes a reusable helper function `send_telegram_message`
that other strategy scripts can import, and also provides a simple CLI
so messages can be dispatched directly from the terminal.
"""

import argparse
import logging
import os
import sys
from typing import Optional

import requests
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)


def _get_env(name: str) -> Optional[str]:
    """Fetch an environment variable and fallback to config module if present."""
    value = os.getenv(name)
    if value:
        return value

    try:
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID  # type: ignore
    except ImportError:  # pragma: no cover - optional dependency
        return None

    if name == "TELEGRAM_BOT_TOKEN":
        return TELEGRAM_BOT_TOKEN
    if name == "TELEGRAM_CHAT_ID":
        return TELEGRAM_CHAT_ID
    return None


def resolve_credentials(token: Optional[str] = None, chat_id: Optional[str] = None) -> tuple[str, str]:
    """Resolve Telegram credentials from overrides, environment, or config."""
    resolved_token = token or _get_env("TELEGRAM_BOT_TOKEN")
    resolved_chat = chat_id or _get_env("TELEGRAM_CHAT_ID")

    if not resolved_token or not resolved_chat:
        missing = []
        if not resolved_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not resolved_chat:
            missing.append("TELEGRAM_CHAT_ID")
        raise RuntimeError("Missing Telegram credentials: " + ", ".join(missing))

    return resolved_token, resolved_chat


def send_telegram_message(message: str, *, token: Optional[str] = None, chat_id: Optional[str] = None, parse_mode: str = "plain", timeout: int = 10) -> None:
    """Send a Telegram message using the configured bot credentials."""
    if not message:
        raise ValueError("Message content must not be empty.")

    resolved_token, resolved_chat = resolve_credentials(token=token, chat_id=chat_id)

    url = f"https://api.telegram.org/bot{resolved_token}/sendMessage"
    payload = {
        "chat_id": resolved_chat,
        "text": message,
        "parse_mode": parse_mode,
    }

    response = requests.post(url, json=payload, timeout=timeout)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        logger.error("Failed to send Telegram message: %s", exc, exc_info=True)
        raise


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments for the notifier."""
    parser = argparse.ArgumentParser(description="Send a Telegram alert message.")
    parser.add_argument("message", nargs="?", help="Message text to send. If omitted, reads from STDIN.")
    parser.add_argument("--token", help="Override Telegram bot token.")
    parser.add_argument("--chat-id", dest="chat_id", help="Override Telegram chat id.")
    parser.add_argument("--parse-mode", default="Markdown", help="Telegram parse mode, defaults to Markdown.")
    parser.add_argument("--timeout", type=int, default=10, help="HTTP request timeout in seconds.")
    return parser.parse_args(argv)


def message_from_args(args: argparse.Namespace) -> str:
    """Determine the message to send based on CLI arguments."""
    if args.message:
        return args.message

    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    raise ValueError("No message provided. Pass text argument or pipe content via STDIN.")


def main(argv: Optional[list[str]] = None) -> None:
    """Entry point for the CLI interface."""
    args = parse_args(argv)
    message = "测试消息"

    send_telegram_message(
        message,
        token=args.token,
        chat_id=args.chat_id,
        parse_mode=args.parse_mode,
        timeout=args.timeout,
    )

    print("Telegram message sent successfully.")


if __name__ == "__main__":
    main()

