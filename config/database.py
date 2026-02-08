"""
数据库配置与会话管理
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = None


def init_db(app):
    """初始化数据库扩展"""
    from config.settings import DATABASE_URI, SQLITE_PATH
    
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
    if "sqlite" in DATABASE_URI and SQLITE_PATH:
        SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    
    # 可选：Flask-Migrate（若已安装）
    try:
        from flask_migrate import Migrate  # type: ignore
        global migrate
        migrate = Migrate(app, db)
    except ImportError:
        pass
    
    with app.app_context():
        from models import user, message, friendship, group  # noqa: F401 - ensure UserGroupRead created
        db.create_all()
    
    return db
