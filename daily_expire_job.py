# daily_expire_job.py

import json
from datetime import datetime, timedelta
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID

GROCERY_JSON_PATH = "/app/notion_grocery.json"

async def send_daily_expire_reminder():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    try:
        with open(GROCERY_JSON_PATH, "r", encoding="utf-8") as f:
            groceries = json.load(f)

        today = datetime.today().date()
        soon = today + timedelta(days=3)

        expiring_items = []
        for item in groceries:
            expiry_raw = item.get("过期日期")
            if not expiry_raw:
                continue
            try:
                expiry_date = datetime.strptime(expiry_raw, "%Y-%m-%d").date()
                if today <= expiry_date <= soon:
                    expiring_items.append((item["名称"], expiry_date))
            except ValueError:
                continue

        if not expiring_items:
            return

        expiring_items.sort(key=lambda x: x[1])
        lines = [f"📦 {name} ➜ {date.strftime('%Y-%m-%d')}" for name, date in expiring_items]
        message = "⚠️ 食材提醒：以下将在 3 天内过期：\n" + "\n".join(lines)

        await bot.send_message(chat_id=TELEGRAM_USER_ID, text=message)

    except Exception as e:
        print(f"❌ 自动推送失败: {e}")
