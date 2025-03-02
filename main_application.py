from flask import Flask, render_template, request, jsonify, session, Response, send_from_directory
import os
from dotenv import load_dotenv
import requests
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

# 配置上传文件
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app = Flask(__name__, 
           template_folder='user_interface_templates',
           static_folder='application_resources')

@app.route('/')
def home():
    return render_template('user_interface.html')

# ... existing code ... 