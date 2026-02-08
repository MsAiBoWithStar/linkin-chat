"""
认证服务：密码哈希、JWT
"""
import jwt
import bcrypt
from datetime import datetime, timedelta
from config.settings import SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_HOURS


def hash_password(password):
    if not password:
        return None
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password, password_hash):
    if not password or not password_hash:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(user_id, link_id):
    payload = {
        "user_id": user_id,
        "link_id": link_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return None
