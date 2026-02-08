"""
辅助函数
"""
from functools import wraps
from flask import request, jsonify
from typing import Optional, Any


def api_response(data=None, message="", code=0):
    """统一 API 响应格式"""
    return jsonify({"code": code, "message": message, "data": data})


def require_json(*keys):
    """要求请求体为 JSON 且包含指定 key"""
    def decorator(f):
        @wraps(f)
        def inner(*args, **kwargs):
            if not request.is_json:
                return api_response(message="需要 JSON 请求体", code=400)
            j = request.get_json() or {}
            for key in keys:
                if key not in j:
                    return api_response(message=f"缺少参数: {key}", code=400)
            return f(*args, **kwargs)
        return inner
    return decorator


def require_auth(f):
    """要求用户已认证，自动从认证头获取用户并注入参数"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 动态导入避免循环依赖
        from services.auth_service import decode_token
        from controllers.user_controller import get_user_by_id
        
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return api_response(message="未登录", code=401)
        token = auth[7:]
        payload = decode_token(token)
        if not payload:
            return api_response(message="无效的令牌", code=401)
        user = get_user_by_id(payload.get("user_id"))
        if not user:
            return api_response(message="用户不存在", code=401)
        return f(*args, user=user, **kwargs)
    return decorated
