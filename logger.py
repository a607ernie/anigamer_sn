# -*- coding: UTF-8 -*-
"""
日誌模組
提供統一的日誌記錄功能，並自動清理 7 天前的舊日誌
"""
import logging
import os
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
import glob


class Logger:
    """日誌管理器"""
    
    def __init__(self, name="anime_scraper", log_dir="logs", max_days=7):
        """
        初始化日誌管理器
        
        Args:
            name: 日誌記錄器名稱
            log_dir: 日誌檔案目錄
            max_days: 保留日誌的天數
        """
        self.log_dir = log_dir
        self.max_days = max_days
        
        # 建立日誌目錄
        os.makedirs(log_dir, exist_ok=True)
        
        # 清理舊日誌
        self.cleanup_old_logs()
        
        # 設定日誌檔案名稱（每天一個檔案）
        today = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"{name}_{today}.log")
        
        # 建立 logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # 避免重複添加 handler
        if not self.logger.handlers:
            # 檔案 handler
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 設定日誌格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # 添加 handler
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def cleanup_old_logs(self):
        """清理 7 天前的舊日誌檔案"""
        cutoff_date = datetime.now() - timedelta(days=self.max_days)
        
        # 找出所有日誌檔案
        log_files = glob.glob(os.path.join(self.log_dir, "*.log"))
        
        for log_file in log_files:
            # 取得檔案修改時間
            file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
            
            # 如果檔案超過保留天數，就刪除
            if file_mtime < cutoff_date:
                try:
                    os.remove(log_file)
                    print(f"已刪除舊日誌: {log_file}")
                except Exception as e:
                    print(f"刪除日誌失敗 {log_file}: {e}")
    
    def info(self, message):
        """記錄 INFO 級別日誌"""
        self.logger.info(message)
    
    def warning(self, message):
        """記錄 WARNING 級別日誌"""
        self.logger.warning(message)
    
    def error(self, message):
        """記錄 ERROR 級別日誌"""
        self.logger.error(message)
    
    def debug(self, message):
        """記錄 DEBUG 級別日誌"""
        self.logger.debug(message)


# 提供全域 logger 實例
def get_logger(name="anime_scraper"):
    """
    取得日誌記錄器
    
    Args:
        name: 日誌記錄器名稱
        
    Returns:
        Logger 實例
    """
    return Logger(name)
