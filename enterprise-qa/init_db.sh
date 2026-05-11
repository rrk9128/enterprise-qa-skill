#!/bin/bash
# 企业智能问答助手 - 数据库初始化脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_FILE="$SCRIPT_DIR/enterprise.db"
SCHEMA_FILE="$SCRIPT_DIR/schema.sql"
DATA_FILE="$SCRIPT_DIR/seed_data.sql"

echo "=========================================="
echo "  企业智能问答助手 - 数据库初始化"
echo "=========================================="

# 清理旧数据库
echo "✓ 清理旧数据库..."
rm -f "$DB_FILE"

# 检查 sqlite3
if ! command -v sqlite3 &> /dev/null; then
    echo "sqlite3 未安装，尝试使用 Python 初始化..."
    if command -v python3 &> /dev/null; then
        python3 "$SCRIPT_DIR/init_db.py"
        exit $?
    else
        echo "错误: sqlite3 和 python3 均不可用"
        echo "请运行: apt-get install sqlite3 或 python3"
        exit 1
    fi
fi

# 检查 schema.sql 是否存在
if [ ! -f "$SCHEMA_FILE" ]; then
    echo "错误: schema.sql 不存在: $SCHEMA_FILE"
    exit 1
fi

# 检查 seed_data.sql 是否存在（必须存在）
if [ ! -f "$DATA_FILE" ]; then
    echo "错误: seed_data.sql 不存在: $DATA_FILE"
    echo "请确保种子数据文件存在！"
    exit 1
fi

# 创建表结构
echo "✓ 创建表结构..."
sqlite3 "$DB_FILE" < "$SCHEMA_FILE"

# 导入数据
echo "✓ 导入种子数据..."
sqlite3 "$DB_FILE" < "$DATA_FILE"

# 验证
echo ""
echo "=========================================="
echo "  数据验证"
echo "=========================================="
EMPLOYEE_COUNT=$(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM employees;')
PROJECT_COUNT=$(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM projects;')
PM_COUNT=$(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM project_members;')
ATT_COUNT=$(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM attendance;')
PR_COUNT=$(sqlite3 "$DB_FILE" 'SELECT COUNT(*) FROM performance_reviews;')

echo "  员工数：$EMPLOYEE_COUNT"
echo "  项目数：$PROJECT_COUNT"
echo "  项目成员数：$PM_COUNT"
echo "  考勤记录：$ATT_COUNT"
echo "  绩效记录：$PR_COUNT"

# 验证数据量是否符合要求
if [ "$EMPLOYEE_COUNT" -ne 10 ]; then
    echo "警告: 员工数应为 10，实际 $EMPLOYEE_COUNT"
fi
if [ "$PROJECT_COUNT" -ne 5 ]; then
    echo "警告: 项目数应为 5，实际 $PROJECT_COUNT"
fi
if [ "$PM_COUNT" -ne 12 ]; then
    echo "警告: 项目成员数应为 12，实际 $PM_COUNT"
fi
if [ "$ATT_COUNT" -lt 40 ]; then
    echo "警告: 考勤记录应不少于 40，实际 $ATT_COUNT"
fi
if [ "$PR_COUNT" -lt 17 ]; then
    echo "警告: 绩效记录应不少于 17，实际 $PR_COUNT"
fi

# 快速测试
echo ""
echo "=========================================="
echo "  快速测试"
echo "=========================================="
echo "  张三的部门：$(sqlite3 "$DB_FILE" "SELECT department FROM employees WHERE employee_id='EMP-001';")"
echo "  研发部人数：$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM employees WHERE department='研发部' AND status='active';")"
echo "  张三 2 月迟到：$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM attendance WHERE employee_id='EMP-001' AND status='late' AND date LIKE '2026-02-%';")"

echo ""
echo "✓ 数据库初始化完成：$DB_FILE"
echo "=========================================="
