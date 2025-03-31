FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# 安装 cron
RUN apt-get update && apt-get install -y cron

# 添加 notion 同步任务（每 10 分钟执行一次）
RUN echo "*/10 * * * * /usr/local/bin/python /app/sync_notion.py >> /app/notion_sync.log 2>&1" > /etc/cron.d/notion_sync \
    && chmod 0644 /etc/cron.d/notion_sync

# 添加每日过期提醒任务（每天早上 9 点）
RUN echo "0 9 * * * /usr/local/bin/python /app/daily_expire_job.py >> /app/expire_reminder.log 2>&1" >> /etc/cron.d/notion_sync \
    && crontab /etc/cron.d/notion_sync

# 启动时立即同步一次，然后运行 cron 和 bot
CMD ["sh", "-c", "python /app/sync_notion.py && cron && python bot.py"]
