"""
SQL 安全测试

测试用例 T11: SQL 注入防护
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sql_generator import SQLGenerator


@pytest.fixture
def generator():
    return SQLGenerator()


class TestSQLSafety:
    """SQL 安全性测试"""
    
    def test_safe_sql_detection(self, generator):
        """安全 SQL 检测"""
        safe_sqls = [
            "SELECT * FROM employees WHERE name = ?",
            "SELECT department FROM employees WHERE employee_id = ?",
            "SELECT COUNT(*) FROM projects WHERE status = ?"
        ]
        
        for sql in safe_sqls:
            assert generator.is_safe_sql(sql), f"Should be safe: {sql}"
    
    def test_sql_injection_blocked(self, generator):
        """SQL 注入拦截"""
        dangerous_sqls = [
            "SELECT * FROM users; DROP TABLE users;",
            "SELECT * FROM employees WHERE id = 1 OR 1=1",
            "SELECT * FROM employees; DELETE FROM employees",
            "DROP TABLE employees",
            "DELETE FROM employees WHERE 1=1",
            "UPDATE employees SET admin = true"
        ]
        
        for sql in dangerous_sqls:
            assert not generator.is_safe_sql(sql), f"Should be blocked: {sql}"
    
    def test_comment_injection(self, generator):
        """注释注入"""
        dangerous_sqls = [
            "SELECT * FROM employees -- WHERE admin = 1",
            "SELECT * FROM employees /* comment */ WHERE id = 1"
        ]
        
        for sql in dangerous_sqls:
            assert not generator.is_safe_sql(sql), f"Should be blocked: {sql}"
    
    def test_union_injection(self, generator):
        """UNION 注入"""
        dangerous_sql = "SELECT * FROM employees UNION SELECT * FROM passwords"
        assert not generator.is_safe_sql(dangerous_sql)
    
    def test_parameter_validation(self, generator):
        """参数验证"""
        safe_params = [
            ("张三",),
            ("EMP-001",),
            ("研发部",),
            ("2026-02-%",)
        ]
        
        for params in safe_params:
            assert generator.validate_params(params), f"Should be valid: {params}"
        
        dangerous_params = [
            ("'; DROP TABLE users; --",),
            ('1 OR 1=1',),
            ("admin'--",)
        ]
        
        for params in dangerous_params:
            assert not generator.validate_params(params), f"Should be invalid: {params}"


class TestSQLGeneration:
    """SQL 生成测试"""
    
    def test_employee_department_query(self, generator):
        """员工部门查询 SQL"""
        sql, params = generator.generate("张三的部门是什么？")
        assert sql is not None
        assert "SELECT" in sql.upper()
        assert "department" in sql.lower()
    
    def test_employee_email_query(self, generator):
        """员工邮箱查询 SQL"""
        sql, params = generator.generate("张三的邮箱是什么？")
        assert sql is not None
        assert "email" in sql.lower()
    
    def test_department_count_query(self, generator):
        """部门人数查询 SQL"""
        sql, params = generator.generate("研发部有多少人？")
        assert sql is not None
        assert "COUNT" in sql.upper()
    
    def test_attendance_late_query(self, generator):
        """迟到次数查询 SQL"""
        sql, params = generator.generate("张三2月迟到几次？")
        assert sql is not None
        assert "late" in sql.lower()
    
    def test_project_query(self, generator):
        """项目查询 SQL"""
        sql, params = generator.generate("张三负责哪些项目？")
        assert sql is not None
        assert "projects" in sql.lower()


class TestParameterizedQueries:
    """参数化查询测试"""
    
    def test_no_string_concatenation(self, generator):
        """确保没有字符串拼接"""
        sql, params = generator.generate("张三的部门是什么？")
        
        # SQL 中不应该有实际的员工名
        assert "张三" not in sql or "?" in sql
        # 参数应该在 tuple 中
        assert len(params) > 0


class TestSQLGeneratorBranches:
    """SQL 生成器分支测试"""
    
    def test_department_count_query(self):
        """测试部门人数查询"""
        from src.sql_generator import SQLGenerator
        gen = SQLGenerator()
        sql, params = gen.generate("研发部有多少人？")
        assert "department" in sql.lower() or "研发" in sql
    
    def test_attendance_late_query(self):
        """测试迟到查询"""
        from src.sql_generator import SQLGenerator
        gen = SQLGenerator()
        sql, params = gen.generate("张三2月迟到几次？")
        assert "attendance" in sql.lower() or "late" in sql.lower() or "迟到" in sql
    
    def test_project_query(self):
        """测试项目查询"""
        from src.sql_generator import SQLGenerator
        gen = SQLGenerator()
        sql, params = gen.generate("有哪些在研项目？")
        assert "project" in sql.lower() or "项目" in sql


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
