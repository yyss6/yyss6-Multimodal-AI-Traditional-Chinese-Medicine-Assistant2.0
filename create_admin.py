#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
创建管理员用户的脚本
"""

import sqlite3
from werkzeug.security import generate_password_hash

def create_admin_user():
    """创建一个管理员用户"""
    conn = sqlite3.connect('tcm.db')
    cursor = conn.cursor()
    
    # 检查用户是否已存在
    cursor.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    admin_user = cursor.fetchone()
    
    if admin_user:
        print("管理员用户已存在")
        conn.close()
        return
    
    # 创建管理员用户
    hashed_password = generate_password_hash("admin123")
    
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
        ("admin", "admin@example.com", hashed_password, "admin")
    )
    
    conn.commit()
    conn.close()
    
    print("管理员用户已创建成功！")
    print("用户名: admin")
    print("密码: admin123")
    print("请立即登录并修改默认密码")

if __name__ == "__main__":
    create_admin_user() 