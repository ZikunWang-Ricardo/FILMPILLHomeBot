# query.py
import json
import logging
from openai import OpenAI
from config import OPENAI_PROJ_API_KEY, OPENAI_ASSISTANT_ID_QUERY

client = OpenAI(api_key=OPENAI_PROJ_API_KEY)

# 加载本地缓存的数据
def load_wines():
    with open("/app/notion_wines.json", "r", encoding="utf-8") as f:
        return json.load(f)

# 使用固定的 OpenAI Assistant 来处理自然语言查询并总结结果
def query_wines_with_assistant(query, wines_data):
    prompt = (
        f"以下是酒类数据库：\n{json.dumps(wines_data, ensure_ascii=False)}\n\n"
        f"用户查询的问题是：「{query}」。请根据数据库中的信息，筛选出最符合查询条件的酒，"
        "并用中文以自然、亲切的方式总结并回答给用户。如果没有符合的酒，请礼貌地告知用户。"
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
            assistant_id=OPENAI_ASSISTANT_ID_QUERY
        )

        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                logging.error("❌ Assistant 执行失败")
                return "❌ 抱歉，查询处理失败了，请稍后重试。"

        messages = client.beta.threads.messages.list(thread_id=thread.id)

        for message in messages.data:
            if message.role == 'assistant' and message.content:
                return message.content[0].text.value

        return "⚠️ 抱歉，没有找到合适的回复。"

    except Exception as e:
        logging.exception("❌ 查询过程发生错误：%s", e)
        return "❌ 查询过程发生错误，请稍后重试。"

# 主入口函数
def handle_natural_query(natural_query):
    wines_data = load_wines()
    result = query_wines_with_assistant(natural_query, wines_data)
    return result