"""
LinkIn 全局配置
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 数据库
SQLITE_PATH = BASE_DIR / "database" / "linkin.db"
DATABASE_URI = os.environ.get("DATABASE_URI") or f"sqlite:///{SQLITE_PATH}"

# 安全
SECRET_KEY = os.environ.get("SECRET_KEY") or "linkin-dev-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24 * 7  # 7 天

# 文件存储
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
AVATAR_DIR = BASE_DIR / "storage" / "avatars"
MAX_FILE_SIZE_MB = 20
ALLOWED_EXTENSIONS = None  # None 表示允许所有文件类型

# 通讯码长度
LINK_ID_LENGTH = 8

# CORS（开发时可放宽）
CORS_ORIGINS = ["*"]
