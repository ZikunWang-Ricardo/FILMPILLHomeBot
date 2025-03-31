# cook.py

import json
import time
import logging
from datetime import datetime, timedelta
from openai import OpenAI
from config import OPENAI_PROJ_API_KEY, OPENAI_ASSISTANT_ID_COOK

client = OpenAI(api_key=OPENAI_PROJ_API_KEY)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_recent_ingredients(grocery_data, days=14):
    recent_cutoff = datetime.now() - timedelta(days=days)
    recent = set()

    for item in grocery_data:
        date_str = item.get("购买时间") or item.get("创建时间")
        try:
            purchase_time = datetime.fromisoformat(date_str)
            if purchase_time >= recent_cutoff:
                recent.add(item["名称"])
        except Exception:
            continue

    return list(recent)


def handle_cook_query(query_text: str) -> str:
    try:
        # 1. 读取数据库缓存
        recipes = load_json("/app/notion_recipes.json")
        wines = load_json("/app/notion_wines.json")
        groceries = load_json("/app/notion_grocery.json")

        # 2. 提取近14天冰箱里的“可用食材”
        ingredients = get_recent_ingredients(groceries)

        # 3. 拼接 prompt
        prompt = (
            "你是一位结合“食谱 + 酒单 + 冰箱库存”的智能厨房助理，帮助用户推荐可做的菜，并搭配酒。\n\n"
            f"【用户提问】：{query_text}\n\n"
            f"【菜谱数据】：{json.dumps(recipes, ensure_ascii=False)}\n\n"
            f"【酒单数据】：{json.dumps(wines, ensure_ascii=False)}\n\n"
            f"【最近购买食材】：{json.dumps(ingredients, ensure_ascii=False)}"
        )

        # 4. 创建对话线程
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=[{"type": "text", "text": prompt}]
        )

        # 5. 运行 assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=OPENAI_ASSISTANT_ID_COOK
        )

        while True:
            status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if status.status == "completed":
                break
            elif status.status == "failed":
                logging.error("❌ Cook Assistant 执行失败")
                return "⚠️ 查询失败，请稍后再试。"
            time.sleep(2)

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for msg in messages.data:
            if msg.role == "assistant":
                return msg.content[0].text.value.strip()

        return "⚠️ 没有获得有效回复，请稍后再试。"

    except Exception as e:
        logging.exception("❌ handle_cook_query 出错：%s", e)
        return "⚠️ 查询出错，请稍后再试。"
