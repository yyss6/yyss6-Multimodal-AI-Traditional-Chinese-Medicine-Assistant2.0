import os
from app import app
from config import config

def run_app():
    # 设置环境
    env = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[env])
    
    if env == 'production':
        # 生产环境使用 Waitress
        from waitress import serve
        print("正在生产环境中启动服务器...")
        serve(app, host='0.0.0.0', port=5000, threads=4)
    else:
        # 开发环境使用 Flask 开发服务器
        print("正在开发环境中启动服务器...")
        app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    run_app() 