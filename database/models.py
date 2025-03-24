# database/models.py
"""
Định nghĩa cấu trúc dữ liệu và model cho ứng dụng
"""

import json
import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass


@dataclass
class Preference:
    """Class đại diện cho sở thích của thành viên gia đình"""
    food: str = ""
    hobby: str = ""
    color: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Preference':
        """Tạo đối tượng Preference từ dictionary"""
        return cls(
            food=data.get('food', ''),
            hobby=data.get('hobby', ''),
            color=data.get('color', '')
        )
    
    def to_dict(self) -> Dict:
        """Chuyển đổi đối tượng thành dictionary"""
        return {
            'food': self.food,
            'hobby': self.hobby,
            'color': self.color
        }
    
    def to_json(self) -> str:
        """Chuyển đổi đối tượng thành chuỗi JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class FamilyMember:
    """Class đại diện cho thành viên gia đình"""
    id: Optional[int] = None
    name: str = ""
    age: str = ""
    preferences: Preference = None
    added_on: str = ""
    
    def __post_init__(self):
        """Sau khi khởi tạo, đảm bảo preferences luôn là đối tượng Preference"""
        if self.preferences is None:
            self.preferences = Preference()
        elif isinstance(self.preferences, dict):
            self.preferences = Preference.from_dict(self.preferences)
        
        # Cập nhật thời gian thêm nếu không có
        if not self.added_on:
            self.added_on = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FamilyMember':
        """Tạo đối tượng FamilyMember từ dictionary"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            age=data.get('age', ''),
            preferences=Preference.from_dict(data.get('preferences', {})),
            added_on=data.get('added_on', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
    
    def to_dict(self) -> Dict:
        """Chuyển đổi đối tượng thành dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'preferences': self.preferences.to_dict(),
            'added_on': self.added_on
        }


@dataclass
class Event:
    """Class đại diện cho sự kiện"""
    id: Optional[int] = None
    title: str = ""
    date: str = ""
    time: str = ""
    description: str = ""
    participants: List[str] = None
    created_by: str = ""
    created_on: str = ""
    
    def __post_init__(self):
        """Sau khi khởi tạo, đảm bảo participants luôn là list"""
        if self.participants is None:
            self.participants = []
        
        # Cập nhật thời gian tạo nếu không có
        if not self.created_on:
            self.created_on = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        """Tạo đối tượng Event từ dictionary"""
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            date=data.get('date', ''),
            time=data.get('time', ''),
            description=data.get('description', ''),
            participants=data.get('participants', []),
            created_by=data.get('created_by', ''),
            created_on=data.get('created_on', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
    
    def to_dict(self) -> Dict:
        """Chuyển đổi đối tượng thành dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'date': self.date,
            'time': self.time,
            'description': self.description,
            'participants': self.participants,
            'created_by': self.created_by,
            'created_on': self.created_on
        }


@dataclass
class Note:
    """Class đại diện cho ghi chú"""
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    tags: List[str] = None
    created_by: str = ""
    created_on: str = ""
    
    def __post_init__(self):
        """Sau khi khởi tạo, đảm bảo tags luôn là list"""
        if self.tags is None:
            self.tags = []
        
        # Cập nhật thời gian tạo nếu không có
        if not self.created_on:
            self.created_on = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Note':
        """Tạo đối tượng Note từ dictionary"""
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            content=data.get('content', ''),
            tags=data.get('tags', []),
            created_by=data.get('created_by', ''),
            created_on=data.get('created_on', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
    
    def to_dict(self) -> Dict:
        """Chuyển đổi đối tượng thành dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'tags': self.tags,
            'created_by': self.created_by,
            'created_on': self.created_on
        }


@dataclass
class ChatHistory:
    """Class đại diện cho lịch sử trò chuyện"""
    id: Optional[int] = None
    member_id: str = ""
    timestamp: str = ""
    messages: List[Dict] = None
    summary: str = ""
    
    def __post_init__(self):
        """Sau khi khởi tạo, đảm bảo messages luôn là list"""
        if self.messages is None:
            self.messages = []
        
        # Cập nhật thời gian nếu không có
        if not self.timestamp:
            self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatHistory':
        """Tạo đối tượng ChatHistory từ dictionary"""
        return cls(
            id=data.get('id'),
            member_id=data.get('member_id', ''),
            timestamp=data.get('timestamp', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            messages=data.get('messages', []),
            summary=data.get('summary', '')
        )
    
    def to_dict(self) -> Dict:
        """Chuyển đổi đối tượng thành dictionary"""
        return {
            'id': self.id,
            'member_id': self.member_id,
            'timestamp': self.timestamp,
            'messages': self.messages,
            'summary': self.summary
        }