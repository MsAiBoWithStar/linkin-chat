"""
通知服务：未读数量、推送（与 WebSocket 配合由 api/websocket 使用）
"""
from models.message import Message
from models.group import UserGroupRead


def get_unread_count(user_id, chat_type="user", chat_id=None):
    """
    获取未读数量。
    chat_type: 'user' 私聊则 chat_id 为对方 user_id；'group' 群聊则 chat_id 为 group_id。
    """
    if chat_type == "group":
        return get_group_unread_count(user_id, chat_id)
    q = Message.query.filter(
        Message.is_read == False,  # type: ignore
        Message.receiver_id == user_id,
        Message.sender_id == chat_id,
    )
    return q.count()


def get_group_unread_count(user_id, group_id):
    """群聊未读数：该群中 id 大于用户 last_read_message_id 的消息数"""
    rec = UserGroupRead.query.filter(
        UserGroupRead.user_id == user_id,
        UserGroupRead.group_id == group_id,
    ).first()
    last_id = rec.last_read_message_id if rec else 0
    return Message.query.filter(
        Message.group_id == group_id,
        Message.id > last_id,
        Message.sender_id != user_id,
    ).count()


def get_unread_summary(user_id):
    """
    返回当前用户所有会话的未读汇总。
    列表项: { "chat_type": "user"|"group", "chat_id": int, "unread": int }
    """
    from controllers import friend_controller
    from controllers.group import get_user_groups

    summary = []
    for f in friend_controller.get_friends(user_id):
        fid = f["id"] if isinstance(f, dict) else getattr(f, "id", None)
        if fid is None:
            continue
        cnt = get_unread_count(user_id, "user", fid)
        if cnt > 0:
            summary.append({"chat_type": "user", "chat_id": fid, "unread": cnt})
    for g in get_user_groups(user_id):
        gid = g["id"] if isinstance(g, dict) else g.id
        cnt = get_group_unread_count(user_id, gid)
        if cnt > 0:
            summary.append({"chat_type": "group", "chat_id": gid, "unread": cnt})
    return summary
