"""
WebSocket 实时消息推送（Flask-SocketIO）
"""
from flask_socketio import emit, join_room, leave_room
from services.auth_service import decode_token
from controllers import user_controller


def init_websocket(socketio):
    @socketio.on("connect")
    def on_connect():
        print(f"[WebSocket] 客户端连接: {socketio.server.environ.get('REMOTE_ADDR', 'unknown')}")

    @socketio.on("authenticate")
    def on_authenticate(data):
        token = (data or {}).get("token")
        if not token:
            print("[WebSocket] 认证失败: 缺少token")
            emit("auth_fail", {"message": "需要 token"})
            return
        payload = decode_token(token)
        if not payload:
            print("[WebSocket] 认证失败: token无效")
            emit("auth_fail", {"message": "token 无效"})
            return
        user_id = payload.get("user_id")
        # 加入个人房间，用于接收私聊与通知
        join_room(f"user_{user_id}")
        print(f"[WebSocket] 用户 {user_id} 已认证并加入房间 user_{user_id}")
        emit("authenticated", {"user_id": user_id})

    @socketio.on("join_chat")
    def on_join_chat(data):
        """加入会话（用于前端标记当前在哪个聊天窗口）"""
        room = (data or {}).get("room")
        if room:
            join_room(room)  # type: ignore

    @socketio.on("leave_chat")
    def on_leave_chat(data):
        room = (data or {}).get("room")
        if room:
            leave_room(room)  # type: ignore

    @socketio.on("disconnect")
    def on_disconnect():
        print("[WebSocket] 客户端断开连接")


def push_private_message(receiver_id, message_dict):
    """向指定用户推送私聊消息"""
    from flask_socketio import emit
    # 需在 socketio 上下文里调用
    emit("new_message", message_dict, room=f"user_{receiver_id}")  # type: ignore


def push_group_message(group_id, message_dict):
    """向群组房间推送消息（前端需先 join_chat room=group_<id>）"""
    from flask_socketio import emit
    emit("new_message", message_dict, room=f"group_{group_id}")  # type: ignore
