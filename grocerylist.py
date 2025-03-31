# grocerylist.py

import json
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from config import NOTION_API_KEY, NOTION_DATABASE_ID_GROCERY

GROCERY_JSON_PATH = "/app/notion_grocery.json"
NOTION_API_URL = "https://api.notion.com/v1/pages/"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# 缓存选择项
selected_items_by_chat = {}

# 显示当前未使用食材
async def grocerylist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(GROCERY_JSON_PATH, "r", encoding="utf-8") as f:
            groceries = json.load(f)

        if not groceries:
            await update.message.reply_text("🍽️ 当前没有未使用的食材。")
            return

        chat_id = update.effective_chat.id
        selected_items_by_chat[chat_id] = set()

        keyboard = []
        for item in groceries:
            name = item["名称"]
            keyboard.append([
                InlineKeyboardButton(f"⬜ {name}", callback_data=f"toggle::{name}")
            ])

        keyboard.append([
            InlineKeyboardButton("✅ 更新库存到 Notion", callback_data="confirm_update")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🧺 当前未使用的食材：点击选择后确认更新：", reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text("❌ 获取食材列表失败。")
        print(f"/grocerylist 错误: {e}")

# 回调处理
async def mark_used_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat.id

    if data.startswith("toggle::"):
        name = data.split("::")[1]
        selected = selected_items_by_chat.setdefault(chat_id, set())
        if name in selected:
            selected.remove(name)
        else:
            selected.add(name)

        # 重建键盘
        with open(GROCERY_JSON_PATH, "r", encoding="utf-8") as f:
            groceries = json.load(f)

        keyboard = []
        for item in groceries:
            item_name = item["名称"]
            checked = "✅" if item_name in selected else "⬜"
            keyboard.append([
                InlineKeyboardButton(f"{checked} {item_name}", callback_data=f"toggle::{item_name}")
            ])
        keyboard.append([
            InlineKeyboardButton("✅ 更新库存到 Notion", callback_data="confirm_update")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)

    elif data == "confirm_update":
        selected = selected_items_by_chat.get(chat_id, set())
        if not selected:
            await query.edit_message_text("⚠️ 未选择任何食材。")
            return

        # 查询并更新每个食材的 Notion 页面
        success = 0
        for name in selected:
            search_payload = {
                "page_size": 1,
                "filter": {
                    "property": "名称",
                    "rich_text": {"equals": name}
                }
            }
            search_resp = requests.post(
                f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID_GROCERY}/query",
                headers=HEADERS,
                json=search_payload
            ).json()

            results = search_resp.get("results")
            if not results:
                continue

            page_id = results[0]["id"]
            update_resp = requests.patch(
                f"{NOTION_API_URL}{page_id}",
                headers=HEADERS,
                json={"properties": {"已使用": {"checkbox": True}}}
            )

            if update_resp.status_code in [200, 204]:
                success += 1

        await query.edit_message_text(f"✅ 已标记 {success} 项为已使用。")