#!/usr/bin/env python3
"""
企业智能问答助手 - 数据库初始化脚本

用法: python init_db.py
"""

import os
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "enterprise.db")
SCHEMA_FILE = os.path.join(SCRIPT_DIR, "schema.sql")
DATA_FILE = os.path.join(SCRIPT_DIR, "seed_data.sql")


def main():
    print("=" * 50)
    print("  企业智能问答助手 - 数据库初始化")
    print("=" * 50)
    
    # 检查 schema.sql 是否存在
    if not os.path.exists(SCHEMA_FILE):
        print(f"错误: schema.sql 不存在: {SCHEMA_FILE}")
        sys.exit(1)
    
    # 检查 seed_data.sql 是否存在（必须存在）
    if not os.path.exists(DATA_FILE):
        print(f"错误: seed_data.sql 不存在: {DATA_FILE}")
        print("请确保种子数据文件存在！")
        sys.exit(1)
    
    # 清理旧数据库
    print("✓ 清理旧数据库...")
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    
    # 创建连接
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 创建表结构
    print("✓ 创建表结构...")
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    
    # 导入数据
    print("✓ 导入种子数据...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data_sql = f.read()
    cursor.executescript(data_sql)
    
    # 提交并关闭
    conn.commit()
    
    # 验证
    print("")
    print("=" * 50)
    print("  数据验证")
    print("=" * 50)
    
    cursor.execute("SELECT COUNT(*) FROM employees")
    employee_count = cursor.fetchone()[0]
    print(f"  员工数：{employee_count}")
    
    cursor.execute("SELECT COUNT(*) FROM projects")
    project_count = cursor.fetchone()[0]
    print(f"  项目数：{project_count}")
    
    cursor.execute("SELECT COUNT(*) FROM project_members")
    pm_count = cursor.fetchone()[0]
    print(f"  项目成员数：{pm_count}")
    
    cursor.execute("SELECT COUNT(*) FROM attendance")
    att_count = cursor.fetchone()[0]
    print(f"  考勤记录：{att_count}")
    
    cursor.execute("SELECT COUNT(*) FROM performance_reviews")
    pr_count = cursor.fetchone()[0]
    print(f"  绩效记录：{pr_count}")
    
    # 验证数据量
    if employee_count != 10:
        print(f"  警告: 员工数应为 10，实际 {employee_count}")
    if project_count != 5:
        print(f"  警告: 项目数应为 5，实际 {project_count}")
    if pm_count != 12:
        print(f"  警告: 项目成员数应为 12，实际 {pm_count}")
    if att_count < 40:
        print(f"  警告: 考勤记录应不少于 40，实际 {att_count}")
    if pr_count < 17:
        print(f"  警告: 绩效记录应不少于 17，实际 {pr_count}")
    
    # 快速测试
    print("")
    print("=" * 50)
    print("  快速测试")
    print("=" * 50)
    
    cursor.execute("SELECT department FROM employees WHERE employee_id='EMP-001'")
    dept = cursor.fetchone()[0]
    print(f"  张三的部门：{dept}")
    
    cursor.execute("SELECT COUNT(*) FROM employees WHERE department='研发部' AND status='active'")
    rd_count = cursor.fetchone()[0]
    print(f"  研发部人数：{rd_count}")
    
    cursor.execute("SELECT COUNT(*) FROM attendance WHERE employee_id='EMP-001' AND status='late' AND date LIKE '2026-02-%'")
    late_count = cursor.fetchone()[0]
    print(f"  张三 2 月迟到：{late_count}")
    
    conn.close()
    
    print("")
    print(f"✓ 数据库初始化完成：{DB_FILE}")
    print("=" * 50)


if __name__ == "__main__":
    main()
