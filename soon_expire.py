# soon_expire.py

import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

GROCERY_JSON_PATH = "/app/notion_grocery.json"

async def soon_expire(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            await update.message.reply_text("✅ 接下来 3 天内没有即将过期的食材。")
            return

        expiring_items.sort(key=lambda x: x[1])
        lines = [f"📦 {name} ➜ {date.strftime('%Y-%m-%d')}" for name, date in expiring_items]

        message = "⚠️ 以下食材将在 3 天内过期：\n" + "\n".join(lines)
        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text("❌ 无法读取过期信息，请稍后重试。")
        print(f"/soon_expire 错误: {e}")
