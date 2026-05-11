#!/usr/bin/env python3
"""
企业智能问答助手 - 命令行工具

用法:
    python cli.py "张三的部门是什么？"
    python cli.py "年假怎么计算？"
"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.query_engine import EnterpriseQA


def main():
    if len(sys.argv) < 2:
        print("用法: python cli.py <问题>")
        print("示例: python cli.py '张三的部门是什么？'")
        sys.exit(1)
    
    question = sys.argv[1]
    
    # 获取配置
    db_path = os.environ.get("ENTERPRISE_QA_DB_PATH", "./enterprise.db")
    kb_path = os.environ.get("ENTERPRISE_QA_KB_PATH", "./knowledge")
    
    # 如果相对路径，转换为脚本所在目录
    if not os.path.isabs(db_path):
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(script_dir, db_path)
    if not os.path.isabs(kb_path):
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        kb_path = os.path.join(script_dir, kb_path)
    
    try:
        # 创建问答实例
        qa = EnterpriseQA(db_path=db_path, kb_path=kb_path)
        
        # 处理问题
        result = qa.query(question)
        
        # 输出结果
        print("\n" + "=" * 50)
        print(f"问题: {question}")
        print("=" * 50)
        print(f"\n答案:\n{result.to_markdown()}")
        
        if result.error:
            print(f"\n错误: {result.error}")
        
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("\n请先运行 init_db.sh 初始化数据库")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
