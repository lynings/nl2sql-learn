# User 表结构

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## 字段说明
- id: 用户唯一标识
- username: 用户名，唯一
- email: 电子邮箱，唯一
- password_hash: 加密后的密码
- status: 用户状态（active/inactive/pending）
- created_at: 创建时间
- updated_at: 最后更新时间

## 业务规则
1. 用户名和邮箱必须唯一
2. 密码必须加密存储
3. 状态只能是预定义的值 