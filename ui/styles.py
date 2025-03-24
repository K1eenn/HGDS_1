# ui/styles.py
"""
Quản lý CSS và định dạng giao diện cho ứng dụng
"""

import streamlit as st

class StyleManager:
    """
    Quản lý CSS và định dạng giao diện cho ứng dụng
    """
    
    @staticmethod
    def apply_base_styles():
        """Áp dụng CSS cơ bản cho ứng dụng"""
        st.markdown("""
        <style>
        /* Kiểu chung cho toàn bộ ứng dụng */
        body {
            font-family: 'Roboto', sans-serif;
            color: #333;
        }
        
        /* Tiêu đề chính */
        .main-header {
            text-align: center;
            color: #6ca395;
            font-style: italic;
            margin-bottom: 20px;
            font-size: 2.2rem;
        }
        
        /* Định dạng cho các phần */
        .section-header {
            color: #4b7a6d;
            font-weight: 500;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 0.5rem;
        }
        
        /* Định dạng form */
        .stForm > div {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
        }
        
        /* Định dạng các nút */
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
        
        /* Định dạng các tab */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 40px;
            white-space: pre-wrap;
            background-color: #f8f9fa;
            border-radius: 4px 4px 0 0;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #6ca395;
            color: white;
        }
        
        /* Định dạng cho expander */
        .streamlit-expanderHeader {
            background-color: #f8f9fa;
            border-radius: 10px;
        }
        
        /* Định dạng tin nhắn */
        .stChatMessage {
            background-color: #f8f9fa;
            border-radius: 15px;
            padding: 0.75rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        
        /* Tin nhắn người dùng */
        .stChatMessage[data-testid="user-message"] {
            background-color: #e8f0fe;
            border-left: 4px solid #6ca395;
        }
        
        /* Tin nhắn trợ lý */
        .stChatMessage[data-testid="assistant-message"] {
            background-color: #ffffff;
            border-left: 4px solid #b8b8b8;
        }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def apply_suggestion_box_styles():
        """Áp dụng CSS cho hộp gợi ý"""
        st.markdown("""
        <style>
        /* Container cho câu hỏi gợi ý */
        .suggestion-container {
            margin-top: 20px;
            margin-bottom: 20px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
        }
        
        /* Tiêu đề phần gợi ý */
        .suggestion-title {
            font-size: 16px;
            font-weight: 500;
            margin-bottom: 10px;
            color: #555;
        }
        
        /* Khung chứa các nút gợi ý */
        .suggestion-box {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        /* Nút gợi ý */
        .suggestion-button {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 20px;
            padding: 8px 15px;
            font-size: 14px;
            color: #555;
            transition: all 0.3s;
            cursor: pointer;
            text-align: center;
        }
        
        .suggestion-button:hover {
            background-color: #e8f0fe;
            border-color: #6ca395;
            color: #333;
        }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def apply_member_card_styles():
        """Áp dụng CSS cho thẻ thành viên"""
        st.markdown("""
        <style>
        /* Card cho thành viên */
        .member-card {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border-left: 4px solid #6ca395;
        }
        
        /* Tên thành viên */
        .member-name {
            font-size: 18px;
            font-weight: 500;
            color: #333;
            margin-bottom: 5px;
        }
        
        /* Tuổi thành viên */
        .member-age {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }
        
        /* Sở thích */
        .member-preferences {
            font-size: 14px;
            color: #555;
            margin-bottom: 5px;
        }
        
        /* Nhãn sở thích */
        .preference-label {
            font-weight: 500;
            color: #6ca395;
        }
        
        /* Giá trị sở thích */
        .preference-value {
            font-style: italic;
        }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def apply_event_card_styles():
        """Áp dụng CSS cho thẻ sự kiện"""
        st.markdown("""
        <style>
        /* Card cho sự kiện */
        .event-card {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border-left: 4px solid #4b7a6d;
        }
        
        /* Tiêu đề sự kiện */
        .event-title {
            font-size: 18px;
            font-weight: 500;
            color: #333;
            margin-bottom: 5px;
        }
        
        /* Thời gian sự kiện */
        .event-datetime {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }
        
        /* Mô tả sự kiện */
        .event-description {
            font-size: 14px;
            color: #555;
            margin-bottom: 10px;
        }
        
        /* Người tham gia */
        .event-participants {
            font-size: 14px;
            color: #555;
        }
        
        /* Nhãn người tham gia */
        .participants-label {
            font-weight: 500;
            color: #4b7a6d;
        }
        
        /* Tên người tham gia */
        .participant-name {
            display: inline-block;
            background-color: #f0f0f0;
            padding: 3px 8px;
            border-radius: 10px;
            margin: 2px;
            font-size: 12px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def apply_note_card_styles():
        """Áp dụng CSS cho thẻ ghi chú"""
        st.markdown("""
        <style>
        /* Card cho ghi chú */
        .note-card {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border-left: 4px solid #f9c846;
        }
        
        /* Tiêu đề ghi chú */
        .note-title {
            font-size: 18px;
            font-weight: 500;
            color: #333;
            margin-bottom: 5px;
        }
        
        /* Nội dung ghi chú */
        .note-content {
            font-size: 14px;
            color: #555;
            margin-bottom: 10px;
            white-space: pre-line;
        }
        
        /* Thẻ */
        .note-tags {
            font-size: 14px;
            color: #555;
        }
        
        /* Nhãn thẻ */
        .tags-label {
            font-weight: 500;
            color: #f9c846;
        }
        
        /* Tên thẻ */
        .tag-name {
            display: inline-block;
            background-color: #f9f4e1;
            padding: 3px 8px;
            border-radius: 10px;
            margin: 2px;
            font-size: 12px;
            color: #bf9730;
        }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def apply_all_styles():
        """Áp dụng tất cả CSS"""
        StyleManager.apply_base_styles()
        StyleManager.apply_suggestion_box_styles()
        StyleManager.apply_member_card_styles()
        StyleManager.apply_event_card_styles()
        StyleManager.apply_note_card_styles()