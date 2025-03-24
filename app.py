# app.py
"""
File chính của ứng dụng Trợ lý Gia đình
"""

import streamlit as st
from audio_recorder_streamlit import audio_recorder
import datetime
import os
import time
import json
import logging
from dotenv import load_dotenv
from PIL import Image
import asyncio

# Import các module tự tạo
from database.db_manager import DatabaseManager
from services.openai_service import OpenAIService
from services.tavily_service import TavilyService
from ui.components import UIComponents
from ui.styles import StyleManager
from utils import DateUtils, AsyncHelper, Logger, ConfigManager

# Tải biến môi trường
load_dotenv()

# Thiết lập logger
logger = Logger.setup(logfile="logs/family_assistant.log")

# Cấu trúc khởi tạo session state
def initialize_session_state():
    """Khởi tạo và đảm bảo tất cả các biến session state cần thiết tồn tại"""
    if "current_member" not in st.session_state:
        st.session_state.current_member = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "suggested_question" not in st.session_state:
        st.session_state.suggested_question = None
    if "process_suggested" not in st.session_state:
        st.session_state.process_suggested = False
    if "question_cache" not in st.session_state:
        st.session_state.question_cache = {}
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = None
    if "openai_service" not in st.session_state:
        st.session_state.openai_service = None
    if "tavily_service" not in st.session_state:
        st.session_state.tavily_service = None
    if "prev_speech_hash" not in st.session_state:
        st.session_state.prev_speech_hash = None
    if "editing_member" not in st.session_state:
        st.session_state.editing_member = None
    if "editing_event" not in st.session_state:
        st.session_state.editing_event = None
    if "last_api_key" not in st.session_state:
        st.session_state.last_api_key = ""


def create_system_prompt():
    """Tạo system prompt cho trợ lý AI"""
    if not st.session_state.db_manager:
        return ""
    
    family_data = st.session_state.db_manager.get_all_family_members()
    events_data = st.session_state.db_manager.get_all_events()
    notes_data = st.session_state.db_manager.get_all_notes()
    
    system_prompt = f"""
    Bạn là trợ lý gia đình thông minh tên là AIRA (AI Relationship Assistant). 
    Nhiệm vụ của bạn là giúp quản lý thông tin về các thành viên trong gia đình, 
    sở thích của họ, các sự kiện, ghi chú, và phân tích hình ảnh liên quan đến gia đình. 
    Khi người dùng yêu cầu, bạn phải thực hiện ngay các hành động sau:
    
    1. Thêm thông tin về thành viên gia đình (tên, tuổi, sở thích)
    2. Cập nhật sở thích của thành viên gia đình
    3. Thêm, cập nhật, hoặc xóa sự kiện
    4. Thêm ghi chú
    5. Phân tích hình ảnh người dùng đưa ra (món ăn, hoạt động gia đình, v.v.)
    6. Tìm kiếm thông tin thực tế khi được hỏi về tin tức, thời tiết, thể thao, và sự kiện hiện tại
    
    QUAN TRỌNG: Khi cần thực hiện các hành động trên, bạn PHẢI sử dụng đúng cú pháp lệnh đặc biệt này (người dùng sẽ không nhìn thấy):
    
    - Thêm thành viên: ##ADD_FAMILY_MEMBER:{{"name":"Tên","age":"Tuổi","preferences":{{"food":"Món ăn","hobby":"Sở thích","color":"Màu sắc"}}}}##
    - Cập nhật sở thích: ##UPDATE_PREFERENCE:{{"id":"id_thành_viên","key":"loại_sở_thích","value":"giá_trị"}}##
    - Thêm sự kiện: ##ADD_EVENT:{{"title":"Tiêu đề","date":"YYYY-MM-DD","time":"HH:MM","description":"Mô tả","participants":["Tên1","Tên2"]}}##
    - Cập nhật sự kiện: ##UPDATE_EVENT:{{"id":"id_sự_kiện","title":"Tiêu đề mới","date":"YYYY-MM-DD","time":"HH:MM","description":"Mô tả mới","participants":["Tên1","Tên2"]}}##
    - Xóa sự kiện: ##DELETE_EVENT:id_sự_kiện##
    - Thêm ghi chú: ##ADD_NOTE:{{"title":"Tiêu đề","content":"Nội dung","tags":["tag1","tag2"]}}##
    
    QUY TẮC THÊM SỰ KIỆN ĐƠN GIẢN:
    1. Khi được yêu cầu thêm sự kiện, hãy thực hiện NGAY LẬP TỨC mà không cần hỏi thêm thông tin không cần thiết.
    2. Khi người dùng nói "ngày mai" hoặc "tuần sau", hãy tự động tính toán ngày trong cú pháp YYYY-MM-DD.
    3. Nếu không có thời gian cụ thể, sử dụng thời gian mặc định là 19:00.
    4. Sử dụng mô tả ngắn gọn từ yêu cầu của người dùng.
    5. Chỉ hỏi thông tin nếu thực sự cần thiết, tránh nhiều bước xác nhận.
    6. Sau khi thêm/cập nhật/xóa sự kiện, tóm tắt ngắn gọn hành động đã thực hiện.
    
    TÌM KIẾM THÔNG TIN THỜI GIAN THỰC:
    1. Khi người dùng hỏi về tin tức, thời tiết, thể thao, sự kiện hiện tại, thông tin sản phẩm mới, hoặc bất kỳ dữ liệu cập nhật nào, hệ thống đã tự động tìm kiếm thông tin thực tế cho bạn.
    2. Hãy sử dụng thông tin tìm kiếm này để trả lời người dùng một cách chính xác và đầy đủ.
    3. Luôn đề cập đến nguồn thông tin khi sử dụng kết quả tìm kiếm.
    4. Nếu không có thông tin tìm kiếm, hãy trả lời dựa trên kiến thức của bạn và lưu ý rằng thông tin có thể không cập nhật.
    
    Hôm nay là {datetime.datetime.now().strftime("%d/%m/%Y")}.
    
    CẤU TRÚC JSON PHẢI CHÍNH XÁC như trên. Đảm bảo dùng dấu ngoặc kép cho cả keys và values. Đảm bảo các dấu ngoặc nhọn và vuông được đóng đúng cách.
    
    QUAN TRỌNG: Khi người dùng yêu cầu tạo sự kiện mới, hãy luôn sử dụng lệnh ##ADD_EVENT:...## trong phản hồi của bạn mà không cần quá nhiều bước xác nhận.
    
    Đối với hình ảnh:
    - Nếu người dùng gửi hình ảnh món ăn, hãy mô tả món ăn, và đề xuất cách nấu hoặc thông tin dinh dưỡng nếu phù hợp
    - Nếu là hình ảnh hoạt động gia đình, hãy mô tả hoạt động và đề xuất cách ghi nhớ khoảnh khắc đó
    - Với bất kỳ hình ảnh nào, hãy giúp người dùng liên kết nó với thành viên gia đình hoặc sự kiện nếu phù hợp
    
    PHONG CÁCH:
    1. Cá nhân hóa thông tin dựa trên người dùng hiện tại
    2. Giao tiếp thân thiện, ngắn gọn nhưng đầy đủ
    3. Sử dụng emoji phù hợp cho các chủ đề
    4. Luôn đề xuất các bước tiếp theo hoặc gợi ý liên quan
    """
    
    # Thêm thông tin về người dùng hiện tại
    if st.session_state.current_member and st.session_state.current_member in family_data:
        current_member = family_data[st.session_state.current_member]
        system_prompt += f"""
        THÔNG TIN NGƯỜI DÙNG HIỆN TẠI:
        Bạn đang trò chuyện với: {current_member.get('name')}
        Tuổi: {current_member.get('age', '')}
        Sở thích: {json.dumps(current_member.get('preferences', {}), ensure_ascii=False)}
        
        QUAN TRỌNG: Hãy điều chỉnh cách giao tiếp và đề xuất phù hợp với người dùng này. Các sự kiện và ghi chú sẽ được ghi danh nghĩa người này tạo.
        """
    
    # Thêm thông tin dữ liệu
    system_prompt += f"""
    Thông tin hiện tại về gia đình:
    {json.dumps(family_data, ensure_ascii=False, indent=2)}
    
    Sự kiện sắp tới:
    {json.dumps(events_data, ensure_ascii=False, indent=2)}
    
    Ghi chú:
    {json.dumps(notes_data, ensure_ascii=False, indent=2)}
    
    Hãy hiểu và đáp ứng nhu cầu của người dùng một cách tự nhiên và hữu ích. Không hiển thị các lệnh đặc biệt
    trong phản hồi của bạn, chỉ sử dụng chúng để thực hiện các hành động được yêu cầu.
    """
    
    return system_prompt


def process_commands(response: str, current_member: str = None):
    """Xử lý các lệnh từ phản hồi của trợ lý AI"""
    if not st.session_state.openai_service or not st.session_state.db_manager:
        return
    
    commands = st.session_state.openai_service.process_assistant_response(response)
    
    if "ADD_EVENT" in commands:
        details = commands["ADD_EVENT"]
        
        # Xử lý các từ ngữ tương đối về thời gian
        if details.get('date') and not details['date'][0].isdigit():
            relative_date = DateUtils.get_date_from_relative_term(details['date'])
            if relative_date:
                details['date'] = relative_date.strftime("%Y-%m-%d")
        
        # Thêm thông tin về người tạo sự kiện
        if current_member:
            details['created_by'] = current_member
        
        event_id = st.session_state.db_manager.add_event(details)
        if event_id:
            st.success(f"Đã thêm sự kiện: {details.get('title', '')}")
    
    if "UPDATE_EVENT" in commands:
        details = commands["UPDATE_EVENT"]
        
        # Xử lý các từ ngữ tương đối về thời gian
        if details.get('date') and not details['date'][0].isdigit():
            relative_date = DateUtils.get_date_from_relative_term(details['date'])
            if relative_date:
                details['date'] = relative_date.strftime("%Y-%m-%d")
        
        success = st.session_state.db_manager.update_event(details.get('id'), details)
        if success:
            st.success(f"Đã cập nhật sự kiện: {details.get('title', '')}")
    
    if "DELETE_EVENT" in commands:
        event_id = commands["DELETE_EVENT"]
        success = st.session_state.db_manager.delete_event(event_id)
        if success:
            st.success("Đã xóa sự kiện!")
    
    if "ADD_FAMILY_MEMBER" in commands:
        details = commands["ADD_FAMILY_MEMBER"]
        member_id = st.session_state.db_manager.add_family_member(details)
        if member_id:
            st.success(f"Đã thêm thành viên: {details.get('name', '')}")
    
    if "UPDATE_PREFERENCE" in commands:
        details = commands["UPDATE_PREFERENCE"]
        member_id = details.get("id")
        key = details.get("key")
        value = details.get("value")
        
        success = st.session_state.db_manager.update_preference(member_id, key, value)
        if success:
            st.success("Đã cập nhật sở thích!")
    
    if "ADD_NOTE" in commands:
        details = commands["ADD_NOTE"]
        
        # Thêm thông tin về người tạo ghi chú
        if current_member:
            details['created_by'] = current_member
        
        note_id = st.session_state.db_manager.add_note(details)
        if note_id:
            st.success("Đã thêm ghi chú!")


async def handle_assistant_response(query: str):
    """Xử lý phản hồi từ trợ lý AI"""
    if not st.session_state.openai_service:
        return
    
    placeholder = st.empty()
    tavily_info = None
    
    # Đệm tin nhắn người dùng vào danh sách tin nhắn
    st.session_state.messages.append({
        "role": "user", 
        "content": [{
            "type": "text",
            "text": query
        }]
    })
    
    # Kiểm tra xem có cần tìm kiếm thông tin thực tế không
    if st.session_state.tavily_service:
        need_search, search_query = st.session_state.openai_service.detect_search_intent(query)
        
        if need_search:
            placeholder.info(f"🔍 Đang tìm kiếm thông tin về: '{search_query}'...")
            tavily_info = await st.session_state.tavily_service.search_and_summarize(search_query)
    
    # Tạo system prompt
    system_prompt = create_system_prompt()
    
    # Thêm thông tin tìm kiếm vào system prompt nếu có
    if tavily_info:
        search_info = f"""
        THÔNG TIN TÌM KIẾM:
        Câu hỏi: {query}
        
        Kết quả:
        {tavily_info}
        
        Hãy sử dụng thông tin này để trả lời câu hỏi của người dùng một cách đầy đủ và chính xác. Đảm bảo đề cập đến nguồn thông tin.
        """
        system_prompt += "\n\n" + search_info
        placeholder.empty()
    
    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""
        
        # Stream phản hồi từ OpenAI
        for chunk in st.session_state.openai_service.stream_chat_completion(
            st.session_state.messages,
            system_prompt=system_prompt
        ):
            full_response += chunk
            response_container.markdown(full_response + "▌")
        
        # Hiển thị phản hồi cuối cùng
        response_container.markdown(full_response)
    
    # Xử lý các lệnh trong phản hồi
    process_commands(full_response, st.session_state.current_member)
    
    # Thêm phản hồi vào danh sách tin nhắn
    st.session_state.messages.append({
        "role": "assistant", 
        "content": [{
            "type": "text",
            "text": full_response
        }]
    })
    
    # Lưu lịch sử trò chuyện nếu đang chat với một thành viên cụ thể
    if st.session_state.current_member and st.session_state.db_manager:
        summary = await st.session_state.openai_service.generate_chat_summary(st.session_state.messages)
        st.session_state.db_manager.save_chat_history(
            st.session_state.current_member,
            st.session_state.messages,
            summary
        )


def handle_suggested_question(question: str):
    """Xử lý khi người dùng chọn câu hỏi gợi ý"""
    st.session_state.suggested_question = question
    st.session_state.process_suggested = True
    
    # Hiển thị tin nhắn người dùng
    with st.chat_message("user"):
        st.markdown(question)
    
    # Xử lý phản hồi từ trợ lý
    AsyncHelper.run_async(handle_assistant_response)(question)
    
    # Đặt lại trạng thái
    st.session_state.suggested_question = None
    st.session_state.process_suggested = False


def add_image_to_messages():
    """Thêm hình ảnh vào tin nhắn"""
    if st.session_state.uploaded_img is not None:
        img_type = st.session_state.uploaded_img.type
        raw_img = Image.open(st.session_state.uploaded_img)
        img = UIComponents.get_image_base64(raw_img)
        
        # Thêm hình ảnh vào tin nhắn
        st.session_state.messages.append({
            "role": "user", 
            "content": [{
                "type": "image_url",
                "image_url": {"url": f"data:{img_type};base64,{img}"}
            }]
        })
        
        # Hiển thị hình ảnh
        with st.chat_message("user"):
            st.image(raw_img)
        
        # Xử lý phản hồi từ trợ lý
        AsyncHelper.run_async(handle_assistant_response)("Hãy phân tích hình ảnh này.")
        
        # Xóa hình ảnh đã tải lên để tránh xử lý lại
        st.session_state.uploaded_img = None
        st.rerun()
    
    elif "camera_img" in st.session_state and st.session_state.camera_img is not None:
        raw_img = Image.open(st.session_state.camera_img)
        img = UIComponents.get_image_base64(raw_img)
        
        # Thêm hình ảnh vào tin nhắn
        st.session_state.messages.append({
            "role": "user", 
            "content": [{
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img}"}
            }]
        })
        
        # Hiển thị hình ảnh
        with st.chat_message("user"):
            st.image(raw_img)
        
        # Xử lý phản hồi từ trợ lý
        AsyncHelper.run_async(handle_assistant_response)("Hãy phân tích hình ảnh này.")
        
        # Xóa hình ảnh đã chụp để tránh xử lý lại
        st.session_state.camera_img = None
        st.rerun()


def reset_conversation():
    """Xóa lịch sử trò chuyện hiện tại"""
    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        # Trước khi xóa, lưu lịch sử trò chuyện nếu đang trò chuyện với một thành viên
        if (st.session_state.current_member and 
            st.session_state.openai_service and 
            st.session_state.db_manager):
            
            summary = AsyncHelper.run_async(
                st.session_state.openai_service.generate_chat_summary
            )(st.session_state.messages)
            
            st.session_state.db_manager.save_chat_history(
                st.session_state.current_member,
                st.session_state.messages,
                summary
            )
        
        # Xóa tin nhắn
        st.session_state.messages = []


def create_suggested_questions():
    """Tạo danh sách câu hỏi gợi ý dựa trên người dùng hiện tại"""
    if not st.session_state.openai_service or not st.session_state.db_manager:
        return UIComponents.fallback_suggested_questions()
    
    # Cache key cho câu hỏi gợi ý
    cache_key = f"suggested_questions_{st.session_state.current_member}_{datetime.datetime.now().strftime('%Y-%m-%d_%H')}"
    
    # Tạo câu hỏi gợi ý nếu chưa có trong cache
    if "question_cache" not in st.session_state or cache_key not in st.session_state.question_cache:
        # Tạo câu hỏi gợi ý dựa trên người dùng hiện tại
        member_info = {}
        if st.session_state.current_member:
            member = st.session_state.db_manager.get_family_member(st.session_state.current_member)
            if member:
                member_info = {
                    "name": member.get("name", ""),
                    "age": member.get("age", ""),
                    "preferences": member.get("preferences", {})
                }
        
        # Lấy các sự kiện sắp tới
        all_events = st.session_state.db_manager.get_all_events()
        upcoming_events = DateUtils.get_upcoming_events(all_events, 14)
        
        # Lấy chủ đề từ lịch sử trò chuyện gần đây
        recent_topics = []
        if st.session_state.current_member:
            chat_history = st.session_state.db_manager.get_chat_history(st.session_state.current_member, 3)
            for chat in chat_history:
                summary = chat.get("summary", "")
                if summary:
                    recent_topics.append(summary)
        
        try:
            # Tạo câu hỏi gợi ý
            suggested_questions = AsyncHelper.run_async(
                st.session_state.openai_service.generate_dynamic_suggested_questions
            )(member_info, upcoming_events, recent_topics, 5)
            
            # Nếu không có câu hỏi từ OpenAI, sử dụng phương pháp dự phòng
            if not suggested_questions:
                suggested_questions = UIComponents.fallback_suggested_questions(
                    st.session_state.current_member,
                    5
                )
            
            # Lưu vào cache
            if "question_cache" not in st.session_state:
                st.session_state.question_cache = {}
            
            st.session_state.question_cache[cache_key] = suggested_questions
            return suggested_questions
        
        except Exception as e:
            logger.error(f"Lỗi khi tạo câu hỏi gợi ý: {e}")
            fallback_questions = UIComponents.fallback_suggested_questions(
                st.session_state.current_member,
                5
            )
            st.session_state.question_cache[cache_key] = fallback_questions
            return fallback_questions
    else:
        # Lấy câu hỏi từ cache
        return st.session_state.question_cache[cache_key]


def api_key_changed(openai_api_key):
    """Kiểm tra xem API key đã thay đổi chưa"""
    return openai_api_key != st.session_state.last_api_key


def main():
    # --- Cấu hình trang ---
    st.set_page_config(
        page_title="Trợ lý Gia đình",
        page_icon="👨‍👩‍👧‍👦",
        layout="centered",
        initial_sidebar_state="expanded",
    )
    
    # Áp dụng CSS tùy chỉnh
    StyleManager.apply_all_styles()
    
    # Khởi tạo session state
    initialize_session_state()
    
    # --- Tiêu đề ---
    st.markdown("<h1 class='main-header'>👨‍👩‍👧‍👦 <i>Trợ lý Gia đình</i> 💬</h1>", unsafe_allow_html=True)
    
    # --- Thanh bên ---
    with st.sidebar:
        # Tải secrets
        secrets = ConfigManager.load_secrets(st.secrets)
        default_openai_api_key = secrets.get("openai_api_key", "")
        default_tavily_api_key = secrets.get("tavily_api_key", "")
        default_db_path = secrets.get("db_path", "family_assistant.db")
        
        # API Keys
        with st.popover("🔐 API Keys"):
            openai_api_key = st.text_input(
                "OpenAI API Key:", 
                value=default_openai_api_key, 
                type="password",
                key="openai_api_key"
            )
            tavily_api_key = st.text_input(
                "Tavily API Key:", 
                value=default_tavily_api_key, 
                type="password",
                key="tavily_api_key"
            )
            
            if tavily_api_key:
                st.success("✅ Tính năng tìm kiếm thời gian thực đã được kích hoạt!")
            else:
                st.warning("⚠️ Vui lòng nhập Tavily API Key để kích hoạt tính năng tìm kiếm thông tin thời gian thực.")
        
        # Khởi tạo database manager (nếu chưa có)
        if st.session_state.db_manager is None:
            st.session_state.db_manager = DatabaseManager(default_db_path)
        
        # Khởi tạo dịch vụ OpenAI nếu cần
        if ConfigManager.validate_api_key(openai_api_key) and api_key_changed(openai_api_key):
            st.session_state.openai_service = OpenAIService(openai_api_key)
            st.session_state.last_api_key = openai_api_key
            
            # Nếu có cả Tavily API key, khởi tạo dịch vụ Tavily
            if tavily_api_key:
                st.session_state.tavily_service = TavilyService(
                    tavily_api_key, 
                    st.session_state.openai_service
                )
            else:
                st.session_state.tavily_service = None
        
        # Chọn người dùng hiện tại
        st.write("## 👤 Chọn người dùng")
        
        # Tạo danh sách tên thành viên và ID
        family_data = st.session_state.db_manager.get_all_family_members()
        member_options = {"Chung (Không cá nhân hóa)": None}
        for member_id, member in family_data.items():
            member_options[member["name"]] = member_id
        
        # Dropdown chọn người dùng
        selected_member_name = st.selectbox(
            "Bạn đang trò chuyện với tư cách ai?",
            options=list(member_options.keys()),
            index=0
        )
        
        # Cập nhật người dùng hiện tại
        new_member_id = member_options[selected_member_name]
        
        # Nếu người dùng thay đổi, cập nhật session state và khởi tạo lại tin nhắn
        if new_member_id != st.session_state.current_member:
            st.session_state.current_member = new_member_id
            st.session_state.messages = []
            st.rerun()
        
        # Hiển thị thông tin người dùng hiện tại
        if st.session_state.current_member:
            member = family_data[st.session_state.current_member]
            st.info(f"Đang trò chuyện với tư cách: **{member.get('name')}**")
            
            # Hiển thị lịch sử trò chuyện trước đó
            chat_history = st.session_state.db_manager.get_chat_history(st.session_state.current_member)
            if chat_history:
                with st.expander("📜 Lịch sử trò chuyện trước đó"):
                    for idx, history in enumerate(chat_history):
                        st.write(f"**{history.get('timestamp')}**")
                        st.write(f"*{history.get('summary', 'Không có tóm tắt')}*")
                        
                        # Nút để tải lại cuộc trò chuyện cũ
                        if st.button(f"Tải lại cuộc trò chuyện này", key=f"load_chat_{idx}"):
                            st.session_state.messages = history.get('messages', [])
                            st.rerun()
                        st.divider()
        
        # Quản lý thành viên gia đình
        UIComponents.family_management_ui(st.session_state.db_manager)
        
        st.divider()
        
        # Quản lý sự kiện
        UIComponents.events_management_ui(
            st.session_state.db_manager,
            st.session_state.current_member
        )
        
        st.divider()
        
        # Quản lý ghi chú
        UIComponents.notes_management_ui(
            st.session_state.db_manager,
            st.session_state.current_member
        )
        
        st.divider()
        
        # Phần tìm kiếm và truy vấn thông tin thực tế
        if st.session_state.tavily_service:
            with st.expander("🔍 Tìm kiếm thông tin"):
                st.write("**Tìm kiếm thông tin thực tế**")
                st.info("✅ Trợ lý sẽ tự động tìm kiếm thông tin khi bạn hỏi về tin tức, thời tiết, thể thao, v.v.")
                
                with st.form("manual_search_form"):
                    search_query = st.text_input("Nhập từ khóa tìm kiếm:")
                    search_button = st.form_submit_button("🔍 Tìm kiếm")
                    
                    if search_button and search_query:
                        with st.spinner("Đang tìm kiếm..."):
                            search_result = AsyncHelper.run_async(
                                st.session_state.tavily_service.search_and_summarize
                            )(search_query)
                            st.write("### Kết quả tìm kiếm")
                            st.write(search_result)
        
        # Nút làm mới câu hỏi gợi ý
        if st.button("🔄 Làm mới câu hỏi gợi ý"):
            # Xóa cache để tạo câu hỏi mới
            if "question_cache" in st.session_state:
                st.session_state.question_cache = {}
            st.rerun()
        
        # Nút xóa lịch sử trò chuyện
        st.button(
            "🗑️ Xóa lịch sử trò chuyện", 
            on_click=reset_conversation,
        )
    
    # --- Nội dung chính ---
    # Kiểm tra nếu người dùng đã nhập OpenAI API Key, nếu không thì hiển thị cảnh báo
    if not ConfigManager.validate_api_key(openai_api_key):
        st.write("#")
        st.warning("⬅️ Vui lòng nhập OpenAI API Key để tiếp tục...")
        UIComponents.display_welcome()
    
    else:
        # Hiển thị các tin nhắn trước đó nếu có
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                for content in message["content"]:
                    if content["type"] == "text":
                        st.write(content["text"])
                    elif content["type"] == "image_url":      
                        st.image(content["image_url"]["url"])
        
        # Hiển thị banner thông tin người dùng hiện tại
        if st.session_state.current_member and st.session_state.current_member in family_data:
            member_name = family_data[st.session_state.current_member].get("name", "")
            st.info(f"👤 Đang trò chuyện với tư cách: **{member_name}**")
        elif st.session_state.current_member is None:
            st.info("👨‍👩‍👧‍👦 Đang trò chuyện trong chế độ chung")
        
        # Hiển thị banner thông tin về tìm kiếm
        if st.session_state.tavily_service:
            st.success("🔍 Trợ lý có khả năng tìm kiếm thông tin thời gian thực! Hỏi về tin tức, thể thao, thời tiết, v.v.")
        
        # Kiểm tra và xử lý câu hỏi gợi ý đã chọn
        if st.session_state.process_suggested and st.session_state.suggested_question:
            # Xử lý bằng hàm đã định nghĩa
            handle_suggested_question(st.session_state.suggested_question)
            
            # Rerun để cập nhật giao diện
            st.rerun()
        
        # Tạo và hiển thị câu hỏi gợi ý
        if st.session_state.openai_service:
            suggested_questions = create_suggested_questions()
            
            # Hiển thị câu hỏi gợi ý
            UIComponents.display_suggested_questions(
                suggested_questions,
                handle_suggested_question
            )
        
        # Thêm chức năng hình ảnh
        with st.sidebar:
            st.divider()
            st.write("## 🖼️ Hình ảnh")
            st.write("Thêm hình ảnh để hỏi trợ lý về món ăn, hoạt động gia đình...")
            
            # UI cho upload hình ảnh và chụp ảnh
            cols_img = st.columns(2)
            with cols_img[0]:
                with st.popover("📁 Tải lên"):
                    st.file_uploader(
                        "Tải lên hình ảnh:", 
                        type=["png", "jpg", "jpeg"],
                        accept_multiple_files=False,
                        key="uploaded_img",
                        on_change=add_image_to_messages,
                    )
            
            with cols_img[1]:
                with st.popover("📸 Camera"):
                    activate_camera = st.checkbox("Bật camera")
                    if activate_camera:
                        st.camera_input(
                            "Chụp ảnh", 
                            key="camera_img",
                            on_change=add_image_to_messages,
                        )
        
        # Ghi âm
        st.write("🎤 Bạn có thể nói:")
        speech_input = audio_recorder("Nhấn để nói", icon_size="2x", neutral_color="#6ca395")
        if speech_input and st.session_state.prev_speech_hash != hash(speech_input):
            st.session_state.prev_speech_hash = hash(speech_input)
            
            if st.session_state.openai_service:
                transcript = st.session_state.openai_service.transcribe_audio(speech_input)
                
                # Hiển thị tin nhắn người dùng
                with st.chat_message("user"):
                    st.markdown(transcript)
                
                # Xử lý phản hồi từ trợ lý
                AsyncHelper.run_async(handle_assistant_response)(transcript)
        
        # Chat input
        if prompt := st.chat_input("Xin chào! Tôi có thể giúp gì cho gia đình bạn?"):
            # Hiển thị tin nhắn người dùng
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Xử lý phản hồi từ trợ lý
            AsyncHelper.run_async(handle_assistant_response)(prompt)


# Nếu là file chính
if __name__ == "__main__":
    main()