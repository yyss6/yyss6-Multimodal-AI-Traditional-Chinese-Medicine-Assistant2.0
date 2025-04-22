from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
import sqlite3
from datetime import datetime

herbs = Blueprint('herbs', __name__, url_prefix='/herbs')

# 初始化中药数据库
def init_herbs_db():
    conn = sqlite3.connect('tcm.db')
    c = conn.cursor()
    
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
        classic_source TEXT
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
    
    conn.commit()
    conn.close()

# 初始化数据库
init_herbs_db()

# 自动初始化样例数据
def auto_init_sample_data():
    """自动初始化中药和方剂样例数据"""
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM herbs")
    herb_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM formulas")
    formula_count = cursor.fetchone()[0]
    
    # 如果没有数据，则添加样例数据
    if herb_count == 0 or formula_count == 0:
        # 样例中药数据
        sample_herbs = [
            
            {
                'name': '人参', 'pinyin': 'Renshen', 'alias': '园参、黄参、血参、生晒参', 
                'category': '补气药', 'property': '微温', 'taste': '甘、微苦', 
                'meridian': '脾、肺、心、肾经', 
                'functions': '大补元气，复脉固脱，补脾益肺，生津，安神。', 
                'indications': '气虚体弱，脾肺虚弱，食少倦怠，肺虚喘咳，津伤口渴，内热消渴，气血亏虚，心悸怔仲，脱肛，久泻不止，惊悸失眠，阳痿宫冷。', 
                'usage': '煎服、研末冲服。'
            },
            {
                'name': '黄芪', 'pinyin': 'Huangqi', 'alias': '蜀芪、绵芪、黄耆', 
                'category': '补气药', 'property': '微温', 'taste': '甘', 
                'meridian': '肺、脾经', 
                'functions': '补气固表，利水消肿，托毒排脓，生肌。', 
                'indications': '气虚乏力，食少便溏，中气下陷，久泻脱肛，表虚自汗，气虚水肿，痈疽难溃，久溃不敛。', 
                'usage': '煎服，或泡酒。'
            },
            {
                'name': '白术', 'pinyin': 'Baizhu', 'alias': '于术、菊术', 
                'category': '补气药', 'property': '温', 'taste': '辛、甘、苦', 
                'meridian': '脾、胃经', 
                'functions': '健脾益气，燥湿利水，止汗，安胎。', 
                'indications': '脾胃虚弱，食少倦怠，胃下垂，泄泻，痰饮眩悸，水肿，自汗，胎动不安。', 
                'usage': '煎服，或研末。'
            },
            {
                'name': '甘草', 'pinyin': 'Gancao', 'alias': '甜草、蜜草、国老', 
                'category': '补气药', 'property': '平', 'taste': '甘', 
                'meridian': '心、肺、脾、胃经', 
                'functions': '补脾益气，润肺止咳，清热解毒，调和诸药。', 
                'indications': '脾胃虚弱，倦怠乏力，心悸气短，咳嗽痰多，痈肿疮毒，缓急解痉，缓解药物毒性。', 
                'usage': '煎服，或研末冲服。'
            },
            {
                'name': '当归', 'pinyin': 'Danggui', 'alias': '干归、秦当归', 
                'category': '补血药', 'property': '温', 'taste': '甘、辛', 
                'meridian': '肝、心、脾经', 
                'functions': '补血活血，调经止痛，润肠通便。', 
                'indications': '血虚萎黄，眩晕心悸，月经不调，经闭痛经，虚寒腹痛，肠燥便秘，风湿痹痛，跌扑损伤，痈疽疮疡。', 
                'usage': '煎服，或泡酒。'
            }


        ]
        
        # 样例方剂数据
        sample_formulas = [
            
            {
                'name': '四君子汤', 'pinyin': 'Sijunzi Tang', 'alias': '人参汤',
                'category': '补气剂', 
                'composition': '人参9g，白术9g，茯苓9g，甘草6g',
                'preparation': '水煎服',
                'functions': '补气健脾，和胃降逆。',
                'indications': '脾胃虚弱，气虚下陷，脘腹胀满，食欲不振，大便溏薄，倦怠乏力，面色萎黄。',
                'classic_source': '《太平惠民和剂局方》'
            },
            {
                'name': '四物汤', 'pinyin': 'Siwu Tang', 'alias': '补血汤',
                'category': '补血剂', 
                'composition': '当归9g，熟地黄9g，白芍9g，川芎6g',
                'preparation': '水煎服',
                'functions': '补血调经，活血化瘀。',
                'indications': '血虚证，月经不调，经色淡少，面色苍白，唇甲色淡，头晕眼花，心悸怔忡，失眠多梦。',
                'classic_source': '《太平惠民和剂局方》'
            },
            {
                'name': '六味地黄丸', 'pinyin': 'Liuwei Dihuang Wan', 'alias': '地黄丸',
                'category': '滋阴剂', 
                'composition': '熟地黄24g，山茱萸12g，山药12g，泽泻9g，牡丹皮9g，茯苓9g',
                'preparation': '水煎服或制成丸剂',
                'functions': '滋阴补肾，养肝明目。',
                'indications': '肾阴不足，腰膝酸软，骨蒸潮热，盗汗遗精，内热消渴，咽干口燥，眩晕耳鸣。',
                'classic_source': '《小儿药证直诀》'
            },
            {
                'name': '桂枝汤', 'pinyin': 'Guizhi Tang', 'alias': '桂枝饮',
                'category': '解表剂', 
                'composition': '桂枝9g，白芍9g，生姜9g，大枣12g，甘草6g',
                'preparation': '水煎服',
                'functions': '发汗解表，调和营卫，缓急止痛。',
                'indications': '风寒表证，恶风发热，汗出不畅，头痛鼻塞，肢体酸痛。',
                'classic_source': '《伤寒论》'
            },
            {
                'name': '麻黄汤', 'pinyin': 'Mahuang Tang', 'alias': '麻黄饮',
                'category': '解表剂', 
                'composition': '麻黄9g，桂枝6g，杏仁9g，甘草3g',
                'preparation': '水煎服',
                'functions': '发汗解表，宣肺平喘。',
                'indications': '风寒束表，恶寒发热，无汗而喘，头痛身疼，鼻塞声重，咳嗽气喘。',
                'classic_source': '《伤寒论》'
            }
        ]
        
        try:
            # 插入样例中药数据
            for herb in sample_herbs:
                cursor.execute("""
                INSERT OR IGNORE INTO herbs 
                (name, pinyin, alias, category, property, taste, meridian, functions, indications, usage) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    herb['name'], herb['pinyin'], herb['alias'], herb['category'], 
                    herb['property'], herb['taste'], herb['meridian'], 
                    herb['functions'], herb['indications'], herb['usage']
                ))
            
            # 插入样例方剂数据
            for formula in sample_formulas:
                cursor.execute("""
                INSERT OR IGNORE INTO formulas 
                (name, pinyin, alias, category, composition, preparation, functions, 
                indications, classic_source, effect) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    formula['name'], formula['pinyin'], formula['alias'], formula['category'],
                    formula['composition'], formula['preparation'], formula['functions'],
                    formula['indications'], formula['classic_source'], formula.get('effect', formula['functions'])
                ))
            
            conn.commit()
            print("样例数据已自动初始化")
        except Exception as e:
            conn.rollback()
            print(f"初始化样例数据时出错: {str(e)}")
        finally:
            conn.close()

# 执行自动初始化样例数据
auto_init_sample_data()

@herbs.route('/herbs')
def herbs_list():
    """显示中药列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 6
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
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
    cursor.execute(count_query, params)
    total = cursor.fetchone()[0]
    
    # 调试输出
    print(f"查询到的中药总数: {total}")
    
    # 添加分页
    query += " ORDER BY name LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    # 执行查询
    cursor.execute(query, params)
    herbs_data = cursor.fetchall()
    
    # 调试输出
    print(f"当前页面中药数: {len(herbs_data)}")
    if len(herbs_data) > 0:
        print(f"第一个中药: {dict(herbs_data[0])}")
    
    # 获取所有分类
    cursor.execute("SELECT DISTINCT category FROM herbs ORDER BY category")
    categories = [row[0] for row in cursor.fetchall() if row[0]]
    
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    # 调试用：输出当前结果到文件
    with open('herbs_debug.txt', 'w') as f:
        f.write(f"总记录数: {total}\n")
        f.write(f"当前页: {page}\n")
        f.write(f"每页显示: {per_page}\n")
        f.write(f"总页数: {total_pages}\n")
        f.write(f"搜索词: {search}\n")
        f.write(f"分类: {category}\n")
        f.write(f"分类列表: {categories}\n")
        f.write(f"中药数据: {len(herbs_data)}\n")
        for herb in herbs_data:
            herb_dict = dict(herb)
            f.write(f"ID: {herb_dict.get('id')}, 名称: {herb_dict.get('name')}, 拼音: {herb_dict.get('pinyin')}\n")
    
    return render_template('herbs_list.html', 
                          herbs=herbs_data, 
                          page=page, 
                          total_pages=total_pages, 
                          search=search,
                          category=category,
                          categories=categories,
                          per_page=per_page)

@herbs.route('/herb/<int:herb_id>')
def herb_detail(herb_id):
    """显示中药详情"""
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM herbs WHERE id = ?", (herb_id,))
    herb = cursor.fetchone()
    
    is_favorite = False
    if current_user.is_authenticated:
        cursor.execute(
            "SELECT COUNT(*) FROM favorite_herbs WHERE user_id = ? AND herb_id = ?",
            (current_user.id, herb_id)
        )
        is_favorite = cursor.fetchone()[0] > 0
    
    conn.close()
    
    if not herb:
        flash('中药不存在', 'danger')
        return redirect(url_for('herbs.herbs_list'))
    
    return render_template('herb_detail.html', herb=herb, is_favorite=is_favorite)

@herbs.route('/formulas')
def formulas_list():
    """显示方剂列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 4
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
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
    
    # 添加分页
    query += " ORDER BY name LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    formulas_data = cursor.fetchall()
    
    # 获取所有分类
    cursor.execute("SELECT DISTINCT category FROM formulas ORDER BY category")
    categories = [row[0] for row in cursor.fetchall() if row[0]]
    
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('formulas_list.html',
                          formulas=formulas_data, 
                          page=page, 
                          total_pages=total_pages, 
                          search=search,
                          category=category,
                          categories=categories,
                          per_page=per_page)

@herbs.route('/formula/<int:formula_id>')
def formula_detail(formula_id):
    """显示方剂详情"""
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM formulas WHERE id = ?", (formula_id,))
    formula = cursor.fetchone()
    
    is_favorite = False
    if current_user.is_authenticated:
        cursor.execute(
            "SELECT COUNT(*) FROM favorite_formulas WHERE user_id = ? AND formula_id = ?",
            (current_user.id, formula_id)
        )
        is_favorite = cursor.fetchone()[0] > 0
    
    conn.close()
    
    if not formula:
        flash('方剂不存在', 'danger')
        return redirect(url_for('herbs.formulas_list'))
    
    return render_template('formula_detail.html', formula=formula, is_favorite=is_favorite)

@herbs.route('/toggle_favorite_herb/<int:herb_id>', methods=['POST'])
@login_required
def toggle_favorite_herb(herb_id):
    """收藏/取消收藏中药"""
    conn = sqlite3.connect('tcm.db')
    cursor = conn.cursor()
    
    # 检查中药是否存在
    cursor.execute("SELECT COUNT(*) FROM herbs WHERE id = ?", (herb_id,))
    if cursor.fetchone()[0] == 0:
        conn.close()
        return jsonify({'success': False, 'message': '中药不存在'}), 404
    
    # 检查是否已收藏
    cursor.execute(
        "SELECT COUNT(*) FROM favorite_herbs WHERE user_id = ? AND herb_id = ?",
        (current_user.id, herb_id)
    )
    is_favorite = cursor.fetchone()[0] > 0
    
    if is_favorite:
        # 取消收藏
        cursor.execute(
            "DELETE FROM favorite_herbs WHERE user_id = ? AND herb_id = ?",
            (current_user.id, herb_id)
        )
        message = '已取消收藏'
        status = False
    else:
        # 添加收藏
        cursor.execute(
            "INSERT INTO favorite_herbs (user_id, herb_id) VALUES (?, ?)",
            (current_user.id, herb_id)
        )
        message = '已收藏'
        status = True
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'is_favorite': status,
        'message': message
    })

@herbs.route('/toggle_favorite_formula/<int:formula_id>', methods=['POST'])
@login_required
def toggle_favorite_formula(formula_id):
    """收藏/取消收藏方剂"""
    conn = sqlite3.connect('tcm.db')
    cursor = conn.cursor()
    
    # 检查方剂是否存在
    cursor.execute("SELECT COUNT(*) FROM formulas WHERE id = ?", (formula_id,))
    if cursor.fetchone()[0] == 0:
        conn.close()
        return jsonify({'success': False, 'message': '方剂不存在'}), 404
    
    # 检查是否已收藏
    cursor.execute(
        "SELECT COUNT(*) FROM favorite_formulas WHERE user_id = ? AND formula_id = ?",
        (current_user.id, formula_id)
    )
    is_favorite = cursor.fetchone()[0] > 0
    
    if is_favorite:
        # 取消收藏
        cursor.execute(
            "DELETE FROM favorite_formulas WHERE user_id = ? AND formula_id = ?",
            (current_user.id, formula_id)
        )
        message = '已取消收藏'
        status = False
    else:
        # 添加收藏
        cursor.execute(
            "INSERT INTO favorite_formulas (user_id, formula_id) VALUES (?, ?)",
            (current_user.id, formula_id)
        )
        message = '已收藏'
        status = True
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'is_favorite': status,
        'message': message
    })

@herbs.route('/my_favorites')
@login_required
def my_favorites():
    """显示用户的收藏"""
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取收藏的中药
    cursor.execute("""
        SELECT h.* FROM herbs h
        JOIN favorite_herbs fh ON h.id = fh.herb_id
        WHERE fh.user_id = ?
        ORDER BY fh.added_at DESC
    """, (current_user.id,))
    favorite_herbs = cursor.fetchall()
    
    # 获取收藏的方剂
    cursor.execute("""
        SELECT f.* FROM formulas f
        JOIN favorite_formulas ff ON f.id = ff.formula_id
        WHERE ff.user_id = ?
        ORDER BY ff.added_at DESC
    """, (current_user.id,))
    favorite_formulas = cursor.fetchall()
    
    conn.close()
    
    # 定义每页显示数量，但在我的收藏页面不使用分页
    per_page = 20
    
    return render_template('my_favorites.html', 
                          favorite_herbs=favorite_herbs,
                          favorite_formulas=favorite_formulas,
                          per_page=per_page) 