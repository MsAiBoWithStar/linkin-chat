"""
消息业务逻辑
"""
from config.database import db
from models.message import Message
from models.group import UserGroupRead
from controllers.friend_controller import is_friend
from controllers.group import is_member


def send_private_message(sender_id, receiver_id, content=None, file_path=None, file_name=None):
    if not is_friend(sender_id, receiver_id):
        return None, "仅好友可发送消息"
    msg_type = "file" if file_path else "text"
    msg = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        message_type=msg_type,
        content=content,
        file_path=file_path,
        file_name=file_name,
    )
    db.session.add(msg)
    db.session.commit()
    return msg, None


def send_group_message(sender_id, group_id, content=None, file_path=None, file_name=None):
    if not is_member(sender_id, group_id):
        return None, "您不在该群中"
    msg_type = "file" if file_path else "text"
    msg = Message(
        sender_id=sender_id,
        group_id=group_id,
        message_type=msg_type,
        content=content,
        file_path=file_path,
        file_name=file_name,
    )
    db.session.add(msg)
    db.session.commit()
    return msg, None


def get_private_messages(user_id, other_id, unread_only=False, limit=100, offset=0):
    q = Message.query.filter(
        Message.group_id.is_(None),  # type: ignore
        db.or_(  # type: ignore
            (Message.sender_id == user_id) & (Message.receiver_id == other_id),
            (Message.sender_id == other_id) & (Message.receiver_id == user_id),
        ),
    ).order_by(Message.created_at.desc()).limit(limit).offset(offset)
    if unread_only:
        q = q.filter(Message.is_read == False, Message.receiver_id == user_id)  # type: ignore
    return list(reversed(q.all()))


def get_group_messages(user_id, group_id, unread_only=False, limit=100, offset=0):
    if not is_member(user_id, group_id):
        return []
    q = Message.query.filter(Message.group_id == group_id).order_by(Message.created_at.desc()).limit(limit).offset(offset)
    if unread_only:
        q = q.filter(Message.is_read == False)  # type: ignore
    return list(reversed(q.all()))


def mark_as_read(user_id: int, chat_type: str = "user", chat_id=None):
    if chat_type == "user":
        criteria = [  # type: ignore
            Message.receiver_id == user_id,
            Message.sender_id == chat_id,
            Message.is_read == False,  # type: ignore
        ]
        Message.query.filter(*criteria).update({"is_read": True}, synchronize_session=False)  # type: ignore
    else:
        last_msg = Message.query.filter(Message.group_id == chat_id).order_by(Message.id.desc()).first()
        if last_msg:
            filters = [  # type: ignore
                UserGroupRead.user_id == user_id,
                UserGroupRead.group_id == chat_id,  # type: ignore
            ]
            rec = UserGroupRead.query.filter(*filters).first()  # type: ignore
            if rec:
                rec.last_read_message_id = max(rec.last_read_message_id, last_msg.id)
            else:
                db.session.add(UserGroupRead(
                    user_id=user_id, group_id=int(chat_id) if chat_id else 0, last_read_message_id=last_msg.id
                ))
    db.session.commit()


def search_messages(user_id, keyword, limit=50):
    """搜索当前用户可见的消息（私聊+群），按时间倒序"""
    if not keyword or not keyword.strip():
        return []
    from controllers.friend_controller import get_friends
    from controllers.group import get_user_groups
    keyword = f"%{keyword.strip()}%"
    friend_ids = [f["id"] for f in get_friends(user_id)]
    group_ids = [g["id"] for g in get_user_groups(user_id)]
    
    # 构建私聊条件
    if friend_ids:
        private_conditions = [
            db.and_(Message.sender_id == user_id, Message.receiver_id.in_(friend_ids)),  # type: ignore
            db.and_(Message.receiver_id == user_id, Message.sender_id.in_(friend_ids)),  # type: ignore
        ]
        cond_private = db.or_(*private_conditions)  # type: ignore
    else:
        cond_private = None
    
    # 构建群组条件
    if group_ids:
        cond_group = Message.group_id.in_(group_ids)  # type: ignore
    else:
        cond_group = None
    
    # 构建完整条件
    filters = [
        Message.message_type == "text",
        Message.content.isnot(None),  # type: ignore
        Message.content.like(keyword),  # type: ignore
    ]
    
    if cond_private is not None and cond_group is not None:
        filters.append(db.or_(  # type: ignore
            db.and_(Message.group_id.is_(None), cond_private),  # type: ignore
            db.and_(Message.group_id.isnot(None), cond_group),  # type: ignore
        ))
    elif cond_private is not None:
        filters.append(Message.group_id.is_(None))  # type: ignore
        filters.append(cond_private)
    elif cond_group is not None:
        filters.append(Message.group_id.isnot(None))  # type: ignore
        filters.append(cond_group)
    else:
        return []
    
    q = Message.query.filter(*filters).order_by(Message.created_at.desc()).limit(limit)  # type: ignore
    return q.all()
