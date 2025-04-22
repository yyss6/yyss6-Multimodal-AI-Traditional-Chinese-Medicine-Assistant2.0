# 多模态岐黄智语

一个基于Flask的智能聊天应用，集成了DeepSeek AI模型和EasyOCR图像识别功能，支持多模态交互，专注于中医健康咨询。

## 功能特点

- **智能对话**：基于DeepSeek AI模型的自然语言处理能力
- **中医知识**：内置中医理论和实践知识库
- **多模态输入**：支持文本、图片、文档等多种输入方式
- **图像识别**：使用EasyOCR进行图像文字识别，提取图片中的文本内容
- **文件处理**：支持上传和处理多种文件格式（TXT、PDF、DOC、DOCX、图片等）
- **音频转写**：支持音频文件的内容转写
- **知识文章**：提供丰富的中医健康文章，支持评论、点赞、收藏功能
- **实时响应**：流式响应，即时显示AI回复
- **会话历史**：保存对话历史，支持上下文理解
- **美观界面**：现代化的用户界面设计，支持暗色主题

## 技术栈

- **后端**：Python、Flask
- **前端**：HTML、CSS、JavaScript
- **AI模型**：DeepSeek API
- **图像识别**：EasyOCR
- **数据存储**：SQLite

## 已修复的问题

### 前端问题
- **highlight.min.js错误**：修复了咨询页面中`Uncaught ReferenceError: require is not defined`错误。问题原因是在浏览器环境中使用了Node.js版本的highlight.js库。已将引用改为浏览器专用版本：`https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@10.7.2/build/highlight.min.js`

### 后端问题
- **Response未定义错误**：修复了聊天接口`/chat`路由中的`name 'Response' is not defined`错误。问题原因是没有从Flask导入Response类。已在app.py文件头部添加Response导入。

## 安装步骤

### 前提条件

- Python 3.8+
- pip（Python包管理器）
- Git

### 安装过程

1. **克隆仓库**

```bash
git clone https://github.com/yyss6/多模态岐黄智语.git
cd 多模态岐黄智语
```

2. **创建并激活虚拟环境**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**

创建`.env`文件，添加以下内容：

```
DEEPSEEK_API_KEY=your_deepseek_api_key
```

5. **创建上传目录**

```bash
mkdir -p static/uploads
```

6. **运行应用**

```bash
# 开发环境
python run.py

# 生产环境
python run_production.py
```

## 使用方法

1. **启动应用**：运行应用后，在浏览器中访问 `http://localhost:5000`

2. **聊天功能**：
   - 在输入框中输入健康问题或中医相关咨询
   - 点击发送按钮或按Enter键发送消息
   - AI将实时生成并显示回复

3. **文件上传**：
   - 点击"上传文件"按钮选择文件
   - 点击"上传图片"按钮选择图片
   - 或直接将文件拖放到输入区域
   - 也可以直接粘贴剪贴板中的图片

4. **图片处理**：
   - 上传图片后，系统会自动使用EasyOCR识别图片中的文字
   - 识别结果会显示在预览区域
   - AI回复时会考虑图片中的文字内容

5. **文档处理**：
   - 上传文档后，系统会提取文档内容
   - 文档内容会显示在预览区域
   - AI回复时会考虑文档内容

6. **音频处理**：
   - 上传音频文件后，系统会尝试转写音频内容
   - 转写结果会显示在预览区域
   - AI回复时会考虑音频转写内容

7. **文章功能**：
   - 浏览文章：访问 `/article/list` 浏览所有健康文章
   - 文章详情：点击文章标题查看详情
   - 评论文章：登录后可在文章页面发表评论
   - 点赞收藏：登录后可对喜欢的文章进行点赞和收藏
   - 文章搜索：通过关键词或分类筛选查找相关文章

## 自定义配置

可以在`config.py`