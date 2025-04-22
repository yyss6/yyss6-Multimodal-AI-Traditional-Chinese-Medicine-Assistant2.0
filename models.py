import sqlite3
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid

# 数据库路径
DB_PATH = 'tcm.db'

# 确保数据库存在
def create_db_if_not_exists():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'patient',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    
    # 创建用户健康档案表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS health_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        gender TEXT,
        birth_date TEXT,
        height REAL,
        weight REAL,
        blood_type TEXT,
        allergies TEXT,
        chronic_diseases TEXT,
        family_history TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # 创建诊断记录表（如果不存在）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS diagnosis_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        symptoms TEXT,
        diagnosis TEXT,
        prescription TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # 创建处方记录表（如果不存在）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prescription_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        herbs TEXT,
        dosage TEXT,
        usage TEXT,
        notes TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # 创建预约记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        doctor_id INTEGER,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (doctor_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# 用户类
class User(UserMixin):
    def __init__(self, id, username, email, password_hash, role, created_at, last_login=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at
        self.last_login = last_login
    
    @staticmethod
    def get_by_id(user_id):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                role=user_data['role'],
                created_at=user_data['created_at'],
                last_login=user_data['last_login']
            )
        return None
    
    @staticmethod
    def get_by_username(username):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                role=user_data['role'],
                created_at=user_data['created_at'],
                last_login=user_data['last_login']
            )
        return None
    
    @staticmethod
    def get_by_email(email):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user_data = cursor.fetchone()
        
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                role=user_data['role'],
                created_at=user_data['created_at'],
                last_login=user_data['last_login']
            )
        return None
    
    @staticmethod
    def create(username, password, email=None, role='patient'):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        password_hash = generate_password_hash(password)
        
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, role)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return User.get_by_id(user_id)
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, self.id))
            
            conn.commit()
            conn.close()
            self.last_login = now
        except Exception as e:
            print(f"更新登录时间出错: {str(e)}")
            if conn:
                conn.close()

# 健康档案类
class HealthProfile:
    def __init__(self, id, user_id, name, gender=None, birth_date=None, height=None, 
                 weight=None, blood_type=None, allergies=None, chronic_diseases=None, 
                 family_history=None, last_updated=None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.gender = gender
        self.birth_date = birth_date
        self.height = height
        self.weight = weight
        self.blood_type = blood_type
        self.allergies = allergies
        self.chronic_diseases = chronic_diseases
        self.family_history = family_history
        self.last_updated = last_updated
    
    @staticmethod
    def get_by_user_id(user_id):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM health_profiles WHERE user_id = ?", (user_id,))
        profile_data = cursor.fetchone()
        
        conn.close()
        
        if profile_data:
            return HealthProfile(
                id=profile_data['id'],
                user_id=profile_data['user_id'],
                name=profile_data['name'],
                gender=profile_data['gender'],
                birth_date=profile_data['birth_date'],
                height=profile_data['height'],
                weight=profile_data['weight'],
                blood_type=profile_data['blood_type'],
                allergies=profile_data['allergies'],
                chronic_diseases=profile_data['chronic_diseases'],
                family_history=profile_data['family_history'],
                last_updated=profile_data['last_updated']
            )
        return None
    
    @staticmethod
    def create(user_id, name, gender=None, birth_date=None, height=None, 
               weight=None, blood_type=None, allergies=None, chronic_diseases=None, 
               family_history=None):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO health_profiles 
            (user_id, name, gender, birth_date, height, weight, blood_type, 
             allergies, chronic_diseases, family_history)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, gender, birth_date, height, weight, blood_type, 
             allergies, chronic_diseases, family_history)
        )
        
        conn.commit()
        profile_id = cursor.lastrowid
        conn.close()
        
        return HealthProfile.get_by_id(profile_id)
    
    @staticmethod
    def get_by_id(profile_id):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM health_profiles WHERE id = ?", (profile_id,))
        profile_data = cursor.fetchone()
        
        conn.close()
        
        if profile_data:
            return HealthProfile(
                id=profile_data['id'],
                user_id=profile_data['user_id'],
                name=profile_data['name'],
                gender=profile_data['gender'],
                birth_date=profile_data['birth_date'],
                height=profile_data['height'],
                weight=profile_data['weight'],
                blood_type=profile_data['blood_type'],
                allergies=profile_data['allergies'],
                chronic_diseases=profile_data['chronic_diseases'],
                family_history=profile_data['family_history'],
                last_updated=profile_data['last_updated']
            )
        return None
    
    def update(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            UPDATE health_profiles SET
            name = ?, gender = ?, birth_date = ?, height = ?, weight = ?,
            blood_type = ?, allergies = ?, chronic_diseases = ?, family_history = ?,
            last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (self.name, self.gender, self.birth_date, self.height, self.weight,
             self.blood_type, self.allergies, self.chronic_diseases, self.family_history,
             self.id)
        )
        
        conn.commit()
        conn.close()

# 诊断记录类
class DiagnosisRecord:
    def __init__(self, id, user_id, symptoms, diagnosis, prescription, timestamp):
        self.id = id
        self.user_id = user_id
        self.symptoms = symptoms
        self.diagnosis = diagnosis
        self.prescription = prescription
        self.timestamp = timestamp
    
    @staticmethod
    def create(user_id, symptoms, diagnosis, prescription):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO diagnosis_records (user_id, symptoms, diagnosis, prescription) VALUES (?, ?, ?, ?)",
            (user_id, symptoms, diagnosis, prescription)
        )
        
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        
        return DiagnosisRecord.get_by_id(record_id)
    
    @staticmethod
    def get_by_id(record_id):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM diagnosis_records WHERE id = ?", (record_id,))
        record_data = cursor.fetchone()
        
        conn.close()
        
        if record_data:
            return DiagnosisRecord(
                id=record_data['id'],
                user_id=record_data['user_id'],
                symptoms=record_data['symptoms'],
                diagnosis=record_data['diagnosis'],
                prescription=record_data['prescription'],
                timestamp=record_data['timestamp']
            )
        return None
    
    @staticmethod
    def get_by_user_id(user_id, limit=10):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM diagnosis_records WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        records = cursor.fetchall()
        
        conn.close()
        
        return [DiagnosisRecord(
            id=record['id'],
            user_id=record['user_id'],
            symptoms=record['symptoms'],
            diagnosis=record['diagnosis'],
            prescription=record['prescription'],
            timestamp=record['timestamp']
        ) for record in records]

# 预约类
class Appointment:
    def __init__(self, id, user_id, doctor_id, appointment_date, appointment_time, 
                 status, notes, created_at):
        self.id = id
        self.user_id = user_id
        self.doctor_id = doctor_id
        self.appointment_date = appointment_date
        self.appointment_time = appointment_time
        self.status = status
        self.notes = notes
        self.created_at = created_at
    
    @staticmethod
    def create(user_id, doctor_id, appointment_date, appointment_time, notes=None):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO appointments 
            (user_id, doctor_id, appointment_date, appointment_time, notes) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, doctor_id, appointment_date, appointment_time, notes)
        )
        
        conn.commit()
        appointment_id = cursor.lastrowid
        conn.close()
        
        return Appointment.get_by_id(appointment_id)
    
    @staticmethod
    def get_by_id(appointment_id):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM appointments WHERE id = ?", (appointment_id,))
        appointment_data = cursor.fetchone()
        
        conn.close()
        
        if appointment_data:
            return Appointment(
                id=appointment_data['id'],
                user_id=appointment_data['user_id'],
                doctor_id=appointment_data['doctor_id'],
                appointment_date=appointment_data['appointment_date'],
                appointment_time=appointment_data['appointment_time'],
                status=appointment_data['status'],
                notes=appointment_data['notes'],
                created_at=appointment_data['created_at']
            )
        return None
    
    @staticmethod
    def get_by_user_id(user_id, limit=10):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM appointments WHERE user_id = ? ORDER BY appointment_date DESC LIMIT ?",
            (user_id, limit)
        )
        appointments = cursor.fetchall()
        
        conn.close()
        
        return [Appointment(
            id=appointment['id'],
            user_id=appointment['user_id'],
            doctor_id=appointment['doctor_id'],
            appointment_date=appointment['appointment_date'],
            appointment_time=appointment['appointment_time'],
            status=appointment['status'],
            notes=appointment['notes'],
            created_at=appointment['created_at']
        ) for appointment in appointments]
    
    @staticmethod
    def get_by_doctor_id(doctor_id, limit=10):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM appointments WHERE doctor_id = ? ORDER BY appointment_date DESC LIMIT ?",
            (doctor_id, limit)
        )
        appointments = cursor.fetchall()
        
        conn.close()
        
        return [Appointment(
            id=appointment['id'],
            user_id=appointment['user_id'],
            doctor_id=appointment['doctor_id'],
            appointment_date=appointment['appointment_date'],
            appointment_time=appointment['appointment_time'],
            status=appointment['status'],
            notes=appointment['notes'],
            created_at=appointment['created_at']
        ) for appointment in appointments]
    
    def update_status(self, status):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE appointments SET status = ? WHERE id = ?",
            (status, self.id)
        )
        
        conn.commit()
        conn.close()
        
        self.status = status

# 初始化数据库
create_db_if_not_exists() 