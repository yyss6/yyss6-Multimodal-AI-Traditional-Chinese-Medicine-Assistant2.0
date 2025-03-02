# AI聊天应用程序

一个基于Flask的智能聊天应用，集成了DeepSeek AI模型和EasyOCR图像识别功能，支持多模态交互。

## 功能特点

- **智能对话**：基于DeepSeek AI模型的自然语言处理能力
- **多模态输入**：支持文本、图片、文档等多种输入方式
- **图像识别**：使用EasyOCR进行图像文字识别，提取图片中的文本内容
- **文件处理**：支持上传和处理多种文件格式（TXT、PDF、DOC、DOCX、图片等）
- **音频转写**：支持音频文件的内容转写
- **实时响应**：流式响应，即时显示AI回复
- **会话历史**：保存对话历史，支持上下文理解
- **美观界面**：现代化的用户界面设计，支持暗色主题

## 技术栈

- **后端**：Python、Flask
- **前端**：HTML、CSS、JavaScript
- **AI模型**：DeepSeek API
- **图像识别**：EasyOCR
- **数据存储**：SQLite

## 安装步骤

### 前提条件

- Python 3.8+
- pip（Python包管理器）
- Git

### 安装过程

1. **克隆仓库**

```bash
git clone https://github.com/yyss6/-AI-.git
cd -AI-
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
   - 在输入框中输入问题或消息
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

## 自定义配置

可以在`config.py`文件中修改以下配置：

- 服务器端口
- 上传文件大小限制
- 允许的文件类型
- 其他应用程序设置

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议。请遵循以下步骤：

1. Fork本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建一个Pull Request

## 许可证

本项目采用MIT许可证 - 详情请参见LICENSE文件

## 联系方式

如有任何问题或建议，请通过GitHub Issues与我们联系。 