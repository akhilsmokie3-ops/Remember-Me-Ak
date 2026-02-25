#!/usr/bin/env python3
"""
Remember-Me Telegram Bot Entry Point
=====================================
Launches the Kernel with desktop layer and connects to Telegram.
"""

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Remember-Me AI — Telegram Bot")
    parser.add_argument("--model", type=str, default="tiny", help="Model to load")
    parser.add_argument("--token", type=str, default=None, help="Telegram bot token (or set REMEMBER_ME_TELEGRAM_TOKEN)")
    args = parser.parse_args()

    # Import after argparse so --help works without deps
    from remember_me.kernel import Kernel
    from remember_me.desktop.telegram_bot import TelegramAdapter

    kernel = Kernel(model_key=args.model, enable_desktop=True)

    token = args.token or os.environ.get("REMEMBER_ME_TELEGRAM_TOKEN")
    if not token:
        print("ERROR: Telegram token required. Use --token or set REMEMBER_ME_TELEGRAM_TOKEN")
        sys.exit(1)

    bot = TelegramAdapter(kernel, token=token)

    try:
        bot.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        kernel.shutdown()


if __name__ == "__main__":
    main()
