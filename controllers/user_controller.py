"""
用户业务逻辑
"""
from config.database import db
from models.user import User
from utils.id_generator import generate_link_id
from utils.validators import is_valid_nickname, is_valid_link_id


def get_user_by_id(user_id):
    return User.query.get(user_id)


def get_user_by_link_id(link_id):
    return User.query.filter(User.link_id == link_id).first()


def create_user(nickname, link_id=None, password=None):
    if not is_valid_nickname(nickname):
        return None, "昵称无效"
    if link_id and link_id.strip():
        if not is_valid_link_id(link_id):
            return None, "通讯码必须为8位数字"
        if get_user_by_link_id(link_id):
            return None, "该通讯码已被使用"
    else:
        link_id = generate_link_id()
    user = User(link_id=link_id, nickname=nickname.strip())
    if password:
        from services.auth_service import hash_password
        user.password_hash = hash_password(password)
    db.session.add(user)
    db.session.commit()
    return user, None


def update_profile(user_id, nickname=None, avatar=None):
    user = get_user_by_id(user_id)
    if not user:
        return None, "用户不存在"
    if nickname is not None:
        if not is_valid_nickname(nickname):
            return None, "昵称无效"
        user.nickname = nickname.strip()
    if avatar is not None:
        user.avatar = avatar
    db.session.commit()
    return user, None
