# debug_recipes.py
import requests
from config import NOTION_API_KEY, NOTION_DATABASE_ID_RECIPES

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def test_recipe_db():
    response = requests.post(
        f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID_RECIPES}/query",
        headers=HEADERS,
        json={"page_size": 10}
    )

    data = response.json()

    if response.status_code != 200:
        print("❌ 请求失败：", response.status_code)
        print(data)
        return

    results = data.get("results", [])
    if not results:
        print("⚠️ 没有获取到任何条目，可能是数据库为空或没有权限")
        return

    print(f"✅ 获取到 {len(results)} 条菜谱：")
    for item in results:
        title = item["properties"]["菜名"]["title"]
        if title:
            print("🍽", title[0]["plain_text"])
        else:
            print("❓ 无标题项")

if __name__ == "__main__":
    test_recipe_db()
