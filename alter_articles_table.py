#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库迁移脚本 - 为articles表添加summary列，为formulas表添加created_at列
"""

import sqlite3

def alter_articles_table():
    """为articles表添加summary列"""
    conn = sqlite3.connect('tcm.db')
    cursor = conn.cursor()
    
    try:
        # 检查articles表结构
        cursor.execute("PRAGMA table_info(articles)")
        columns_info = cursor.fetchall()
        columns = [column[1] for column in columns_info]
        
        print(f"当前表结构: {columns}")
        
        if 'summary' not in columns:
            print("正在添加summary列...")
            
            # 获取现有列，用于构建新的CREATE TABLE和INSERT语句
            columns_for_select = []
            columns_for_create = []
            
            for col in columns_info:
                col_name = col[1]
                col_type = col[2]
                is_not_null = col[3]
                default_value = col[4]
                is_pk = col[5]
                
                columns_for_select.append(col_name)
                
                # 构建列定义
                col_def = f"{col_name} {col_type}"
                if is_pk:
                    col_def += " PRIMARY KEY"
                if is_not_null:
                    col_def += " NOT NULL"
                if default_value is not None:
                    col_def += f" DEFAULT {default_value}"
                    
                columns_for_create.append(col_def)
            
            # 添加新的summary列
            columns_for_create.append("summary TEXT")
            
            # 构建CREATE TABLE语句
            create_table_sql = f"CREATE TABLE articles_temp (\n  " + ",\n  ".join(columns_for_create) + "\n)"
            print(f"执行创建临时表SQL:\n{create_table_sql}")
            cursor.execute(create_table_sql)
            
            # 构建INSERT语句
            select_columns = ", ".join(columns_for_select)
            insert_sql = f"INSERT INTO articles_temp ({select_columns}) SELECT {select_columns} FROM articles"
            print(f"执行数据迁移SQL:\n{insert_sql}")
            cursor.execute(insert_sql)
            
            # 删除旧表并重命名新表
            cursor.execute("DROP TABLE articles")
            cursor.execute("ALTER TABLE articles_temp RENAME TO articles")
            
            print("summary列添加成功!")
        else:
            print("summary列已存在，无需修改")
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"发生错误: {str(e)}")
        
        # 如果出错，尝试直接添加列（如果表没有被删除的话）
        try:
            print("尝试使用ALTER TABLE直接添加summary列...")
            cursor.execute("ALTER TABLE articles ADD COLUMN summary TEXT")
            conn.commit()
            print("使用ALTER TABLE添加summary列成功!")
        except Exception as e2:
            conn.rollback()
            print(f"直接添加列也失败: {str(e2)}")
    finally:
        conn.close()
        
def add_created_at_to_formulas():
    """为formulas表添加created_at列"""
    conn = sqlite3.connect('tcm.db')
    cursor = conn.cursor()
    
    try:
        # 检查formulas表结构
        cursor.execute("PRAGMA table_info(formulas)")
        columns_info = cursor.fetchall()
        columns = [column[1] for column in columns_info]
        
        print(f"formulas表结构: {columns}")
        
        if 'created_at' not in columns:
            print("正在为formulas表添加created_at列...")
            
            # 获取现有列，用于构建新的CREATE TABLE和INSERT语句
            columns_for_select = []
            columns_for_create = []
            
            for col in columns_info:
                col_name = col[1]
                col_type = col[2]
                is_not_null = col[3]
                default_value = col[4]
                is_pk = col[5]
                
                columns_for_select.append(col_name)
                
                # 构建列定义
                col_def = f"{col_name} {col_type}"
                if is_pk:
                    col_def += " PRIMARY KEY"
                if is_not_null:
                    col_def += " NOT NULL"
                if default_value is not None:
                    col_def += f" DEFAULT {default_value}"
                    
                columns_for_create.append(col_def)
            
            # 添加新的created_at列
            columns_for_create.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
            # 构建CREATE TABLE语句
            create_table_sql = f"CREATE TABLE formulas_temp (\n  " + ",\n  ".join(columns_for_create) + "\n)"
            print(f"执行创建临时表SQL:\n{create_table_sql}")
            cursor.execute(create_table_sql)
            
            # 构建INSERT语句
            select_columns = ", ".join(columns_for_select)
            insert_sql = f"INSERT INTO formulas_temp ({select_columns}) SELECT {select_columns} FROM formulas"
            print(f"执行数据迁移SQL:\n{insert_sql}")
            cursor.execute(insert_sql)
            
            # 删除旧表并重命名新表
            cursor.execute("DROP TABLE formulas")
            cursor.execute("ALTER TABLE formulas_temp RENAME TO formulas")
            
            print("created_at列添加成功!")
        else:
            print("created_at列已存在，无需修改")
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"为formulas表添加created_at列出错: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    alter_articles_table()
    add_created_at_to_formulas() 