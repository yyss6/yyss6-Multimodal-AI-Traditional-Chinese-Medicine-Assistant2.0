#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time
import math
import uuid
import base64
import random
import string
import chardet
import sqlite3
import requests
import logging
import ssl
import numpy as np
from io import BytesIO
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_from_directory, Response
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from functools import wraps
from models import User, HealthProfile, DiagnosisRecord, Appointment
from forms import RegistrationForm, LoginForm, HealthProfileForm, ChangePasswordForm
from utils import admin_required

# 导入蓝图
from auth_routes import auth
from herb_routes import herbs
from appointment_routes import appointment
from export_routes import export
from knowledge_routes import knowledge
from admin_routes import admin
from article_routes import article

# 配置上传文件
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'ogg', 'doc', 'docx'}

# 初始化Flask应用
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB 上传限制
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key_here')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # 禁用缓存

# 配置Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录以访问此页面'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

# 注册蓝图
app.register_blueprint(auth)
app.register_blueprint(herbs)
app.register_blueprint(appointment)
app.register_blueprint(export)
app.register_blueprint(knowledge)
app.register_blueprint(admin)
app.register_blueprint(article)

# 从环境变量中获取API密钥
api_key = os.environ.get("DEEPSEEKV3_API_KEY") or os.getenv("DEEPSEEKV3_API_KEY")
if not api_key:
    print("警告：未设置Deepseek API密钥，使用默认测试密钥")
    api_key = "sk-d58d65360aa34f97bd4bbef897dad186"  # 默认API密钥，仅用于测试

print(f"使用的API密钥: {api_key[:8]}..." if len(api_key) > 8 else "API密钥无效")

# 验证API密钥格式
if not api_key.startswith("sk-") or len(api_key) < 20:
    print("警告：API密钥格式可能不正确")

# 中医相关的系统提示词
TCM_SYSTEM_PROMPT = """你是一位经验丰富的中医AI助手，具备以下能力：
1. 四诊合参：通过望闻问切的描述进行辨证
2. 病因分析：分析疾病的内外因素和发病机理
3. 辨证论治：根据症状进行辨证，制定治疗方案
4. 方剂开具：根据辨证结果开具合适的中药处方
5. 养生建议：提供饮食起居、生活方式等调养建议

诊断原则：
1. 整体观念：从整体角度分析病情
2. 辨证施治：根据证型选择治法
3. 因人制宜：考虑个体差异
4. 预防为主：注重预防保健
5. 注意事项：提醒可能的禁忌和注意事项

请用中文回答，保持专业性的同时确保通俗易懂。对于需要当面诊断的情况，建议患者及时就医。"""

class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)

# 创建一个带有重试机制的会话
http_session = requests.Session()
retries = Retry(
    total=5,  # 增加重试次数到5次
    backoff_factor=1,  # 增加重试间隔
    status_forcelist=[500, 502, 503, 504, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529],
    allowed_methods=['POST', 'GET'],  # 允许重试的请求方法
    raise_on_status=False
)

# 使用自定义的 TLS 适配器
adapter = TLSAdapter(max_retries=retries)
http_session.mount('https://', adapter)
http_session.verify = False  # 禁用 SSL 验证

# 设置请求头
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_file_content(file_path):
    """读取不同类型文件的内容"""
    file_extension = file_path.split('.')[-1].lower()
    content = ""

    try:
        if file_extension == 'txt':
            # 首先检测文件编码
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']

            # 使用检测到的编码读取文件
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()

        elif file_extension == 'docx':
            doc = docx.Document(file_path)
            content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])

        elif file_extension == 'pdf':
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                content = '\n'.join([page.extract_text() for page in pdf_reader.pages])

        return content

    except Exception as e:
        return f"文件读取错误: {str(e)}"

def generate_session_id(length=32):
    """生成随机会话ID"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_system_prompt(symptoms, mode):
    """根据症状和模式生成系统提示"""
    # 基本系统提示
    system_prompt = """你是一个专业的中医AI助手，具有深厚的中医理论知识和临床经验。
你的任务是根据用户描述的症状，提供中医诊断和治疗建议。
请遵循以下原则：
1. 使用严谨的中医理论进行分析，包括阴阳五行、脏腑经络、气血津液等
2. 根据症状进行辨证论治，可能的情况下给出相应的中医病名
3. 提供详细的诊断分析，解释症状与证型的关系
4. 推荐合适的治疗方法，包括方剂、针灸、食疗等
5. 使用专业但易懂的语言，避免晦涩难懂的术语
6. 如果信息不足，主动询问更多相关症状或体征
7. 对于复杂或危急情况，建议用户及时就医

如果用户上传了文件或图片，请仔细分析其中的内容，这些可能包含重要的医学信息、检查报告或相关资料。"""

    # 根据症状添加上下文
    if symptoms and isinstance(symptoms, list) and len(symptoms) > 0:
        symptoms_text = "、".join(symptoms)
        system_prompt += f"\n\n用户主诉症状：{symptoms_text}。请针对这些症状进行分析。"
    
    # 根据模式添加特定指导
    if mode == 'diagnosis':
        system_prompt += """
\n当前模式：辨证诊断
在这个模式下，请着重进行以下分析：
1. 详细分析用户描述的症状
2. 根据症状进行中医辨证分型
3. 分析病因病机
4. 提供可能的中医诊断
5. 解释症状与证型的关系
6. 如果需要，可以询问更多的症状信息以完善诊断"""
    elif mode == 'prescription':
        system_prompt += """
\n当前模式：处方开具
在这个模式下，请着重进行以下分析：
1. 基于用户症状进行辨证
2. 推荐适合的中药方剂，包括组成和剂量
3. 详细说明方剂的功效和主治
4. 提供用药建议，如煎煮方法、服用时间等
5. 说明注意事项和可能的不良反应
6. 提供配合的食疗建议"""
    
    return system_prompt

def process_file(file):
    """处理上传文件，返回文件内容、类型和路径"""
    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if ext in ['txt', 'doc', 'docx', 'pdf']:
            # 处理文本文件
            content = read_file_content(file_path)
            return content, 'text', file_path
        elif ext in ['png', 'jpg', 'jpeg', 'gif']:
            # 处理图片文件
            return process_image_file(file_path), 'image', file_path
        elif ext in ['mp3', 'wav', 'ogg']:
            # 处理音频文件
            return process_audio_file(file_path), 'audio', file_path
        else:
            return f"不支持的文件类型: {ext}", 'unknown', file_path
    except Exception as e:
        return f"文件处理失败: {str(e)}", 'error', None

def process_image_file(file_path):
    """处理图片文件，使用EasyOCR进行文字识别，返回识别文本"""
    try:
        with Image.open(file_path) as img:
            # 调整图片大小
            max_size = (800, 800)
            img.thumbnail(max_size, Image.LANCZOS)
            
            # 保存处理后的图片
            img.save(file_path, optimize=True, quality=85)
            
            # 转换为base64
            img_base64 = base64.b64encode(open(file_path, 'rb').read()).decode('utf-8')
            
            # 使用EasyOCR进行文字识别
            reader = easyocr.Reader(['ch_sim', 'en'])  # 支持中文和英文
            img_cv = cv2.imread(file_path)
            ocr_results = reader.readtext(img_cv)
            
            # 提取识别的文本
            ocr_text = ""
            if ocr_results:
                for detection in ocr_results:
                    ocr_text += detection[1] + " "
            
            # 如果OCR没有识别到文字或文字很少，使用Deepseek API进行图像内容识别
            if len(ocr_text.strip()) < 10:
                # 使用Deepseek API进行图像内容识别
                ocr_prompt = "请详细描述这张图片，如果图片包含文字，请提取出所有可见的文字内容。"
                ocr_messages = [
                    {"role": "system", "content": "你是一个精确的图像识别和OCR助手，你的任务是描述图像内容并精确提取图像中的所有文字。"},
                    {"role": "user", "content": [
                        {"type": "text", "text": ocr_prompt},
                        {"type": "image_url", 
                         "image_url": {"url": f"data:image/{img.format.lower()};base64,{img_base64}"}}
                    ]}
                ]
                
                # 设置API请求
                api_url = "https://api.deepseek.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                
                # 使用deepseek-chat模型
                data = {
                    "model": "deepseek-chat",
                    "messages": ocr_messages,
                    "max_tokens": 4000
                }
                
                # 发送请求
                vision_session = requests.Session()
                vision_retries = Retry(total=2, backoff_factor=0.5)
                vision_session.mount('https://', TLSAdapter(max_retries=vision_retries))
                
                try:
                    response = vision_session.post(api_url, json=data, headers=headers, timeout=30)
                    if response.status_code == 200:
                        result = response.json()
                        api_text = result["choices"][0]["message"]["content"]
                        # 如果EasyOCR识别到了一些文字，添加到API结果前面
                        if ocr_text.strip():
                            ocr_text = f"EasyOCR识别文字：\n{ocr_text.strip()}\n\n图像内容描述：\n{api_text}"
                        else:
                            ocr_text = api_text
                    else:
                        # 尝试获取更详细的错误信息
                        error_detail = ""
                        try:
                            error_json = response.json()
                            if "error" in error_json and "message" in error_json["error"]:
                                error_detail = f": {error_json['error']['message']}"
                        except:
                            pass
                        # 如果EasyOCR识别到了文字，返回这些文字
                        if ocr_text.strip():
                            ocr_text = f"EasyOCR识别文字：\n{ocr_text.strip()}\n\n(图像API识别服务返回错误: {response.status_code}{error_detail})"
                        else:
                            ocr_text = f"图像识别服务返回错误: {response.status_code}{error_detail}"
                except Exception as request_error:
                    # 如果EasyOCR识别到了文字，返回这些文字
                    if ocr_text.strip():
                        ocr_text = f"EasyOCR识别文字：\n{ocr_text.strip()}\n\n(图像API识别请求错误: {str(request_error)})"
                    else:
                        ocr_text = f"图像识别请求错误: {str(request_error)}"
            else:
                # EasyOCR识别到足够的文字，直接使用
                ocr_text = f"图片中识别的文字：\n{ocr_text.strip()}"
            
            return ocr_text
    except Exception as e:
        return f"图像处理错误: {str(e)}"

def process_audio_file(file_path):
    """处理音频文件，返回转写的文本"""
    try:
        # 调用语音识别API
        url = "https://api.deepseek.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        with open(file_path, 'rb') as audio_file:
            files = {
                'file': (os.path.basename(file_path), audio_file, 'audio/mpeg'),
                'model': (None, 'whisper-large-v3')
            }
            
            response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            return response.json().get('text', '音频转写失败')
        else:
            return f"语音识别失败: {response.status_code}"
    except Exception as e:
        return f"音频处理错误: {str(e)}"

@app.route('/')
def home():
    # 为新用户创建会话ID
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()
    
    # 根据用户是否登录，初始化不同的历史记录会话
    session_key = f'chat_history_{current_user.id}' if current_user.is_authenticated else 'chat_history_guest'
    if session_key not in session:
        session[session_key] = []
    
    # 如果当前用户已认证，获取一些用户数据
    user_data = None
    if current_user.is_authenticated:
        conn = sqlite3.connect('tcm.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取用户诊断记录数量
        cursor.execute("SELECT COUNT(*) FROM diagnosis_records WHERE user_id = ?", (current_user.id,))
        records_count = cursor.fetchone()[0]
        
        # 获取用户预约数量
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE user_id = ?", (current_user.id,))
        appointments_count = cursor.fetchone()[0]
        
        conn.close()
        
        user_data = {
            'records_count': records_count,
            'appointments_count': appointments_count
        }
    
    return render_template('index.html', user_data=user_data)

@app.route('/chat', methods=['POST'])
def chat():
    # 获取请求数据
    user_message = request.json.get('message', '').strip()
    symptoms = request.json.get('symptoms', [])
    mode = request.json.get('mode', 'general')
    files = request.json.get('files', [])
    
    # 如果用户消息为空，直接返回
    if not user_message and not files:
        return jsonify({
            'status': 'error',
            'message': '请输入您的问题或上传文件'
        })
    
    # 获取会话ID和聊天历史
    session_id = session.get('session_id', generate_session_id())
    session['session_id'] = session_id
    
    # 根据用户是否登录，使用不同的会话键
    session_key = f'chat_history_{current_user.id}' if current_user.is_authenticated else 'chat_history_guest'
    
    # 确保聊天历史存在
    if session_key not in session:
        session[session_key] = []
    
    chat_history = session.get(session_key, [])
    
    # 添加用户ID信息
    user_id = current_user.id if current_user.is_authenticated else None
    
    # 处理文件上传的内容
    uploaded_file_content = ""
    if files:
        for file in files:
            file_type = file.get('type', '')
            file_content = file.get('content', '')
            if file_content:
                uploaded_file_content += f"\n文件内容: {file_content}"
    
    # 生成系统提示
    system_prompt = generate_system_prompt(symptoms, mode)
    
    # 构建API请求体
    messages = []
    
    # 添加系统消息
    messages.append({
        "role": "system",
        "content": system_prompt
    })
    
    # 添加聊天历史
    for msg in chat_history:
        messages.append(msg)
    
    # 如果有上传的文件内容，添加到用户消息中
    if uploaded_file_content:
        user_content = f"{user_message}\n\n以下是上传的文件内容:{uploaded_file_content}"
    else:
        user_content = user_message
    
    # 添加新的用户消息
    user_message_obj = {
        "role": "user",
        "content": user_content
    }
    messages.append(user_message_obj)
    
    # 将用户消息添加到历史记录
    chat_history.append(user_message_obj)
    
    # 保存更新后的历史记录到会话中
    session[session_key] = chat_history
    
    # API请求设置
    url = "https://api.deepseek.com/v1/chat/completions"
    
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 4000,
        "user": session_id
    }
    
    try:
        # 使用流式响应
        def generate():
            response = http_session.post(url, json=payload, headers=headers, stream=True, timeout=60)
            
            if response.status_code != 200:
                error_message = f"API请求失败，状态码: {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data and 'message' in error_data['error']:
                        error_message += f", 错误信息: {error_data['error']['message']}"
                except:
                    pass
                
                print(error_message)
                yield f"data: {json.dumps({'status': 'error', 'message': error_message})}\n\n"
                return
            
            # 用于累积完整的AI回复
            full_response = ""
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    
                    # 跳过无关行
                    if not line_text.startswith('data: '):
                        continue
                    
                    # 提取JSON数据
                    data_str = line_text[6:]  # 去除'data: '前缀
                    
                    # 处理特殊情况
                    if data_str == '[DONE]':
                        # 流式响应结束
                        break
                            
                    try:
                        data = json.loads(data_str)
                        
                        # 提取生成的内容增量
                        if 'choices' in data and len(data['choices']) > 0:
                            choice = data['choices'][0]
                            if 'delta' in choice and 'content' in choice['delta']:
                                content_delta = choice['delta']['content']
                                full_response += content_delta
                                yield f"data: {json.dumps({'status': 'success', 'message': content_delta, 'done': False})}\n\n"
                            
                            # 检查是否生成完成
                            if choice.get('finish_reason') is not None:
                                # 保存聊天历史
                                ai_response_obj = {
                                    "role": "assistant",
                                    "content": full_response
                                }
                                chat_history.append(ai_response_obj)
                                session[session_key] = chat_history
                                # 确保更改被保存到会话
                                session.modified = True
                                
                                # 保存诊断记录到数据库
                                if mode == 'diagnosis' and current_user.is_authenticated:
                                    conn = sqlite3.connect('tcm.db')
                                    cursor = conn.cursor()
                                    
                                    cursor.execute(
                                        """
                                        INSERT INTO diagnosis_records 
                                        (user_id, symptoms, diagnosis, prescription) 
                                        VALUES (?, ?, ?, ?)
                                        """,
                                        (user_id, user_content, full_response, "")
                                    )
                                    
                                    conn.commit()
                                    record_id = cursor.lastrowid
                                    conn.close()
                                    
                                    yield f"data: {json.dumps({'status': 'success', 'message': '', 'done': True, 'record_id': record_id})}\n\n"
                                else:
                                    yield f"data: {json.dumps({'status': 'success', 'message': '', 'done': True})}\n\n"
                    except json.JSONDecodeError as e:
                        print(f"JSON解析错误: {e}")
                        continue
                
        return Response(generate(), mimetype='text/event-stream')
    
    except Exception as e:
        print(f"出现异常: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'处理请求时出错: {str(e)}'
        })

@app.route('/clear', methods=['POST'])
def clear_history():
    """清除对话历史"""
    # 根据用户是否登录，使用不同的会话键
    session_key = f'chat_history_{current_user.id}' if current_user.is_authenticated else 'chat_history_guest'
    
    # 清空对应的历史记录
    session[session_key] = []
    session.modified = True
    return jsonify({"status": "success"})

@app.route('/api/chat_history', methods=['GET'])
def get_chat_history():
    """获取当前会话的聊天历史"""
    # 根据用户是否登录，使用不同的会话键
    session_key = f'chat_history_{current_user.id}' if current_user.is_authenticated else 'chat_history_guest'
    
    # 从会话中获取历史记录
    chat_history = session.get(session_key, [])
    
    # 只返回用户和助手的消息，不返回系统提示
    filtered_history = [msg for msg in chat_history if msg.get('role') in ['user', 'assistant']]
    return jsonify({
        "status": "success", 
        "history": filtered_history
    })

@app.route('/api/records', methods=['GET'])
def get_records():
    conn = sqlite3.connect('tcm.db')
    c = conn.cursor()
    c.execute('SELECT * FROM diagnosis_records ORDER BY timestamp DESC LIMIT 50')
    records = c.fetchall()
    conn.close()
    return jsonify([{
        'id': r[0],
        'symptoms': r[1],
        'diagnosis': r[2],
        'prescription': r[3],
        'timestamp': r[4]
    } for r in records])

@app.route('/api/prescriptions', methods=['GET'])
def get_prescriptions():
    conn = sqlite3.connect('tcm.db')
    c = conn.cursor()
    c.execute('SELECT * FROM prescription_records ORDER BY timestamp DESC LIMIT 50')
    prescriptions = c.fetchall()
    conn.close()
    return jsonify([{
        'id': p[0],
        'herbs': p[1],
        'dosage': p[2],
        'usage': p[3],
        'notes': p[4],
        'timestamp': p[5]
    } for p in prescriptions])

@app.route('/api/prescriptions', methods=['POST'])
def add_prescription():
    data = request.json
    conn = sqlite3.connect('tcm.db')
    c = conn.cursor()
    c.execute('INSERT INTO prescription_records (herbs, dosage, usage, notes) VALUES (?, ?, ?, ?)',
              (data['herbs'], data['dosage'], data['usage'], data['notes']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# 添加图标路由
@app.route('/favicon.ico')
def favicon():
    return '', 204  # 返回空响应

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        try:
            content, file_type, file_path = process_file(file)
            filename = os.path.basename(file_path) if file_path else ''
            
            response_data = {
                'file_url': url_for('static', filename=f'uploads/{filename}', _external=True) if filename else '',
                'content': content,
                'type': file_type
            }
            
            # 如果是图片，添加base64编码
            if file_type == 'image' and file_path:
                try:
                    with Image.open(file_path) as img:
                        buffered = io.BytesIO()
                        img.save(buffered, format=img.format)
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        response_data['base64'] = f"data:image/{img.format.lower()};base64,{img_str}"
                except Exception as e:
                    print(f"图片编码错误: {str(e)}")
            
            return jsonify(response_data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': '不支持的文件类型'}), 400

# 访问个人中心
@app.route('/dashboard')
@login_required
def dashboard():
    """用户个人中心"""
    # 获取用户信息
    user = current_user
    
    # 获取用户的预约和收藏数量
    conn = sqlite3.connect('tcm.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE user_id = ?", (user.id,))
    appointment_count = cursor.fetchone()[0] or 0
    
    # 获取收藏数量
    cursor.execute("SELECT COUNT(*) FROM favorite_herbs WHERE user_id = ?", (user.id,))
    favorite_herbs_count = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM favorite_formulas WHERE user_id = ?", (user.id,))
    favorite_formulas_count = cursor.fetchone()[0] or 0
    
    favorites_count = favorite_herbs_count + favorite_formulas_count
    
    # 获取最近的预约
    cursor.execute("""
        SELECT * FROM appointments 
        WHERE user_id = ? 
        ORDER BY appointment_date DESC, appointment_time DESC LIMIT 5
    """, (user.id,))
    recent_appointments = cursor.fetchall()
    
    # 获取健康档案
    cursor.execute("SELECT * FROM health_profiles WHERE user_id = ?", (user.id,))
    health_profile = cursor.fetchone()
    
    # 获取医生信息用于显示预约医生姓名
    cursor.execute("SELECT id, username FROM users WHERE role = 'doctor'")
    doctors = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
    return render_template('dashboard.html', 
                          user=user,
                          appointments=appointment_count,
                          favorites=favorites_count,
                          recent_appointments=recent_appointments,
                          health_profile=health_profile,
                          doctors=doctors)

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """提供上传文件的访问"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000, debug=True) 