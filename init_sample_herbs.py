import sqlite3

def init_sample_herbs():
    """初始化中药和方剂样例数据"""
    conn = sqlite3.connect('tcm.db')
    cursor = conn.cursor()
    
    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM herbs")
    herb_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM formulas")
    formula_count = cursor.fetchone()[0]
    
    # 如果已有数据，先清空表
    if herb_count > 0:
        cursor.execute("DELETE FROM herbs")
    
    if formula_count > 0:
        cursor.execute("DELETE FROM formulas")
    
    # 样例中药数据
    sample_herbs = [
        {
            'name': '人参', 'pinyin': 'Renshen', 'alias': '园参、黄参、血参、生晒参', 
            'category': '补气药', 'property': '微温', 'taste': '甘、微苦', 
            'meridian': '脾、肺、心、肾经', 
            'functions': '大补元气，复脉固脱，补脾益肺，生津，安神。', 
            'indications': '气虚体弱，脾肺虚弱，食少倦怠，肺虚喘咳，津伤口渴，内热消渴，气血亏虚，心悸怔仲，脱肛，久泻不止，惊悸失眠，阳痿宫冷。', 
            'usage': '煎服、研末冲服。',
            'image_url': '/static/images/herbs/renshen.jpg'
        },
        {
            'name': '黄芪', 'pinyin': 'Huangqi', 'alias': '蜀芪、绵芪、黄耆', 
            'category': '补气药', 'property': '微温', 'taste': '甘', 
            'meridian': '肺、脾经', 
            'functions': '补气固表，利水消肿，托毒排脓，生肌。', 
            'indications': '气虚乏力，食少便溏，中气下陷，久泻脱肛，表虚自汗，气虚水肿，痈疽难溃，久溃不敛。', 
            'usage': '煎服，或泡酒。',
            'image_url': '/static/images/herbs/huangqi.jpg'
        },
        {
            'name': '白术', 'pinyin': 'Baizhu', 'alias': '于术、菊术', 
            'category': '补气药', 'property': '温', 'taste': '辛、甘、苦', 
            'meridian': '脾、胃经', 
            'functions': '健脾益气，燥湿利水，止汗，安胎。', 
            'indications': '脾胃虚弱，食少倦怠，胃下垂，泄泻，痰饮眩悸，水肿，自汗，胎动不安。', 
            'usage': '煎服，或研末。',
            'image_url': '/static/images/herbs/baizhu.jpg'
        },
        {
            'name': '甘草', 'pinyin': 'Gancao', 'alias': '甜草、蜜草、国老', 
            'category': '补气药', 'property': '平', 'taste': '甘', 
            'meridian': '心、肺、脾、胃经', 
            'functions': '补脾益气，润肺止咳，清热解毒，调和诸药。', 
            'indications': '脾胃虚弱，倦怠乏力，心悸气短，咳嗽痰多，痈肿疮毒，缓急解痉，缓解药物毒性。', 
            'usage': '煎服，或研末冲服。',
            'image_url': '/static/images/herbs/gancao.jpg'
        },
        {
            'name': '当归', 'pinyin': 'Danggui', 'alias': '干归、秦当归', 
            'category': '补血药', 'property': '温', 'taste': '甘、辛', 
            'meridian': '肝、心、脾经', 
            'functions': '补血活血，调经止痛，润肠通便。', 
            'indications': '血虚萎黄，眩晕心悸，月经不调，经闭痛经，虚寒腹痛，肠燥便秘，风湿痹痛，跌扑损伤，痈疽疮疡。', 
            'usage': '煎服，或泡酒。',
            'image_url': '/static/images/herbs/danggui.jpg'
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
            (name, pinyin, alias, category, property, taste, meridian, functions, indications, usage, image_url) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                herb['name'], herb['pinyin'], herb['alias'], herb['category'], 
                herb['property'], herb['taste'], herb['meridian'], 
                herb['functions'], herb['indications'], herb['usage'], herb['image_url']
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
        print("样例数据已成功添加！")
    except Exception as e:
        conn.rollback()
        print(f"添加样例数据时出错: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_sample_herbs() 