#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文章路由模块
用于处理文章相关的路由和功能
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import sqlite3
from datetime import datetime

article = Blueprint('article', __name__, url_prefix='/article')

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
    return conn

@article.route('/')
def index():
    """文章首页，重定向到文章列表"""
    return redirect(url_for('article.article_list'))

@article.route('/list')
def article_list():
    """显示文章列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 4
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 构建查询条件
    query = "SELECT * FROM articles"
    params = []
    
    if search:
        query += " WHERE (title LIKE ? OR content LIKE ? OR tags LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    if category:
        if search:
            query += " AND category = ?"
        else:
            query += " WHERE category = ?"
        params.append(category)
    
    # 获取总数
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]
    
    # 添加分页和排序
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    articles = cursor.fetchall()
    
    # 获取所有分类
    cursor.execute("SELECT DISTINCT category FROM articles ORDER BY category")
    categories = [row[0] for row in cursor.fetchall() if row[0]]
    
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('articles_list.html', 
                          articles=articles, 
                          page=page, 
                          total_pages=total_pages, 
                          search=search,
                          category=category,
                          categories=categories)

@article.route('/<int:article_id>')
def detail(article_id):
    """显示文章详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 更新浏览量
    cursor.execute("UPDATE articles SET view_count = view_count + 1 WHERE id = ?", (article_id,))
    conn.commit()
    
    # 获取文章
    cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    article = cursor.fetchone()
    
    if not article:
        conn.close()
        flash('文章不存在', 'danger')
        return redirect(url_for('article.article_list'))
    
    # 获取相关文章
    if article['tags']:
        tags = article['tags'].split(',')
        placeholders = ', '.join(['?' for _ in tags])
        like_conditions = ' OR '.join([f"tags LIKE ?" for _ in tags])
        params = [f"%{tag.strip()}%" for tag in tags]
        
        cursor.execute(f"""
            SELECT * FROM articles 
            WHERE id != ? AND ({like_conditions})
            ORDER BY created_at DESC LIMIT 5
        """, [article_id] + params)
        related_articles = cursor.fetchall()
    else:
        related_articles = []
    
    # 获取热门文章
    cursor.execute("""
        SELECT * FROM articles 
        WHERE id != ? 
        ORDER BY view_count DESC 
        LIMIT 5
    """, (article_id,))
    popular_articles = cursor.fetchall()
    
    # 获取热门标签
    cursor.execute("""
        SELECT tags FROM articles
        WHERE tags IS NOT NULL AND tags != ''
    """)
    
    all_tags = []
    for row in cursor.fetchall():
        if row['tags']:
            all_tags.extend([tag.strip() for tag in row['tags'].split(',')])
    
    # 计算标签频率
    tag_counts = {}
    for tag in all_tags:
        if tag:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    # 获取最常用的10个标签
    popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    popular_tags = [tag[0] for tag in popular_tags]
    
    # 检查当前用户是否已点赞/收藏
    is_liked = False
    is_favorited = False
    if current_user.is_authenticated:
        cursor.execute(
            "SELECT id FROM article_likes WHERE article_id = ? AND user_id = ?", 
            (article_id, current_user.id)
        )
        is_liked = cursor.fetchone() is not None
        
        cursor.execute(
            "SELECT id FROM article_favorites WHERE article_id = ? AND user_id = ?", 
            (article_id, current_user.id)
        )
        is_favorited = cursor.fetchone() is not None
    
    # 获取评论数
    cursor.execute(
        "SELECT COUNT(*) FROM article_comments WHERE article_id = ?", 
        (article_id,)
    )
    comment_count = cursor.fetchone()[0]
    
    # 获取点赞数
    cursor.execute(
        "SELECT COUNT(*) FROM article_likes WHERE article_id = ?", 
        (article_id,)
    )
    like_count = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('article_detail.html', 
                          article=article, 
                          related_articles=related_articles,
                          popular_articles=popular_articles,
                          is_liked=is_liked,
                          is_favorited=is_favorited,
                          comment_count=comment_count,
                          like_count=like_count,
                          popular_tags=popular_tags)

@article.route('/<int:article_id>/comments', methods=['GET'])
def get_comments(article_id):
    """获取文章评论"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.*, u.username 
        FROM article_comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.article_id = ?
        ORDER BY c.created_at DESC
    """, (article_id,))
    
    comments = cursor.fetchall()
    conn.close()
    
    comments_list = []
    for comment in comments:
        comments_list.append({
            'id': comment['id'],
            'content': comment['content'],
            'username': comment['username'],
            'created_at': comment['created_at']
        })
    
    return jsonify({'comments': comments_list})

@article.route('/<int:article_id>/comments', methods=['POST'])
@login_required
def add_comment(article_id):
    """添加文章评论"""
    content = request.form.get('content', '').strip()
    
    if not content:
        return jsonify({'success': False, 'message': '评论内容不能为空'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查文章是否存在
    cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '文章不存在'}), 404
    
    # 添加评论
    cursor.execute("""
        INSERT INTO article_comments (article_id, user_id, content) 
        VALUES (?, ?, ?)
    """, (article_id, current_user.id, content))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True, 
        'message': '评论添加成功',
        'comment': {
            'content': content,
            'username': current_user.username,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    })

@article.route('/<int:article_id>/like', methods=['POST'])
@login_required
def toggle_like(article_id):
    """切换文章点赞状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查文章是否存在
    cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '文章不存在'}), 404
    
    # 检查是否已经点赞
    cursor.execute(
        "SELECT id FROM article_likes WHERE article_id = ? AND user_id = ?", 
        (article_id, current_user.id)
    )
    like = cursor.fetchone()
    
    if like:
        # 取消点赞
        cursor.execute(
            "DELETE FROM article_likes WHERE article_id = ? AND user_id = ?", 
            (article_id, current_user.id)
        )
        message = '取消点赞成功'
        is_liked = False
    else:
        # 添加点赞
        cursor.execute(
            "INSERT INTO article_likes (article_id, user_id) VALUES (?, ?)", 
            (article_id, current_user.id)
        )
        message = '点赞成功'
        is_liked = True
    
    conn.commit()
    
    # 获取点赞数
    cursor.execute(
        "SELECT COUNT(*) FROM article_likes WHERE article_id = ?", 
        (article_id,)
    )
    like_count = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'success': True, 
        'message': message,
        'is_liked': is_liked,
        'like_count': like_count
    })

@article.route('/<int:article_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(article_id):
    """切换文章收藏状态"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查文章是否存在
    cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '文章不存在'}), 404
    
    # 检查是否已经收藏
    cursor.execute(
        "SELECT id FROM article_favorites WHERE article_id = ? AND user_id = ?", 
        (article_id, current_user.id)
    )
    favorite = cursor.fetchone()
    
    if favorite:
        # 取消收藏
        cursor.execute(
            "DELETE FROM article_favorites WHERE article_id = ? AND user_id = ?", 
            (article_id, current_user.id)
        )
        message = '取消收藏成功'
        is_favorited = False
    else:
        # 添加收藏
        cursor.execute(
            "INSERT INTO article_favorites (article_id, user_id) VALUES (?, ?)", 
            (article_id, current_user.id)
        )
        message = '收藏成功'
        is_favorited = True
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True, 
        'message': message,
        'is_favorited': is_favorited
    })

@article.route('/user/favorites')
@login_required
def user_favorites():
    """显示用户收藏的文章"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取用户收藏的文章总数
    cursor.execute("""
        SELECT COUNT(*) FROM article_favorites 
        WHERE user_id = ?
    """, (current_user.id,))
    total = cursor.fetchone()[0]
    
    # 获取用户收藏的文章
    cursor.execute("""
        SELECT a.* FROM articles a
        JOIN article_favorites f ON a.id = f.article_id
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC
        LIMIT ? OFFSET ?
    """, (current_user.id, per_page, (page - 1) * per_page))
    
    articles = cursor.fetchall()
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('user_favorites.html', 
                          articles=articles, 
                          page=page, 
                          total_pages=total_pages) 