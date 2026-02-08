"""
群组与群成员模型
"""
from datetime import datetime
from typing import Optional
from config.database import db


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_name = db.Column(db.String(128), nullable=False)
    group_avatar = db.Column(db.String(256), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(
        self,
        group_name: str,
        owner_id: int,
        group_avatar: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.group_name = group_name
        self.owner_id = owner_id
        self.group_avatar = group_avatar

    owner = db.relationship("User", foreign_keys=[owner_id])
    members = db.relationship("GroupMember", backref="group", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "group_name": self.group_name,
            "group_avatar": self.group_avatar,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GroupMember(db.Model):
    __tablename__ = "group_members"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(16), nullable=False, default="member")  # owner / admin / member
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("group_id", "user_id", name="uq_group_member"),)

    def __init__(
        self,
        group_id: int,
        user_id: int,
        role: str = "member",
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.group_id = group_id
        self.user_id = user_id
        self.role = role

    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "user_id": self.user_id,
            "role": self.role,
            "user": self.user.to_dict() if self.user else None,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }


class UserGroupRead(db.Model):
    """用户在某群的已读位置（用于未读数）"""
    __tablename__ = "user_group_read"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=False)
    last_read_message_id = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (db.UniqueConstraint("user_id", "group_id", name="uq_user_group_read"),)

    def __init__(
        self,
        user_id: int,
        group_id: int,
        last_read_message_id: int = 0,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.user_id = user_id
        self.group_id = group_id
        self.last_read_message_id = last_read_message_id
