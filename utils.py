
import datetime
import asyncio
import functools
import logging
from typing import Optional, Callable, Any

logger = logging.getLogger('family_assistant')

class DateUtils:
    @staticmethod
    def get_date_from_relative_term(term: str) -> Optional[datetime.date]:
        """Chuyển đổi từ mô tả tương đối về ngày thành ngày thực tế"""
        today = datetime.datetime.now().date()
        
        term = term.lower().strip()
        
        if term in ["hôm nay", "today"]:
            return today
        elif term in ["ngày mai", "mai", "tomorrow"]:
            return today + datetime.timedelta(days=1)
        elif term in ["ngày kia", "day after tomorrow"]:
            return today + datetime.timedelta(days=2)
        elif term in ["hôm qua", "yesterday"]:
            return today - datetime.timedelta(days=1)
        elif any(keyword in term for keyword in ["tuần tới", "tuần sau", "next week"]):
            return today + datetime.timedelta(days=7)
        elif any(keyword in term for keyword in ["tuần trước", "last week"]):
            return today - datetime.timedelta(days=7)
        elif any(keyword in term for keyword in ["tháng tới", "tháng sau", "next month"]):
            # Đơn giản hóa bằng cách thêm 30 ngày
            return today + datetime.timedelta(days=30)
        elif "ngày" in term and term.replace("ngày", "").strip().isdigit():
            # Xử lý "ngày 15"
            day = int(term.replace("ngày", "").strip())
            current_month = today.month
            current_year = today.year
            
            # Nếu ngày trong tháng đã qua, lấy tháng sau
            if day < today.day:
                if current_month == 12:
                    current_month = 1
                    current_year += 1
                else:
                    current_month += 1
            
            try:
                return datetime.date(current_year, current_month, day)
            except ValueError:
                # Xử lý trường hợp ngày không hợp lệ (ví dụ: ngày 31 tháng 2)
                return None
        
        return None

class AsyncHelper:
    @staticmethod
    def run_async(func: Callable) -> Callable:
        """Decorator để chạy hàm bất đồng bộ trong môi trường đồng bộ"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return asyncio.run(func(*args, **kwargs))
        return wrapper

class Logger:
    @staticmethod
    def setup(level=logging.INFO):
        """Thiết lập logger"""
        logging.basicConfig(
            level=level, 
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        return logging.getLogger('family_assistant')