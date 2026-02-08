"""
群组业务逻辑
"""
from config.database import db
from models.group import Group, GroupMember, UserGroupRead
from models.message import Message
from models.user import User
from controllers.friend_controller import is_friend


def is_member(user_id, group_id):
    return GroupMember.query.filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
    ).first() is not None


def get_member_role(user_id, group_id):
    m = GroupMember.query.filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
    ).first()
    return m.role if m else None


def create_group(owner_id, group_name, member_ids=None):
    member_ids = member_ids or []
    group = Group(owner_id=owner_id, group_name=group_name)
    db.session.add(group)
    db.session.flush()
    owner_member = GroupMember(group_id=group.id, user_id=owner_id, role="owner")
    db.session.add(owner_member)
    for uid in member_ids:
        if uid != owner_id and is_friend(owner_id, uid):
            db.session.add(GroupMember(group_id=group.id, user_id=uid, role="member"))
    db.session.commit()
    return group, None


def invite_member(operator_id, group_id, user_id):
    if not is_member(operator_id, group_id):
        return None, "您不在该群中"
    role = get_member_role(operator_id, group_id)
    if role not in ("owner", "admin"):
        return None, "无权限邀请"
    if is_member(user_id, group_id):
        return None, "已在群中"
    if not is_friend(operator_id, user_id):
        return None, "仅可邀请好友"
    db.session.add(GroupMember(group_id=group_id, user_id=user_id, role="member"))
    db.session.commit()
    return True, None


def kick_member(operator_id, group_id, user_id):
    if not is_member(operator_id, group_id):
        return None, "您不在该群中"
    op_role = get_member_role(operator_id, group_id)
    target_role = get_member_role(user_id, group_id)
    if not target_role:
        return None, "该用户不在群中"
    if op_role == "member":
        return None, "无权限"
    if target_role == "owner":
        return None, "不能踢出群主"
    if op_role == "admin" and target_role == "admin":
        return None, "管理员不能踢出管理员"
    GroupMember.query.filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
    ).delete()
    db.session.commit()
    return True, None


def dissolve_group(operator_id, group_id):
    g = Group.query.get(group_id)
    if not g:
        return None, "群不存在"
    if g.owner_id != operator_id:
        return None, "仅群主可解散"
    Message.query.filter(Message.group_id == group_id).delete(synchronize_session=False)  # type: ignore
    UserGroupRead.query.filter(UserGroupRead.group_id == group_id).delete(synchronize_session=False)  # type: ignore
    db.session.delete(g)
    db.session.commit()
    return True, None


def get_user_groups(user_id):
    members = GroupMember.query.filter(GroupMember.user_id == user_id).all()
    return [m.group.to_dict() for m in members if m.group]


def get_group_members(group_id, current_user_id):
    """获取群成员列表（仅群成员可调）"""
    if not is_member(current_user_id, group_id):
        return None
    members = GroupMember.query.filter(GroupMember.group_id == group_id).all()
    return [m.to_dict() for m in members]
