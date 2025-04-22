#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
统一启动脚本
根据环境变量FLASK_ENV自动选择开发或生产模式
"""

import os
from app import app
from config import config

def run_app():
    # 设置环境
    env = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[env])
    
    # 确保模板路径正确
    print(f"当前工作目录: {os.getcwd()}")
    print(f"模板路径: {app.template_folder}")
    
    if env == 'production':
        # 生产环境使用 Waitress
        from waitress import serve
        print(f"AI中医智能诊疗助手服务已启动在 http://localhost:{app.config.get('PORT', 5000)}")
        print("使用Waitress作为生产级WSGI服务器")
        serve(app, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), threads=4)
    else:
        # 开发环境使用 Flask 开发服务器
        print("正在开发环境中启动服务器...")
        app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    run_app() 