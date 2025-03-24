import streamlit as st
import datetime
import json
import base64
from io import BytesIO
from PIL import Image
from typing import Dict, List, Optional, Any, Union, Callable
import hashlib
import random

class UIComponents:
    @staticmethod
    def get_image_base64(image_raw: Image.Image) -> str:
        """Chuyển đổi hình ảnh sang base64"""
        buffered = BytesIO()
        image_raw.save(buffered, format=image_raw.format)
        img_byte = buffered.getvalue()
        return base64.b64encode(img_byte).decode('utf-8')
    
    @staticmethod
    def apply_custom_css():
        """Áp dụng CSS tùy chỉnh cho ứng dụng"""
        st.markdown("""
        <style>
        .main-header {
            text-align: center;
            color: #6ca395;
            font-style: italic;
            margin-bottom: 20px;
        }
        
        .suggestion-container {
            margin-top: 20px;
            margin-bottom: 20px;
        }
        
        .suggestion-title {
            font-size: 16px;
            font-weight: 500;
            margin-bottom: 10px;
            color: #555;
        }
        
        .suggestion-box {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .stButton>button {
            border-radius: 20px;
            border: 1px solid #e0e0e0;
            background-color: #f8f9fa;
            transition: all 0.3s;
        }
        
        .stButton>button:hover {
            background-color: #e8f0fe;
            border-color: #6ca395;
        }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def display_welcome():
        """Hiển thị thông báo chào mừng"""
        st.write("""
        ### Chào mừng bạn đến với Trợ lý Gia đình!
        
        Ứng dụng này giúp bạn:
        
        - 👨‍👩‍👧‍👦 Lưu trữ thông tin và sở thích của các thành viên trong gia đình
        - 📅 Quản lý các sự kiện gia đình
        - 📝 Tạo và lưu trữ các ghi chú
        - 💬 Trò chuyện với trợ lý AI để cập nhật thông tin
        - 👤 Cá nhân hóa trò chuyện theo từng thành viên
        - 🔍 Tìm kiếm thông tin thời gian thực
        - 📜 Lưu lịch sử trò chuyện và tạo tóm tắt tự động
        
        Để bắt đầu, hãy nhập OpenAI API Key của bạn ở thanh bên trái.
        """)
    
    @staticmethod
    def display_suggested_questions(questions: List[str], 
                                   on_question_click: Callable[[str], None]):
        """Hiển thị câu hỏi gợi ý"""
        st.markdown('<div class="suggestion-container">', unsafe_allow_html=True)
        st.markdown('<div class="suggestion-title">💡 Câu hỏi gợi ý cho bạn:</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="suggestion-box">', unsafe_allow_html=True)
        
        # Chia câu hỏi thành 2 dòng
        row1, row2 = st.columns([1, 1])
        
        with row1:
            for i, question in enumerate(questions[:3]):
                if st.button(
                    question,
                    key=f"suggest_q_{i}",
                    use_container_width=True
                ):
                    on_question_click(question)
        
        with row2:
            for i, question in enumerate(questions[3:], 3):
                if st.button(
                    question,
                    key=f"suggest_q_{i}",
                    use_container_width=True
                ):
                    on_question_click(question)
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    @staticmethod
    def family_management_ui(db_manager: Any):
        """UI cho phần quản lý thành viên gia đình"""
        st.write("## Thông tin Gia đình")
        
        # Phần thêm thành viên gia đình
        with st.expander("➕ Thêm thành viên gia đình"):
            with st.form("add_family_form"):
                member_name = st.text_input("Tên")
                member_age = st.text_input("Tuổi")
                st.write("Sở thích:")
                food_pref = st.text_input("Món ăn yêu thích")
                hobby_pref = st.text_input("Sở thích")
                color_pref = st.text_input("Màu yêu thích")
                
                add_member_submitted = st.form_submit_button("Thêm")
                
                if add_member_submitted and member_name:
                    details = {
                        "name": member_name,
                        "age": member_age,
                        "preferences": {
                            "food": food_pref,
                            "hobby": hobby_pref,
                            "color": color_pref
                        }
                    }
                    db_manager.add_family_member(details)
                    st.success(f"Đã thêm {member_name} vào gia đình!")
        
        # Xem và chỉnh sửa thành viên gia đình
        with st.expander("👥 Thành viên gia đình"):
            family_data = db_manager.get_all_family_members()
            
            if not family_data:
                st.write("Chưa có thành viên nào trong gia đình")
            else:
                for member_id, member in family_data.items():
                    st.write(f"**{member['name']}** ({member.get('age', '')})")
                    
                    # Hiển thị sở thích
                    if "preferences" in member:
                        for pref_key, pref_value in member["preferences"].items():
                            if pref_value:
                                st.write(f"- {pref_key.capitalize()}: {pref_value}")
                    
                    # Nút chỉnh sửa cho mỗi thành viên
                    if st.button(f"Chỉnh sửa {member['name']}", key=f"edit_{member_id}"):
                        st.session_state.editing_member = member_id
        
        # Form chỉnh sửa thành viên (xuất hiện khi đang chỉnh sửa)
        if "editing_member" in st.session_state and st.session_state.editing_member:
            member_id = st.session_state.editing_member
            member = db_manager.get_family_member(member_id)
            
            if member:
                with st.form(f"edit_member_{member_id}"):
                    st.write(f"Chỉnh sửa: {member.get('name', 'Không tên')}")
                    
                    # Các trường chỉnh sửa
                    new_name = st.text_input("Tên", member.get("name", ""))
                    new_age = st.text_input("Tuổi", member.get("age", ""))
                    
                    # Sở thích
                    st.write("Sở thích:")
                    prefs = member.get("preferences", {})
                    new_food = st.text_input("Món ăn yêu thích", prefs.get("food", ""))
                    new_hobby = st.text_input("Sở thích", prefs.get("hobby", ""))
                    new_color = st.text_input("Màu yêu thích", prefs.get("color", ""))
                    
                    save_edits = st.form_submit_button("Lưu")
                    cancel_edits = st.form_submit_button("Hủy")
                    
                    if save_edits:
                        updated_details = {
                            "name": new_name,
                            "age": new_age,
                            "preferences": {
                                "food": new_food,
                                "hobby": new_hobby,
                                "color": new_color
                            }
                        }
                        db_manager.update_family_member(member_id, updated_details)
                        st.session_state.editing_member = None
                        st.success("Đã cập nhật thông tin!")
                        st.rerun()
                    
                    if cancel_edits:
                        st.session_state.editing_member = None
                        st.rerun()
            else:
                st.error(f"Không tìm thấy thành viên với ID: {member_id}")
                st.session_state.editing_member = None
    
    @staticmethod
    def events_management_ui(db_manager: Any, current_member: Optional[str] = None):
        """UI cho phần quản lý sự kiện"""
        st.write("## Sự kiện")
        
        # Phần thêm sự kiện
        with st.expander("📅 Thêm sự kiện"):
            with st.form("add_event_form"):
                event_title = st.text_input("Tiêu đề sự kiện")
                event_date = st.date_input("Ngày")
                event_time = st.time_input("Giờ")
                event_desc = st.text_area("Mô tả")
                
                # Multi-select cho người tham gia
                family_data = db_manager.get_all_family_members()
                member_names = [member.get("name", "") for member_id, member in family_data.items()]
                participants = st.multiselect("Người tham gia", member_names)
                
                add_event_submitted = st.form_submit_button("Thêm sự kiện")
                
                if add_event_submitted and event_title:
                    details = {
                        "title": event_title,
                        "date": event_date.strftime("%Y-%m-%d"),
                        "time": event_time.strftime("%H:%M"),
                        "description": event_desc,
                        "participants": participants,
                        "created_by": current_member
                    }
                    db_manager.add_event(details)
                    st.success(f"Đã thêm sự kiện: {event_title}!")
        
        # Xem sự kiện
        with st.expander("📆 Sự kiện"):
            # Phần hiển thị chế độ lọc
            mode = st.radio(
                "Chế độ hiển thị:",
                ["Tất cả sự kiện", "Sự kiện của tôi", "Sự kiện tôi tham gia"],
                horizontal=True,
                disabled=not current_member
            )
            
            # Lấy tất cả sự kiện và lọc theo chế độ
            events_data = db_manager.get_all_events()
            display_events = {}
            
            if current_member:
                member = db_manager.get_family_member(current_member)
                current_member_name = member.get("name", "") if member else ""
                
                if mode == "Sự kiện của tôi":
                    display_events = {
                        event_id: event for event_id, event in events_data.items()
                        if event.get("created_by") == current_member
                    }
                elif mode == "Sự kiện tôi tham gia" and current_member_name:
                    display_events = {
                        event_id: event for event_id, event in events_data.items()
                        if current_member_name in event.get("participants", [])
                    }
                else:
                    display_events = events_data
            else:
                display_events = events_data
            
            # Sắp xếp sự kiện theo ngày
            try:
                sorted_events = sorted(
                    display_events.items(),
                    key=lambda x: (x[1].get("date", ""), x[1].get("time", ""))
                )
            except Exception as e:
                st.error(f"Lỗi khi sắp xếp sự kiện: {e}")
                sorted_events = []
            
            if not sorted_events:
                st.write("Không có sự kiện nào")
            
            for event_id, event in sorted_events:
                st.write(f"**{event.get('title', 'Sự kiện không tiêu đề')}**")
                st.write(f"📅 {event.get('date', 'Chưa đặt ngày')} | ⏰ {event.get('time', 'Chưa đặt giờ')}")
                
                if event.get('description'):
                    st.write(event.get('description', ''))
                
                if event.get('participants'):
                    st.write(f"👥 {', '.join(event.get('participants', []))}")
                
                # Hiển thị người tạo
                if event.get('created_by'):
                    creator = db_manager.get_family_member(event.get('created_by'))
                    creator_name = creator.get("name", "") if creator else ""
                    if creator_name:
                        st.write(f"👤 Tạo bởi: {creator_name}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Chỉnh sửa", key=f"edit_event_{event_id}"):
                        st.session_state.editing_event = event_id
                with col2:
                    if st.button(f"Xóa", key=f"delete_event_{event_id}"):
                        db_manager.delete_event(event_id)
                        st.success(f"Đã xóa sự kiện!")
                        st.rerun()
                st.divider()
        
        # Form chỉnh sửa sự kiện (xuất hiện khi đang chỉnh sửa)
        if "editing_event" in st.session_state and st.session_state.editing_event:
            event_id = st.session_state.editing_event
            events_data = db_manager.get_all_events()
            
            if event_id in events_data:
                event = events_data[event_id]
                
                with st.form(f"edit_event_{event_id}"):
                    st.write(f"Chỉnh sửa sự kiện: {event['title']}")
                    
                    # Chuyển đổi định dạng ngày
                    try:
                        event_date_obj = datetime.datetime.strptime(event["date"], "%Y-%m-%d").date()
                    except:
                        event_date_obj = datetime.date.today()
                    
                    # Chuyển đổi định dạng giờ
                    try:
                        event_time_obj = datetime.datetime.strptime(event["time"], "%H:%M").time()
                    except:
                        event_time_obj = datetime.datetime.now().time()
                    
                    # Các trường chỉnh sửa
                    new_title = st.text_input("Tiêu đề", event["title"])
                    new_date = st.date_input("Ngày", event_date_obj)
                    new_time = st.time_input("Giờ", event_time_obj)
                    new_desc = st.text_area("Mô tả", event["description"])
                    
                    # Multi-select cho người tham gia
                    family_data = db_manager.get_all_family_members()
                    member_names = [member.get("name", "") for member_id, member in family_data.items()]
                    new_participants = st.multiselect("Người tham gia", member_names, default=event.get("participants", []))
                    
                    save_event_edits = st.form_submit_button("Lưu")
                    cancel_event_edits = st.form_submit_button("Hủy")
                    
                    if save_event_edits:
                        updated_details = {
                            "title": new_title,
                            "date": new_date.strftime("%Y-%m-%d"),
                            "time": new_time.strftime("%H:%M"),
                            "description": new_desc,
                            "participants": new_participants
                        }
                        db_manager.update_event(event_id, updated_details)
                        st.session_state.editing_event = None
                        st.success("Đã cập nhật sự kiện!")
                        st.rerun()
                    
                    if cancel_event_edits:
                        st.session_state.editing_event = None
                        st.rerun()
            else:
                st.error(f"Không tìm thấy sự kiện với ID: {event_id}")
                st.session_state.editing_event = None
    
    @staticmethod
    def notes_management_ui(db_manager: Any, current_member: Optional[str] = None):
        """UI cho phần quản lý ghi chú"""
        st.write("## Ghi chú")
        
        # Phần thêm ghi chú
        with st.expander("📝 Thêm ghi chú"):
            with st.form("add_note_form"):
                note_title = st.text_input("Tiêu đề ghi chú")
                note_content = st.text_area("Nội dung")
                note_tags = st.text_input("Thẻ (phân cách bằng dấu phẩy)")
                
                add_note_submitted = st.form_submit_button("Thêm ghi chú")
                
                if add_note_submitted and note_title:
                    tags = [tag.strip() for tag in note_tags.split(",")] if note_tags else []
                    details = {
                        "title": note_title,
                        "content": note_content,
                        "tags": tags,
                        "created_by": current_member
                    }
                    db_manager.add_note(details)
                    st.success(f"Đã thêm ghi chú: {note_title}!")
        
        # Xem ghi chú
        with st.expander("📋 Danh sách ghi chú"):
            # Lấy tất cả ghi chú
            notes_data = db_manager.get_all_notes()
            
            # Lọc ghi chú theo người dùng hiện tại
            if current_member:
                filtered_notes = {
                    note_id: note for note_id, note in notes_data.items()
                    if note.get("created_by") == current_member
                }
            else:
                filtered_notes = notes_data
            
            # Sắp xếp ghi chú theo ngày tạo
            try:
                sorted_notes = sorted(
                    filtered_notes.items(),
                    key=lambda x: x[1].get("created_on", ""),
                    reverse=True
                )
            except Exception as e:
                st.error(f"Lỗi khi sắp xếp ghi chú: {e}")
                sorted_notes = []
            
            if not sorted_notes:
                st.write("Không có ghi chú nào")
            
            for note_id, note in sorted_notes:
                st.write(f"**{note.get('title', 'Ghi chú không tiêu đề')}**")
                st.write(note.get('content', ''))
                
                if note.get('tags'):
                    tags = ', '.join([f"#{tag}" for tag in note['tags']])
                    st.write(f"🏷️ {tags}")
                
                # Hiển thị người tạo
                if note.get('created_by'):
                    creator = db_manager.get_family_member(note.get('created_by'))
                    creator_name = creator.get("name", "") if creator else ""
                    if creator_name:
                        st.write(f"👤 Tạo bởi: {creator_name}")
                
                if st.button(f"Xóa", key=f"delete_note_{note_id}"):
                    db_manager.delete_note(note_id)
                    st.success(f"Đã xóa ghi chú!")
                    st.rerun()
                st.divider()
    
    @staticmethod
    def fallback_suggested_questions(member_id: Optional[str] = None, max_questions: int = 5) -> List[str]:
        """Tạo câu hỏi gợi ý dự phòng khi không có API key"""
        # Tạo seed dựa trên ngày và ID thành viên để tạo sự đa dạng
        random_seed = int(hashlib.md5(f"{datetime.datetime.now().strftime('%Y-%m-%d_%H')}_{member_id or 'guest'}".encode()).hexdigest(), 16) % 10000
        random.seed(random_seed)
        
        # Mẫu câu thông tin cụ thể theo nhiều chủ đề khác nhau
        question_templates = {
            "food": [
                "Top 10 món {food} ngon nhất Việt Nam?",
                "Công thức làm món {food} ngon tại nhà?",
                "5 biến tấu món {food} cho bữa {meal}?"
            ],
            "movies": [
                "Top 5 phim chiếu rạp tuần này?",
                "Phim mới ra mắt {movie1}?",
                "Đánh giá phim {movie1}?"
            ],
            "football": [
                "Kết quả Champions League?",
                "BXH Ngoại hạng Anh?",
                "Chuyển nhượng bóng đá?"
            ],
            "technology": [
                "So sánh iPhone 16 Pro và Samsung S24 Ultra?",
                "5 tính năng AI mới trên smartphone 2024?",
                "Đánh giá laptop gaming {laptop_model}?"
            ],
            "health": [
                "5 loại thực phẩm tăng cường miễn dịch?",
                "3 bài tập cardio đốt mỡ bụng hiệu quả?",
                "Thực đơn 7 ngày giàu protein?"
            ],
            "family": [
                "10 hoạt động cuối tuần gắn kết gia đình?",
                "Bí quyết dạy trẻ quản lý tài chính?",
                "Lịch trình khoa học cho trẻ?"
            ],
            "news": [
                "Tin kinh tế?",
                "Tin thời tiết?",
                "Tin giáo dục?"
            ]
        }
        
        # Các biến thay thế trong mẫu câu
        replacements = {
            "food": ["phở", "bánh mì", "cơm rang", "gỏi cuốn", "bún chả"],
            "meal": ["sáng", "trưa", "tối", "xế"],
            "movie1": ["The Beekeeper", "Dune 2", "Godzilla x Kong", "Deadpool 3"],
            "laptop_model": ["Asus ROG", "Lenovo Legion", "MSI Titan"]
        }
        
        # Lấy ngẫu nhiên các câu hỏi từ mỗi chủ đề
        all_categories = list(question_templates.keys())
        random.shuffle(all_categories)
        
        selected_categories = all_categories[:max_questions]
        questions = []
        
        for category in selected_categories:
            template = random.choice(question_templates[category])
            
            # Thay thế các biến trong template
            question = template
            for key, values in replacements.items():
                if "{" + key + "}" in question:
                    question = question.replace("{" + key + "}", random.choice(values))
            
            questions.append(question)
        
        return questions