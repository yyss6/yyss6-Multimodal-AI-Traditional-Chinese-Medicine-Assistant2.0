from flask import Flask, render_template, request, jsonify, session, Response, url_for
import requests
import os
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import urllib3
import ssl
from werkzeug.utils import secure_filename
import docx
import PyPDF2
import chardet
import random
import string
import sqlite3
from datetime import datetime
import json
from PIL import Image
import io
import base64
import easyocr
import numpy as np
import cv2

# 配置上传文件
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'mp3', 'wav', 'ogg'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# 创建上传目录
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 创建数据库
def init_db():
    conn = sqlite3.connect('tcm.db')
    c = conn.cursor()
    
    # 创建诊断记录表
    c.execute('''CREATE TABLE IF NOT EXISTS diagnosis_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  symptoms TEXT,
                  diagnosis TEXT,
                  prescription TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # 创建处方记录表
    c.execute('''CREATE TABLE IF NOT EXISTS prescription_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  herbs TEXT,
                  dosage TEXT,
                  usage TEXT,
                  notes TEXT,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

# 初始化数据库
init_db()

# 禁用 SSL 警告
urllib3.disable_warnings()

# 加载环境变量
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.secret_key = os.urandom(24)  # 设置 session 密钥

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
    # 为新用户创建会话ID和历史记录
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()
        session['history'] = []
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        symptoms = data.get('symptoms', [])
        mode = data.get('mode', 'default')
        files = data.get('files', [])
        
        # 创建一个session_id，如果不存在则创建新的
        session_id = session.get('session_id')
        if not session_id:
            session_id = generate_session_id()
            session['session_id'] = session_id
            session['history'] = []
            
        # 获取历史记录
        history = session.get('history', [])
        
        # 检查是否有图片文件
        has_image = any(file.get('type') == 'image' for file in files)
        
        # 构建消息历史
        messages = [
            {"role": "system", "content": generate_system_prompt(symptoms, mode)}
        ]
        
        for item in history:
            role = "user" if item["isUser"] else "assistant"
            messages.append({"role": role, "content": item["content"]})
        
        # 构建当前用户消息
        if has_image:
            # 多模态消息（包含图片）
            user_message = []
            
            # 添加文本部分
            if message:
                user_message.append({"type": "text", "text": message})
            
            # 添加文件内容
            for file in files:
                if file.get('type') == 'image':
                    # 不再直接添加图片，而是添加OCR识别的文本
                    if 'content' in file:
                        if message:
                            message += f"\n\n图片 {file.get('name', '')} 的识别内容：\n{file.get('content', '')}"
                        else:
                            message = f"图片 {file.get('name', '')} 的识别内容：\n{file.get('content', '')}"
                        
                        # 如果之前没有添加文本，现在添加
                        if not any(item.get('type') == 'text' for item in user_message):
                            user_message.append({"type": "text", "text": message})
                        # 否则更新最后一个文本项
                        else:
                            for item in user_message:
                                if item.get('type') == 'text':
                                    item['text'] = message
                                    break
                else:
                    # 添加其他类型文件的内容描述
                    if message:
                        message += f"\n\n{file.get('type', '文档')} {file.get('name', '')} 的内容：\n{file.get('content', '')}"
                    else:
                        message = f"{file.get('type', '文档')} {file.get('name', '')} 的内容：\n{file.get('content', '')}"
                    
                    # 如果之前没有添加文本，现在添加
                    if not any(item.get('type') == 'text' for item in user_message):
                        user_message.append({"type": "text", "text": message})
                    # 否则更新最后一个文本项
                    else:
                        for item in user_message:
                            if item.get('type') == 'text':
                                item['text'] = message
                                break
            
            # 添加当前用户输入
            messages.append({"role": "user", "content": user_message})
            
            # 保存到历史记录的简化版本
            history_content = message
            for file in files:
                if file.get('type') == 'image':
                    history_content += f"\n[图片: {file.get('name', '未命名')}]"
                else:
                    history_content += f"\n[{file.get('type', '文档')}: {file.get('name', '未命名')}]"
            
            history.append({"isUser": True, "content": history_content, "timestamp": int(time.time() * 1000)})
        else:
            # 纯文本消息
            user_input = message
            
            # 如果有文件内容，添加到用户输入中
            if files:
                user_input += "\n\n提供的文件内容："
                for file in files:
                    file_type = file.get('type', '文档')
                    if file_type == 'audio':
                        user_input += f"\n\n音频 {file.get('name', '')} 的转写内容：\n{file.get('content', '')}"
                    else:
                        user_input += f"\n\n{file_type} {file.get('name', '')} 的内容：\n{file.get('content', '')}"
            
            # 添加当前用户输入
            messages.append({"role": "user", "content": user_input})
            
            # 添加用户消息到历史记录
            history.append({"isUser": True, "content": user_input, "timestamp": int(time.time() * 1000)})
        
        session['history'] = history
        
        # 设置API请求
        url = "https://api.deepseek.com/v1/chat/completions"
        api_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 选择合适的模型 - 现在总是使用deepseek-chat，因为我们已经将图片转换为文本
        model_name = "deepseek-chat"
        
        api_data = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.7,
            "stream": True
        }

        # 创建具有重试机制的会话
        req_session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[502, 503, 504])
        req_session.mount('https://', TLSAdapter(max_retries=retries))
        
        # 创建响应
        def generate():
            try:
                # 使用stream=True进行流式传输
                resp = req_session.post(url, json=api_data, headers=api_headers, stream=True, timeout=60)
                resp.raise_for_status()  # 确保请求成功
                
                buffer = ""
                for line in resp.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]  # 移除 "data: " 前缀
                            if data_str.strip() == "[DONE]":
                                break
                            
                            try:
                                data_json = json.loads(data_str)
                                if 'choices' in data_json and len(data_json['choices']) > 0:
                                    delta = data_json['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        buffer += content
                                        yield content
                            except json.JSONDecodeError as e:
                                print(f"JSON解析错误: {e}")
                                continue
                
                # 添加AI回复到历史记录
                if buffer:
                    current_history = session.get('history', [])
                    current_history.append({"isUser": False, "content": buffer, "timestamp": int(time.time() * 1000)})
                    session['history'] = current_history
                
            except requests.exceptions.Timeout as e:
                error_msg = f"API请求超时: {str(e)}"
                print(error_msg)
                yield error_msg
            except requests.exceptions.ConnectionError as e:
                error_msg = f"API连接错误: {str(e)}"
                print(error_msg)
                yield error_msg
            except requests.exceptions.HTTPError as e:
                error_msg = f"API HTTP错误: {str(e)}"
                print(error_msg)
                yield error_msg  
            except Exception as e:
                error_msg = f"API请求错误: {str(e)}"
                print(error_msg)
                yield error_msg
        
        return Response(generate(), mimetype='text/plain')
    
    except Exception as e:
        print(f"处理请求时出错: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印完整的错误堆栈
        return jsonify({'error': str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear_history():
    """清除对话历史"""
    session['history'] = []
    return jsonify({"status": "success"})

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

if __name__ == '__main__':
    # 在生产环境中使用 gunicorn
    if os.environ.get('FLASK_ENV') == 'production':
        from gunicorn.app.base import BaseApplication

        class StandaloneApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    if key in self.cfg.settings and value is not None:
                        self.cfg.set(key, value)

            def load(self):
                return self.application

        options = {
            'bind': '0.0.0.0:5000',
            'workers': 4,  # 建议设置为 CPU 核心数 * 2 + 1
            'worker_class': 'sync',
            'timeout': 120,
            'keepalive': 5,
            'errorlog': 'error.log',
            'accesslog': 'access.log',
            'loglevel': 'info'
        }

        StandaloneApplication(app, options).run()
    else:
        # 在开发环境中使用 Flask 开发服务器
        app.run(host='0.0.0.0', port=5000, debug=True) 