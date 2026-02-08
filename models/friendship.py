"""
好友关系模型
"""
from datetime import datetime
from config.database import db


class Friendship(db.Model):
    __tablename__ = "friendships"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "friend_id", name="uq_friendship"),)

    def __init__(
        self,
        user_id: int,
        friend_id: int,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.user_id = user_id
        self.friend_id = friend_id

    user = db.relationship("User", foreign_keys=[user_id])
    friend = db.relationship("User", foreign_keys=[friend_id])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "friend_id": self.friend_id,
            "friend": self.friend.to_dict() if self.friend else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
