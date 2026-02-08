"""
好友业务逻辑
"""
from config.database import db
from models.user import User
from models.friendship import Friendship


def get_friends(user_id):
    """获取用户好友列表"""
    rows = Friendship.query.filter(Friendship.user_id == user_id).all()
    return [r.friend.to_dict() for r in rows if r.friend]


def is_friend(user_id, friend_id):
    if user_id == friend_id:
        return True
    return Friendship.query.filter(
        Friendship.user_id == user_id,
        Friendship.friend_id == friend_id,
    ).first() is not None


def add_friend(user_id, friend_id):
    if user_id == friend_id:
        return None, "不能添加自己为好友"
    if is_friend(user_id, friend_id):
        return None, "已是好友"
    f1 = Friendship(user_id=user_id, friend_id=friend_id)
    f2 = Friendship(user_id=friend_id, friend_id=user_id)
    db.session.add_all([f1, f2])
    db.session.commit()
    return True, None


def remove_friend(user_id, friend_id, clear_history=False):
    if not is_friend(user_id, friend_id):
        return None, "不是好友关系"
    Friendship.query.filter(
        ((Friendship.user_id == user_id) & (Friendship.friend_id == friend_id))
        | ((Friendship.user_id == friend_id) & (Friendship.friend_id == user_id))
    ).delete(synchronize_session=False)
    if clear_history:
        from models.message import Message
        Message.query.filter(
            ((Message.sender_id == user_id) & (Message.receiver_id == friend_id))
            | ((Message.sender_id == friend_id) & (Message.receiver_id == user_id))
        ).delete(synchronize_session=False)
    db.session.commit()
    return True, None


def search_user_by_link_id_or_nickname(link_id=None, nickname=None):
    q = User.query
    if link_id and link_id.strip():
        q = q.filter(User.link_id == link_id.strip())
    if nickname and nickname.strip():
        q = q.filter(User.nickname.contains(nickname.strip()))  # type: ignore
    if not link_id and not nickname:
        return []
    return q.limit(20).all()
