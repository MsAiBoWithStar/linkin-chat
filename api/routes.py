"""
REST API 路由
"""
from typing import Optional, Any
from flask import request, current_app
from utils.helpers import api_response, require_json, require_auth
from services.auth_service import create_token, decode_token, check_password, hash_password
from controllers import user_controller, friend_controller, message_controller
from controllers.group import (
    create_group,
    get_user_groups,
    get_group_members,
    get_member_role,
    invite_member,
    kick_member,
    dissolve_group,
)
from models.user import User
from models.group import Group
from services import file_service
from services.notification_service import get_unread_summary


def current_user() -> Optional[Any]:
    """从 Authorization: Bearer <token> 获取当前用户"""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    payload = decode_token(token)
    if not payload:
        return None
    return user_controller.get_user_by_id(payload.get("user_id"))


def register_routes(app):
    # ---------- 认证 ----------
    @app.route("/api/register", methods=["POST"])
    @require_json("nickname")
    def register():
        data = request.get_json()
        nickname = data.get("nickname", "").strip()
        link_id = (data.get("link_id") or "").strip() or None
        password = data.get("password") or None
        if not password:
            return api_response(message="需要密码", code=400)
        user, err = user_controller.create_user(nickname, link_id=link_id, password=password)
        if err:
            return api_response(message=err, code=400)
        assert user is not None, "User creation returned None"
        token = create_token(user.id, user.link_id)
        return api_response(data={"user": user.to_dict(), "token": token})

    @app.route("/api/login", methods=["POST"])
    def login():
        data = request.get_json() or {}
        link_id = (data.get("link_id") or "").strip()
        password = data.get("password")
        if not link_id:
            return api_response(message="需要通讯码", code=400)
        if not password:
            return api_response(message="需要密码", code=400)
        user = user_controller.get_user_by_link_id(link_id)
        if not user:
            return api_response(message="用户不存在", code=404)
        if not user.password_hash:
            return api_response(message="该账号未设置密码", code=401)
        if not check_password(password, user.password_hash):
            return api_response(message="通讯码或密码错误", code=401)
        assert user is not None, "User is not None at this point"
        token = create_token(user.id, user.link_id)
        return api_response(data={"user": user.to_dict(), "token": token})

    # ---------- 用户 ----------
    @app.route("/api/me", methods=["GET"])
    @require_auth
    def me(user):
        return api_response(data=user.to_dict())

    @app.route("/api/profile", methods=["PUT"])
    @require_auth
    def update_profile(user):
        data = request.get_json() or {}
        nickname = data.get("nickname")
        avatar = data.get("avatar")
        if request.files and "avatar" in request.files:
            path = file_service.save_avatar(request.files["avatar"])
            if path:
                avatar = path
        user, err = user_controller.update_profile(user.id, nickname=nickname, avatar=avatar)
        if err:
            return api_response(message=err, code=400)
        assert user is not None, "User is not None after update"
        socketio = getattr(current_app, "socketio", None)
        if socketio:
            updated = user.to_dict()
            # 通知好友同步更新头像和昵称
            friends = friend_controller.get_friends(user.id)
            for f in friends:
                socketio.emit("profile_updated", {"user": updated}, to=f"user_{f['id']}", namespace='/')
            # 通知自己多端同步
            socketio.emit("profile_updated", {"user": updated}, to=f"user_{user.id}", namespace='/')
        return api_response(data=user.to_dict())

    # ---------- 好友 ----------
    @app.route("/api/friends", methods=["GET"])
    @require_auth
    def friends(user):
        return api_response(data=friend_controller.get_friends(user.id))

    @app.route("/api/friends/search", methods=["POST"])
    @require_json()
    @require_auth
    def search_user(user):
        data = request.get_json()
        link_id = data.get("link_id")
        nickname = data.get("nickname")
        users = friend_controller.search_user_by_link_id_or_nickname(link_id=link_id, nickname=nickname)
        return api_response(data=[u.to_dict() for u in users])

    @app.route("/api/friends/add", methods=["POST"])
    @require_json("friend_id")
    @require_auth
    def add_friend(user):
        friend_id = request.get_json().get("friend_id")
        try:
            friend_id = int(friend_id)
        except (TypeError, ValueError):
            return api_response(message="friend_id 无效", code=400)
        ok, err = friend_controller.add_friend(user.id, friend_id)
        if err:
            return api_response(message=err, code=400)
        
        # 通知双方刷新好友列表
        socketio = getattr(current_app, "socketio", None)
        if socketio:
            friend = user_controller.get_user_by_id(friend_id)
            if friend:
                # 通知当前用户刷新好友列表
                socketio.emit("friend_added", {
                    "friend": friend.to_dict(),
                    "message": f"成功添加好友 {friend.nickname}"
                }, to=f"user_{user.id}", namespace='/')
                # 通知对方刷新好友列表
                socketio.emit("friend_added", {
                    "friend": user.to_dict(),
                    "message": f"{user.nickname} 添加你为好友"
                }, to=f"user_{friend_id}", namespace='/')
                print(f"[WebSocket] 好友添加通知: user_{user.id} <-> user_{friend_id}")
        
        return api_response(data=True)

    @app.route("/api/friends/delete", methods=["POST"])
    @require_json("friend_id")
    @require_auth
    def delete_friend(user):
        data = request.get_json()
        friend_id = data.get("friend_id")
        clear_history = data.get("clear_history", False)
        try:
            friend_id = int(friend_id)
        except (TypeError, ValueError):
            return api_response(message="friend_id 无效", code=400)
        ok, err = friend_controller.remove_friend(user.id, friend_id, clear_history=clear_history)
        if err:
            return api_response(message=err, code=400)
        
        # 通知双方刷新好友列表
        socketio = getattr(current_app, "socketio", None)
        if socketio:
            # 通知当前用户刷新
            socketio.emit("friend_removed", {
                "friend_id": friend_id
            }, to=f"user_{user.id}", namespace='/')
            # 通知对方刷新
            socketio.emit("friend_removed", {
                "friend_id": user.id
            }, to=f"user_{friend_id}", namespace='/')
            print(f"[WebSocket] 好友删除通知: user_{user.id} X user_{friend_id}")
        
        return api_response(data=True)

    # ---------- 消息 ----------
    def _emit_message(msg, receiver_ids):
        """
        推送消息给指定接收方
        receiver_ids: 单个ID (int) 或 ID 列表 (list)
        """
        socketio = getattr(current_app, "socketio", None)
        if not socketio:
            return
        
        msg_dict = msg.to_dict()
        
        if isinstance(receiver_ids, int):
            # 私聊：推送给接收方和发送方（多设备同步）
            socketio.emit("new_message", msg_dict, to=f"user_{receiver_ids}", namespace='/')
            socketio.emit("new_message", msg_dict, to=f"user_{msg.sender_id}", namespace='/')
        elif isinstance(receiver_ids, list):
            # 群聊：推送给所有成员
            for receiver_id in receiver_ids:
                socketio.emit("new_message", msg_dict, to=f"user_{receiver_id}", namespace='/')

    @app.route("/api/messages/private", methods=["POST"])
    @require_json()
    @require_auth
    def send_private(user):
        data = request.get_json()
        to_user = data.get("to_user")  # link_id 或 user_id
        # 获取接收方
        if isinstance(to_user, int):
            receiver = user_controller.get_user_by_id(to_user)
        else:
            receiver = user_controller.get_user_by_link_id(str(to_user))
        if not receiver:
            return api_response(message="对方不存在", code=404)
        # 发送消息
        msg, err = message_controller.send_private_message(
            user.id, receiver.id,
            content=data.get("content"),
            file_path=data.get("file_path"),
            file_name=data.get("file_name")
        )
        if err:
            return api_response(message=err, code=400)
        assert msg is not None, "Message is not None"
        # 推送消息
        _emit_message(msg, receiver.id)
        print(f"[WebSocket] 推送私聊消息 #{msg.id} 从 user_{user.id} 到 user_{receiver.id}")
        return api_response(data=msg.to_dict())

    @app.route("/api/messages/private/<int:other_id>", methods=["GET"])
    @require_auth
    def get_private(user, other_id):
        unread_only = request.args.get("unread_only", "").lower() == "true"
        limit = min(int(request.args.get("limit", 100)), 200)
        offset = max(0, int(request.args.get("offset", 0)))
        messages = message_controller.get_private_messages(user.id, other_id, unread_only=unread_only, limit=limit, offset=offset)
        return api_response(data=[m.to_dict() for m in messages])

    @app.route("/api/messages/group", methods=["POST"])
    @require_json("group_id")
    @require_auth
    def send_group(user):
        data = request.get_json()
        group_id = data.get("group_id")
        try:
            group_id = int(group_id)
        except (TypeError, ValueError):
            return api_response(message="group_id 无效", code=400)
        # 发送消息
        msg, err = message_controller.send_group_message(
            user.id, group_id,
            content=data.get("content"),
            file_path=data.get("file_path"),
            file_name=data.get("file_name")
        )
        if err:
            return api_response(message=err, code=400)
        assert msg is not None, "Message is not None"
        # 获取群成员并推送消息
        from controllers.group import get_group_members
        members = get_group_members(group_id, user.id) or []
        receiver_ids = [m['user_id'] for m in members]
        _emit_message(msg, receiver_ids)
        print(f"[WebSocket] 推送群消息 #{msg.id} 到群 {group_id}，成员数: {len(receiver_ids)}")
        return api_response(data=msg.to_dict())

    @app.route("/api/messages/group/<int:group_id>", methods=["GET"])
    @require_auth
    def get_group_messages_route(user, group_id):
        unread_only = request.args.get("unread_only", "").lower() == "true"
        limit = min(int(request.args.get("limit", 100)), 200)
        offset = max(0, int(request.args.get("offset", 0)))
        messages = message_controller.get_group_messages(user.id, group_id, unread_only=unread_only, limit=limit, offset=offset)
        return api_response(data=[m.to_dict() for m in messages])

    @app.route("/api/messages/search", methods=["GET"])
    @require_auth
    def message_search(user):
        q = request.args.get("q", "").strip()
        limit = min(int(request.args.get("limit", 50)), 100)
        messages = message_controller.search_messages(user.id, q, limit=limit)
        return api_response(data=[m.to_dict() for m in messages])

    @app.route("/api/messages/unread-summary", methods=["GET"])
    @require_auth
    def unread_summary(user):
        return api_response(data=get_unread_summary(user.id))

    @app.route("/api/messages/read", methods=["POST"])
    @require_json("chat_type", "chat_id")
    @require_auth
    def mark_read(user):
        data = request.get_json()
        message_controller.mark_as_read(
            user.id,
            chat_type=data.get("chat_type"),
            chat_id=data.get("chat_id"),
        )
        return api_response(data=True)

    # ---------- 群组 ----------
    @app.route("/api/groups", methods=["GET"])
    @require_auth
    def groups(user):
        return api_response(data=get_user_groups(user.id))

    @app.route("/api/groups", methods=["POST"])
    @require_json("group_name")
    @require_auth
    def create_group_route(user):
        data = request.get_json()
        member_ids = data.get("member_ids") or []
        try:
            member_ids = [int(x) for x in member_ids]
        except (TypeError, ValueError):
            member_ids = []
        group, err = create_group(user.id, data["group_name"], member_ids)
        if err:
            return api_response(message=err, code=400)
        socketio = getattr(current_app, "socketio", None)
        if socketio:
            notify_ids = {user.id, *member_ids}
            for uid in notify_ids:
                message = "群聊已创建" if uid == user.id else f"你被邀请加入群聊 {group.group_name}"
                socketio.emit("group_added", {
                    "group": group.to_dict(),
                    "group_id": group.id,
                    "message": message
                }, to=f"user_{uid}", namespace='/')
        return api_response(data=group.to_dict())

    @app.route("/api/groups/<int:group_id>/invite", methods=["POST"])
    @require_json("user_id")
    @require_auth
    def group_invite(user, group_id):
        user_id = request.get_json().get("user_id")
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return api_response(message="user_id 无效", code=400)
        ok, err = invite_member(user.id, group_id, user_id)
        if err:
            return api_response(message=err, code=400)
        socketio = getattr(current_app, "socketio", None)
        if socketio:
            group = Group.query.get(group_id)
            if group:
                socketio.emit("group_added", {
                    "group": group.to_dict(),
                    "group_id": group.id,
                    "message": f"你被邀请加入群聊 {group.group_name}"
                }, to=f"user_{user_id}", namespace='/')
        return api_response(data=True)

    @app.route("/api/groups/<int:group_id>/kick", methods=["POST"])
    @require_json("user_id")
    @require_auth
    def group_kick(user, group_id):
        user_id = request.get_json().get("user_id")
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return api_response(message="user_id 无效", code=400)
        ok, err = kick_member(user.id, group_id, user_id)
        if err:
            return api_response(message=err, code=400)
        socketio = getattr(current_app, "socketio", None)
        if socketio:
            socketio.emit("group_removed", {
                "group_id": group_id,
                "message": "你已被移出群聊"
            }, to=f"user_{user_id}", namespace='/')
        return api_response(data=True)

    @app.route("/api/groups/<int:group_id>/members", methods=["GET"])
    @require_auth
    def group_members(user, group_id):
        members = get_group_members(group_id, user.id)
        if members is None:
            return api_response(message="无权限", code=403)
        return api_response(data=members)

    @app.route("/api/groups/<int:group_id>/dissolve", methods=["POST"])
    @require_auth
    def group_dissolve(user, group_id):
        members = get_group_members(group_id, user.id) or []
        ok, err = dissolve_group(user.id, group_id)
        if err:
            return api_response(message=err, code=400)
        socketio = getattr(current_app, "socketio", None)
        if socketio:
            for member in members:
                socketio.emit("group_removed", {
                    "group_id": group_id,
                    "message": "群聊已解散"
                }, to=f"user_{member['user_id']}", namespace='/')
        return api_response(data=True)

    # ---------- 文件上传 ----------
    @app.route("/api/upload", methods=["POST"])
    @require_auth
    def upload(user):
        if "file" not in request.files:
            return api_response(message="需要 file 字段", code=400)
        path = file_service.save_upload(request.files["file"])
        if not path:
            return api_response(message="文件类型不允许或无效", code=400)
        return api_response(data={"file_path": path, "file_name": request.files["file"].filename})
