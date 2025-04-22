#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, Blueprint, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

app = Flask(__name__)
app.config['SECRET_KEY'] = 'testkey123'

# 创建表单类
class RegistrationForm(FlaskForm):
    """用户注册表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')

class LoginForm(FlaskForm):
    """用户登录表单"""
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

# 创建认证蓝图
auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    form = RegistrationForm()
    if form.validate_on_submit():
        # 假装注册成功
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    form = LoginForm()
    if form.validate_on_submit():
        # 假装登录成功
        flash('登录成功', 'success')
        return redirect(url_for('home'))
    
    return render_template('login.html', form=form)

# 注册蓝图
app.register_blueprint(auth)

@app.route('/')
def home():
    """首页"""
    return "欢迎来到首页!"

@app.route('/test')
def test():
    """测试路由"""
    return "测试成功!"

if __name__ == '__main__':
    app.run(debug=True, port=5001) 