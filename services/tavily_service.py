import requests
import logging
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger('family_assistant')

class TavilyService:
    def __init__(self, api_key: str, openai_service: Any):
        """Khởi tạo dịch vụ Tavily"""
        self.api_key = api_key
        self.openai_service = openai_service
        self.search_url = "https://api.tavily.com/search"
        self.extract_url = "https://api.tavily.com/extract"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.retries = 3
        self.retry_delay = 1
    
    async def _async_request(self, url: str, data: Dict, attempt: int = 0) -> Optional[Dict]:
        """Thực hiện HTTP request bất đồng bộ với retry"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Lỗi API Tavily: {response.status} - {error_text}")
                        
                        # Retry nếu cần
                        if attempt < self.retries:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            return await self._async_request(url, data, attempt + 1)
                        return None
        except Exception as e:
            logger.error(f"Lỗi khi gọi Tavily API: {e}")
            
            # Retry nếu cần
            if attempt < self.retries:
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
                return await self._async_request(url, data, attempt + 1)
            return None
    
    async def search(self, 
                     query: str, 
                     search_depth: str = "advanced", 
                     max_results: int = 3, 
                     include_domains: Optional[List[str]] = None, 
                     exclude_domains: Optional[List[str]] = None) -> Optional[Dict]:
        """Tìm kiếm bất đồng bộ với Tavily"""
        data = {
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results
        }
        
        if include_domains:
            data["include_domains"] = include_domains
        
        if exclude_domains:
            data["exclude_domains"] = exclude_domains
        
        return await self._async_request(self.search_url, data)
    
    async def extract(self, 
                      url: str, 
                      include_images: bool = False, 
                      extract_depth: str = "basic") -> Optional[Dict]:
        """Trích xuất nội dung bất đồng bộ từ URL với Tavily"""
        data = {
            "urls": url if isinstance(url, list) else [url],
            "include_images": include_images,
            "extract_depth": extract_depth
        }
        
        return await self._async_request(self.extract_url, data)
    
    async def search_and_summarize(self, query: str) -> str:
        """Tìm kiếm và tổng hợp thông tin từ kết quả tìm kiếm"""
        try:
            # Thực hiện tìm kiếm với Tavily
            search_results = await self.search(query)
            
            if not search_results or "results" not in search_results:
                return "Không tìm thấy kết quả nào."
            
            # Trích xuất thông tin từ top kết quả
            urls_to_extract = [result["url"] for result in search_results["results"][:3]]
            extracted_contents = []
            
            # Trích xuất nội dung bất đồng bộ từ nhiều URL
            extraction_tasks = [self.extract(url) for url in urls_to_extract]
            extract_results = await asyncio.gather(*extraction_tasks)
            
            for i, extract_result in enumerate(extract_results):
                if extract_result and "results" in extract_result and len(extract_result["results"]) > 0:
                    content = extract_result["results"][0].get("raw_content", "")
                    # Giới hạn độ dài nội dung để tránh token quá nhiều
                    if len(content) > 8000:
                        content = content[:8000] + "..."
                    extracted_contents.append({
                        "url": urls_to_extract[i],
                        "content": content
                    })
            
            if not extracted_contents:
                return "Không thể trích xuất nội dung từ các kết quả tìm kiếm."
            
            # Tổng hợp thông tin sử dụng OpenAI
            # Chuẩn bị prompt cho việc tổng hợp
            prompt = f"""
            Dưới đây là các nội dung trích xuất từ internet liên quan đến câu hỏi: "{query}"
            
            {json.dumps(extracted_contents, ensure_ascii=False)}
            
            Hãy tổng hợp thông tin từ các nguồn trên để trả lời câu hỏi một cách đầy đủ và chính xác.
            Hãy trình bày thông tin một cách rõ ràng, có cấu trúc.
            Nếu thông tin từ các nguồn khác nhau mâu thuẫn, hãy đề cập đến điều đó.
            Hãy ghi rõ nguồn thông tin (URL) ở cuối mỗi phần thông tin.
            """
            
            # Gọi API OpenAI để tổng hợp thông tin
            # Sử dụng phương thức đồng bộ vì chúng ta cần kết quả ngay
            response = self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": "Bạn là trợ lý tổng hợp thông tin. Nhiệm vụ của bạn là tổng hợp thông tin từ nhiều nguồn để cung cấp câu trả lời đầy đủ, chính xác và có cấu trúc."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            summarized_info = response.choices[0].message.content
            
            # Thêm thông báo về nguồn
            sources_info = "\n\n**Nguồn thông tin:**\n" + "\n".join([f"- {result['url']}" for result in search_results["results"][:3]])
            
            return f"{summarized_info}\n{sources_info}"
        
        except Exception as e:
            logger.error(f"Lỗi trong quá trình tìm kiếm và tổng hợp: {e}")
            return f"Có lỗi xảy ra trong quá trình tìm kiếm và tổng hợp thông tin: {str(e)}"