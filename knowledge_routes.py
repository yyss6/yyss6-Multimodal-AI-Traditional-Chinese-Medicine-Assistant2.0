from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import sqlite3
from datetime import datetime

knowledge = Blueprint('knowledge', __name__, url_prefix='/knowledge')

# 初始化知识库数据库
def init_knowledge_db():
    conn = sqlite3.connect('tcm.db')
    c = conn.cursor()
    
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        view_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'published'
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
        image_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        view_count INTEGER DEFAULT 0
    )
    ''')
    
    conn.commit()
    conn.close()

# 初始化数据库
init_knowledge_db()

@knowledge.route('/articles')
def articles_list():
    """显示文章列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 4
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
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

@knowledge.route('/article/<int:article_id>')
def article_detail(article_id):
    """重定向到文章详情页"""
    # 重定向到article蓝图中的detail路由
    return redirect(url_for('article.detail', article_id=article_id))

@knowledge.route('/seasonal')
def seasonal_health():
    """季节养生指南"""
    # 获取当前季节
    now = datetime.now()
    month = now.month
    
    if month in [3, 4, 5]:
        current_season = '春季'
    elif month in [6, 7, 8]:
        current_season = '夏季'
    elif month in [9, 10, 11]:
        current_season = '秋季'
    else:
        current_season = '冬季'
    
    season = request.args.get('season', current_season)
    
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM seasonal_health WHERE season = ?", (season,))
    seasonal_health_data = cursor.fetchone()
    
    cursor.execute("SELECT DISTINCT season FROM seasonal_health")
    all_seasons = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('seasonal_health.html', 
                          seasonal_health=seasonal_health_data,
                          current_season=season,
                          all_seasons=all_seasons)

@knowledge.route('/video_tutorials')
def video_tutorials():
    """视频教程列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 3
    category = request.args.get('category', '')
    
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 构建查询条件
    query = "SELECT * FROM video_tutorials"
    params = []
    
    if category:
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
    videos = cursor.fetchall()
    
    # 获取所有分类
    cursor.execute("SELECT DISTINCT category FROM video_tutorials ORDER BY category")
    categories = [row[0] for row in cursor.fetchall() if row[0]]
    
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('video_tutorials.html', 
                          videos=videos, 
                          page=page, 
                          total_pages=total_pages,
                          category=category,
                          categories=categories)

@knowledge.route('/video/<int:video_id>')
def video_detail(video_id):
    """视频详情"""
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 更新浏览量
    cursor.execute("UPDATE video_tutorials SET view_count = view_count + 1 WHERE id = ?", (video_id,))
    conn.commit()
    
    # 获取视频
    cursor.execute("SELECT * FROM video_tutorials WHERE id = ?", (video_id,))
    video = cursor.fetchone()
    
    if not video:
        conn.close()
        flash('视频不存在', 'danger')
        return redirect(url_for('knowledge.video_tutorials'))
    
    # 获取相关视频
    cursor.execute("""
        SELECT * FROM video_tutorials 
        WHERE id != ? AND category = ?
        ORDER BY created_at DESC LIMIT 5
    """, (video_id, video['category']))
    related_videos = cursor.fetchall()
    
    conn.close()
    
    return render_template('video_detail.html', video=video, related_videos=related_videos)

@knowledge.route('/init_sample_knowledge')
def init_sample_knowledge():
    """初始化样例知识库数据"""
    conn = sqlite3.connect('tcm.db')
    cursor = conn.cursor()
    
    # 样例文章数据
    sample_articles = [
        {
            'title': '中医望诊：看舌苔辨病理',
            'content': """<p>舌诊是中医诊断的重要方法之一，通过观察舌体和舌苔的变化，可以了解人体内脏的生理病理变化。</p>
            <p><strong>正常舌象：</strong>舌质淡红，苔薄白略润，舌体柔软，舌形适中，舌下络脉色淡青，无明显曲张。</p>
            <h4>舌质的辨别</h4>
            <p>1. <strong>淡白舌：</strong>多为气血两虚、阳气不足。</p>
            <p>2. <strong>红舌：</strong>多为热证，常见于里热证。</p>
            <p>3. <strong>绛舌：</strong>舌色深红如赤，为热极或热入营血。</p>
            <p>4. <strong>青紫舌：</strong>多为血瘀或阳气不足。</p>
            <h4>舌苔的辨别</h4>
            <p>1. <strong>白苔：</strong>一般为外感风寒或寒湿证。</p>
            <p>2. <strong>黄苔：</strong>多为里热证。</p>
            <p>3. <strong>灰黑苔：</strong>多为热极伤阴或寒极凝结。</p>
            <p>4. <strong>厚腻苔：</strong>多为湿浊阻滞。</p>
            <p>通过仔细观察舌象的变化，结合其他诊断方法，可以全面了解病情，为中医辨证施治提供重要依据。</p>""",
            'author': '张三',
            'category': '中医基础',
            'tags': '舌诊,中医诊断,舌苔,辨证',
            'image_url': 'https://example.com/images/tongue_diagnosis.jpg'
        },
        {
            'title': '经络养生：穴位按摩指南',
            'content': """<p>穴位按摩是一种简单易行的自我保健方法，通过刺激特定穴位，疏通经络，调和气血，达到防病治病的目的。</p>
            <h4>常用穴位及其功效</h4>
            <p>1. <strong>合谷穴：</strong>位于手背，第一、二掌骨间，偏向第二掌骨。主治头面部疾病，如头痛、牙痛、感冒等。</p>
            <p>2. <strong>足三里：</strong>位于膝下三寸，胫骨外侧一横指处。具有健脾胃、强筋骨、提高免疫力的作用。</p>
            <p>3. <strong>关元穴：</strong>位于脐下三寸。具有补元气、调气血、理下焦的功效。</p>
            <p>4. <strong>涌泉穴：</strong>位于足底前三分之一处。能滋肾纳气，清热平肝，镇静安神。</p>
            <h4>按摩方法</h4>
            <p>1. <strong>指压法：</strong>用拇指或食指指腹垂直按压穴位。</p>
            <p>2. <strong>揉法：</strong>用拇指指腹在穴位上做圆周运动。</p>
            <p>3. <strong>点按法：</strong>用指尖有节律地按压穴位。</p>
            <p>每个穴位按摩1-3分钟，每天可进行2-3次，长期坚持可增强体质，预防疾病。</p>""",
            'author': '李四',
            'category': '经络养生',
            'tags': '穴位按摩,经络,自我保健,养生',
            'image_url': 'https://example.com/images/acupoint_massage.jpg'
        },
        {
            'title': '四季养生：中医饮食调理',
            'content': """<p>中医认为，饮食养生应顺应四时阴阳变化，根据不同季节的特点，调整饮食结构和习惯，以达到防病保健的目的。</p>
            <h4>春季养生</h4>
            <p>春属木，与肝相应。饮食宜温补，少酸增甘，以养肝阳。适宜食物：菠菜、荠菜、韭菜、春笋等。</p>
            <h4>夏季养生</h4>
            <p>夏属火，与心相应。饮食宜清淡，少咸增苦，以养心阴。适宜食物：苦瓜、荷叶、绿豆、西瓜等。</p>
            <h4>秋季养生</h4>
            <p>秋属金，与肺相应。饮食宜滋润，少辛增酸，以养肺阴。适宜食物：梨、银耳、百合、蜂蜜等。</p>
            <h4>冬季养生</h4>
            <p>冬属水，与肾相应。饮食宜温补，少咸增苦，以养肾阳。适宜食物：羊肉、核桃、黑芝麻、枸杞等。</p>
            <p>此外，还应注意饮食有节，不过饥过饱，定时定量，细嚼慢咽，以保护脾胃功能。</p>""",
            'author': '王五',
            'category': '饮食养生',
            'tags': '四季养生,饮食调理,中医养生,食疗',
            'image_url': 'https://example.com/images/seasonal_diet.jpg'
        },
        {
            'title': '中医体质辨识与养生',
            'content': """<p>中医体质学说认为，人的体质是先天禀赋与后天获得的综合表现，不同体质的人应采取不同的养生方法。</p>
            <h4>常见体质类型</h4>
            <p>1. <strong>平和质：</strong>体格健壮，面色红润，精力充沛，抗病能力强。养生要点：保持规律生活，适度运动。</p>
            <p>2. <strong>气虚质：</strong>易疲劳，气短懒言，面色淡白。养生要点：适当运动，如太极拳、八段锦；饮食宜甘温补气，如人参、黄芪、大枣等。</p>
            <p>3. <strong>阳虚质：</strong>怕冷，手脚冰凉，面色苍白。养生要点：保暖，避免寒凉；食用温阳食物，如羊肉、韭菜、生姜等。</p>
            <p>4. <strong>阴虚质：</strong>手足心热，口干咽燥，面色潮红。养生要点：保持心情舒畅，避免情绪激动；食用滋阴食物，如百合、银耳、梨等。</p>
            <p>5. <strong>痰湿质：</strong>体形肥胖，腹部松软，面垢油光。养生要点：控制饮食，适当运动；忌肥甘厚腻，宜食利湿健脾食物，如薏苡仁、赤小豆等。</p>
            <p>了解自己的体质特点，采取相应的养生方法，才能达到事半功倍的效果。</p>""",
            'author': '赵六',
            'category': '体质养生',
            'tags': '中医体质,体质辨识,养生保健,个性化养生',
            'image_url': 'https://example.com/images/constitution_health.jpg'
        },
        {
            'title': '传统中医食疗方',
            'content': """<p>中医食疗是运用中医理论指导饮食，将食物与药物有机结合，达到防治疾病、强身健体的目的。以下是一些常用的传统食疗方。</p>
            <h4>益气健脾类</h4>
            <p><strong>山药粥：</strong>山药30克，大米100克，红枣5枚。功效：健脾益气，滋养肺肾。适用于脾肺虚弱，食欲不振，大便溏薄等。</p>
            <p><strong>黄芪炖鸡：</strong>黄芪30克，乌鸡半只，生姜、葱适量。功效：补气养血，健脾益气。适用于气血两虚，脾胃虚弱等。</p>
            <h4>滋阴润燥类</h4>
            <p><strong>百合杏仁糊：</strong>百合30克，杏仁10克，冰糖适量。功效：润肺止咳，养阴清热。适用于肺燥干咳，咽干喉痒等。</p>
            <p><strong>银耳莲子羹：</strong>银耳15克，莲子20克，冰糖适量。功效：养阴润肺，健脾补肾。适用于阴虚内热，口干咽燥等。</p>
            <h4>温阳补肾类</h4>
            <p><strong>羊肉萝卜汤：</strong>羊肉250克，白萝卜300克，生姜、葱适量。功效：温阳散寒，益气补虚。适用于肾阳不足，畏寒肢冷等。</p>
            <p><strong>枸杞炖猪腰：</strong>枸杞20克，猪腰1对，姜、盐适量。功效：滋补肝肾，益精明目。适用于肝肾阴虚，眼睛干涩，视力减退等。</p>
            <p>中医食疗讲究因人、因时、因地制宜，选择合适的食疗方，坚持食用，可以起到很好的保健作用。</p>""",
            'author': '孙七',
            'category': '食疗保健',
            'tags': '中医食疗,食补,传统食疗方,药膳',
            'image_url': 'https://example.com/images/food_therapy.jpg'
        }
    ]
    
    # 样例季节养生数据
    sample_seasonal_health = [
        {
            'season': '春季',
            'title': '春季养生指南',
            'content': """<p>春季是万物复苏的季节，也是人体阳气生发的时期。中医认为"春主生发"，养生应顺应春季特点，注重保护肝脏，调畅情志。</p>
            <p>春季养生的核心是"养阳防风"。此时养生应注意以下几个方面：</p>""",
            'foods': '春笋、菠菜、荠菜、韭菜、香椿、芦笋等嫩绿蔬菜；大枣、桑椹等水果',
            'exercises': '八段锦、五禽戏、慢跑、散步等舒缓运动',
            'tips': '早睡早起，保持心情舒畅；适当增加户外活动，呼吸新鲜空气；避免过于辛辣刺激的食物',
            'image_url': 'https://example.com/images/spring_health.jpg'
        },
        {
            'season': '夏季',
            'title': '夏季养生指南',
            'content': """<p>夏季气温高，湿度大，是一年中阳气最盛的时期。中医认为"夏主长"，养生应注重清热祛湿，保护心脏功能。</p>
            <p>夏季养生的核心是"养阴防暑"。此时养生应注意以下几个方面：</p>""",
            'foods': '绿豆、苦瓜、冬瓜、黄瓜、西瓜、荷叶、莲子等清热解暑食物',
            'exercises': '太极拳、游泳、晨练或傍晚运动，避免正午高温时段',
            'tips': '注意防暑降温，避免过度贪凉；保持室内通风，适当开启空调；多饮水，少食油腻辛辣食物',
            'image_url': 'https://example.com/images/summer_health.jpg'
        },
        {
            'season': '秋季',
            'title': '秋季养生指南',
            'content': """<p>秋季气候干燥，阳气渐收，阴气渐长。中医认为"秋主收敛"，养生应注重滋阴润燥，保护肺脏功能。</p>
            <p>秋季养生的核心是"养阴防燥"。此时养生应注意以下几个方面：</p>""",
            'foods': '梨、百合、银耳、蜂蜜、莲藕、胡萝卜、南瓜等滋阴润燥食物',
            'exercises': '太极拳、五禽戏、散步等舒缓运动',
            'tips': '保持心情舒畅，避免悲郁情绪；适当增加室内湿度；早睡早起，保证充足睡眠',
            'image_url': 'https://example.com/images/autumn_health.jpg'
        },
        {
            'season': '冬季',
            'title': '冬季养生指南',
            'content': """<p>冬季寒冷干燥，是一年中阴气最盛的时期。中医认为"冬主藏"，养生应注重温补肾阳，保护肾脏功能。</p>
            <p>冬季养生的核心是"养阳防寒"。此时养生应注意以下几个方面：</p>""",
            'foods': '羊肉、狗肉、韭菜、生姜、大葱、胡椒等温阳食物；核桃、黑芝麻、枸杞等补肾食物',
            'exercises': '八段锦、太极拳、室内运动，保持适当运动量',
            'tips': '注意保暖，特别是头部和足部；不宜过早脱去冬衣；保持室内空气流通；早睡晚起，保证充足睡眠',
            'image_url': 'https://example.com/images/winter_health.jpg'
        }
    ]
    
    # 样例视频教程数据
    sample_videos = [
        {
            'title': '太极拳基础入门教学',
            'description': '本视频详细讲解了太极拳的基本站姿、手型和基础动作，适合初学者循序渐进地学习太极拳。',
            'category': '太极拳',
            'video_url': 'https://example.com/videos/taichi_basic.mp4',
            'thumbnail_url': 'https://example.com/images/taichi_thumbnail.jpg',
            'duration': '45:30',
            'instructor': '王老师'
        },
        {
            'title': '八段锦完整教学',
            'description': '八段锦是中国传统的养生功法，本视频详细讲解了八段锦的每一个动作要领和呼吸方法，帮助您正确练习。',
            'category': '养生功法',
            'video_url': 'https://example.com/videos/baduanjin.mp4',
            'thumbnail_url': 'https://example.com/images/baduanjin_thumbnail.jpg',
            'duration': '38:45',
            'instructor': '李老师'
        },
        {
            'title': '中医艾灸疗法详解',
            'description': '艾灸是中医传统疗法之一，本视频介绍了艾灸的基本原理、适应症和操作方法，包括常用穴位的定位和灸法。',
            'category': '中医疗法',
            'video_url': 'https://example.com/videos/moxibustion.mp4',
            'thumbnail_url': 'https://example.com/images/moxibustion_thumbnail.jpg',
            'duration': '52:15',
            'instructor': '张老师'
        },
        {
            'title': '五行穴位按摩保健法',
            'description': '根据五行学说和穴位理论，本视频教您如何通过按摩特定穴位，调节五脏六腑功能，预防疾病，增强体质。',
            'category': '穴位按摩',
            'video_url': 'https://example.com/videos/acupoint_massage.mp4',
            'thumbnail_url': 'https://example.com/images/acupoint_massage_thumbnail.jpg',
            'duration': '40:20',
            'instructor': '刘老师'
        },
        {
            'title': '中医养生茶饮制作方法',
            'description': '本视频介绍了多种具有不同功效的中医养生茶饮的配方和制作方法，包括四季养生茶、调理脾胃茶、安神茶等。',
            'category': '食疗养生',
            'video_url': 'https://example.com/videos/health_tea.mp4',
            'thumbnail_url': 'https://example.com/images/health_tea_thumbnail.jpg',
            'duration': '35:50',
            'instructor': '周老师'
        }
    ]
    
    try:
        # 插入样例文章数据
        for article in sample_articles:
            cursor.execute("""
            INSERT OR IGNORE INTO articles 
            (title, content, author, category, tags, image_url, created_at, status) 
            VALUES (?, ?, ?, ?, ?, ?, datetime('now', '-' || ? || ' days'), ?)
            """, (
                article['title'], article['content'], article['author'], 
                article['category'], article['tags'], article['image_url'],
                hash(article['title']) % 30,  # 随机生成过去30天内的日期
                'published'  # 添加status字段
            ))
        
        # 插入样例季节养生数据
        for seasonal in sample_seasonal_health:
            cursor.execute("""
            INSERT OR IGNORE INTO seasonal_health 
            (season, title, content, foods, exercises, tips, image_url) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                seasonal['season'], seasonal['title'], seasonal['content'],
                seasonal['foods'], seasonal['exercises'], seasonal['tips'],
                seasonal['image_url']
            ))
        
        # 插入样例视频教程数据
        for video in sample_videos:
            cursor.execute("""
            INSERT OR IGNORE INTO video_tutorials 
            (title, description, category, video_url, thumbnail_url, duration, instructor, created_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', '-' || ? || ' days'))
            """, (
                video['title'], video['description'], video['category'],
                video['video_url'], video['thumbnail_url'], video['duration'],
                video['instructor'], hash(video['title']) % 30  # 随机生成过去30天内的日期
            ))
        
        conn.commit()
        flash('样例知识库数据已成功添加！', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'添加样例知识库数据时出错：{str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('knowledge.articles_list')) 

@knowledge.route('/api/articles/<int:article_id>/comments', methods=['POST'])
def add_comment(article_id):
    """重定向到文章评论API"""
    # 将请求转发到article蓝图中的add_comment路由
    return redirect(url_for('article.add_comment', article_id=article_id))

@knowledge.route('/api/articles/<int:article_id>/like', methods=['POST'])
def toggle_like(article_id):
    """重定向到文章点赞API"""
    # 将请求转发到article蓝图中的toggle_like路由
    return redirect(url_for('article.toggle_like', article_id=article_id))

@knowledge.route('/api/articles/<int:article_id>/favorite', methods=['POST'])
def toggle_favorite(article_id):
    """重定向到文章收藏API"""
    # 将请求转发到article蓝图中的toggle_favorite路由
    return redirect(url_for('article.toggle_favorite', article_id=article_id))

@knowledge.route('/api/articles/<int:article_id>/comments', methods=['GET'])
def get_article_comments(article_id):
    """重定向到文章评论获取API"""
    # 将请求转发到article蓝图中的get_comments路由
    return redirect(url_for('article.get_comments', article_id=article_id))