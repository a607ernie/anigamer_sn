#!/bin/bash
set -e

# 確保目錄權限正確
chmod 777 /app/data /app/logs || true

# 如果 sn_list.txt 已存在，確保它可讀寫
if [ -f /app/data/sn_list.txt ]; then
    chmod 666 /app/data/sn_list.txt || true
fi

# 建立 cron job：每天凌晨 2 點執行
echo "0 2 * * * cd /app && python3 run.py -p 3 >> /var/log/cron.log 2>&1" > /etc/cron.d/anime-scraper

# 設定cron job 權限
chmod 0644 /etc/cron.d/anime-scraper

# 註冊 cron job
crontab /etc/cron.d/anime-scraper

# 建立 log 檔案
touch /var/log/cron.log

# 初次執行一次（可選）
echo "執行初次爬取..."
cd /app && python3 run.py -p 3 || true

# 啟動 cron 並持續輸出 log
echo "Cron 已啟動，每天凌晨 2 點執行爬蟲..."
cron && tail -f /var/log/cron.log
