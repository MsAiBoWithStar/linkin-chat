-- LinkIn 数据库初始化（参考）
-- 实际表结构由 SQLAlchemy 的 db.create_all() 自动创建，本文件仅作文档与手工初始化参考。

-- users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id VARCHAR(16) NOT NULL UNIQUE,
    nickname VARCHAR(64) NOT NULL DEFAULT '',
    avatar VARCHAR(256),
    password_hash VARCHAR(128),
    created_at DATETIME,
    updated_at DATETIME
);
CREATE INDEX IF NOT EXISTS ix_users_link_id ON users(link_id);

-- friendships
CREATE TABLE IF NOT EXISTS friendships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    friend_id INTEGER NOT NULL REFERENCES users(id),
    created_at DATETIME,
    UNIQUE(user_id, friend_id)
);

-- groups
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name VARCHAR(128) NOT NULL,
    group_avatar VARCHAR(256),
    owner_id INTEGER NOT NULL REFERENCES users(id),
    created_at DATETIME
);

-- group_members
CREATE TABLE IF NOT EXISTS group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES groups(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    role VARCHAR(16) NOT NULL DEFAULT 'member',
    joined_at DATETIME,
    UNIQUE(group_id, user_id)
);

-- messages
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL REFERENCES users(id),
    receiver_id INTEGER REFERENCES users(id),
    group_id INTEGER REFERENCES groups(id),
    message_type VARCHAR(16) NOT NULL DEFAULT 'text',
    content TEXT,
    file_path VARCHAR(512),
    file_name VARCHAR(256),
    is_read BOOLEAN DEFAULT 0,
    created_at DATETIME
);
