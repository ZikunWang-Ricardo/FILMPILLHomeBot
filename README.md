# 🍷 Grocery & WineBot - Personal AI Assistant for Life

A Telegram bot built with OpenAI GPT-4o and Notion API, designed to manage your grocery inventory, wine collection, and recipe suggestions using photos, natural language, and buttons. It's your personal cooking and lifestyle assistant.

---

## 📦 Features

### 🔍 Image Recognition
- **/receipt**: Upload Swedish supermarket receipts ➜ Translate and extract items ➜ Save to Notion Grocery DB
- **/wine**: Upload wine bottle photo ➜ Extract wine info (name, year, type, alcohol, flavor, rating, origin) ➜ Save to Notion Wine DB

### 🧠 Smart Interactions
- **/query <text>**: Query wine database using natural language (e.g. "red wine from France")
- **/pair <food>**: Recommend wine for a meal (e.g. "steak with mushrooms")
- **/cook <query>**: Suggest recipes based on your inventory and preferences (e.g. "I want Sichuan food" or "I have tofu and eggs")
- **/soon_expire**: List items that will expire within 3 days

### ✅ Grocery Management
- **/grocerylist**: View all current ingredients ➜ Select used items ➜ Confirm update ➜ Sync to Notion DB

---

## 📂 Project Structure

```
winebot/
├── bot.py                    # Main bot entry
├── assistant_vision.py       # Wine photo recognition via GPT-4o
├── receipt_ocr.py            # Receipt OCR via GPT-4o
├── cook.py                   # Cooking recommendation and pairing
├── query.py                  # Wine database querying
├── pair.py                   # Food-wine pairing
├── soon_expire.py            # Expiry warning
├── grocerylist.py            # Inventory UI and check buttons
├── notion.py                 # Notion API - wine DB
├── notion_grocery.py         # Notion API - grocery DB
├── sync_notion.py            # Data sync to local JSON
├── config.py                 # Loads API keys from .env
├── requirements.txt          # Python dependencies
├── Dockerfile
├── .env                      # API keys (not committed)
├── .gitignore
├── notion_wines.json         # Local wine cache
├── notion_grocery.json       # Local grocery cache
├── notion_recipes.json       # Local recipes cache
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/yourname/winebot.git
cd winebot
```

### 2. Create your `.env` file
```env
# Telegram
TELEGRAM_BOT_TOKEN=your-telegram-token

# OpenAI
OPENAI_PROJ_API_KEY=sk-xxxx
OPENAI_ASSISTANT_ID_WINE=asst-xxxx
OPENAI_ASSISTANT_ID_GROCERY=asst-xxxx
OPENAI_ASSISTANT_ID_COOK=asst-xxxx

# Notion
NOTION_API_KEY=secret_xxx
NOTION_DATABASE_ID=your-wine-db-id
NOTION_DATABASE_ID_GROCERY=your-grocery-db-id
NOTION_DATABASE_ID_RECIPES=your-recipe-db-id
```

### 3. Build and run with Docker
```bash
docker-compose up --build
```

---

## 🧠 Technologies Used
- [OpenAI GPT-4o (Vision)](https://platform.openai.com)
- [Telegram Bot API](https://core.telegram.org/bots)
- [Notion API](https://developers.notion.com)
- Python Async/Await, Docker

---

## 📌 Future Ideas
- Daily reminders: auto-push /soon_expire
- Auto cleanup "used" groceries
- Group usage support
- Web dashboard with charts

---

## 🧑‍🍳 Made by RicardoWang
With GPT assistance and a lot of good food 😋
