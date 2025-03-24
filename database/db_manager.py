# database/db_manager.py
"""
Quản lý cơ sở dữ liệu và cung cấp các phương thức truy cập dữ liệu
"""

import sqlite3
import json
import os
import datetime
import logging
import threading
from typing import Dict, List, Optional, Any, Union, Tuple
from .models import FamilyMember, Event, Note, ChatHistory, Preference

logger = logging.getLogger('family_assistant')

class DatabaseManager:
    """Quản lý cơ sở dữ liệu SQLite cho ứng dụng Trợ lý Gia đình"""
    
    def __init__(self, db_path: str = "family_assistant.db"):
        """Khởi tạo kết nối với cơ sở dữ liệu SQLite"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.lock = threading.RLock()  # Thêm khóa để đồng bộ hóa truy cập
        self._initialize_db()
    
    def _initialize_db(self):
        """Khởi tạo database với các bảng cần thiết"""
        try:
            # Đảm bảo thư mục tồn tại
            os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
            
            # Tạo kết nối và cursor với check_same_thread=False để cho phép sử dụng ở nhiều thread
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Để kết quả truy vấn dạng dict
            self.cursor = self.conn.cursor()
            
            # Tạo các bảng nếu chưa tồn tại
            self._create_tables()
            
            logger.info(f"Đã khởi tạo kết nối tới database: {self.db_path}")
        except Exception as e:
            logger.error(f"Lỗi khi khởi tạo database: {e}")
            raise
    
    def _create_tables(self):
        """Tạo các bảng trong database"""
        with self.lock:  # Sử dụng khóa khi truy cập database
            # Bảng thành viên gia đình
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_members (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age TEXT,
                preferences TEXT,
                added_on TEXT
            )
            ''')
            
            # Bảng sự kiện
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                date TEXT,
                time TEXT,
                description TEXT,
                participants TEXT,
                created_by TEXT,
                created_on TEXT
            )
            ''')
            
            # Bảng ghi chú
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT,
                tags TEXT,
                created_by TEXT,
                created_on TEXT
            )
            ''')
            
            # Bảng lịch sử chat
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY,
                member_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                messages TEXT NOT NULL,
                summary TEXT
            )
            ''')
            
            self.conn.commit()
    
    def close(self):
        """Đóng kết nối database"""
        with self.lock:
            if self.conn:
                self.conn.close()
    
    # === Các phương thức cho thành viên gia đình ===
    def get_all_family_members(self) -> Dict[str, Dict]:
        """Lấy tất cả thành viên gia đình"""
        try:
            with self.lock:
                self.cursor.execute('SELECT * FROM family_members')
                rows = self.cursor.fetchall()
                
                result = {}
                for row in rows:
                    member_id = str(row['id'])
                    result[member_id] = {
                        'name': row['name'],
                        'age': row['age'],
                        'preferences': json.loads(row['preferences']) if row['preferences'] else {},
                        'added_on': row['added_on']
                    }
                
                return result
        except Exception as e:
            logger.error(f"Lỗi khi lấy dữ liệu thành viên: {e}")
            return {}
    
    def get_family_member(self, member_id: str) -> Optional[Dict]:
        """Lấy thông tin một thành viên cụ thể"""
        try:
            with self.lock:
                self.cursor.execute('SELECT * FROM family_members WHERE id = ?', (member_id,))
                row = self.cursor.fetchone()
                
                if row:
                    return {
                        'name': row['name'],
                        'age': row['age'],
                        'preferences': json.loads(row['preferences']) if row['preferences'] else {},
                        'added_on': row['added_on']
                    }
                return None
        except Exception as e:
            logger.error(f"Lỗi khi lấy thành viên ID={member_id}: {e}")
            return None
    
    def add_family_member(self, details: Dict) -> str:
        """Thêm thành viên gia đình mới"""
        try:
            preferences = json.dumps(details.get('preferences', {}))
            added_on = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with self.lock:
                self.cursor.execute(
                    'INSERT INTO family_members (name, age, preferences, added_on) VALUES (?, ?, ?, ?)',
                    (details.get('name', ''), details.get('age', ''), preferences, added_on)
                )
                self.conn.commit()
                
                # Trả về ID mới tạo
                member_id = str(self.cursor.lastrowid)
                logger.info(f"Đã thêm thành viên mới: {details.get('name')} với ID={member_id}")
                return member_id
        except Exception as e:
            logger.error(f"Lỗi khi thêm thành viên: {e}")
            with self.lock:
                self.conn.rollback()
            raise
    
    def update_family_member(self, member_id: str, details: Dict) -> bool:
        """Cập nhật thông tin thành viên"""
        try:
            updates = []
            params = []
            
            if 'name' in details:
                updates.append("name = ?")
                params.append(details['name'])
            
            if 'age' in details:
                updates.append("age = ?")
                params.append(details['age'])
            
            if 'preferences' in details:
                updates.append("preferences = ?")
                params.append(json.dumps(details['preferences']))
            
            if not updates:
                return False
            
            query = f"UPDATE family_members SET {', '.join(updates)} WHERE id = ?"
            params.append(member_id)
            
            with self.lock:
                self.cursor.execute(query, params)
                self.conn.commit()
                
                return self.cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật thành viên ID={member_id}: {e}")
            with self.lock:
                self.conn.rollback()
            return False
    
    def update_preference(self, member_id: str, key: str, value: str) -> bool:
        """Cập nhật sở thích của thành viên"""
        try:
            with self.lock:
                # Lấy sở thích hiện tại
                self.cursor.execute('SELECT preferences FROM family_members WHERE id = ?', (member_id,))
                row = self.cursor.fetchone()
                
                if not row:
                    return False
                
                preferences = json.loads(row['preferences']) if row['preferences'] else {}
                preferences[key] = value
                
                # Cập nhật sở thích
                self.cursor.execute(
                    'UPDATE family_members SET preferences = ? WHERE id = ?',
                    (json.dumps(preferences), member_id)
                )
                self.conn.commit()
                
                return True
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật sở thích cho thành viên ID={member_id}: {e}")
            with self.lock:
                self.conn.rollback()
            return False
    
    # === Các phương thức cho sự kiện ===
    def get_all_events(self) -> Dict[str, Dict]:
        """Lấy tất cả sự kiện"""
        try:
            with self.lock:
                self.cursor.execute('SELECT * FROM events')
                rows = self.cursor.fetchall()
                
                result = {}
                for row in rows:
                    event_id = str(row['id'])
                    result[event_id] = {
                        'title': row['title'],
                        'date': row['date'],
                        'time': row['time'],
                        'description': row['description'],
                        'participants': json.loads(row['participants']) if row['participants'] else [],
                        'created_by': row['created_by'],
                        'created_on': row['created_on']
                    }
                
                return result
        except Exception as e:
            logger.error(f"Lỗi khi lấy dữ liệu sự kiện: {e}")
            return {}
    
    def add_event(self, details: Dict) -> Optional[str]:
        """Thêm sự kiện mới"""
        try:
            participants = json.dumps(details.get('participants', []))
            created_on = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with self.lock:
                self.cursor.execute(
                    '''INSERT INTO events 
                       (title, date, time, description, participants, created_by, created_on) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (
                        details.get('title', ''),
                        details.get('date', ''),
                        details.get('time', ''),
                        details.get('description', ''),
                        participants,
                        details.get('created_by', ''),
                        created_on
                    )
                )
                self.conn.commit()
                
                # Trả về ID mới tạo
                event_id = str(self.cursor.lastrowid)
                logger.info(f"Đã thêm sự kiện mới: {details.get('title')} với ID={event_id}")
                return event_id
        except Exception as e:
            logger.error(f"Lỗi khi thêm sự kiện: {e}")
            with self.lock:
                self.conn.rollback()
            return None
    
    def update_event(self, event_id: str, details: Dict) -> bool:
        """Cập nhật thông tin sự kiện"""
        try:
            updates = []
            params = []
            
            for field in ['title', 'date', 'time', 'description']:
                if field in details:
                    updates.append(f"{field} = ?")
                    params.append(details[field])
            
            if 'participants' in details:
                updates.append("participants = ?")
                params.append(json.dumps(details['participants']))
            
            if not updates:
                return False
            
            query = f"UPDATE events SET {', '.join(updates)} WHERE id = ?"
            params.append(event_id)
            
            with self.lock:
                self.cursor.execute(query, params)
                self.conn.commit()
                
                return self.cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật sự kiện ID={event_id}: {e}")
            with self.lock:
                self.conn.rollback()
            return False
    
    def delete_event(self, event_id: str) -> bool:
        """Xóa sự kiện"""
        try:
            with self.lock:
                self.cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
                self.conn.commit()
                
                return self.cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Lỗi khi xóa sự kiện ID={event_id}: {e}")
            with self.lock:
                self.conn.rollback()
            return False
    
    def filter_events_by_member(self, member_id: Optional[str] = None) -> Dict[str, Dict]:
        """Lọc sự kiện theo thành viên cụ thể"""
        try:
            if not member_id:
                return self.get_all_events()
            
            # Lấy thông tin thành viên
            member = self.get_family_member(member_id)
            if not member:
                return {}
            
            member_name = member.get('name', '')
            
            # Lấy tất cả sự kiện
            all_events = self.get_all_events()
            
            # Lọc sự kiện theo người tạo hoặc người tham gia
            filtered_events = {}
            for event_id, event in all_events.items():
                if (event.get('created_by') == member_id or 
                    member_name in event.get('participants', [])):
                    filtered_events[event_id] = event
            
            return filtered_events
        except Exception as e:
            logger.error(f"Lỗi khi lọc sự kiện theo thành viên ID={member_id}: {e}")
            return {}
    
    # === Các phương thức cho ghi chú ===
    def get_all_notes(self) -> Dict[str, Dict]:
        """Lấy tất cả ghi chú"""
        try:
            with self.lock:
                self.cursor.execute('SELECT * FROM notes')
                rows = self.cursor.fetchall()
                
                result = {}
                for row in rows:
                    note_id = str(row['id'])
                    result[note_id] = {
                        'title': row['title'],
                        'content': row['content'],
                        'tags': json.loads(row['tags']) if row['tags'] else [],
                        'created_by': row['created_by'],
                        'created_on': row['created_on']
                    }
                
                return result
        except Exception as e:
            logger.error(f"Lỗi khi lấy dữ liệu ghi chú: {e}")
            return {}
    
    def add_note(self, details: Dict) -> Optional[str]:
        """Thêm ghi chú mới"""
        try:
            tags = json.dumps(details.get('tags', []))
            created_on = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with self.lock:
                self.cursor.execute(
                    'INSERT INTO notes (title, content, tags, created_by, created_on) VALUES (?, ?, ?, ?, ?)',
                    (
                        details.get('title', ''),
                        details.get('content', ''),
                        tags,
                        details.get('created_by', ''),
                        created_on
                    )
                )
                self.conn.commit()
                
                # Trả về ID mới tạo
                note_id = str(self.cursor.lastrowid)
                logger.info(f"Đã thêm ghi chú mới: {details.get('title')} với ID={note_id}")
                return note_id
        except Exception as e:
            logger.error(f"Lỗi khi thêm ghi chú: {e}")
            with self.lock:
                self.conn.rollback()
            return None
    
    def delete_note(self, note_id: str) -> bool:
        """Xóa ghi chú"""
        try:
            with self.lock:
                self.cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
                self.conn.commit()
                
                return self.cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Lỗi khi xóa ghi chú ID={note_id}: {e}")
            with self.lock:
                self.conn.rollback()
            return False
    
    # === Các phương thức cho lịch sử chat ===
    def get_chat_history(self, member_id: str, limit: int = 10) -> List[Dict]:
        """Lấy lịch sử chat của một thành viên"""
        try:
            with self.lock:
                self.cursor.execute(
                    'SELECT * FROM chat_history WHERE member_id = ? ORDER BY timestamp DESC LIMIT ?',
                    (member_id, limit)
                )
                rows = self.cursor.fetchall()
                
                result = []
                for row in rows:
                    result.append({
                        'timestamp': row['timestamp'],
                        'messages': json.loads(row['messages']),
                        'summary': row['summary']
                    })
                
                return result
        except Exception as e:
            logger.error(f"Lỗi khi lấy lịch sử chat cho thành viên ID={member_id}: {e}")
            return []
    
    def save_chat_history(self, member_id: str, messages: List[Dict], summary: Optional[str] = None) -> bool:
        """Lưu lịch sử chat cho một thành viên"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            messages_json = json.dumps(messages)
            
            with self.lock:
                self.cursor.execute(
                    'INSERT INTO chat_history (member_id, timestamp, messages, summary) VALUES (?, ?, ?, ?)',
                    (member_id, timestamp, messages_json, summary or "")
                )
                self.conn.commit()
                
                # Giới hạn số lượng lịch sử lưu trữ
                self._limit_chat_history(member_id, 10)
                
                return True
        except Exception as e:
            logger.error(f"Lỗi khi lưu lịch sử chat cho thành viên ID={member_id}: {e}")
            with self.lock:
                self.conn.rollback()
            return False
    
    def _limit_chat_history(self, member_id: str, limit: int) -> None:
        """Giới hạn số lượng lịch sử chat lưu trữ cho một thành viên"""
        try:
            with self.lock:
                # Lấy ID của các bản ghi cần xóa
                self.cursor.execute(
                    '''SELECT id FROM chat_history 
                       WHERE member_id = ? 
                       ORDER BY timestamp DESC 
                       LIMIT -1 OFFSET ?''',
                    (member_id, limit)
                )
                rows = self.cursor.fetchall()
                
                # Nếu có bản ghi cần xóa
                if rows:
                    ids_to_delete = [str(row['id']) for row in rows]
                    placeholders = ', '.join(['?'] * len(ids_to_delete))
                    
                    self.cursor.execute(
                        f'DELETE FROM chat_history WHERE id IN ({placeholders})',
                        ids_to_delete
                    )
                    self.conn.commit()
        except Exception as e:
            logger.error(f"Lỗi khi giới hạn lịch sử chat cho thành viên ID={member_id}: {e}")
            with self.lock:
                self.conn.rollback()