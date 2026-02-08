# LinkIn - 即时通讯应用

一个现代化的实时即时通讯平台，支持私聊、群聊、文件传输等功能。

## 主要功能

- **用户认证** — 注册/登录、通讯码（Link ID）管理
- **好友管理** — 添加/删除好友、搜索用户
- **私聊** — 实时文本消息、文件传输
- **群聊** — 创建群组、邀请/移除成员、解散群组
- **消息功能** — 消息搜索、未读数统计、标记已读
- **个人资料** — 头像上传、昵称修改
- **多语言支持** — 中英文切换
- **实时推送** — WebSocket 即时消息通知

## 技术栈

### 后端

- **Python 3.8+**
- **Flask** — Web 框架
- **Flask-SocketIO** — WebSocket 实时通讯
- **SQLAlchemy** — ORM 数据库框架
- **Flask-SQLAlchemy** — Flask 数据库集成
- **JWT** — 身份验证
- **bcrypt** — 密码加密

### 前端

- **Vue 3** — 前端框架（CDN 引入）
- **原生 CSS** — 响应式设计和动画效果

### 数据库

- **SQLite** — 轻量级数据库（开发环境）

## 项目结构

```
LinkIn/
├── app.py                  # 应用入口
├── requirements.txt        # 项目依赖
├── config/                 # 配置模块
│   ├── settings.py         # 应用设置
│   └── database.py         # 数据库配置
├── models/                 # 数据模型
│   ├── user.py            # 用户模型
│   ├── friendship.py       # 好友关系模型
│   ├── message.py         # 消息模型
│   └── group.py           # 群组模型
├── controllers/           # 业务逻辑
│   ├── user_controller.py
│   ├── friend_controller.py
│   ├── message_controller.py
│   └── group.py
├── services/              # 服务层
│   ├── auth_service.py    # 认证服务
│   ├── file_service.py    # 文件服务
│   └── notification_service.py
├── api/                   # API 路由
│   ├── routes.py          # REST API
│   └── websocket.py       # WebSocket 事件处理
├── utils/                 # 工具函数
│   ├── helpers.py
│   ├── validators.py
│   └── id_generator.py
├── frontend/              # 前端文件
│   ├── templates/
│   │   └── index.html     # 主页面
│   └── static/
│       ├── css/           # 样式文件
│       ├── js/            # JavaScript
│       └── i18n/          # 国际化文件
├── database/              # 数据库文件
│   └── init_db.sql        # 数据库初始化脚本
└── storage/               # 存储目录
    ├── uploads/           # 上传文件
    └── avatars/           # 用户头像
```

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/MsAiBoWithStar/linkin-chat.git
cd linkin-chat
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 运行应用

```bash
python app.py
```

应用将启动在 `http://127.0.0.1:5000`，浏览器访问即可使用。

## 使用说明

1. 首次访问点击"注册"，系统自动生成 8 位通讯码
2. 使用通讯码或昵称搜索并添加好友
3. 点击好友头像开始聊天
4. 支持发送文本、图片、文件
5. 可创建群组进行多人聊天
6. 右上角可切换中英文语言

## 许可证

MIT License

