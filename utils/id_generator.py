"""
8 位数字通讯码（LinkID）生成器
"""
import random
from config.database import db
from models.user import User


def generate_link_id(length=8):
    """
    生成唯一的 8 位数字 LinkID。
    若与已有用户冲突则递归重试。
    """
    digits = "0123456789"
    # 首位不为 0，避免与数字歧义
    first = random.choice(digits[1:])
    rest = "".join(random.choices(digits, k=length - 1))
    link_id = first + rest
    if link_id_exists(link_id):
        return generate_link_id(length)
    return link_id


def link_id_exists(link_id):
    """检查 link_id 是否已被占用"""
    return db.session.query(User).filter(User.link_id == link_id).first() is not None
