from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import sqlite3
from utils import admin_required
from datetime import datetime
import os
from werkzeug.utils import secure_filename

admin = Blueprint('admin', __name__, url_prefix='/admin')

# 数据库连接函数
def get_db_connection():
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
    return conn

# 管理员控制面板
@admin.route('/')
@admin_required
def dashboard():
    """管理员控制面板"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取各种统计数据
    cursor.execute("SELECT COUNT(*) FROM herbs")
    herbs_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM formulas")
    formulas_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM articles")
    articles_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM video_tutorials")
    videos_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users")
    users_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM appointments")
    appointments_count = cursor.fetchone()[0]
    
    # 获取最近添加的内容
    cursor.execute("SELECT * FROM herbs ORDER BY id DESC LIMIT 5")
    recent_herbs = cursor.fetchall()
    
    cursor.execute("SELECT * FROM articles ORDER BY created_at DESC LIMIT 5")
    recent_articles = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                          herbs_count=herbs_count,
                          formulas_count=formulas_count,
                          articles_count=articles_count,
                          videos_count=videos_count,
                          users_count=users_count,
                          appointments_count=appointments_count,
                          recent_herbs=recent_herbs,
                          recent_articles=recent_articles)

# 中药管理
@admin.route('/herbs')
@admin_required
def manage_herbs():
    """中药管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    conn = get_db_connection()
    
    # 构建查询条件
    query = "SELECT * FROM herbs"
    params = []
    
    if search:
        query += " WHERE (name LIKE ? OR pinyin LIKE ? OR alias LIKE ?)"
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
    cursor = conn.cursor()
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]
    
    # 添加分页和排序
    query += " ORDER BY name LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    herbs = cursor.fetchall()
    
    # 获取所有分类
    cursor.execute("SELECT DISTINCT category FROM herbs ORDER BY category")
    categories = [row[0] for row in cursor.fetchall() if row[0]]
    
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('admin/herbs_manage.html', 
                          herbs=herbs, 
                          page=page, 
                          total_pages=total_pages, 
                          search=search,
                          category=category,
                          categories=categories,
                          per_page=per_page)

@admin.route('/herb/<int:herb_id>')
@admin_required
def view_herb(herb_id):
    """查看中药详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM herbs WHERE id = ?", (herb_id,))
    herb = cursor.fetchone()
    
    if not herb:
        conn.close()
        flash('中药不存在', 'danger')
        return redirect(url_for('admin.manage_herbs'))
    
    conn.close()
    
    return render_template('admin/herb_view.html', herb=herb)

@admin.route('/herb/add', methods=['GET', 'POST'])
@admin_required
def add_herb():
    """添加中药"""
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash('中药名称不能为空', 'danger')
            return redirect(url_for('admin.add_herb'))
        
        # 获取表单数据
        pinyin = request.form.get('pinyin', '')
        alias = request.form.get('alias', '')
        category = request.form.get('category', '')
        property = request.form.get('property', '')
        taste = request.form.get('taste', '')
        meridian = request.form.get('meridian', '')
        functions = request.form.get('functions', '')
        indications = request.form.get('indications', '')
        usage = request.form.get('usage', '')
        dosage = request.form.get('dosage', '')
        contraindications = request.form.get('contraindications', '')
        side_effects = request.form.get('side_effects', '')
        storage = request.form.get('storage', '')
        image_url = request.form.get('image_url', '')
        
        # 处理上传的图片
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                upload_folder = os.path.join('static', 'images', 'herbs')
                
                # 确保上传目录存在
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                file_path = os.path.join(upload_folder, filename)
                image_file.save(file_path)
                image_url = '/' + file_path  # 存储相对路径
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO herbs (name, pinyin, alias, category, property, taste, meridian, 
                functions, indications, usage, dosage, contraindications, side_effects, storage, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, pinyin, alias, category, property, taste, meridian, 
                      functions, indications, usage, dosage, contraindications, side_effects, storage, image_url))
            
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            
            flash(f'中药 {name} 添加成功', 'success')
            return redirect(url_for('admin.view_herb', herb_id=new_id))
        except sqlite3.IntegrityError:
            conn.close()
            flash(f'中药名称 {name} 已存在', 'danger')
            return redirect(url_for('admin.add_herb'))
        
    # GET 请求，显示添加表单
    # 获取所有分类
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM herbs ORDER BY category")
    db_categories = [row[0] for row in cursor.fetchall() if row[0]]
    
    # 确保包含补气药和补血药
    categories = list(set(db_categories + ['补气药', '补血药']))
    categories.sort()  # 按字母顺序排序
    
    conn.close()
    
    return render_template('admin/add_herb.html', categories=categories)

@admin.route('/herb/edit/<int:herb_id>', methods=['GET', 'POST'])
@admin_required
def edit_herb(herb_id):
    """编辑中药"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM herbs WHERE id = ?", (herb_id,))
    herb = cursor.fetchone()
    
    if not herb:
        conn.close()
        flash('中药不存在', 'danger')
        return redirect(url_for('admin.manage_herbs'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash('中药名称不能为空', 'danger')
            return redirect(url_for('admin.edit_herb', herb_id=herb_id))
        
        # 获取表单数据
        pinyin = request.form.get('pinyin', '')
        alias = request.form.get('alias', '')
        category = request.form.get('category', '')
        property = request.form.get('property', '')
        taste = request.form.get('taste', '')
        meridian = request.form.get('meridian', '')
        functions = request.form.get('functions', '')
        indications = request.form.get('indications', '')
        usage = request.form.get('usage', '')
        dosage = request.form.get('dosage', '')
        contraindications = request.form.get('contraindications', '')
        side_effects = request.form.get('side_effects', '')
        storage = request.form.get('storage', '')
        image_url = request.form.get('image_url', herb['image_url'])
        
        # 处理上传的图片
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                upload_folder = os.path.join('static', 'images', 'herbs')
                
                # 确保上传目录存在
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                file_path = os.path.join(upload_folder, filename)
                image_file.save(file_path)
                image_url = '/' + file_path  # 存储相对路径
        
        try:
            cursor.execute("""
                UPDATE herbs SET name=?, pinyin=?, alias=?, category=?, property=?, taste=?, meridian=?, 
                functions=?, indications=?, usage=?, dosage=?, contraindications=?, side_effects=?, storage=?, image_url=?
                WHERE id=?
                """, (name, pinyin, alias, category, property, taste, meridian, 
                      functions, indications, usage, dosage, contraindications, side_effects, storage, image_url, herb_id))
            
            conn.commit()
            conn.close()
            
            flash(f'中药 {name} 更新成功', 'success')
            return redirect(url_for('admin.view_herb', herb_id=herb_id))
        except sqlite3.IntegrityError:
            conn.close()
            flash(f'中药名称 {name} 已存在', 'danger')
            return redirect(url_for('admin.edit_herb', herb_id=herb_id))
    
    # GET 请求，显示编辑表单
    # 获取所有分类
    cursor.execute("SELECT DISTINCT category FROM herbs ORDER BY category")
    db_categories = [row[0] for row in cursor.fetchall() if row[0]]
    
    # 确保包含补气药和补血药
    categories = list(set(db_categories + ['补气药', '补血药']))
    categories.sort()  # 按字母顺序排序
    
    conn.close()
    
    return render_template('admin/edit_herb.html', herb=herb, categories=categories)

@admin.route('/herb/delete/<int:herb_id>', methods=['POST'])
@admin_required
def delete_herb(herb_id):
    """删除中药"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM herbs WHERE id = ?", (herb_id,))
    herb = cursor.fetchone()
    
    if not herb:
        conn.close()
        flash('中药不存在', 'danger')
        return redirect(url_for('admin.manage_herbs'))
    
    herb_name = herb['name']
    
    # 检查是否有方剂引用了这个中药
    # 这里需要根据实际应用情况修改查询
    # cursor.execute("SELECT COUNT(*) FROM formula_herbs WHERE herb_id = ?", (herb_id,))
    # references = cursor.fetchone()[0]
    
    # if references > 0:
    #     conn.close()
    #     flash(f'无法删除中药 {herb_name}，因为有 {references} 个方剂引用了它', 'danger')
    #     return redirect(url_for('admin.view_herb', herb_id=herb_id))
    
    # 删除收藏记录
    cursor.execute("DELETE FROM favorite_herbs WHERE herb_id = ?", (herb_id,))
    
    # 删除中药
    cursor.execute("DELETE FROM herbs WHERE id = ?", (herb_id,))
    
    conn.commit()
    conn.close()
    
    flash(f'中药 {herb_name} 已删除', 'success')
    return redirect(url_for('admin.manage_herbs'))

# 方剂管理
@admin.route('/formulas')
@admin_required
def formulas():
    """方剂管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row  # 设置row_factory为sqlite3.Row
    cursor = conn.cursor()
    
    # 构建查询条件
    query = "SELECT * FROM formulas"
    params = []
    
    if search:
        query += " WHERE (name LIKE ? OR pinyin LIKE ? OR alias LIKE ?)"
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
    query += " ORDER BY name LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    formulas = [dict(row) for row in cursor.fetchall()]  # 将Row对象转换为字典
    
    # 获取所有分类
    cursor.execute("SELECT DISTINCT category FROM formulas ORDER BY category")
    categories = [row[0] for row in cursor.fetchall() if row[0]]
    
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('admin/manage_formulas.html', 
                          formulas=formulas, 
                          page=page, 
                          total_pages=total_pages, 
                          total=total,
                          search=search,
                          category=category,
                          categories=categories,
                          per_page=per_page)

# 添加方剂
@admin.route('/formula/add', methods=['GET', 'POST'])
@admin_required
def add_formula():
    """添加方剂"""
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash('方剂名称不能为空', 'danger')
            return redirect(url_for('admin.add_formula'))
        
        # 获取表单数据
        pinyin = request.form.get('pinyin', '')
        alias = request.form.get('alias', '')
        category = request.form.get('category', '')
        composition = request.form.get('composition', '')
        preparation = request.form.get('preparation', '')
        functions = request.form.get('functions', '')
        indications = request.form.get('indications', '')
        usage = request.form.get('usage', '')
        contraindications = request.form.get('contraindications', '')
        modifications = request.form.get('modifications', '')
        classic_source = request.form.get('classic_source', '')
        effect = request.form.get('effect', functions)  # 如果未提供，使用功效字段
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO formulas (name, pinyin, alias, category, composition, preparation, 
                functions, indications, usage, contraindications, modifications, classic_source, effect)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, pinyin, alias, category, composition, preparation, 
                      functions, indications, usage, contraindications, modifications, classic_source, effect))
            
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            
            flash(f'方剂 {name} 添加成功', 'success')
            return redirect(url_for('admin.formulas'))
        except sqlite3.IntegrityError:
            conn.close()
            flash(f'方剂名称 {name} 已存在', 'danger')
            return redirect(url_for('admin.add_formula'))
        
    # GET 请求，显示添加表单
    # 获取所有分类
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM formulas ORDER BY category")
    categories = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    
    return render_template('admin/add_formula.html', categories=categories)

# 查看方剂详情
@admin.route('/formula/<int:formula_id>')
@admin_required
def view_formula(formula_id):
    """查看方剂详情"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM formulas WHERE id = ?", (formula_id,))
    formula = cursor.fetchone()
    
    if not formula:
        conn.close()
        flash('方剂不存在', 'danger')
        return redirect(url_for('admin.formulas'))
    
    conn.close()
    
    return render_template('admin/formula_view.html', formula=formula)

# 编辑方剂
@admin.route('/formula/edit/<int:formula_id>', methods=['GET', 'POST'])
@admin_required
def edit_formula(formula_id):
    """编辑方剂"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM formulas WHERE id = ?", (formula_id,))
    formula = cursor.fetchone()
    
    if not formula:
        conn.close()
        flash('方剂不存在', 'danger')
        return redirect(url_for('admin.formulas'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash('方剂名称不能为空', 'danger')
            return redirect(url_for('admin.edit_formula', formula_id=formula_id))
        
        # 获取表单数据
        pinyin = request.form.get('pinyin', '')
        alias = request.form.get('alias', '')
        category = request.form.get('category', '')
        composition = request.form.get('composition', '')
        preparation = request.form.get('preparation', '')
        functions = request.form.get('functions', '')
        indications = request.form.get('indications', '')
        usage = request.form.get('usage', '')
        contraindications = request.form.get('contraindications', '')
        modifications = request.form.get('modifications', '')
        classic_source = request.form.get('classic_source', '')
        effect = request.form.get('effect', functions)  # 如果未提供，使用功效字段
        
        try:
            cursor.execute("""
                UPDATE formulas SET 
                name=?, pinyin=?, alias=?, category=?, composition=?, preparation=?,
                functions=?, indications=?, usage=?, contraindications=?, modifications=?, 
                classic_source=?, effect=?
                WHERE id=?
                """, (name, pinyin, alias, category, composition, preparation, 
                      functions, indications, usage, contraindications, modifications, 
                      classic_source, effect, formula_id))
            
            conn.commit()
            conn.close()
            
            flash(f'方剂 {name} 更新成功', 'success')
            return redirect(url_for('admin.view_formula', formula_id=formula_id))
        except sqlite3.IntegrityError:
            conn.close()
            flash(f'方剂名称 {name} 已存在', 'danger')
            return redirect(url_for('admin.edit_formula', formula_id=formula_id))
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'更新方剂时出错: {str(e)}', 'danger')
            return redirect(url_for('admin.edit_formula', formula_id=formula_id))
    
    # GET 请求，显示编辑表单
    # 获取所有分类
    cursor.execute("SELECT DISTINCT category FROM formulas ORDER BY category")
    categories = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    
    return render_template('admin/formula_edit.html', formula=formula, categories=categories)

# 删除方剂
@admin.route('/formula/delete/<int:formula_id>', methods=['POST'])
@admin_required
def delete_formula(formula_id):
    """删除方剂"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM formulas WHERE id = ?", (formula_id,))
    formula = cursor.fetchone()
    
    if not formula:
        conn.close()
        flash('方剂不存在', 'danger')
        return redirect(url_for('admin.formulas'))
    
    formula_name = formula['name']
    
    # 删除方剂
    cursor.execute("DELETE FROM formulas WHERE id = ?", (formula_id,))
    
    conn.commit()
    conn.close()
    
    flash(f'方剂 {formula_name} 已删除', 'success')
    return redirect(url_for('admin.formulas'))

# 文章管理
@admin.route('/articles')
@admin_required
def manage_articles():
    """文章管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    conn = get_db_connection()
    
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
    cursor = conn.cursor()
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
    
    return render_template('admin/articles_manage.html', 
                          articles=articles, 
                          page=page, 
                          total_pages=total_pages, 
                          search=search,
                          category=category,
                          categories=categories,
                          per_page=per_page)

# 文章管理部分
@admin.route('/article/add', methods=['GET', 'POST'])
@admin_required
def add_article():
    """添加文章"""
    if request.method == 'POST':
        title = request.form.get('title')
        if not title:
            flash('文章标题不能为空', 'danger')
            return redirect(url_for('admin.add_article'))
        
        # 获取表单数据
        content = request.form.get('content', '')
        summary = request.form.get('summary', '')
        category = request.form.get('category', '')
        tags = request.form.get('tags', '')
        author = request.form.get('author', current_user.username)
        status = request.form.get('status', 'published')
        image_url = request.form.get('image_url', '')
        
        # 处理上传的图片
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                upload_folder = os.path.join('static', 'images', 'articles')
                
                # 确保上传目录存在
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                file_path = os.path.join(upload_folder, filename)
                image_file.save(file_path)
                image_url = '/' + file_path  # 存储相对路径
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
            INSERT INTO articles (
                title, content, summary, category, tags, author, status, 
                created_at, view_count, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), 0, ?)
            """, (title, content, summary, category, tags, author, status, image_url))
            
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            
            flash(f'文章 "{title}" 添加成功', 'success')
            return redirect(url_for('admin.manage_articles'))
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'添加文章时出错: {str(e)}', 'danger')
            return redirect(url_for('admin.add_article'))
        
    # GET 请求，显示添加表单
    # 获取所有分类
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM articles ORDER BY category")
    categories = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    
    return render_template('admin/article_add.html', categories=categories)

@admin.route('/article/edit/<int:article_id>', methods=['GET', 'POST'])
@admin_required
def edit_article(article_id):
    """编辑文章"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    article = cursor.fetchone()
    
    if not article:
        conn.close()
        flash('文章不存在', 'danger')
        return redirect(url_for('admin.manage_articles'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        if not title:
            flash('文章标题不能为空', 'danger')
            return redirect(url_for('admin.edit_article', article_id=article_id))
        
        # 获取表单数据
        content = request.form.get('content', '')
        summary = request.form.get('summary', '')
        category = request.form.get('category', '')
        tags = request.form.get('tags', '')
        author = request.form.get('author', article['author'])
        status = request.form.get('status', 'published')
        image_url = request.form.get('image_url', article['image_url'])
        
        # 处理上传的图片
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                upload_folder = os.path.join('static', 'images', 'articles')
                
                # 确保上传目录存在
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                file_path = os.path.join(upload_folder, filename)
                image_file.save(file_path)
                image_url = '/' + file_path  # 存储相对路径
        
        try:
            cursor.execute("""
            UPDATE articles SET 
                title = ?, content = ?, summary = ?, category = ?, tags = ?, 
                author = ?, status = ?, image_url = ?
            WHERE id = ?
            """, (title, content, summary, category, tags, author, status, image_url, article_id))
            
            conn.commit()
            conn.close()
            
            flash(f'文章 "{title}" 更新成功', 'success')
            return redirect(url_for('article.detail', article_id=article_id))
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'更新文章时出错: {str(e)}', 'danger')
            return redirect(url_for('admin.edit_article', article_id=article_id))
    
    # GET 请求，显示编辑表单
    # 获取所有分类
    cursor.execute("SELECT DISTINCT category FROM articles ORDER BY category")
    categories = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()
    
    return render_template('admin/article_edit.html', article=article, categories=categories)

@admin.route('/article/delete/<int:article_id>', methods=['POST'])
@admin_required
def delete_article(article_id):
    """删除文章"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT title, image_url FROM articles WHERE id = ?", (article_id,))
    article = cursor.fetchone()
    
    if not article:
        conn.close()
        flash('文章不存在', 'danger')
        return redirect(url_for('admin.manage_articles'))
    
    # 删除文章图片
    if article['image_url'] and os.path.exists(os.path.join('static', article['image_url'].lstrip('/'))):
        os.remove(os.path.join('static', article['image_url'].lstrip('/')))
    
    # 删除文章
    cursor.execute("DELETE FROM articles WHERE id = ?", (article_id,))
    conn.commit()
    conn.close()
    
    flash(f'文章 "{article["title"]}" 已删除', 'success')
    return redirect(url_for('admin.manage_articles'))

# 视频管理
@admin.route('/videos')
@admin_required
def manage_videos():
    """视频管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    conn = get_db_connection()
    
    # 构建查询条件
    query = "SELECT * FROM video_tutorials"
    params = []
    
    if search:
        query += " WHERE (title LIKE ? OR description LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
    
    if category:
        if search:
            query += " AND category = ?"
        else:
            query += " WHERE category = ?"
        params.append(category)
    
    # 获取总数
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    cursor = conn.cursor()
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]
    
    # 添加分页和排序
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    videos = cursor.fetchall()
    
    # 获取所有分类
    cursor.execute("SELECT DISTINCT category FROM video_tutorials ORDER BY category")
    categories = [row[0] for row in cursor.fetchall() if row[0]]
    
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('admin/videos_manage.html', 
                          videos=videos, 
                          page=page, 
                          total_pages=total_pages, 
                          search=search,
                          category=category,
                          categories=categories,
                          per_page=per_page)

# 用户管理
@admin.route('/users')
@admin_required
def manage_users():
    """用户管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    
    conn = get_db_connection()
    
    # 构建查询条件
    query = "SELECT * FROM users"
    params = []
    
    if search:
        query += " WHERE (username LIKE ? OR email LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
    
    if role:
        if search:
            query += " AND role = ?"
        else:
            query += " WHERE role = ?"
        params.append(role)
    
    # 获取总数
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    cursor = conn.cursor()
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]
    
    # 添加分页和排序
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    users = cursor.fetchall()
    
    # 获取所有角色
    cursor.execute("SELECT DISTINCT role FROM users ORDER BY role")
    roles = [row[0] for row in cursor.fetchall() if row[0]]
    
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('admin/users_manage.html', 
                          users=users, 
                          page=page, 
                          total_pages=total_pages, 
                          search=search,
                          role=role,
                          roles=roles,
                          per_page=per_page)

# 添加视频
@admin.route('/video/add', methods=['GET', 'POST'])
@admin_required
def add_video():
    """添加视频教程"""
    if request.method == 'POST':
        title = request.form.get('title')
        if not title:
            flash('视频标题不能为空', 'danger')
            return redirect(url_for('admin.add_video'))
        
        # 获取表单数据
        description = request.form.get('description', '')
        category = request.form.get('category', '')
        video_url = request.form.get('video_url', '')
        duration = request.form.get('duration', '')
        instructor = request.form.get('instructor', '')
        thumbnail_url = request.form.get('thumbnail_url', '')
        
        # 处理上传的缩略图
        if 'thumbnail' in request.files:
            thumbnail_file = request.files['thumbnail']
            if thumbnail_file and thumbnail_file.filename:
                filename = secure_filename(thumbnail_file.filename)
                upload_folder = os.path.join('static', 'images', 'videos')
                
                # 确保上传目录存在
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                file_path = os.path.join(upload_folder, filename)
                thumbnail_file.save(file_path)
                thumbnail_url = '/' + file_path  # 存储相对路径
        
        # 处理上传的视频文件
        if 'video' in request.files:
            video_file = request.files['video']
            if video_file and video_file.filename:
                filename = secure_filename(video_file.filename)
                upload_folder = os.path.join('static', 'videos')
                
                # 确保上传目录存在
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                file_path = os.path.join(upload_folder, filename)
                video_file.save(file_path)
                video_url = '/' + file_path  # 存储相对路径
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
            INSERT INTO video_tutorials 
            (title, description, category, video_url, thumbnail_url, duration, instructor, created_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (title, description, category, video_url, thumbnail_url, duration, instructor))
            
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            
            flash(f'视频教程 {title} 添加成功', 'success')
            return redirect(url_for('admin.manage_videos'))
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'添加视频教程时出错: {str(e)}', 'danger')
            return redirect(url_for('admin.add_video'))
        
    # GET 请求，显示添加表单
    return render_template('admin/video_add.html')

@admin.route('/video/edit/<int:video_id>', methods=['GET', 'POST'])
@admin_required
def edit_video(video_id):
    """编辑视频教程"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM video_tutorials WHERE id = ?", (video_id,))
    video = cursor.fetchone()
    
    if not video:
        conn.close()
        flash('视频不存在', 'danger')
        return redirect(url_for('admin.manage_videos'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        if not title:
            flash('视频标题不能为空', 'danger')
            return redirect(url_for('admin.edit_video', video_id=video_id))
        
        # 获取表单数据
        description = request.form.get('description', '')
        category = request.form.get('category', '')
        video_url = request.form.get('video_url', video['video_url'])
        duration = request.form.get('duration', '')
        instructor = request.form.get('instructor', '')
        thumbnail_url = request.form.get('thumbnail_url', video['thumbnail_url'])
        
        # 处理上传的缩略图
        if 'thumbnail' in request.files:
            thumbnail_file = request.files['thumbnail']
            if thumbnail_file and thumbnail_file.filename:
                filename = secure_filename(thumbnail_file.filename)
                upload_folder = os.path.join('static', 'images', 'videos')
                
                # 确保上传目录存在
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                file_path = os.path.join(upload_folder, filename)
                thumbnail_file.save(file_path)
                thumbnail_url = '/' + file_path  # 存储相对路径
        
        # 处理上传的视频文件
        if 'video' in request.files:
            video_file = request.files['video']
            if video_file and video_file.filename:
                filename = secure_filename(video_file.filename)
                upload_folder = os.path.join('static', 'videos')
                
                # 确保上传目录存在
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                
                file_path = os.path.join(upload_folder, filename)
                video_file.save(file_path)
                video_url = '/' + file_path  # 存储相对路径
        
        try:
            cursor.execute("""
            UPDATE video_tutorials SET 
            title = ?, description = ?, category = ?, video_url = ?, 
            thumbnail_url = ?, duration = ?, instructor = ? 
            WHERE id = ?
            """, (title, description, category, video_url, thumbnail_url, duration, instructor, video_id))
            
            conn.commit()
            conn.close()
            
            flash(f'视频教程 {title} 更新成功', 'success')
            return redirect(url_for('admin.manage_videos'))
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'更新视频教程时出错: {str(e)}', 'danger')
            return redirect(url_for('admin.edit_video', video_id=video_id))
    
    # GET 请求，显示编辑表单
    conn.close()
    return render_template('admin/video_edit.html', video=video)

@admin.route('/video/delete/<int:video_id>', methods=['POST'])
@admin_required
def delete_video(video_id):
    """删除视频教程"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM video_tutorials WHERE id = ?", (video_id,))
    video = cursor.fetchone()
    
    if not video:
        conn.close()
        flash('视频不存在', 'danger')
        return redirect(url_for('admin.manage_videos'))
    
    try:
        # 删除视频文件
        if video['video_url'] and os.path.exists(os.path.join('static', video['video_url'].lstrip('/'))):
            os.remove(os.path.join('static', video['video_url'].lstrip('/')))
        
        # 删除缩略图
        if video['thumbnail_url'] and os.path.exists(os.path.join('static', video['thumbnail_url'].lstrip('/'))):
            os.remove(os.path.join('static', video['thumbnail_url'].lstrip('/')))
        
        # 删除数据库记录
        cursor.execute("DELETE FROM video_tutorials WHERE id = ?", (video_id,))
        conn.commit()
        conn.close()
        
        flash('视频教程删除成功', 'success')
    except Exception as e:
        conn.rollback()
        conn.close()
        flash(f'删除视频教程时出错: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_videos'))

# 修改用户角色
@admin.route('/user/role/<int:user_id>', methods=['POST'])
@admin_required
def change_user_role(user_id):
    """修改用户角色"""
    if user_id == current_user.id:
        flash('不能修改自己的角色', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    new_role = request.form.get('role')
    if not new_role:
        flash('角色不能为空', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        flash('用户不存在', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()
    
    flash(f'用户 {user["username"]} 的角色已更新为 {new_role}', 'success')
    return redirect(url_for('admin.manage_users')) 