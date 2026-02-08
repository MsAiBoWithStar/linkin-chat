"""
数据模型 - 统一导出
"""
from config.database import db
from models.user import User
from models.friendship import Friendship
from models.message import Message
from models.group import Group, GroupMember, UserGroupRead

__all__ = ["db", "User", "Friendship", "Message", "Group", "GroupMember", "UserGroupRead"]
