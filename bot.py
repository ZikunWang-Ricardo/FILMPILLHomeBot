# bot.py

import logging
import tempfile
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from assistant_vision import create_or_get_wine_assistant, analyze_image_with_assistant
from receipt_ocr import create_or_get_grocery_assistant, analyze_receipt_with_assistant
from notion import add_wine_to_notion
from notion_grocery import add_grocery_to_notion
from query import handle_natural_query
from pair import handle_food_pairing
from cook import handle_cook_query
from soon_expire import soon_expire
from grocerylist import grocerylist, mark_used_callback
from config import TELEGRAM_BOT_TOKEN

logging.basicConfig(level=logging.INFO)

assistant_id_wine = create_or_get_wine_assistant()
assistant_id_grocery = create_or_get_grocery_assistant()

current_mode = {}  # chat_id ➜ "wine" 或 "grocery"

keyboard = [["/wine", "/receipt"], ["/cook", "/soon_expire"], ["/grocerylist"]]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_mode[update.effective_chat.id] = "grocery"
    await update.message.reply_text(
    "欢迎来到小王私厨智能管理系统，请选择需要使用的功能：\n\n"
    "/start - 初始化并显示主菜单\n"
    "/receipt - 切换到超市小票识别模式\n"
    "/wine - 切换到酒瓶识别模式\n"
    "/query <条件> - 查询酒单内容\n"
    "/pair <食物描述> - 推荐搭配的酒类\n"
    "/cook <自然语言> - 推荐可做的菜和配酒\n"
    "/soon_expire - 查看未来三天将过期的食材\n"
    "/grocerylist - 显示食材库存并批量勾选已使用"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 使用指南：\n\n"
        "/start - 初始化并显示主菜单\n"
        "/receipt - 切换到超市小票识别模式\n"
        "/wine - 切换到酒瓶识别模式\n"
        "/query <条件> - 查询酒单内容\n"
        "/pair <食物描述> - 推荐搭配的酒类\n"
        "/cook <自然语言> - 推荐可做的菜和配酒\n"
        "/soon_expire - 查看未来三天将过期的食材\n"
        "/grocerylist - 显示食材库存并批量勾选已使用"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_path = file.file_path
    telegram_file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
        await file.download_to_drive(f.name)
        image_path = f.name

    chat_id = update.effective_chat.id
    mode = current_mode.get(chat_id, "grocery")

    if mode == "wine":
        await update.message.reply_text("📷 正在识别酒瓶信息，请稍候...")
        wine_data = analyze_image_with_assistant(image_path, assistant_id_wine)

        if wine_data:
            wine_data["照片"] = telegram_file_url
            result = add_wine_to_notion(wine_data)

            if result == "updated":
                await update.message.reply_text(f"已更新记录：{wine_data['名称']}，购买次数 +1")
            elif result == "created":
                await update.message.reply_text(f"🍷 新酒已添加：{wine_data['名称']}")
            else:
                await update.message.reply_text("写入 Notion 失败，请稍后重试。")
        else:
            await update.message.reply_text("❌ 未能识别这瓶酒的详细信息。")

    else:
        await update.message.reply_text("📷 正在识别小票信息，请稍候...")
        grocery_data = analyze_receipt_with_assistant(image_path, assistant_id_grocery)

        if grocery_data:
            result = add_grocery_to_notion(grocery_data)
            await update.message.reply_text(result)
        else:
            await update.message.reply_text("❌ 无法识别小票内容。")

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = " ".join(context.args)
    if not query_text:
        await update.message.reply_text("请输入查询内容，例如：/query 最近买的法国红酒")
        return

    await update.message.reply_text("🔎 正在查询中，请稍候...")
    result = handle_natural_query(query_text)
    await update.message.reply_text(result)

async def handle_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    food_text = " ".join(context.args)
    if not food_text:
        await update.message.reply_text("请输入晚餐内容，例如：/pair 黑椒牛排配蘑菇")
        return

    await update.message.reply_text("🍽️ 正在分析搭配中...")
    result = handle_food_pairing(food_text)
    await update.message.reply_text(result)

async def handle_cook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = " ".join(context.args)
    if not query_text:
        await update.message.reply_text("请输入做菜相关内容，例如：/cook 我想吃川菜 或 冰箱里有豆腐和鸡蛋能做什么")
        return

    await update.message.reply_text("👨‍🍳 正在查询可做菜品，请稍候...")
    result = handle_cook_query(query_text)
    await update.message.reply_text(result)

async def set_mode_wine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_mode[update.effective_chat.id] = "wine"
    await update.message.reply_text("🍷 已切换到酒类识别模式，请发送酒瓶照片。")

async def set_mode_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_mode[update.effective_chat.id] = "grocery"
    await update.message.reply_text("🛒 已切换到小票识别模式，请发送超市小票。")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("wine", set_mode_wine))
    app.add_handler(CommandHandler("receipt", set_mode_receipt))
    app.add_handler(CommandHandler("query", handle_query))
    app.add_handler(CommandHandler("pair", handle_pair))
    app.add_handler(CommandHandler("cook", handle_cook))
    app.add_handler(CommandHandler("soon_expire", soon_expire))
    app.add_handler(CommandHandler("grocerylist", grocerylist))
    app.add_handler(CallbackQueryHandler(mark_used_callback))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()
