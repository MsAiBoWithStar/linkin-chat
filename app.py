"""
LinkIn 应用入口：创建 Flask 应用、注册路由与 WebSocket
"""
import os
from pathlib import Path
from typing import Optional

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO

from config.settings import BASE_DIR, UPLOAD_DIR, AVATAR_DIR
from config.database import init_db
from api.routes import register_routes
from api.websocket import init_websocket

socketio: Optional[SocketIO] = None


def create_app():
    app = Flask(
        __name__,
        static_folder=str(BASE_DIR / "frontend" / "static"),
        template_folder=str(BASE_DIR / "frontend" / "templates"),
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "linkin-dev-secret")

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    init_db(app)

    register_routes(app)

    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
    init_websocket(socketio)
    app.socketio = socketio  # type: ignore

    # 静态文件：上传与头像
    @app.route("/storage/<path:subpath>")
    def storage(subpath):
        parts = subpath.split("/", 1)
        if len(parts) == 2 and parts[0] in ("uploads", "avatars"):
            folder = UPLOAD_DIR if parts[0] == "uploads" else AVATAR_DIR
            return send_from_directory(folder, parts[1])
        return "", 404

    @app.route("/")
    def index():
        from flask import send_file
        return send_file(str(BASE_DIR / "frontend" / "templates" / "index.html"))

    return app


app = create_app()


if __name__ == "__main__":
    # 确保目录存在
    (BASE_DIR / "database").mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    if socketio is not None:
        socketio.run(app, host="0.0.0.0", port=5000, debug=True)
