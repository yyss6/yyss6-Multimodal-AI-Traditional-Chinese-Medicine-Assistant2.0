import sqlite3

def fix_database():
    conn = sqlite3.connect('tcm.db')
    cursor = conn.cursor()
    
    # 检查表结构
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    
    # 查找是否有password列
    has_password = False
    has_password_hash = False
    
    for col in columns:
        if col[1] == 'password':
            has_password = True
        if col[1] == 'password_hash':
            has_password_hash = True
    
    if has_password and not has_password_hash:
        print("找到password列，重命名为password_hash...")
        # 创建新表
        cursor.execute('''
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'patient',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        ''')
        
        # 复制数据
        cursor.execute("INSERT INTO users_new (id, username, email, password_hash, role, created_at, last_login) SELECT id, username, email, password, role, created_at, last_login FROM users")
        
        # 删除旧表
        cursor.execute("DROP TABLE users")
        
        # 重命名新表
        cursor.execute("ALTER TABLE users_new RENAME TO users")
        
        print("数据库结构已修复！")
    elif not has_password_hash:
        print("未找到password_hash列，重新创建users表...")
        # 删除旧表
        cursor.execute("DROP TABLE IF EXISTS users")
        
        # 创建新表
        cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'patient',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        ''')
        
        print("users表已重新创建！")
    else:
        print("数据库结构正常，不需要修复。")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_database() 