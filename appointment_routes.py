from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import User, Appointment
from forms import AppointmentForm
import sqlite3
from datetime import datetime, timedelta

appointment = Blueprint('appointment', __name__, url_prefix='/appointment')

@appointment.route('/appointments', methods=['GET'])
@login_required
def appointments():
    """显示用户的预约列表"""
    user_appointments = Appointment.get_by_user_id(current_user.id)
    
    if current_user.role == 'doctor':
        # 如果是医生，也显示别人对该医生的预约
        doctor_appointments = Appointment.get_by_doctor_id(current_user.id)
    else:
        doctor_appointments = []
    
    return render_template('appointments.html', 
                          user_appointments=user_appointments,
                          doctor_appointments=doctor_appointments)

@appointment.route('/make_appointment', methods=['GET', 'POST'])
@login_required
def make_appointment():
    """创建新预约"""
    form = AppointmentForm()
    
    # 获取所有医生用户
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE role = 'doctor'")
    doctors = cursor.fetchall()
    conn.close()
    
    doctor_choices = [(doctor['id'], doctor['username']) for doctor in doctors]
    form.doctor_id.choices = doctor_choices
    
    if form.validate_on_submit():
        # 检查时间是否可用
        conn = sqlite3.connect('tcm.db')
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM appointments 
            WHERE doctor_id = ? AND appointment_date = ? AND appointment_time = ? AND status != 'cancelled'
            """,
            (form.doctor_id.data, form.appointment_date.data.strftime('%Y-%m-%d'), form.appointment_time.data)
        )
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            flash('所选时间已被预约，请选择其他时间', 'danger')
        else:
            appointment = Appointment.create(
                user_id=current_user.id,
                doctor_id=form.doctor_id.data,
                appointment_date=form.appointment_date.data.strftime('%Y-%m-%d'),
                appointment_time=form.appointment_time.data,
                notes=form.notes.data
            )
            
            if appointment:
                flash('预约创建成功', 'success')
                return redirect(url_for('appointment.appointments'))
            else:
                flash('预约创建失败，请稍后再试', 'danger')
    
    return render_template('make_appointment.html', form=form)

@appointment.route('/cancel_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    """取消预约"""
    appointment = Appointment.get_by_id(appointment_id)
    
    if not appointment:
        flash('预约不存在', 'danger')
        return redirect(url_for('appointment.appointments'))
    
    # 检查是否是用户自己的预约或医生的预约
    if appointment.user_id != current_user.id and appointment.doctor_id != current_user.id:
        flash('无权操作此预约', 'danger')
        return redirect(url_for('appointment.appointments'))
    
    appointment.update_status('cancelled')
    flash('预约已取消', 'success')
    return redirect(url_for('appointment.appointments'))

@appointment.route('/complete_appointment/<int:appointment_id>', methods=['POST'])
@login_required
def complete_appointment(appointment_id):
    """完成预约（仅医生可操作）"""
    if current_user.role != 'doctor':
        flash('只有医生可以完成预约', 'danger')
        return redirect(url_for('appointment.appointments'))
    
    appointment = Appointment.get_by_id(appointment_id)
    
    if not appointment:
        flash('预约不存在', 'danger')
        return redirect(url_for('appointment.appointments'))
    
    # 检查是否是分配给该医生的预约
    if appointment.doctor_id != current_user.id:
        flash('无权操作此预约', 'danger')
        return redirect(url_for('appointment.appointments'))
    
    appointment.update_status('completed')
    flash('预约已完成', 'success')
    return redirect(url_for('appointment.appointments'))

@appointment.route('/api/available_times', methods=['GET'])
@login_required
def available_times():
    """获取医生的可用时间（用于Ajax请求）"""
    doctor_id = request.args.get('doctor_id', type=int)
    date_str = request.args.get('date')
    
    if not doctor_id or not date_str:
        return jsonify({'error': '缺少参数'}), 400
    
    # 所有可能的预约时间
    all_times = ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', 
                '14:00', '14:30', '15:00', '15:30', '16:00', '16:30']
    
    # 查询已经被预约的时间
    conn = sqlite3.connect('tcm.db')
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT appointment_time FROM appointments 
        WHERE doctor_id = ? AND appointment_date = ? AND status != 'cancelled'
        """,
        (doctor_id, date_str)
    )
    booked_times = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    # 计算可用时间
    available_times = [time for time in all_times if time not in booked_times]
    
    return jsonify({
        'available_times': available_times
    }) 