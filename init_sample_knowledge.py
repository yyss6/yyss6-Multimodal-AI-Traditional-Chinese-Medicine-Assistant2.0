import sqlite3

def init_sample_knowledge():
    """初始化健康知识库样例数据"""
    conn = sqlite3.connect('tcm.db')
    cursor = conn.cursor()
    
    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM articles")
    article_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM seasonal_health")
    seasonal_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM video_tutorials")
    video_count = cursor.fetchone()[0]
    
    # 如果已有数据，先清空表
    if article_count > 0:
        cursor.execute("DELETE FROM articles")
    
    if seasonal_count > 0:
        cursor.execute("DELETE FROM seasonal_health")
    
    if video_count > 0:
        cursor.execute("DELETE FROM video_tutorials")
    
    # 样例文章数据
    sample_articles = [
        {
            'title': '中医体质辨识与调理方法',
            'content': '中医体质学说认为，人的体质是先天遗传和后天获得的，体现为形态结构、生理功能和心理状态方面综合的、相对稳定的固有特性。中医将体质分为平和质、气虚质、阳虚质、阴虚质、痰湿质、湿热质、血瘀质、气郁质、特禀质九种基本类型。每种体质都有其特点和调理方法。平和质是理想的体质状态，表现为形体适中、面色红润、精力充沛等特点；气虚质多表现为易疲乏、声音低弱、自汗等；阳虚质常见怕冷、四肢不温、精神不振等；阴虚质则有手足心热、口干、眼干等表现。根据自己的体质特点，采取相应的饮食调理、起居调摄、运动锻炼和情志调养，可以改善体质状态，增强健康水平。',
            'author': '张伯礼',
            'category': '中医养生',
            'tags': '体质辨识,养生保健,中医理论',
            'image_url': '/static/images/articles/constitution.jpg'
        },
        {
            'title': '艾灸养生的科学与艺术',
            'content': '艾灸是中医传统疗法之一，利用艾叶燃烧产生的热力和药力，熏灼体表特定穴位，以达到防病治病、保健强身的目的。艾叶性温，具有温经、散寒、除湿、止血、消瘀、安胎等功效。艾灸疗法适用于多种虚寒性疾病，如脾胃虚寒、肾阳不足、风寒湿痹等。常用的艾灸方法包括悬灸、着灸、温灸、隔物灸等。在家庭保健中，艾灸应注意穴位准确、火力适中、时间适宜，避免灼伤皮肤。特别需要注意的是，发热病、阴虚火旺等热性病证，孕妇腹部和腰骶部，皮肤破损处等都不宜使用艾灸。科学合理地应用艾灸，能够起到很好的养生保健效果。',
            'author': '李忠',
            'category': '中医外治',
            'tags': '艾灸,保健方法,穴位疗法',
            'image_url': '/static/images/articles/moxibustion.jpg'
        },
        {
            'title': '四季养生茶饮配方与功效',
            'content': '不同季节应当饮用不同的养生茶，以适应自然界阴阳变化，达到调和人体阴阳的目的。春季气候多变，常饮桑叶菊花茶、薄荷茶等，具有疏风散热之效；夏季炎热，宜饮绿茶、荷叶茶、金银花茶等清热解暑之品；秋季干燥，适宜饮用菊花茶、百合茶、梨皮茶等滋阴润燥之剂；冬季寒冷，可选用红茶、生姜红枣茶、桂圆茶等温补之饮。此外，各种体质也有相应的养生茶饮：气虚体质宜饮黄芪茶、人参茶；阳虚体质适合肉桂茶、附子理中茶；阴虚体质则应选择麦冬茶、百合茶等。养生茶饮既能品味茶香，又有保健功效，是传统中医养生方法的重要组成部分。',
            'author': '王琦',
            'category': '饮食养生',
            'tags': '养生茶,四季养生,体质调理',
            'image_url': '/static/images/articles/tea.jpg'
        },
        {
            'title': '中医经络穴位按摩与自我保健',
            'content': '经络穴位按摩是中医外治法的重要组成部分，具有疏通经络、调和气血、防病治病的作用。常用的自我保健穴位包括：百会穴，位于头顶正中线与两耳尖连线的交点，按揉此穴能醒脑开窍、益智安神；合谷穴，位于手背第一、二掌骨间，拇指指腹按揉可缓解头面部疼痛；足三里穴，在膝下三寸，外膝眼直下，按揉能健脾胃、强筋骨；涌泉穴，在足底前三分之一处凹陷中，早晚按摩可滋阴降火、强肾健脑。穴位按摩手法一般以指揉、指按、指掐等为主，力度以局部产生酸、麻、胀、热感为宜，每次按摩3-5分钟，每日1-2次。经常进行穴位按摩，能增强体质，预防疾病。',
            'author': '石学敏',
            'category': '经络养生',
            'tags': '穴位按摩,自我保健,经络理论',
            'image_url': '/static/images/articles/acupoint.jpg'
        },
        {
            'title': '中医药膳食疗与现代营养学',
            'content': '中医药膳是将中药与食物相结合，依据中医理论指导下制作的具有食疗作用的膳食。与现代营养学相比，中医药膳更注重个体差异和整体调理。例如，黄芪炖鸡不仅含有丰富的蛋白质和微量元素，更具有补气健脾的功效；枸杞子不仅含有丰富的胡萝卜素和维生素，还有滋补肝肾、明目的作用。现代研究表明，许多传统药膳确实具有显著的保健功效：如山药含有多糖和黏液蛋白，既是良好的碳水化合物来源，又能健脾养胃；大枣富含维生素C和环磷酸腺苷，既提供营养，又能补中益气、养血安神。将中医药膳与现代营养学结合，可以更科学地指导人们的饮食健康。',
            'author': '李时珍',
            'category': '饮食养生',
            'tags': '药膳食疗,营养健康,传统食疗',
            'image_url': '/static/images/articles/medicinal_diet.jpg'
        }
    ]
    
    # 样例季节养生数据
    sample_seasonal_health = [
        {
            'season': '春季',
            'title': '春季养生指南',
            'content': '春季是万物生长的季节，养生应当顺应春天阳气升发的特点。在情志调摄方面，应保持心情舒畅，戒除焦躁；在起居方面，宜早睡早起，适当午休；在运动方面，可选择舒缓的活动，如太极拳、散步等，以助阳气生发；在穿着方面，应根据天气变化及时增减衣物，谨防春寒侵袭。',
            'foods': '春季饮食应当以温补为主，如芽菜、春笋、菠菜等新鲜蔬菜，既能补充维生素，又能顺应春季阳气升发的特点。适当食用小麦、大枣等甘温食物，以养肝护脾。少食油腻、辛辣食物，以防助湿生热。',
            'exercises': '春季锻炼以舒展筋骨、疏通经络为宜。可选择传统导引术、八段锦、五禽戏等中医传统健身方法，也可进行慢跑、健步走、太极拳等有氧运动。运动量应循序渐进，避免过度劳累。',
            'tips': '1. 春季肝气旺盛，易出现情绪波动，应注意调节情绪，保持心态平和。\n2. 春季气候多变，应及时增减衣物，防止感冒。\n3. 春困现象常见，可适当午休，但不宜过长。\n4. 春季是过敏性疾病高发期，过敏体质者应做好防护。',
            'image_url': '/static/images/seasonal/spring.jpg'
        },
        {
            'season': '夏季',
            'title': '夏季养生要点',
            'content': '夏季气温高，阳气外发，养生应当注重清热祛湿，养阴消暑。在生活作息上，可适当晚睡早起，顺应自然界阳盛阴衰的变化；注意防暑降温，避免长时间在烈日下活动；保持室内通风，但避免长时间处于空调环境中，防止"空调病"；注意个人卫生，勤洗澡、勤换衣，预防皮肤病。',
            'foods': '夏季饮食应清淡为主，可多食用苦味食物，如苦瓜、莲子、荷叶等，具有清热解暑、消除疲劳的作用。多食用西瓜、黄瓜、番茄等水分充足的瓜果蔬菜，补充水分和电解质。少食油腻、辛辣和烧烤类食物，以免增加体内热量。',
            'exercises': '夏季运动应选择清晨或傍晚气温较低时进行，避开中午高温时段。适宜进行游泳、太极拳、瑜伽等低强度运动。运动量应适中，避免大汗淋漓，以防体内阳气过度外泄。运动后及时补充水分和电解质。',
            'tips': '1. 夏季饮水应少量多次，不宜一次饮用过多冷饮，以防伤脾胃。\n2. 午休有助于恢复体力，但不宜超过30分钟。\n3. 夏季出汗多，应及时补充水分，但不宜大量饮用冰镇饮料。\n4. 防范雷雨天气，注意用电安全。',
            'image_url': '/static/images/seasonal/summer.jpg'
        },
        {
            'season': '秋季',
            'title': '秋季养生法则',
            'content': '秋季气候干燥，阳气渐收，阴气渐长，养生重点应放在润燥养阴、收敛保肺上。起居方面，应早睡早起，保证充足睡眠；情志方面，保持心情舒畅，避免忧郁；衣着方面，及时添加衣物，谨防秋凉；此外，应注意保湿，可使用加湿器增加室内湿度，或用温水洗脸，保护皮肤。',
            'foods': '秋季饮食宜滋阴润燥，可多食用梨、百合、银耳、蜂蜜等具有润肺止咳作用的食物。适当食用一些温补食材，如山药、南瓜、莲子等，以增强脾胃功能。少食辛辣刺激性食物，如辣椒、生姜、大蒜等，以免加重燥邪。',
            'exercises': '秋季运动应以舒缓为主，可选择太极拳、八段锦、瑜伽等柔和的运动方式。也可进行慢跑、健步走等有氧运动，但应控制运动量，避免大汗淋漓。运动前做好热身，运动后及时添加衣物，防止受凉。',
            'tips': '1. 秋季昼夜温差大，应适时增减衣物，防止感冒。\n2. 秋季空气干燥，应保持室内适度湿润，预防呼吸道疾病。\n3. 秋季是慢性病复发的高发季节，慢性病患者应做好防护。\n4. 适当进行户外活动，享受秋高气爽的自然环境。',
            'image_url': '/static/images/seasonal/autumn.jpg'
        },
        {
            'season': '冬季',
            'title': '冬季养生智慧',
            'content': '冬季天寒地冻，是养藏的季节。中医认为应当"春夏养阳，秋冬养阴"，冬季养生要点是"藏精蓄锐"。起居方面，宜早睡晚起，保证充足睡眠；情志方面，保持内心平静，避免大悲大喜；防寒保暖方面，注意头部、颈部、腰部和足部的保暖，尤其是背部和脚部，避免寒邪侵袭。',
            'foods': '冬季饮食应以温补为主，可适当食用羊肉、牛肉、鸡肉等温热食物，以增强阳气。多食用当季蔬菜水果，如白萝卜、南瓜、红薯等，补充维生素和矿物质。适当食用一些温性调味品，如姜、桂皮、八角等，以温中散寒。少食生冷食物，避免损伤脾胃阳气。',
            'exercises': '冬季运动应在阳光充足的上午进行，避开早晚寒冷时段。可选择八段锦、五禽戏、太极拳等传统健身方法，也可进行慢跑、健步走、室内健身等活动。运动前充分热身，运动量由小到大，避免出大汗后立即停止，防止寒邪趁虚而入。',
            'tips': '1. 冬季室内外温差大，进出房间应注意适应，防止感冒。\n2. 保持室内通风，但避免直接吹风，保持适宜温度。\n3. 冬季是心脑血管疾病高发期，患者应避免剧烈运动和情绪波动。\n4. 坚持泡脚习惯，可促进血液循环，改善睡眠质量。',
            'image_url': '/static/images/seasonal/winter.jpg'
        }
    ]
    
    # 样例视频教程数据
    sample_videos = [
        {
            'title': '中医经络穴位按摩基础教程',
            'description': '本视频详细介绍了人体十二经络的分布规律、重要穴位的定位方法和常用按摩手法。通过学习，您可以掌握自我保健的基本穴位按摩技术，包括头部、颈部、腰部和四肢的主要穴位。特别适合初学者入门。',
            'category': '经络养生',
            'video_url': '/static/videos/acupoint_massage.mp4',
            'thumbnail_url': '/static/images/videos/acupoint_thumb.jpg',
            'duration': '18:30',
            'instructor': '王明'
        },
        {
            'title': '四季养生药膳制作教程',
            'description': '跟随中医药膳专家学习四季养生药膳的制作方法。春季以疏肝理气为主，夏季注重清热解暑，秋季重在润燥养阴，冬季则以温补为主。本视频详细讲解了各季节的代表性药膳做法，包括材料选择、配比和烹饪技巧。',
            'category': '饮食养生',
            'video_url': '/static/videos/seasonal_diet.mp4',
            'thumbnail_url': '/static/images/videos/diet_thumb.jpg',
            'duration': '25:45',
            'instructor': '李芳'
        },
        {
            'title': '中医四诊检查方法详解',
            'description': '中医四诊包括望、闻、问、切四种诊断方法。本视频由资深中医专家讲解如何进行四诊检查，包括观察面色舌象、听声闻气味、询问病史症状和脉诊按诊技巧。通过学习，可以初步了解中医诊断的基本方法和思路。',
            'category': '中医理论',
            'video_url': '/static/videos/tcm_diagnosis.mp4',
            'thumbnail_url': '/static/images/videos/diagnosis_thumb.jpg',
            'duration': '32:10',
            'instructor': '张伟'
        },
        {
            'title': '传统导引养生功法演示',
            'description': '导引是中国古代的养生方法，结合呼吸吐纳和形体活动。本视频详细演示了八段锦、五禽戏、易筋经三种经典导引功法的标准动作和呼吸要领。适合各年龄段人群学习，特别适合中老年人健身养生。',
            'category': '运动养生',
            'video_url': '/static/videos/daoyin.mp4',
            'thumbnail_url': '/static/images/videos/daoyin_thumb.jpg',
            'duration': '28:50',
            'instructor': '陈强'
        }
    ]
    
    try:
        # 插入样例文章数据
        for article in sample_articles:
            cursor.execute("""
            INSERT OR IGNORE INTO articles 
            (title, content, author, category, tags, image_url) 
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                article['title'], article['content'], article['author'], 
                article['category'], article['tags'], article['image_url']
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
            (title, description, category, video_url, thumbnail_url, duration, instructor) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                video['title'], video['description'], video['category'],
                video['video_url'], video['thumbnail_url'], video['duration'],
                video['instructor']
            ))
        
        conn.commit()
        print("知识库样例数据已成功添加！")
    except Exception as e:
        conn.rollback()
        print(f"添加知识库样例数据时出错: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_sample_knowledge() 