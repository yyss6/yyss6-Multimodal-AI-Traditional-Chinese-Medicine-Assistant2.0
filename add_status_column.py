#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库迁移脚本 - 为articles表添加status列
"""

import sqlite3

def add_status_to_articles():
    """为articles表添加status列"""
    conn = sqlite3.connect('tcm.db')
    cursor = conn.cursor()
    
    try:
        # 检查articles表结构
        cursor.execute("PRAGMA table_info(articles)")
        columns_info = cursor.fetchall()
        columns = [column[1] for column in columns_info]
        
        print(f"当前表结构: {columns}")
        
        if 'status' not in columns:
            print("正在添加status列...")
            
            # 尝试直接添加列
            try:
                cursor.execute("ALTER TABLE articles ADD COLUMN status TEXT DEFAULT 'published'")
                conn.commit()
                print("status列添加成功!")
            except sqlite3.OperationalError as e:
                print(f"直接添加列失败: {str(e)}")
                
                # 如果直接添加失败，则采用创建临时表的方式
                print("使用临时表方式添加status列...")
                
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
                
                # 添加新的status列
                columns_for_create.append("status TEXT DEFAULT 'published'")
                
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
                
                conn.commit()
                print("使用临时表方式添加status列成功!")
        else:
            print("status列已存在，无需修改")
        
    except Exception as e:
        conn.rollback()
        print(f"发生错误: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_status_to_articles() 