from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, DateField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from wtforms import ValidationError
from models import User

class LoginForm(FlaskForm):
    """用户登录表单"""
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    """用户注册表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')
    
    def validate_username(self, field):
        if User.get_by_username(field.data):
            raise ValidationError('用户名已被使用，请更换一个')

class HealthProfileForm(FlaskForm):
    """健康档案表单"""
    name = StringField('姓名', validators=[DataRequired()])
    gender = SelectField('性别', choices=[('男', '男'), ('女', '女'), ('其他', '其他')], validators=[Optional()])
    birth_date = DateField('出生日期', format='%Y-%m-%d', validators=[Optional()])
    height = FloatField('身高(cm)', validators=[Optional()])
    weight = FloatField('体重(kg)', validators=[Optional()])
    blood_type = SelectField('血型', choices=[
        ('A型', 'A型'), ('B型', 'B型'), ('AB型', 'AB型'), ('O型', 'O型'), ('未知', '未知')
    ], validators=[Optional()])
    allergies = TextAreaField('过敏史', validators=[Optional()])
    chronic_diseases = TextAreaField('慢性病史', validators=[Optional()])
    family_history = TextAreaField('家族病史', validators=[Optional()])
    submit = SubmitField('保存')

class ChangePasswordForm(FlaskForm):
    """修改密码表单"""
    old_password = PasswordField('当前密码', validators=[DataRequired()])
    new_password = PasswordField('新密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认新密码', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('修改密码')

class AppointmentForm(FlaskForm):
    """预约表单"""
    appointment_date = DateField('预约日期', format='%Y-%m-%d', validators=[DataRequired()])
    appointment_time = SelectField('预约时间', choices=[
        ('09:00', '09:00'), ('09:30', '09:30'), ('10:00', '10:00'), ('10:30', '10:30'),
        ('11:00', '11:00'), ('11:30', '11:30'), ('14:00', '14:00'), ('14:30', '14:30'),
        ('15:00', '15:00'), ('15:30', '15:30'), ('16:00', '16:00'), ('16:30', '16:30')
    ], validators=[DataRequired()])
    doctor_id = SelectField('医生', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('预约备注', validators=[Optional()])
    submit = SubmitField('提交预约')

class PrescriptionExportForm(FlaskForm):
    """处方导出表单"""
    format = SelectField('导出格式', choices=[('pdf', 'PDF'), ('txt', '文本文件')], validators=[DataRequired()])
    submit = SubmitField('导出处方') 