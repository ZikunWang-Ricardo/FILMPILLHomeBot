# notion.py
import requests
import logging
from config import NOTION_API_KEY, NOTION_DATABASE_ID

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def print_notion_database_properties():
    response = requests.get(
        f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}",
        headers=headers,
    )

    if response.status_code == 200:
        logging.info("Notion 数据库字段结构如下：")
        data = response.json()
        for key, val in data["properties"].items():
            logging.info(f"- {key}: {val['type']}")
    else:
        logging.error("获取失败：%s", response.text)

def add_wine_to_notion(wine):
    try:
        properties = {
            "名称": {"title": [{"text": {"content": wine["名称"]}}]},
            "类型": {"multi_select": [{"name": t} for t in wine.get("类型", [])]},
            "产地": {"multi_select": [{"name": p} for p in wine.get("产地", [])]},
            "风味": {"multi_select": [{"name": f} for f in wine.get("风味", [])]},
        }

        if wine.get("年份"):
            properties["年份"] = {"rich_text": [{"text": {"content": wine["年份"]}}]}

        if wine.get("酒精度"):
            properties["酒精度数"] = {"number": float(wine["酒精度"])}

        if wine.get("价格"):
            properties["价格"] = {"rich_text": [{"text": {"content": wine["价格"]}}]}

        if wine.get("评分"):
            properties["评分"] = {"rich_text": [{"text": {"content": wine["评分"]}}]}

        data = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": properties
        }

        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=data
        )

        if response.status_code in [200, 201]:
            logging.info("✅ 已成功写入 Notion")
            return "created"
        else:
            logging.error("❌ 写入失败，状态码：%s", response.status_code)
            logging.error("请求内容：%s", data)
            logging.error("错误信息：%s", response.text)
            return None

    except Exception as e:
        logging.exception("❌ add_wine_to_notion 出错：%s", e)
        return None