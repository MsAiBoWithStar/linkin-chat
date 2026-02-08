"""
消息模型
"""
from datetime import datetime
from typing import Optional
from config.database import db


class Message(db.Model):
    __tablename__ = "messages"
    __table_args__ = (
        db.Index("ix_messages_sender_created", "sender_id", "created_at"),
        db.Index("ix_messages_receiver_created", "receiver_id", "created_at"),
        db.Index("ix_messages_group_created", "group_id", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # 私聊
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=True)   # 群聊
    message_type = db.Column(db.String(16), nullable=False, default="text")  # text / file
    content = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(512), nullable=True)
    file_name = db.Column(db.String(256), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(
        self,
        sender_id: int,
        message_type: str = "text",
        receiver_id: Optional[int] = None,
        group_id: Optional[int] = None,
        content: Optional[str] = None,
        file_path: Optional[str] = None,
        file_name: Optional[str] = None,
        is_read: bool = False,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.sender_id = sender_id
        self.message_type = message_type
        self.receiver_id = receiver_id
        self.group_id = group_id
        self.content = content
        self.file_path = file_path
        self.file_name = file_name
        self.is_read = is_read

    sender = db.relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = db.relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")

    def to_dict(self):
        # 确保时间格式包含UTC标记，避免前端时区混淆
        created_at_str = None
        if self.created_at:
            created_at_str = self.created_at.isoformat()
            # 如果没有时区信息，添加Z表示UTC
            if not created_at_str.endswith('Z') and '+' not in created_at_str and self.created_at.tzinfo is None:
                created_at_str += 'Z'
        
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "group_id": self.group_id,
            "message_type": self.message_type,
            "content": self.content,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "is_read": self.is_read,
            "created_at": created_at_str,
            "sender": self.sender.to_dict() if self.sender else None,
        }
