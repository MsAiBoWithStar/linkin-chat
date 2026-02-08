"""
用户模型
"""
from datetime import datetime
from typing import Optional
from config.database import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    link_id = db.Column(db.String(16), unique=True, nullable=False, index=True)  # 8位通讯码
    nickname = db.Column(db.String(64), nullable=False, default="")
    avatar = db.Column(db.String(256), nullable=True)  # 头像路径
    password_hash = db.Column(db.String(128), nullable=True)  # 可选：密码
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(
        self,
        link_id: str,
        nickname: str,
        avatar: Optional[str] = None,
        password_hash: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.link_id = link_id
        self.nickname = nickname
        self.avatar = avatar
        self.password_hash = password_hash

    # 关系（Message 侧用 back_populates）
    sent_messages = db.relationship(
        "Message", foreign_keys="Message.sender_id", back_populates="sender", lazy="dynamic"
    )
    received_messages = db.relationship(
        "Message", foreign_keys="Message.receiver_id", back_populates="receiver", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "link_id": self.link_id,
            "nickname": self.nickname,
            "avatar": self.avatar,

            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def display_name(self):
        """显示格式：昵称(通讯码)"""
        return f"{self.nickname}({self.link_id})"

    def __repr__(self):
        return f"<User {self.display_name()}>"
