# services/openai_service.py
"""
Dịch vụ tương tác với OpenAI API
"""

import time
import asyncio
from typing import List, Dict, Generator, Optional, Tuple, Any
from openai import OpenAI, AsyncOpenAI
import logging
import json

logger = logging.getLogger('family_assistant')

class OpenAIService:
    """
    Lớp dịch vụ OpenAI cung cấp các phương thức để tương tác với API của OpenAI
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Khởi tạo dịch vụ OpenAI"""
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
        self.retries = 3
        self.retry_delay = 1
    
    def _handle_api_error(self, e: Exception, operation: str) -> None:
        """Xử lý lỗi API"""
        logger.error(f"Lỗi OpenAI {operation}: {str(e)}")
        
        # Nếu lỗi do quá tải server, đợi và thử lại
        if "rate limit" in str(e).lower() or "capacity" in str(e).lower():
            logger.info(f"Đang đợi trước khi thử lại - {self.retry_delay}s")
            time.sleep(self.retry_delay)
            # Tăng thời gian chờ theo cấp số nhân
            self.retry_delay *= 2
        else:
            # Đặt lại thời gian chờ cho lỗi khác
            self.retry_delay = 1
    
    def stream_chat_completion(self, 
                               messages: List[Dict], 
                               system_prompt: str = "",
                               temperature: float = 0.7,
                               max_tokens: int = 2048) -> Generator[str, None, None]:
        """Tạo và stream phản hồi chat từ OpenAI với retry logic"""
        # Thêm system prompt vào đầu messages
        full_messages = [{"role": "system", "content": system_prompt}]
        full_messages.extend(messages)
        
        # Giới hạn kích thước context để tránh vượt quá token limit
        full_messages = self._limit_context_size(full_messages)
        
        for attempt in range(self.retries):
            try:
                # Gọi API với streaming
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                
                # Stream từng phần phản hồi
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                
                # Đặt lại retry delay sau khi thành công
                self.retry_delay = 1
                return
            
            except Exception as e:
                self._handle_api_error(e, "stream chat completion")
                
                # Nếu đây là lần thử cuối, generate lỗi
                if attempt == self.retries - 1:
                    yield f"Xin lỗi, tôi đang gặp vấn đề kết nối: {str(e)}"
    
    def detect_search_intent(self, query: str) -> Tuple[bool, str]:
        """Phát hiện ý định tìm kiếm trong câu hỏi"""
        for attempt in range(self.retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": """
                            Bạn là một hệ thống phân loại câu hỏi thông minh. Nhiệm vụ của bạn là xác định xem câu hỏi có cần tìm kiếm thông tin thực tế, tin tức mới hoặc dữ liệu cập nhật không.
                            
                            Câu hỏi cần search khi:
                            1. Liên quan đến tin tức, sự kiện hiện tại hoặc gần đây
                            2. Yêu cầu dữ liệu thực tế, số liệu thống kê cập nhật
                            3. Hỏi về kết quả thể thao, giải đấu
                            4. Cần thông tin về giá cả, sản phẩm mới
                            5. Liên quan đến thời tiết, tình hình giao thông hiện tại
                            
                            Câu hỏi KHÔNG cần search khi:
                            1. Liên quan đến quản lý gia đình (thêm thành viên, sự kiện, ghi chú)
                            2. Hỏi ý kiến, lời khuyên cá nhân
                            3. Yêu cầu công thức nấu ăn phổ biến
                            4. Câu hỏi đơn giản về kiến thức phổ thông
                            5. Yêu cầu hỗ trợ sử dụng ứng dụng
                        """},
                        {"role": "user", "content": f"Câu hỏi: {query}\n\nCâu hỏi này có cần tìm kiếm thông tin thực tế không? Trả lời JSON với 2 trường: need_search (true/false) và search_query (câu truy vấn tìm kiếm tối ưu nếu cần search)."}
                    ],
                    temperature=0.1,
                    max_tokens=200,
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(response.choices[0].message.content)
                
                return result.get("need_search", False), result.get("search_query", query)
            
            except Exception as e:
                self._handle_api_error(e, "detect search intent")
                
                # Nếu đây là lần thử cuối, trả về mặc định
                if attempt == self.retries - 1:
                    return False, query
    
    async def generate_chat_summary(self, messages: List[Dict]) -> str:
        """Tạo tóm tắt của một cuộc trò chuyện"""
        # Chuẩn bị dữ liệu cho API
        content_texts = []
        for message in messages:
            if "content" in message:
                # Xử lý cả tin nhắn văn bản và hình ảnh
                if isinstance(message["content"], list):
                    for content in message["content"]:
                        if content["type"] == "text":
                            content_texts.append(f"{message['role'].upper()}: {content['text']}")
                else:
                    content_texts.append(f"{message['role'].upper()}: {message['content']}")
        
        # Ghép tất cả nội dung lại
        full_content = "\n".join(content_texts)
        
        for attempt in range(self.retries):
            try:
                response = await self.async_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Bạn là trợ lý tạo tóm tắt. Hãy tóm tắt cuộc trò chuyện dưới đây thành 1-3 câu ngắn gọn, tập trung vào các thông tin và yêu cầu chính."},
                        {"role": "user", "content": f"Tóm tắt cuộc trò chuyện sau:\n\n{full_content}"}
                    ],
                    temperature=0.3,
                    max_tokens=150
                )
                return response.choices[0].message.content
            
            except Exception as e:
                self._handle_api_error(e, "generate chat summary")
                
                # Nếu đây là lần thử cuối, trả về mặc định
                if attempt == self.retries - 1:
                    return "Không thể tạo tóm tắt vào lúc này."
    
    async def generate_dynamic_suggested_questions(self, 
                                                  member_info: Dict, 
                                                  upcoming_events: List[Dict],
                                                  recent_topics: List[str],
                                                  max_questions: int = 5) -> List[str]:
        """Tạo câu hỏi gợi ý cá nhân hóa"""
        for attempt in range(self.retries):
            try:
                # Tạo nội dung prompt cho OpenAI
                context = {
                    "member": member_info,
                    "upcoming_events": upcoming_events,
                    "recent_topics": recent_topics,
                    "current_time": time.strftime("%H:%M"),
                    "current_day": time.strftime("%A"),
                    "current_date": time.strftime("%Y-%m-%d")
                }
                
                prompt = f"""
                Hãy tạo {max_questions} câu gợi ý đa dạng và cá nhân hóa cho người dùng trợ lý gia đình dựa trên thông tin sau:
                
                Thông tin người dùng: {json.dumps(member_info, ensure_ascii=False)}
                
                Yêu cầu:
                1. Mỗi câu gợi ý nên tập trung vào MỘT sở thích cụ thể, không kết hợp nhiều sở thích
                2. KHÔNG kết thúc câu gợi ý bằng bất kỳ cụm từ nào như "bạn có biết không?", "bạn có muốn không?", v.v.
                3. Đưa ra thông tin cụ thể, chi tiết và chính xác như thể bạn đang viết một bài đăng trên mạng xã hội
                4. Mục đích là cung cấp thông tin hữu ích, không phải bắt đầu cuộc trò chuyện
                5. Chỉ trả về danh sách các câu gợi ý, mỗi câu trên một dòng
                6. Không thêm đánh số hoặc dấu gạch đầu dòng
                
                Trả về chính xác {max_questions} câu gợi ý.
                """
                
                response = await self.async_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Bạn là trợ lý tạo câu hỏi gợi ý cá nhân hóa."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    max_tokens=300
                )
                
                # Xử lý phản hồi
                generated_content = response.choices[0].message.content.strip()
                questions = [q.strip() for q in generated_content.split('\n') if q.strip()]
                
                # Lấy số lượng câu hỏi theo yêu cầu
                return questions[:max_questions]
            
            except Exception as e:
                self._handle_api_error(e, "generate suggested questions")
                
                # Nếu đây là lần thử cuối, trả về danh sách trống
                if attempt == self.retries - 1:
                    return []
    
    def transcribe_audio(self, audio_data: bytes) -> str:
        """Chuyển đổi âm thanh thành văn bản"""
        for attempt in range(self.retries):
            try:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=("audio.wav", audio_data),
                )
                return transcript.text
            
            except Exception as e:
                self._handle_api_error(e, "transcribe audio")
                
                # Nếu đây là lần thử cuối, trả về thông báo lỗi
                if attempt == self.retries - 1:
                    return "Không thể chuyển đổi âm thanh thành văn bản vào lúc này."
    
    def process_assistant_response(self, response: str) -> Dict[str, Any]:
        """Xử lý phản hồi của trợ lý để trích xuất các lệnh"""
        commands = {}
        
        try:
            # Xử lý lệnh thêm sự kiện
            if "##ADD_EVENT:" in response:
                cmd_start = response.index("##ADD_EVENT:") + len("##ADD_EVENT:")
                cmd_end = response.index("##", cmd_start)
                cmd = response[cmd_start:cmd_end].strip()
                
                try:
                    details = json.loads(cmd)
                    if isinstance(details, dict):
                        commands["ADD_EVENT"] = details
                except json.JSONDecodeError:
                    logger.error(f"Lỗi khi phân tích JSON cho ADD_EVENT: {cmd}")
            
            # Xử lý lệnh cập nhật sự kiện
            if "##UPDATE_EVENT:" in response:
                cmd_start = response.index("##UPDATE_EVENT:") + len("##UPDATE_EVENT:")
                cmd_end = response.index("##", cmd_start)
                cmd = response[cmd_start:cmd_end].strip()
                
                try:
                    details = json.loads(cmd)
                    if isinstance(details, dict):
                        commands["UPDATE_EVENT"] = details
                except json.JSONDecodeError:
                    logger.error(f"Lỗi khi phân tích JSON cho UPDATE_EVENT: {cmd}")
            
            # Xử lý lệnh xóa sự kiện
            if "##DELETE_EVENT:" in response:
                cmd_start = response.index("##DELETE_EVENT:") + len("##DELETE_EVENT:")
                cmd_end = response.index("##", cmd_start)
                cmd = response[cmd_start:cmd_end].strip()
                commands["DELETE_EVENT"] = cmd
            
            # Xử lý lệnh thêm thành viên gia đình
            if "##ADD_FAMILY_MEMBER:" in response:
                cmd_start = response.index("##ADD_FAMILY_MEMBER:") + len("##ADD_FAMILY_MEMBER:")
                cmd_end = response.index("##", cmd_start)
                cmd = response[cmd_start:cmd_end].strip()
                
                try:
                    details = json.loads(cmd)
                    if isinstance(details, dict):
                        commands["ADD_FAMILY_MEMBER"] = details
                except json.JSONDecodeError:
                    logger.error(f"Lỗi khi phân tích JSON cho ADD_FAMILY_MEMBER: {cmd}")
            
            # Xử lý lệnh cập nhật sở thích
            if "##UPDATE_PREFERENCE:" in response:
                cmd_start = response.index("##UPDATE_PREFERENCE:") + len("##UPDATE_PREFERENCE:")
                cmd_end = response.index("##", cmd_start)
                cmd = response[cmd_start:cmd_end].strip()
                
                try:
                    details = json.loads(cmd)
                    if isinstance(details, dict):
                        commands["UPDATE_PREFERENCE"] = details
                except json.JSONDecodeError:
                    logger.error(f"Lỗi khi phân tích JSON cho UPDATE_PREFERENCE: {cmd}")
            
            # Xử lý lệnh thêm ghi chú
            if "##ADD_NOTE:" in response:
                cmd_start = response.index("##ADD_NOTE:") + len("##ADD_NOTE:")
                cmd_end = response.index("##", cmd_start)
                cmd = response[cmd_start:cmd_end].strip()
                
                try:
                    details = json.loads(cmd)
                    if isinstance(details, dict):
                        commands["ADD_NOTE"] = details
                except json.JSONDecodeError:
                    logger.error(f"Lỗi khi phân tích JSON cho ADD_NOTE: {cmd}")
            
        except Exception as e:
            logger.error(f"Lỗi khi xử lý phản hồi của trợ lý: {e}")
        
        return commands
    
    def _limit_context_size(self, messages: List[Dict], max_tokens: int = 8000) -> List[Dict]:
        """Giới hạn kích thước context để tránh vượt quá token limit"""
        # Ước tính đơn giản: 4 ký tự ≈ 1 token, đây là ước tính thô
        token_count = 0
        result = []
        
        # Luôn giữ system message và tin nhắn cuối cùng của người dùng
        system_message = next((msg for msg in messages if msg["role"] == "system"), None)
        last_user_message = None
        
        for i in range(len(messages) - 1, -1, -1):
            if messages[i]["role"] == "user":
                last_user_message = messages[i]
                break
        
        # Bỏ qua system message và last_user_message trong vòng lặp chính
        filtered_messages = [msg for msg in messages if 
                            (msg != system_message and msg != last_user_message)]
        
        # Thêm system message vào đầu kết quả
        if system_message:
            content = system_message["content"]
            token_estimate = len(content) // 4
            token_count += token_estimate
            result.append(system_message)
        
        # Thêm các tin nhắn từ mới nhất đến cũ nhất
        for msg in reversed(filtered_messages):
            content = msg["content"]
            # Xử lý cả tin nhắn văn bản và hình ảnh
            if isinstance(content, list):
                text_contents = [item["text"] for item in content if item["type"] == "text"]
                content = "\n".join(text_contents)
            
            token_estimate = len(content) // 4
            
            # Nếu thêm tin nhắn này không vượt quá giới hạn
            if token_count + token_estimate <= max_tokens - 500:  # Dư 500 token cho tin nhắn cuối
                token_count += token_estimate
                result.insert(1, msg)  # Thêm sau system message
            else:
                # Dừng khi đạt giới hạn
                break
        
        # Thêm tin nhắn cuối cùng của người dùng
        if last_user_message:
            content = last_user_message["content"]
            if isinstance(content, list):
                text_contents = [item["text"] for item in content if item["type"] == "text"]
                content = "\n".join(text_contents)
            
            token_estimate = len(content) // 4
            
            # Cắt nội dung nếu quá dài
            if token_estimate > 2000:  # Giới hạn tin nhắn cuối cùng
                if isinstance(last_user_message["content"], list):
                    for i, item in enumerate(last_user_message["content"]):
                        if item["type"] == "text":
                            item["text"] = item["text"][:8000] + "..."  # ~2000 tokens
                else:
                    last_user_message["content"] = last_user_message["content"][:8000] + "..."
            
            result.append(last_user_message)
        
        return result