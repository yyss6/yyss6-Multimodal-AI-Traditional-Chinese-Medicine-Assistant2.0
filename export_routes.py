from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, Response, make_response
from flask_login import login_required, current_user
import sqlite3
from datetime import datetime
import os
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
import io

export = Blueprint('export', __name__, url_prefix='/export')

# 注册中文字体
try:
    # 尝试注册中文字体，如果没有找到，将使用默认字体
    font_path = os.path.join('static', 'fonts', 'simhei.ttf')
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('SimHei', font_path))
except:
    print("警告：无法加载中文字体，PDF导出可能无法正确显示中文")

@export.route('/export_diagnosis/<int:record_id>')
@login_required
def export_diagnosis(record_id):
    """导出诊断记录为PDF"""
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取诊断记录
    cursor.execute("""
        SELECT * FROM diagnosis_records 
        WHERE id = ? AND user_id = ?
    """, (record_id, current_user.id))
    record = cursor.fetchone()
    
    if not record:
        conn.close()
        flash('诊断记录不存在或无权访问', 'danger')
        return redirect(url_for('home'))
    
    # 获取用户健康档案
    cursor.execute("SELECT * FROM health_profiles WHERE user_id = ?", (current_user.id,))
    profile = cursor.fetchone()
    
    conn.close()
    
    # 创建临时文件
    output = io.BytesIO()
    
    # 创建PDF
    c = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    
    # 设置字体
    font_name = 'SimHei' if 'SimHei' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    
    # 报告标题
    c.setFont(font_name, 18)
    c.drawCentredString(width/2, height - 2*cm, "中医诊断报告")
    
    # 报告生成时间
    c.setFont(font_name, 10)
    c.drawRightString(width - 2*cm, height - 3*cm, f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 用户信息
    c.setFont(font_name, 12)
    y_position = height - 4*cm
    
    if profile:
        c.drawString(2*cm, y_position, f"姓名: {profile['name']}")
        y_position -= 0.7*cm
        if profile['gender']:
            c.drawString(2*cm, y_position, f"性别: {profile['gender']}")
            y_position -= 0.7*cm
        if profile['birth_date']:
            c.drawString(2*cm, y_position, f"出生日期: {profile['birth_date']}")
            y_position -= 0.7*cm
    else:
        c.drawString(2*cm, y_position, f"用户ID: {current_user.id}")
        y_position -= 0.7*cm
    
    c.drawString(2*cm, y_position, f"诊断日期: {record['timestamp']}")
    y_position -= 1.5*cm
    
    # 诊断内容
    c.setFont(font_name, 14)
    c.drawString(2*cm, y_position, "症状描述:")
    y_position -= 0.8*cm
    
    c.setFont(font_name, 12)
    # 拆分长文本以适应页面宽度
    symptoms_lines = wrap_text(record['symptoms'], font_name, 12, width - 4*cm)
    for line in symptoms_lines:
        c.drawString(2*cm, y_position, line)
        y_position -= 0.6*cm
    
    y_position -= 0.5*cm
    c.setFont(font_name, 14)
    c.drawString(2*cm, y_position, "诊断结果:")
    y_position -= 0.8*cm
    
    c.setFont(font_name, 12)
    diagnosis_lines = wrap_text(record['diagnosis'], font_name, 12, width - 4*cm)
    for line in diagnosis_lines:
        c.drawString(2*cm, y_position, line)
        y_position -= 0.6*cm
    
    y_position -= 0.5*cm
    c.setFont(font_name, 14)
    c.drawString(2*cm, y_position, "处方建议:")
    y_position -= 0.8*cm
    
    c.setFont(font_name, 12)
    prescription_lines = wrap_text(record['prescription'], font_name, 12, width - 4*cm)
    for line in prescription_lines:
        c.drawString(2*cm, y_position, line)
        y_position -= 0.6*cm
    
    # 添加页脚
    c.setFont(font_name, 10)
    c.drawCentredString(width/2, 1*cm, "本报告由岐黄智语自动生成，仅供参考，请遵医嘱")
    
    c.save()
    
    # 准备文件下载
    output.seek(0)
    filename = f"诊断报告_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@export.route('/export_prescription/<int:prescription_id>', methods=['GET'])
@login_required
def export_prescription(prescription_id):
    """导出处方记录"""
    format_type = request.args.get('format', 'pdf')
    
    conn = sqlite3.connect('tcm.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取处方记录
    cursor.execute("""
        SELECT * FROM prescription_records 
        WHERE id = ? AND user_id = ?
    """, (prescription_id, current_user.id))
    prescription = cursor.fetchone()
    
    if not prescription:
        conn.close()
        flash('处方记录不存在或无权访问', 'danger')
        return redirect(url_for('home'))
    
    # 获取用户健康档案
    cursor.execute("SELECT * FROM health_profiles WHERE user_id = ?", (current_user.id,))
    profile = cursor.fetchone()
    
    conn.close()
    
    if format_type == 'pdf':
        return export_prescription_as_pdf(prescription, profile)
    else:
        return export_prescription_as_text(prescription, profile)

def export_prescription_as_pdf(prescription, profile):
    """导出处方为PDF格式"""
    # 创建临时文件
    output = io.BytesIO()
    
    # 创建PDF
    c = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    
    # 设置字体
    font_name = 'SimHei' if 'SimHei' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    
    # 处方标题
    c.setFont(font_name, 18)
    c.drawCentredString(width/2, height - 2*cm, "中药处方")
    
    # 处方时间
    c.setFont(font_name, 10)
    c.drawRightString(width - 2*cm, height - 3*cm, f"开具时间: {prescription['timestamp']}")
    
    # 用户信息
    c.setFont(font_name, 12)
    y_position = height - 4*cm
    
    if profile:
        c.drawString(2*cm, y_position, f"姓名: {profile['name']}")
        y_position -= 0.7*cm
        if profile['gender']:
            c.drawString(2*cm, y_position, f"性别: {profile['gender']}")
            y_position -= 0.7*cm
        if profile['birth_date']:
            c.drawString(2*cm, y_position, f"出生日期: {profile['birth_date']}")
            y_position -= 0.7*cm
    else:
        c.drawString(2*cm, y_position, f"用户ID: {current_user.id}")
        y_position -= 0.7*cm
    
    # 处方内容
    y_position -= 0.5*cm
    c.setFont(font_name, 14)
    c.drawString(2*cm, y_position, "处方内容:")
    y_position -= 0.8*cm
    
    c.setFont(font_name, 12)
    herbs_lines = wrap_text(prescription['herbs'], font_name, 12, width - 4*cm)
    for line in herbs_lines:
        c.drawString(2*cm, y_position, line)
        y_position -= 0.6*cm
    
    y_position -= 0.5*cm
    c.setFont(font_name, 14)
    c.drawString(2*cm, y_position, "用法用量:")
    y_position -= 0.8*cm
    
    c.setFont(font_name, 12)
    usage_lines = wrap_text(prescription['usage'], font_name, 12, width - 4*cm)
    for line in usage_lines:
        c.drawString(2*cm, y_position, line)
        y_position -= 0.6*cm
    
    if prescription['notes']:
        y_position -= 0.5*cm
        c.setFont(font_name, 14)
        c.drawString(2*cm, y_position, "注意事项:")
        y_position -= 0.8*cm
        
        c.setFont(font_name, 12)
        notes_lines = wrap_text(prescription['notes'], font_name, 12, width - 4*cm)
        for line in notes_lines:
            c.drawString(2*cm, y_position, line)
            y_position -= 0.6*cm
    
    # 添加页脚
    c.setFont(font_name, 10)
    c.drawCentredString(width/2, 1*cm, "本处方由岐黄智语自动生成，仅供参考，请遵医嘱")
    
    c.save()
    
    # 准备文件下载
    output.seek(0)
    filename = f"中药处方_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

def export_prescription_as_text(prescription, profile):
    """导出处方为文本格式"""
    lines = ["===================== 中药处方 ====================="]
    lines.append(f"开具时间: {prescription['timestamp']}")
    lines.append("")
    
    if profile:
        lines.append(f"姓名: {profile['name']}")
        if profile['gender']:
            lines.append(f"性别: {profile['gender']}")
        if profile['birth_date']:
            lines.append(f"出生日期: {profile['birth_date']}")
    else:
        lines.append(f"用户ID: {current_user.id}")
    
    lines.append("")
    lines.append("----------- 处方内容 -----------")
    lines.append(prescription['herbs'])
    lines.append("")
    lines.append("----------- 用法用量 -----------")
    lines.append(prescription['usage'])
    
    if prescription['notes']:
        lines.append("")
        lines.append("----------- 注意事项 -----------")
        lines.append(prescription['notes'])
    
    lines.append("")
    lines.append("本处方由岐黄智语自动生成，仅供参考，请遵医嘱")
    lines.append("===============================================")
    
    content = "\n".join(lines)
    
    # 创建响应
    response = make_response(content)
    response.headers["Content-Disposition"] = f"attachment; filename=中药处方_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    
    return response

def wrap_text(text, font_name, font_size, max_width):
    """将长文本拆分为多行以适应页面宽度"""
    if not text:
        return []
    
    lines = []
    paragraphs = text.split('\n')
    
    for paragraph in paragraphs:
        if not paragraph:
            lines.append("")
            continue
        
        words = paragraph.split(' ')
        current_line = words[0]
        
        for word in words[1:]:
            # 这里我们简化计算，仅按字符数量估算宽度
            # 实际应用中应该使用pdfmetrics.stringWidth计算准确宽度
            if len(current_line + ' ' + word) * (font_size / 2) < max_width:
                current_line += ' ' + word
            else:
                lines.append(current_line)
                current_line = word
        
        lines.append(current_line)
    
    return lines 