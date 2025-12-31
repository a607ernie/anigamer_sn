#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
動畫瘋爬蟲主程式
"""
import argparse
from scraper import AnimeScraper
from logger import get_logger


def main():
    """主程式進入點"""
    # 解析命令列參數
    parser = argparse.ArgumentParser(description="巴哈姆特動畫瘋爬蟲")
    parser.add_argument("-p", "--pages", type=int, default=2, help="要抓取的頁數")
    args = parser.parse_args()

    # 建立日誌記錄器
    logger = get_logger()
    
    logger.info("=" * 50)
    logger.info("動畫瘋爬蟲開始執行")
    logger.info("=" * 50)
    
    try:
        # 建立爬蟲物件
        scraper = AnimeScraper(logger=logger)
        
        # 執行流程：
        # 1. 讀取現有的 sn_list.txt 檔案
        logger.info("步驟 1/6: 讀取現有檔案")
        scraper.parse_existing_file()
        
        # 2. 過濾掉一年以前的舊季度資料
        logger.info("步驟 2/6: 過濾舊季度資料")
        scraper.filter_old_seasons()
        
        # 3. 從網頁抓取新的動畫資料
        logger.info("步驟 3/6: 抓取網頁資料")
        scraper.scrape(pages=args.pages)
        
        # 4. 合併網頁資料與本地資料
        logger.info("步驟 4/6: 合併資料")
        scraper.merge_and_process_data()
        
        # 5. 處理重複的動畫名稱（舊的改為註解）
        logger.info("步驟 5/6: 處理重複項目")
        scraper.process_duplicates()
        
        # 6. 儲存到檔案
        logger.info("步驟 6/6: 儲存檔案")
        scraper.save()
        
        logger.info("=" * 50)
        logger.info("執行完成！")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"執行過程中發生錯誤: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
