# pair.py
import json
import logging
from openai import OpenAI
from config import OPENAI_PROJ_API_KEY, OPENAI_ASSISTANT_ID_PAIR

client = OpenAI(api_key=OPENAI_PROJ_API_KEY)

# 加载本地缓存的酒单数据
def load_wines():
    with open("/app/notion_wines.json", "r", encoding="utf-8") as f:
        return json.load(f)

# 使用固定的 OpenAI Assistant 提供食物与酒的搭配建议
def suggest_wine_pairing(food_description, wines_data):
    prompt = (
        f"你是一位经验丰富的专业侍酒师，以下是当前可供选择的酒类清单：\n"
        f"{json.dumps(wines_data, ensure_ascii=False)}\n\n"
        f"用户今晚的餐食是：「{food_description}」。请从酒单中选择1到3种最合适的酒类，"
        "以中文用亲切、自然的口吻给出具体的搭配建议。如果酒单中没有适合的搭配，"
        "请礼貌地说明并建议用户可以考虑哪些类型的酒。"
    )

    try:
        thread = client.beta.threads.create()

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=OPENAI_ASSISTANT_ID_PAIR
        )

        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                logging.error("❌ Assistant 执行失败")
                return "❌ 抱歉，配酒建议获取失败，请稍后再试。"

        messages = client.beta.threads.messages.list(thread_id=thread.id)

        for message in messages.data:
            if message.role == 'assistant' and message.content:
                return message.content[0].text.value

        return "⚠️ 抱歉，没有找到合适的回复。"

    except Exception as e:
        logging.exception("❌ 配酒过程发生错误：%s", e)
        return "❌ 配酒过程发生错误，请稍后重试。"

# 主入口函数
def handle_food_pairing(food_text):
    wines_data = load_wines()
    result = suggest_wine_pairing(food_text, wines_data)
    return result
