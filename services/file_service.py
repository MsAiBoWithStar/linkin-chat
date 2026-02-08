"""
文件上传与存储
"""
import os
import uuid
from pathlib import Path
from config.settings import UPLOAD_DIR, AVATAR_DIR, MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS


def ensure_dirs():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)


def allowed_file(filename):
    """检查文件是否允许上传"""
    if not filename:
        return False
    # 如果 ALLOWED_EXTENSIONS 为 None，允许所有文件
    if ALLOWED_EXTENSIONS is None:
        return True
    # 没有扩展名的文件也允许
    if "." not in filename:
        return True
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in ALLOWED_EXTENSIONS


def save_upload(file_storage, subdir="uploads"):
    """保存上传文件，返回相对路径"""
    ensure_dirs()
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None
    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    base = UPLOAD_DIR if subdir == "uploads" else AVATAR_DIR
    path = base / name
    file_storage.save(str(path))
    return f"{subdir}/{name}"


def save_avatar(file_storage):
    return save_upload(file_storage, subdir="avatars")
