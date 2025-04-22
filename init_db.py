#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库初始化脚本
用于创建或重建数据库表结构
"""

import sqlite3
import os

def init_db():
    """初始化数据库并创建所需表"""
    # 删除现有数据库文件（如果存在）
    if os.path.exists('tcm.db'):
        os.remove('tcm.db')
    
    # 创建新的数据库
    conn = sqlite3.connect('tcm.db')
    c = conn.cursor()
    
    # 创建用户表
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'patient',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    
    # 创建中药表
    c.execute('''
    CREATE TABLE IF NOT EXISTS herbs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        pinyin TEXT,
        alias TEXT,
        category TEXT,
        property TEXT,
        taste TEXT,
        meridian TEXT,
        functions TEXT,
        indications TEXT,
        usage TEXT,
        dosage TEXT,
        contraindications TEXT,
        side_effects TEXT,
        storage TEXT,
        image_url TEXT
    )
    ''')
    
    # 创建方剂表
    c.execute('''
    CREATE TABLE IF NOT EXISTS formulas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        pinyin TEXT,
        alias TEXT,
        category TEXT,
        composition TEXT,
        preparation TEXT,
        functions TEXT,
        indications TEXT,
        usage TEXT,
        contraindications TEXT,
        modifications TEXT,
        classic_source TEXT,
        effect TEXT
    )
    ''')
    
    # 创建用户收藏中药表
    c.execute('''
    CREATE TABLE IF NOT EXISTS favorite_herbs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        herb_id INTEGER NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (herb_id) REFERENCES herbs (id),
        UNIQUE(user_id, herb_id)
    )
    ''')
    
    # 创建用户收藏方剂表
    c.execute('''
    CREATE TABLE IF NOT EXISTS favorite_formulas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        formula_id INTEGER NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (formula_id) REFERENCES formulas (id),
        UNIQUE(user_id, formula_id)
    )
    ''')

    # 创建文章表
    c.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author TEXT,
        category TEXT,
        tags TEXT,
        image_url TEXT,
        view_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建季节养生表
    c.execute('''
    CREATE TABLE IF NOT EXISTS seasonal_health (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        season TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        foods TEXT,
        exercises TEXT,
        tips TEXT,
        image_url TEXT
    )
    ''')
    
    # 创建视频教程表
    c.execute('''
    CREATE TABLE IF NOT EXISTS video_tutorials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        video_url TEXT NOT NULL,
        thumbnail_url TEXT,
        duration TEXT,
        instructor TEXT,
        view_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建预约表
    c.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        doctor_name TEXT NOT NULL,
        appointment_date DATE NOT NULL,
        appointment_time TIME NOT NULL,
        reason TEXT,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # 创建文章评论表
    c.execute('''
    CREATE TABLE IF NOT EXISTS article_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (article_id) REFERENCES articles (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # 创建文章点赞表
    c.execute('''
    CREATE TABLE IF NOT EXISTS article_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (article_id) REFERENCES articles (id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(article_id, user_id)
    )
    ''')
    
    # 创建文章收藏表
    c.execute('''
    CREATE TABLE IF NOT EXISTS article_favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (article_id) REFERENCES articles (id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(article_id, user_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print("数据库已成功初始化，表结构已创建")

if __name__ == "__main__":
    init_db() 