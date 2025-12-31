# 動畫瘋爬蟲

自動抓取巴哈姆特動畫瘋的動畫列表，並維護 `sn_list.txt`。

## 使用方式

### 本地執行

```bash
source .venv/bin/activate
python run.py -p 2  # 抓取 2 頁
```

### Docker 執行

```bash
# 建置和啟動（背景執行，每天凌晨 2:00 自動執行）
docker-compose up -d

# 手動執行爬蟲
docker-compose exec anime-scraper python3 run.py -p 5

# 查看日誌
docker-compose logs -f
# 或查看本地日誌檔案
cat logs/anime_scraper_20251231.log

# 停止容器
docker-compose down
```

資料儲存在 `./data/sn_list.txt`，日誌儲存在 `./logs/`（自動保留 7 天），容器重啟後不會遺失。

## 功能

- 自動抓取動畫 SN 和標題
- 過濾一年以前的舊季度資料
- 處理重複動畫（舊的改為註解格式）
- 依季度分組儲存
- 支援 Docker 部署與 Cron 自動化
- 完整的日誌記錄（自動清理 7 天前的舊日誌）

## 專案結構

```
.
├── run.py           # 主程式入口
├── scraper.py       # 爬蟲核心邏輯
├── logger.py        # 日誌模組
├── data/            # 資料目錄（sn_list.txt）
└── logs/            # 日誌目錄（保留 7 天）
```

## 輸出格式

```
@2025_1012
113887 all #末世二輪之旅

@2024_1012
#末世二輪之旅
```
