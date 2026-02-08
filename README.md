# LinkIn - 即时通讯应用

一个现代化的实时即时通讯平台，支持私聊、群聊、文件传输等功能。

## 主要功能

- **用户认证** — 注册/登录、通讯码（Link ID）管理
- **好友管理** — 添加/删除好友、搜索用户
- **私聊** — 实时文本消息、文件传输、图片分享
- **群聊** — 创建群组、邀请成员、群消息管理
- **消息功能** — 消息收藏、搜索、未读数统计
- **个人资料** — 头像上传、昵称修改
- **多语言支持** — 中英文切换
- **实时推送** — WebSocket 即时消息推送

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

- **Vue 3** — 前端框架
- **原生 JavaScript** — DOM 操作和事件处理
- **CSS 3** — 响应式设计和动画

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

## 安装指南

1. **安装环境**

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
python app.py
```

应用将启动在 `http://127.0.0.1:5000`

## API 文档

### 认证接口

- `POST /api/register` — 用户注册
- `POST /api/login` — 用户登录

### 用户接口

- `GET /api/me` — 获取当前用户信息
- `PUT /api/profile` — 更新个人资料

### 好友接口

- `GET /api/friends` — 获取好友列表
- `POST /api/friends/search` — 搜索用户
- `POST /api/friends/add` — 添加好友
- `POST /api/friends/delete` — 删除好友

### 消息接口

- `POST /api/messages/private` — 发送私聊消息
- `GET /api/messages/private/<user_id>` — 获取私聊消息
- `POST /api/messages/group` — 发送群消息
- `GET /api/messages/group/<group_id>` — 获取群消息
- `POST /api/messages/read` — 标记消息已读
- `GET /api/messages/search` — 搜索消息

### 群组接口

- `GET /api/groups` — 获取用户群组列表
- `POST /api/groups` — 创建新群组
- `POST /api/groups/<group_id>/invite` — 邀请成员
- `POST /api/groups/<group_id>/kick` — 移除成员
- `POST /api/groups/<group_id>/dissolve` — 解散群组

### WebSocket 事件

- `authenticate` — 用户认证
- `new_message` — 接收新消息
- `friend_added` — 好友添加通知
- `friend_removed` — 好友删除通知
- `group_added` — 群组添加通知
- `profile_updated` — 个人资料更新通知

## 文件传输

用户可以在私聊和群聊中上传和分享文件。文件存储在 `storage/` 目录下，通过 `/storage/<path>` 路由访问。

## 消息搜索

支持在私聊和群聊中搜索文本消息，搜索结果按时间倒序排列。

## 多语言支持

应用支持中文和英文，用户可在界面右上角切换语言，设置会保存在本地。

## 故障排除

### 端口被占用

如果 5000 端口已被占用，可修改 `app.py` 中的 `port` 参数。



