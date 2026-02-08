"""
数据验证
"""
import re


def is_valid_link_id(link_id):
    """通讯码：8 位数字"""
    if not link_id or not isinstance(link_id, str):
        return False
    return bool(re.match(r"^\d{8}$", link_id.strip()))


def is_valid_nickname(nickname):
    """昵称：非空，长度合理"""
    if not nickname or not isinstance(nickname, str):
        return False
    return 1 <= len(nickname.strip()) <= 64
