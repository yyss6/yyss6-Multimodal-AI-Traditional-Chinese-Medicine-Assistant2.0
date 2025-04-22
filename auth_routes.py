from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from models import User, HealthProfile
from forms import LoginForm, RegistrationForm, HealthProfileForm, ChangePasswordForm
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import random
import string

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    # 已登录用户重定向到首页
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.get_by_username(form.username.data)
            if user and user.verify_password(form.password.data):
                login_user(user)
                user.update_last_login()
                flash('登录成功', 'success')
                next_page = request.args.get('next')
                return redirect(next_page if next_page else url_for('home'))
            flash('用户名或密码错误', 'danger')
        except Exception as e:
            print(f"登录过程中出错: {str(e)}")
            flash(f'登录过程中出错，请联系管理员', 'danger')
    
    return render_template('login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    # 如果用户已登录，重定向到首页
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # 检查用户名是否已存在
        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', 
                                    (form.username.data,)).fetchone()
        
        if existing_user:
            conn.close()
            flash('该用户名已被注册，请选择其他用户名', 'danger')
            return render_template('register.html', title='注册', form=form)
        
        # 创建新用户
        hashed_password = generate_password_hash(form.password.data)
        
        try:
            conn.execute(
                'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                (form.username.data, hashed_password, 'patient')
            )
            
            conn.commit()
            conn.close()
            
            flash('注册成功！请登录', 'success')
            return redirect(url_for('auth.login'))
        except sqlite3.Error as e:
            conn.close()
            flash(f'注册失败: {str(e)}', 'danger')
            return render_template('register.html', title='注册', form=form)
    
    return render_template('register.html', title='注册', form=form)

@auth.route('/logout')
@login_required
def logout():
    """用户登出"""
    # 保存当前用户ID，用于保存历史记录
    user_id = current_user.id
    
    # 先执行登出
    logout_user()
    
    # 有选择地清除会话，保留可能需要的游客历史记录
    # 保存当前会话中所有键
    preserved_data = {}
    for key in list(session.keys()):
        if key != f'chat_history_{user_id}' and not key.startswith('_'):
            preserved_data[key] = session[key]
    
    # 清除会话
    session.clear()
    
    # 恢复需要保留的数据
    for key, value in preserved_data.items():
        session[key] = value
    
    # 确保有会话ID
    if 'session_id' not in session:
        session['session_id'] = generate_session_id()
    
    flash('您已成功登出', 'info')
    return redirect(url_for('home'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """用户个人资料"""
    health_profile = HealthProfile.get_by_user_id(current_user.id)
    
    form = HealthProfileForm()
    if request.method == 'GET':
        if health_profile:
            form.name.data = health_profile.name
            form.gender.data = health_profile.gender
            form.birth_date.data = health_profile.birth_date
            form.height.data = health_profile.height
            form.weight.data = health_profile.weight
            form.blood_type.data = health_profile.blood_type
            form.allergies.data = health_profile.allergies
            form.chronic_diseases.data = health_profile.chronic_diseases
            form.family_history.data = health_profile.family_history
    
    if form.validate_on_submit():
        if health_profile:
            health_profile.name = form.name.data
            health_profile.gender = form.gender.data
            health_profile.birth_date = form.birth_date.data
            health_profile.height = form.height.data
            health_profile.weight = form.weight.data
            health_profile.blood_type = form.blood_type.data
            health_profile.allergies = form.allergies.data
            health_profile.chronic_diseases = form.chronic_diseases.data
            health_profile.family_history = form.family_history.data
            health_profile.update()
        else:
            health_profile = HealthProfile.create(
                user_id=current_user.id,
                name=form.name.data,
                gender=form.gender.data,
                birth_date=form.birth_date.data,
                height=form.height.data,
                weight=form.weight.data,
                blood_type=form.blood_type.data,
                allergies=form.allergies.data,
                chronic_diseases=form.chronic_diseases.data,
                family_history=form.family_history.data
            )
        flash('健康档案更新成功', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('profile.html', form=form, health_profile=health_profile)

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = User.get_by_id(current_user.id)
        if user and check_password_hash(user.password_hash, form.old_password.data):
            # 更新密码
            conn = sqlite3.connect('tcm.db')
            cursor = conn.cursor()
            
            new_password_hash = generate_password_hash(form.new_password.data)
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_password_hash, user.id)
            )
            
            conn.commit()
            conn.close()
            
            flash('密码修改成功', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('当前密码错误', 'danger')
    
    return render_template('change_password.html', form=form)

def get_db_connection():
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
    return conn

def generate_session_id(length=32):
    """生成随机会话ID"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length)) 