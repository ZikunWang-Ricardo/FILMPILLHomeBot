# assistant_vision.py
from openai import OpenAI
import time
import json
import logging
from config import OPENAI_PROJ_API_KEY, OPENAI_ASSISTANT_ID

client = OpenAI(api_key=OPENAI_PROJ_API_KEY)

# 使用持久化的 Assistant ID，不再重复创建
def create_or_get_wine_assistant():
    if OPENAI_ASSISTANT_ID:
        return OPENAI_ASSISTANT_ID

    assistant = client.beta.assistants.create(
        name="Wine Recognizer",
        model="gpt-4o",
        instructions=(
            "你是一位葡萄酒识别专家。用户上传酒瓶图片，识别信息并以JSON返回："
            "名称、类型、年份、酒精度、产地、风味、价格、评分。仅返回JSON。"
            "若无法识别，返回空对象{}。"
        )
    )
    logging.info(f"首次创建Assistant，ID：{assistant.id}")
    return assistant.id


def analyze_image_with_assistant(image_path, assistant_id):
    try:
        thread = client.beta.threads.create()

        # 上传图片到OpenAI
        with open(image_path, "rb") as f:
            file = client.files.create(file=f, purpose="assistants")

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=[
                {"type": "text", "text": "请识别这瓶酒"},
                {"type": "image_file", "image_file": {"file_id": file.id}}
            ]
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        # 等待识别完成
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

        # 删除上传的文件释放空间
        client.files.delete(file.id)

        return structured

    except Exception as e:
        logging.exception("❌ analyze_image_with_assistant 全局异常: %s", e)
        return None