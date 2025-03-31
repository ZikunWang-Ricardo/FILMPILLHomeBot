# sync_notion.py

import requests
import json
from config import NOTION_API_KEY, NOTION_DATABASE_ID, NOTION_DATABASE_ID_GROCERY, NOTION_DATABASE_ID_RECIPES

NOTION_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def simplify_data(item):
    props = item["properties"]
    return {
        "名称": props["名称"]["title"][0]["plain_text"] if props["名称"]["title"] else "",
        "酒精度数": props["酒精度数"]["number"],
        "类型": [t["name"] for t in props["类型"]["multi_select"]],
        "风味": [f["name"] for f in props["风味"]["multi_select"]],
        "产地": [p["name"] for p in props["产地"]["multi_select"]],
        "评分": props["评分"]["rich_text"][0]["plain_text"] if props["评分"]["rich_text"] else "",
        "价格": props["价格"]["rich_text"][0]["plain_text"] if props["价格"]["rich_text"] else "",
        "年份": props["年份"]["rich_text"][0]["plain_text"] if props["年份"]["rich_text"] else "",
        "创建时间": item["created_time"]
    }

def simplify_grocery(item):
    props = item["properties"]
    if props.get("已使用", {}).get("checkbox") is True:
        return None

    return {
        "名称": props["名称"]["title"][0]["plain_text"] if props["名称"]["title"] else "",
        "原名": props["原名"]["rich_text"][0]["plain_text"] if props["原名"]["rich_text"] else "",
        "类型": props["类型"]["select"]["name"] if props["类型"].get("select") else "",
        "价格": props["价格"]["number"] if props["价格"].get("number") else 0,
        "购买时间": props["购买时间"]["date"]["start"] if props["购买时间"].get("date") else "",
        "过期日期": props["过期日期"]["date"]["start"] if props.get("过期日期", {}).get("date") else None,
        "存储建议": props["存储建议"]["rich_text"][0]["plain_text"] if props.get("存储建议", {}).get("rich_text") else ""
    }

def simplify_recipe(item):
    props = item["properties"]
    return {
        "菜名": props["菜名"]["title"][0]["plain_text"] if props["菜名"]["title"] else "",
        "菜系": [c["name"] for c in props["菜系"]["multi_select"]],
        "食材": [i["name"] for i in props["食材"]["multi_select"]],
        "难度": props["难度"]["select"]["name"] if props["难度"].get("select") else "",
        "备注": props["备注"]["rich_text"][0]["plain_text"] if props["备注"]["rich_text"] else ""
    }

def query_database(database_id, simplify_func, cache_path):
    all_data = []
    has_more = True
    start_cursor = None

    logging_prefix = f"🔄 正在同步数据库 {database_id}"
    print(logging_prefix + "...")

    while has_more:
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor

        response = requests.post(
            f"{NOTION_URL}/databases/{database_id}/query",
            headers=HEADERS,
            json=payload
        ).json()

        raw_results = response.get("results", [])
        simplified_results = [simplify_func(item) for item in raw_results if simplify_func(item)]
        all_data.extend(simplified_results)

        has_more = response.get("has_more", False)
        start_cursor = response.get("next_cursor", None)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已同步 {len(all_data)} 条数据 ➜ {cache_path}")

def sync_notion_to_local():
    print("🚀 启动 Notion 同步任务...")
    if NOTION_DATABASE_ID:
        query_database(NOTION_DATABASE_ID, simplify_data, "/app/notion_wines.json")
    if NOTION_DATABASE_ID_GROCERY:
        query_database(NOTION_DATABASE_ID_GROCERY, simplify_grocery, "/app/notion_grocery.json")
    if NOTION_DATABASE_ID_RECIPES:
        query_database(NOTION_DATABASE_ID_RECIPES, simplify_recipe, "/app/notion_recipes.json")

if __name__ == "__main__":
    sync_notion_to_local()
