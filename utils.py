# utils.py
"""
Cung cấp các tiện ích và hàm hỗ trợ chung cho ứng dụng
"""

import datetime
import asyncio
import functools
import logging
import os
from typing import Optional, Callable, Any, Dict, List, Tuple, Union

logger = logging.getLogger('family_assistant')

class DateUtils:
    """
    Cung cấp các phương thức xử lý ngày tháng
    """
    
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
    
    @staticmethod
    def format_event_date(date_str: str) -> str:
        """Định dạng lại ngày từ YYYY-MM-DD thành DD/MM/YYYY"""
        try:
            if not date_str:
                return ""
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            return date_obj.strftime("%d/%m/%Y")
        except Exception as e:
            logger.error(f"Lỗi định dạng ngày {date_str}: {e}")
            return date_str
    
    @staticmethod
    def get_upcoming_events(events_data: Dict[str, Dict], days_ahead: int = 14) -> List[Dict]:
        """Lọc và trả về các sự kiện sắp diễn ra trong khoảng thời gian cụ thể"""
        today = datetime.datetime.now().date()
        upcoming = []
        
        for event_id, event in events_data.items():
            try:
                event_date = datetime.datetime.strptime(event.get("date", ""), "%Y-%m-%d").date()
                if event_date >= today:
                    date_diff = (event_date - today).days
                    if date_diff <= days_ahead:
                        upcoming.append({
                            "id": event_id,
                            "title": event.get("title", ""),
                            "date": event.get("date", ""),
                            "days_away": date_diff
                        })
            except Exception as e:
                logger.error(f"Lỗi khi xử lý ngày sự kiện {event.get('title', '')}: {e}")
        
        # Sắp xếp theo ngày tăng dần
        upcoming.sort(key=lambda x: x["days_away"])
        return upcoming


class AsyncHelper:
    """
    Công cụ hỗ trợ chạy các hàm bất đồng bộ
    """
    
    @staticmethod
    def run_async(func: Callable) -> Callable:
        """Decorator để chạy hàm bất đồng bộ trong môi trường đồng bộ"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return asyncio.run(func(*args, **kwargs))
        return wrapper
    
    @staticmethod
    async def gather_with_concurrency(n: int, *tasks) -> List[Any]:
        """Chạy đồng thời nhiều task với giới hạn số lượng task cùng lúc"""
        semaphore = asyncio.Semaphore(n)
        
        async def sem_task(task):
            async with semaphore:
                return await task
        
        return await asyncio.gather(*(sem_task(task) for task in tasks))


class Logger:
    """
    Cung cấp các phương thức thiết lập và sử dụng logger
    """
    
    @staticmethod
    def setup(level: int = logging.INFO, logfile: Optional[str] = None) -> logging.Logger:
        """Thiết lập logger"""
        # Đảm bảo thư mục logs tồn tại
        if logfile:
            os.makedirs(os.path.dirname(logfile) or '.', exist_ok=True)
        
        # Cấu hình cơ bản
        logging.basicConfig(
            level=level, 
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        
        # Tạo logger
        logger = logging.getLogger('family_assistant')
        
        # Thêm handler ghi file nếu có
        if logfile:
            file_handler = logging.FileHandler(logfile, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(file_handler)
        
        return logger
    
    @staticmethod
    def get_logger() -> logging.Logger:
        """Lấy instance của logger"""
        return logging.getLogger('family_assistant')


class ConfigManager:
    """
    Quản lý cấu hình và thiết lập của ứng dụng
    """
    
    @staticmethod
    def load_secrets(streamlit_secrets: Dict = None) -> Dict:
        """Tải các thông tin bí mật (API keys, etc.)"""
        secrets = {}
        
        # Thử lấy từ Streamlit Secrets
        if streamlit_secrets is not None:
            if "api_keys" in streamlit_secrets:
                secrets["openai_api_key"] = streamlit_secrets["api_keys"].get("openai", "")
                secrets["tavily_api_key"] = streamlit_secrets["api_keys"].get("tavily", "")
            
            if "database" in streamlit_secrets:
                secrets["db_path"] = streamlit_secrets["database"].get("path", "family_assistant.db")
        
        # Thử lấy từ biến môi trường nếu chưa có
        if "openai_api_key" not in secrets or not secrets["openai_api_key"]:
            secrets["openai_api_key"] = os.environ.get("OPENAI_API_KEY", "")
        
        if "tavily_api_key" not in secrets or not secrets["tavily_api_key"]:
            secrets["tavily_api_key"] = os.environ.get("TAVILY_API_KEY", "")
        
        if "db_path" not in secrets:
            secrets["db_path"] = os.environ.get("DB_PATH", "family_assistant.db")
        
        return secrets
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Kiểm tra API key có hợp lệ không"""
        if not api_key:
            return False
        
        # Kiểm tra định dạng OpenAI API key
        if api_key.startswith("sk-") and len(api_key) > 20:
            return True
        
        return False


class TextUtility:
    """
    Cung cấp các phương thức xử lý văn bản
    """
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Cắt bớt văn bản nếu quá dài"""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    @staticmethod
    def clean_string(text: str) -> str:
        """Làm sạch chuỗi, loại bỏ các ký tự đặc biệt"""
        import re
        return re.sub(r'[^\w\s]', '', text).strip()
    
    @staticmethod
    def normalize_query(query: str) -> str:
        """Chuẩn hóa câu truy vấn"""
        return query.lower().strip()
    
    @staticmethod
    def extract_tags_from_text(text: str) -> List[str]:
        """Trích xuất các tag từ văn bản"""
        import re
        # Tìm tất cả từ đứng sau dấu #
        tags = re.findall(r'#(\w+)', text)
        # Thêm các từ khóa chung được phân tách bằng dấu phẩy
        if "tags:" in text.lower():
            tag_section = text.lower().split("tags:")[1].split("\n")[0]
            comma_tags = [t.strip() for t in tag_section.split(",")]
            tags.extend(comma_tags)
        
        # Loại bỏ trùng lặp và chuẩn hóa
        cleaned_tags = []
        for tag in tags:
            clean_tag = tag.strip().lower()
            if clean_tag and clean_tag not in cleaned_tags:
                cleaned_tags.append(clean_tag)
        
        return cleaned_tags