# receipt_ocr.py

import time
import json
import logging
from openai import OpenAI
from config import OPENAI_PROJ_API_KEY, OPENAI_ASSISTANT_ID_GROCERY

client = OpenAI(api_key=OPENAI_PROJ_API_KEY)

# ✅ 固定 Assistant ID：优先使用 config 中配置的 ID
def create_or_get_grocery_assistant():
    if OPENAI_ASSISTANT_ID_GROCERY:
        return OPENAI_ASSISTANT_ID_GROCERY

    assistant = client.beta.assistants.create(
        name="Grocery Receipt Parser",
        model="gpt-4o",
        instructions=(
            "你是一位超市小票解析助手。用户上传的是瑞典语的超市购物小票照片。请识别其中的所有商品记录，"
            "返回结构化的 JSON 格式，内容包括：\n"
            "- 购买时间（格式：YYYY-MM-DD）\n"
            "- 商品列表，每项包含：\n"
            "  - 瑞典名（原始商品名称）\n"
            "  - 中文名（翻译为中文）\n"
            "  - 类型（如：蔬菜、水果、乳制品、肉类、饮料、零食等）\n"
            "  - 价格（单位 SEK，浮点数）\n"
            "  - 过期日期（字段名为 “过期日期”，根据类型估算，格式 YYYY-MM-DD）\n"
            "  - 存储建议（如何保存该物品，例如冷藏、冷冻、避光阴凉等）\n"
            "\n"
            "请你根据以下规则判断过期时间与存储方式：\n"
            "- 蔬菜/水果：5天，冷藏保存\n"
            "- 乳制品：10天，冷藏 0~4°C\n"
            "- 肉类：7天，冷藏保鲜，如不尽快食用建议冷冻\n"
            "- 熟食：4天，冷藏密封保存\n"
            "- 饮料：30天，避光阴凉保存（如开封需冷藏）\n"
            "- 零食：90天，密封避光保存\n"
            "- 冷冻食品：180天，零下冷冻保存\n"
            "- 酱料/罐头：365天，未开封避光常温，开封需冷藏\n"
            "\n"
            "若商品为生鲜或不明确的品类，请智能判断存储方式，并给出建议。\n"
            "若无法识别小票内容，请返回空对象 {}。仅返回 JSON 数据，不要其他解释说明。"
        )
    )
    logging.info(f"🧾 创建新 Grocery Assistant，ID：{assistant.id}")
    return assistant.id


def analyze_receipt_with_assistant(image_path, assistant_id):
    try:
        thread = client.beta.threads.create()

        with open(image_path, "rb") as f:
            file = client.files.create(file=f, purpose="assistants")

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=[
                {"type": "text", "text": "请识别这张瑞典超市小票，并添加中文、过期时间和存储建议。"},
                {"type": "image_file", "image_file": {"file_id": file.id}}
            ]
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                logging.error("❌ Assistant 执行失败")
                client.files.delete(file.id)
                return None
            time.sleep(2)

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        assistant_response = None
        for message in messages.data:
            if message.role == 'assistant' and message.content:
                assistant_response = message.content[0].text.value
                break

        if not assistant_response:
            logging.warning("⚠️ 无 assistant 回复消息")
            client.files.delete(file.id)
            return None

        try:
            structured = json.loads(assistant_response)
        except json.JSONDecodeError as e:
            logging.exception("⚠️ JSON解析失败: %s", e)
            client.files.delete(file.id)
            return None

        client.files.delete(file.id)
        return structured

    except Exception as e:
        logging.exception("❌ analyze_receipt_with_assistant 全局异常: %s", e)
        return None