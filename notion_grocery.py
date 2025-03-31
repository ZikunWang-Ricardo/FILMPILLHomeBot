# notion_grocery.py

import requests
import logging
from config import NOTION_API_KEY, NOTION_DATABASE_ID_GROCERY

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def add_grocery_to_notion(grocery_data):
    """
    参数结构示例：
    {
        "购买时间": "2025-03-30",
        "商品列表": [
            {
                "瑞典名": "mjölk",
                "中文名": "牛奶",
                "类型": "乳制品",
                "价格": 15.9,
                "过期日期": "2025-04-09",
                "存储建议": "冷藏 0~4°C，10 天内食用"
            },
            ...
        ]
    }
    """
    try:
        created = 0
        for item in grocery_data["商品列表"]:
            properties = {
                "名称": {"title": [{"text": {"content": item["中文名"]}}]},
                "原名": {"rich_text": [{"text": {"content": item["瑞典名"]}}]},
                "类型": {"select": {"name": item["类型"]}},
                "价格": {"number": float(item["价格"])} if "价格" in item else None,
                "购买时间": {"date": {"start": grocery_data["购买时间"]}},
                "已使用": {"checkbox": False},
            }

            if "过期日期" in item:
                properties["过期日期"] = {"date": {"start": item["过期日期"]}}

            if "存储建议" in item:
                properties["存储建议"] = {"rich_text": [{"text": {"content": item["存储建议"]}}]}

            properties = {k: v for k, v in properties.items() if v is not None}

            data = {
                "parent": {"database_id": NOTION_DATABASE_ID_GROCERY},
                "properties": properties
            }

            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=data
            )

            if response.status_code in [200, 201]:
                logging.info(f"✅ 成功写入商品：{item['中文名']}")
                created += 1
            else:
                logging.warning(f"⚠️ 无法写入商品：{item['中文名']}")
                logging.warning(response.text)

        return f"✅ 已成功添加 {created} 项商品到 Notion。"

    except Exception as e:
        logging.exception("❌ add_grocery_to_notion 出错：%s", e)
        return "⚠️ 写入 Notion 时发生错误。"
