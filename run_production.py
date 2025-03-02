#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
生产环境启动脚本
使用Waitress WSGI服务器替代Flask内置的开发服务器
"""

from waitress import serve
from main_application import app
import os

if __name__ == "__main__":
    # 从环境变量获取端口，如果没有设置则默认为5000
    port = int(os.environ.get("PORT", 5000))
    print(f"AI中医智能诊疗助手服务已启动在 http://localhost:{port}")
    print("使用Waitress作为生产级WSGI服务器")
    # 启动Waitress服务器
    serve(app, host="0.0.0.0", port=port, threads=4) 