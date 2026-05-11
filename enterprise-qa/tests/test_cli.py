"""CLI 模块测试"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cli import main


class TestCLI:
    """CLI 功能测试"""
    
    def test_cli_import(self):
        """测试 CLI 模块可导入"""
        from src.cli import main
        assert callable(main)
    
    def test_cli_module_exists(self):
        """测试 CLI 模块存在"""
        from src import cli
        assert hasattr(cli, 'main')


class TestCLIOutput:
    """CLI 输出测试"""
    
    def test_query_zhangsan(self, capsys):
        """测试查询张三部门"""
        sys.argv = ['cli.py', '张三的部门是什么？']
        try:
            main()
        except SystemExit:
            pass
        captured = capsys.readouterr()
        assert '张三' in captured.out or '研发部' in captured.out
    
    def test_query_wangwu_promotion(self, capsys):
        """测试查询王五晋升条件"""
        sys.argv = ['cli.py', '王五符合P5晋升P6条件吗？']
        try:
            main()
        except SystemExit:
            pass
        captured = capsys.readouterr()
        assert '王五' in captured.out or '晋升' in captured.out or 'P5' in captured.out
    
    def test_query_sql_injection(self, capsys):
        """测试 SQL 注入检测"""
        sys.argv = ['cli.py', "DROP TABLE employees; SELECT * FROM users WHERE '1'='1"]
        try:
            main()
        except SystemExit:
            pass
        captured = capsys.readouterr()
        assert '危险' in captured.out or '注入' in captured.out or '拒绝' in captured.out or '不合法' in captured.out
    
    def test_query_no_match(self, capsys):
        """测试无匹配内容"""
        sys.argv = ['cli.py', 'xyzabc123 可以报销吗？']
        try:
            main()
        except SystemExit:
            pass
        captured = capsys.readouterr()
        assert '未找到' in captured.out or '没有' in captured.out or 'xyzabc123' in captured.out
