FROM python:3.12-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要的系統套件和 cron
RUN apt-get update && \
    apt-get install -y cron && \
    rm -rf /var/lib/apt/lists/*

# 安裝 Python 依賴
RUN pip install --no-cache-dir requests beautifulsoup4

# 複製爬蟲程式檔案
COPY run.py scraper.py logger.py /app/

# 建立資料目錄和日誌目錄，並設定權限
RUN mkdir -p /app/data /app/logs && \
    chmod 777 /app/data /app/logs

# 複製 cron 啟動腳本
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# 使用 entrypoint 啟動 cron
ENTRYPOINT ["/app/entrypoint.sh"]
