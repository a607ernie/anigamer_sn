# -*- coding: UTF-8 -*-
import requests
from bs4 import BeautifulSoup
import time
import re
import os
import argparse
from collections import defaultdict
from datetime import datetime

# ============ 設定區塊 ============
# 模擬瀏覽器的 User-Agent，避免被網站擋掉
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
# 巴哈姆特動畫瘋列表頁面的網址
BASE_URL = "https://ani.gamer.com.tw/animeList.php"
# 輸出檔案名稱（支援 Docker volume 掛載路徑）
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "data/sn_list.txt") if os.path.exists("/app/data") else "sn_list.txt"

class AnimeScraper:
    def __init__(self, output_file=OUTPUT_FILE):
        """初始化動畫爬蟲"""
        self.output_file = output_file
        self.headers = {"User-Agent": USER_AGENT}
        # 資料結構：{ "2025_0103": [ {"sn": "123", "title": "動畫名稱", "line": "完整行內容"} ] }
        # 用來存放最終要輸出的資料，包含從檔案讀取的舊資料和新抓取的資料
        self.data = defaultdict(list) 
        # 暫存從網頁抓取的新資料，之後會與 self.data 合併
        self.scraped_data = defaultdict(list)
        # 記錄已存在的 SN，用來避免重複
        self.existing_sns = set()

    def get_season_key(self, year, month):
        """根據年份和月份計算季度代碼
        
        Args:
            year: 年份（例如：2025）
            month: 月份（1-12）
        
        Returns:
            季度代碼，例如："2025_0103" 代表 2025 年 1-3 月（第一季）
        """
        year = str(year)
        month = int(month)
        if 1 <= month <= 3:
            return f"{year}_0103"  # 第一季：1-3月
        elif 4 <= month <= 6:
            return f"{year}_0406"  # 第二季：4-6月
        elif 7 <= month <= 9:
            return f"{year}_0709"  # 第三季：7-9月
        elif 10 <= month <= 12:
            return f"{year}_1012"  # 第四季：10-12月
        else:
            return f"{year}other"  # 異常月份

    def parse_existing_file(self):
        """讀取現有的 sn_list.txt 檔案，解析並載入到記憶體
        
        這個方法會：
        1. 讀取檔案中的所有行
        2. 識別季度標記（@2025_0103）
        3. 從每一行中提取 SN 和動畫名稱
        4. 將資料存入 self.data 和 self.existing_sns
        5. 保留所有格式，包括註解行（#動畫名稱）
        """
        # 如果檔案不存在，直接返回
        if not os.path.exists(self.output_file):
            return

        current_season = None  # 當前正在處理的季度
        with open(self.output_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()  # 去除前後空白
                if not line:  # 跳過空行
                    continue
                
                if line.startswith('@'):
                    # 這是季度標記行，例如：@2025_0103
                    current_season = line[1:]  # 移除 @ 符號
                    # 確保該季度的列表存在，用來保存順序
                    if current_season not in self.data:
                        self.data[current_season] = []
                else:
                    # 這是動畫資料行，嘗試提取 SN 和標題
                    # 格式範例："12345 all #動畫名稱" 或 "#動畫名稱"（註解）
                    sn_match = re.search(r'(\d+)\s+all\s+#', line)
                    
                    sn = None
                    title = None
                    
                    if sn_match:
                        # 成功找到 SN
                        sn = sn_match.group(1)
                        self.existing_sns.add(sn)  # 記錄這個 SN 已存在
                        # 提取標題（# 後面的部分）
                        parts = line.split('#', 1)
                        if len(parts) > 1:
                            title = parts[1].strip()
                    
                    # 如果沒有季度標記，歸類到 "Misc"
                    season_key = current_season if current_season else "Misc"
                    
                    # 將這一行的資料存入
                    self.data[season_key].append({
                        'sn': sn,          # SN（可能為 None）
                        'title': title,    # 動畫名稱（可能為 None）
                        'line': line       # 原始行內容
                    })

    def scrape(self, pages=2):
        """從巴哈姆特動畫瘋網站抓取動畫列表
        
        Args:
            pages: 要抓取的頁數，預設為 2 頁
        """
        print(f"開始抓取 {pages} 頁的動畫資料...")
        for page in range(1, pages + 1):
            # 建立列表頁面的網址，c=0 表示所有分類，sort=1 表示依時間排序
            url = f"{BASE_URL}?page={page}&c=0&sort=1"
            print(f"正在抓取：{url}")
            try:
                # 發送 HTTP GET 請求，timeout=10 表示 10 秒沒回應就放棄
                resp = requests.get(url, headers=self.headers, timeout=10)
                resp.raise_for_status()  # 如果回應碼不是 200，會拋出例外
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # 找出所有動畫項目（CSS 選擇器）
                items = soup.select('.theme-list-main')
                if not items:
                    print("此頁面沒有找到任何動畫項目")
                    break  # 沒有資料就停止
                    
                # 逐一處理每個動畫項目
                for item in items:
                    self.process_item(item)
                
                # 每抓取一頁後休息 1 秒，避免對伺服器造成過大負擔
                time.sleep(1)
            except Exception as e:
                print(f"抓取第 {page} 頁時發生錯誤：{e}")

    def process_item(self, item):
        """處理單個動畫項目，提取 SN、標題和季度資訊
        
        Args:
            item: BeautifulSoup 解析出的動畫項目元素
        """
        try:
            # 1. 提取動畫標題
            title_tag = item.find('p', class_='theme-name')
            title = title_tag.text.strip() if title_tag else "Unknown"
            
            # 2. 提取年份和月份，計算季度
            time_tag = item.find('p', class_='theme-time')
            if time_tag:
                date_text = time_tag.text  # 例如："年份：2025/10"
                if '年份：' in date_text:
                    date_str = date_text.split('年份：')[1].strip()  # 取出 "2025/10"
                    if '/' in date_str:
                        year_str, month_str = date_str.split('/')  # 分割成年和月
                        season_key = self.get_season_key(year_str, month_str)  # 計算季度代碼
                    else:
                        season_key = "Unknown"
                else:
                    season_key = "Unknown"
            else:
                season_key = "Unknown"

            # 3. 取得動畫詳細頁面的連結
            href = item.get('href')  # 例如："?sn=12345" 或 "animeRef.php?sn=12345"
            if not href:
                print(f"找不到連結：{title}")
                return
            
            # 4. 訪問詳細頁面以取得真正的 SN
            # 因為列表頁面的 href 可能不完整，所以需要到詳細頁面抓取 og:url 的 meta tag
            detail_url = "https://ani.gamer.com.tw/" + str(href)
            req_page = requests.get(detail_url, headers=self.headers, timeout=10)
            time.sleep(1)  # 每次請求後休息 1 秒，避免過於頻繁
            sp_req_page = BeautifulSoup(req_page.text, 'html.parser')
            
            # 5. 從詳細頁面的 og:url meta tag 中提取 SN
            og_url_meta = sp_req_page.find("meta", property="og:url")
            if og_url_meta:
                og_url = og_url_meta['content']  # 例如："https://ani.gamer.com.tw/animeRef.php?sn=12345"
                if 'sn=' in og_url:
                    sn = og_url.split('sn=')[1].split('&')[0]  # 提取 SN
                else:
                    print(f"無法從 og:url 提取 SN：{title}")
                    return
            else:
                print(f"找不到 og:url meta tag：{title}")
                return
            
            # 6. 將抓取到的資料存入暫存區
            if sn:
                print(f"已抓取：{title} ({sn}) -> {season_key}")
                new_line = f"{sn} all #{title}"  # 格式化為輸出格式
                self.scraped_data[season_key].append({
                    'sn': sn,
                    'title': title,
                    'line': new_line
                })
            else:
                print(f"無法提取 SN：{title}")

        except Exception as e:
            print(f"處理項目時發生錯誤：{e}")

    def merge_and_process_data(self):
        """合併網頁抓取的資料與本地檔案的資料
        
        處理邏輯：
        1. 將從網頁抓取的新資料（scraped_data）與本地資料（data）比對
        2. 如果 SN 不存在於本地，則新增到 data 中
        3. 如果 SN 已存在，則跳過（避免重複）
        
        優先權：新抓取的資料 > 本地資料
        """
        # 遍歷所有從網頁抓取的資料
        for season, entries in self.scraped_data.items():
            for entry in entries:
                sn = entry.get('sn')
                if sn and sn not in self.existing_sns:
                    # 這是新的動畫，加入到資料中
                    print(f"新動畫：{entry['title']} ({sn}) -> {season}")
                    self.data[season].append(entry)
                    self.existing_sns.add(sn)  # 記錄這個 SN 已經存在
                elif sn:
                    # SN 已存在，跳過
                    print(f"已存在：{entry['title']} ({sn})")
    
    def process_duplicates(self):
        """處理重複的動畫名稱
        
        處理邏輯：
        1. 找出所有動畫名稱相同但季度不同的項目
        2. 保留最新季度的完整資料（包含 SN）
        3. 將較舊季度的項目改為註解格式（只保留 #動畫名稱）
        
        範例：
        - @2025_1012: 113887 all #末世二輪之旅  <- 保留
        - @2024_1012: #末世二輪之旅              <- 改為註解
        """
        title_map = defaultdict(list)  # {動畫名稱: [(季度, 索引位置), ...]}
        
        # 收集所有有 SN 和標題的項目
        for season, entries in self.data.items():
            for idx, entry in enumerate(entries):
                if entry.get('sn') and entry.get('title'):
                    # 記錄這個動畫名稱出現在哪個季度的哪個位置
                    title_map[entry['title']].append((season, idx))
        
        # 處理每個動畫名稱
        for title, occurrences in title_map.items():
            if len(occurrences) > 1:
                # 這個動畫名稱有多個項目（重複了）
                # 按季度排序，最新的在前面（因為季度格式是 "YYYY_MMDD"，字串比較即可）
                occurrences.sort(key=lambda x: x[0], reverse=True)
                
                # 保留第一個（最新的），其餘改為註解
                for i in range(1, len(occurrences)):
                    season, idx = occurrences[i]
                    print(f"發現重複動畫 '{title}' 於 {season}，改為註解格式")
                    # 修改該行為註解格式（只保留 #標題）
                    self.data[season][idx]['line'] = f"#{title}"

    def filter_old_seasons(self):
        """過濾掉一年以前的舊季度資料
        
        計算方式：
        - 使用季度為單位進行計算
        - 保留最近一年內的季度資料
        - 刪除超過一年的舊季度
        
        範例：
        - 當前日期：2025/12/31（第四季 Q4）
        - 一年前同季度：2024/12/31（第四季 Q4）
        - 會刪除：2024_0709（第三季）及更早的季度
        - 會保留：2024_1012（第四季）及之後的季度
        """
        # 取得系統當前日期
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        
        # 計算當前季度代碼
        current_season = self.get_season_key(current_year, current_month)
        
        # 計算一年前的季度代碼（同一個月份，但年份減 1）
        one_year_ago_year = current_year - 1
        one_year_ago_season = self.get_season_key(one_year_ago_year, current_month)
        
        # 顯示計算結果
        print(f"當前日期：{now.strftime('%Y/%m/%d')}")
        print(f"當前季度：{current_season}")
        print(f"一年前季度：{one_year_ago_season}")
        print(f"將刪除比 {one_year_ago_season} 更舊的季度")
        
        # 找出要刪除的季度
        to_remove = []
        for season in self.data:
            # 比較季度字串（格式：YYYY_MMDD）
            # 因為格式統一，可以直接用字串比較
            # 例如："2024_0709" < "2024_1012" 會是 True
            if season < one_year_ago_season:
                to_remove.append(season)
        
        # 刪除舊季度的資料
        for season in to_remove:
            del self.data[season]
            print(f"已刪除舊季度：{season}")

    def save(self):
        """將處理完的資料儲存到檔案
        
        輸出格式：
        @2025_1012
        113887 all #末世二輪之旅
        113886 all #我的英雄學院 FINAL SEASON
        
        @2024_1012
        #末世二輪之旅
        """
        # 將季度按時間倒序排列（最新的在最上面）
        sorted_seasons = sorted(self.data.keys(), reverse=True)
        
        print(f"正在儲存到 {self.output_file}...")
        with open(self.output_file, 'w', encoding='utf-8') as f:
            for season in sorted_seasons:
                # 寫入季度標記
                f.write(f"@{season}\n")
                # 寫入該季度的所有動畫項目
                for entry in self.data[season]:
                    f.write(f"{entry['line']}\n")

if __name__ == "__main__":
    # 解析命令列參數
    parser = argparse.ArgumentParser(description="巴哈姆特動畫瘋爬蟲")
    parser.add_argument("-p", "--pages", type=int, default=2, help="要抓取的頁數")
    args = parser.parse_args()

    # 建立爬蟲物件
    scraper = AnimeScraper()
    
    # 執行流程：
    # 1. 讀取現有的 sn_list.txt 檔案
    scraper.parse_existing_file()
    
    # 2. 過濾掉一年以前的舊季度資料
    scraper.filter_old_seasons()
    
    # 3. 從網頁抓取新的動畫資料
    scraper.scrape(pages=args.pages)
    
    # 4. 合併網頁資料與本地資料
    scraper.merge_and_process_data()
    
    # 5. 處理重複的動畫名稱（舊的改為註解）
    scraper.process_duplicates()
    
    # 6. 儲存到檔案
    scraper.save()
    
    print("完成！")
