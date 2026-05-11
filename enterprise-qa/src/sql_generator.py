"""
SQL 生成器

根据自然语言问题生成安全的参数化 SQL 查询
"""

import re
from typing import Optional, Tuple, List, Dict, Any


class SQLGenerator:
    """SQL 查询生成器"""
    
    # 员工姓名白名单
    EMPLOYEE_WHITELIST = {
        "张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十",
        "CEO", "离职员工", "EMP-001", "EMP-002", "EMP-003", "EMP-004",
        "EMP-005", "EMP-006", "EMP-007", "EMP-008", "EMP-009", "EMP-000"
    }
    
    # 危险 SQL 模式（用于 SQL 文本检查）
    DANGEROUS_SQL_PATTERNS = [
        r";",  # 多语句分隔
        r"--",  # 注释
        r"/\*.*\*/",  # 块注释
        r"DROP\s+",  # 删除表
        r"DELETE\s+",  # 删除数据
        r"TRUNCATE\s+",  # 清空表
        r"ALTER\s+",  # 修改表结构
        r"INSERT\s+",  # 插入数据
        r"UPDATE\s+.+SET\s+",  # 更新数据
        r"GRANT\s+",  # 授权
        r"REVOKE\s+",  # 撤销权限
        r"EXEC\s*\(",  # 执行存储过程
        r"XP_",  # 扩展存储过程
        r"UNION\s+SELECT\s+",  # UNION SELECT 注入
        r"\bOR\s+1\s*=\s*1",  # OR 1=1
        r"WHERE\s+['\"]?\d+\s*=\s*['\"]?\d+",  # WHERE 1=1 模式
    ]
    
    # 危险参数模式（用于参数值检查）
    DANGEROUS_PARAM_PATTERNS = [
        r"'\s*;\s*",  # 语句终结
        r"--",  # 注释
        r"/\*",  # 块注释开始
        r"OR\s+1\s*=\s*1",  # OR 1=1
        r"UNION",  # UNION
        r"DROP",  # DROP
        r"DELETE",  # DELETE
        r"UPDATE",  # UPDATE
        r"INSERT",  # INSERT
        r"<script",  # XSS
    ]
    
    # 表结构定义
    TABLE_SCHEMAS = {
        "employees": {
            "columns": ["employee_id", "name", "department", "level", "hire_date", "manager_id", "email", "status"],
            "primary_key": "employee_id"
        },
        "projects": {
            "columns": ["project_id", "name", "lead_id", "status", "start_date", "end_date", "budget"],
            "primary_key": "project_id"
        },
        "project_members": {
            "columns": ["project_id", "employee_id", "role", "join_date"],
            "foreign_keys": {"project_id": "projects", "employee_id": "employees"}
        },
        "attendance": {
            "columns": ["id", "employee_id", "date", "status"],
            "foreign_keys": {"employee_id": "employees"}
        },
        "performance_reviews": {
            "columns": ["id", "employee_id", "year", "quarter", "kpi_score", "grade"],
            "foreign_keys": {"employee_id": "employees"}
        }
    }
    
    def __init__(self):
        self.dangerous_sql_patterns = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_SQL_PATTERNS]
        self.dangerous_param_patterns = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PARAM_PATTERNS]
    
    def is_safe_sql(self, sql: str) -> bool:
        """
        检查 SQL 是否安全
        
        Args:
            sql: SQL 语句
            
        Returns:
            bool: 是否安全
        """
        if not sql:
            return False
        
        sql_upper = sql.upper()
        
        # 检查危险 SQL 模式
        for pattern in self.dangerous_sql_patterns:
            if pattern.search(sql):
                return False
        
        return True
    
    def validate_params(self, params: tuple) -> bool:
        """
        验证参数是否安全
        
        Args:
            params: 参数元组
            
        Returns:
            bool: 是否安全
        """
        if not params:
            return True
        
        for param in params:
            param_str = str(param)
            for pattern in self.dangerous_param_patterns:
                if pattern.search(param_str):
                    return False
        
        return True
    
    def extract_employee_name(self, question: str) -> Optional[str]:
        """
        从问题中提取员工姓名（白名单机制）
        
        Args:
            question: 用户问题
            
        Returns:
            str: 员工姓名，如果未找到返回 None
        """
        # 优先匹配白名单中的姓名
        for name in sorted(self.EMPLOYEE_WHITELIST, key=len, reverse=True):
            if name in question:
                return name
        return None
    
    def extract_employee_id(self, question: str) -> Optional[str]:
        """
        从问题中提取员工ID（EMP-xxx 格式）
        
        Args:
            question: 用户问题
            
        Returns:
            str: 员工ID，如果未找到返回 None
        """
        emp_match = re.search(r'EMP-\d+', question, re.IGNORECASE)
        if emp_match:
            emp_id = emp_match.group(0).upper()
            # 验证格式：EMP- 后跟数字
            if re.match(r'EMP-\d+$', emp_id):
                return emp_id
        return None
    
    def extract_year(self, question: str) -> Optional[int]:
        """提取年份"""
        year_match = re.search(r"(\d{4})\s*年", question)
        if year_match:
            return int(year_match.group(1))
        return None
    
    def extract_month(self, question: str) -> Optional[int]:
        """提取月份"""
        month_match = re.search(r"(\d{1,2})\s*月", question)
        if month_match:
            month = int(month_match.group(1))
            if 1 <= month <= 12:
                return month
        return None
    
    def extract_level(self, question: str) -> Optional[str]:
        """提取职级"""
        level_match = re.search(r"P(\d+)", question)
        if level_match:
            return f"P{level_match.group(1)}"
        return None
    
    def generate(self, question: str) -> Tuple[Optional[str], tuple]:
        """
        根据问题生成 SQL 查询
        
        Args:
            question: 自然语言问题
            
        Returns:
            (sql, params) 元组
        """
        question = question.strip()
        
        # 1. 先检查员工姓名白名单
        employee_name = self.extract_employee_name(question)
        
        # 2. 检查是否有 EMP-xxx 格式的员工ID
        employee_id = self.extract_employee_id(question)
        
        # 3. 根据问题类型生成 SQL
        if "部门" in question and employee_name:
            sql = "SELECT department FROM employees WHERE name = ? OR employee_id = ?"
            params = (employee_name, employee_name)
        elif "邮箱" in question and employee_name:
            sql = "SELECT email FROM employees WHERE name = ? OR employee_id = ?"
            params = (employee_name, employee_name)
        elif "职级" in question or "级别" in question:
            sql = "SELECT level FROM employees WHERE name = ? OR employee_id = ?"
            params = (employee_name, employee_name) if employee_name else ("", "")
        elif "上级" in question or "领导" in question:
            sql = """SELECT e.name AS employee_name, m.name AS manager_name 
                      FROM employees e 
                      LEFT JOIN employees m ON e.manager_id = m.employee_id 
                      WHERE e.name = ? OR e.employee_id = ?"""
            params = (employee_name, employee_name) if employee_name else ("", "")
        elif "邮箱" in question and employee_name:
            sql = "SELECT email FROM employees WHERE name = ? OR employee_id = ?"
            params = (employee_name, employee_name)
        elif ("项目" in question) and employee_name:
            sql = """SELECT p.project_id, p.name, pm.role 
                      FROM projects p
                      JOIN project_members pm ON p.project_id = pm.project_id
                      JOIN employees e ON pm.employee_id = e.employee_id
                      WHERE e.name = ? OR e.employee_id = ?
                      ORDER BY p.start_date DESC"""
            params = (employee_name, employee_name)
        elif "迟到" in question and employee_name:
            month = self.extract_month(question)
            if month:
                # 使用精确月份匹配 '____-MM-%'
                date_pattern = f"{'____-%02d-%%' % month}"
                sql = """SELECT COUNT(*) as late_count 
                          FROM attendance a
                          JOIN employees e ON a.employee_id = e.employee_id
                          WHERE (e.name = ? OR e.employee_id = ?)
                          AND a.status = 'late'
                          AND a.date LIKE ?"""
                params = (employee_name, employee_name, date_pattern)
            else:
                sql = """SELECT COUNT(*) as late_count 
                          FROM attendance a
                          JOIN employees e ON a.employee_id = e.employee_id
                          WHERE (e.name = ? OR e.employee_id = ?)
                          AND a.status = 'late'"""
                params = (employee_name, employee_name)
        elif "绩效" in question or "KPI" in question or "考核" in question:
            year = self.extract_year(question)
            if year:
                sql = """SELECT year, quarter, kpi_score, grade 
                          FROM performance_reviews pr
                          JOIN employees e ON pr.employee_id = e.employee_id
                          WHERE e.name = ? AND pr.year = ?
                          ORDER BY year DESC, quarter DESC"""
                params = (employee_name, year) if employee_name else (str(year),)
            else:
                sql = """SELECT year, quarter, kpi_score, grade 
                          FROM performance_reviews pr
                          JOIN employees e ON pr.employee_id = e.employee_id
                          WHERE e.name = ? OR e.employee_id = ?
                          ORDER BY year DESC, quarter DESC"""
                params = (employee_name, employee_name) if employee_name else ("", "")
        elif "平均" in question and ("KPI" in question or "绩效" in question):
            sql = """SELECT AVG(kpi_score) as avg_kpi
                      FROM performance_reviews pr
                      JOIN employees e ON pr.employee_id = e.employee_id
                      WHERE e.name = ? OR e.employee_id = ?"""
            params = (employee_name, employee_name) if employee_name else ("", "")
        elif "部" in question and "多少人" in question:
            dept_match = re.search(r"([^\s]+)部", question)
            if dept_match:
                dept = dept_match.group(1) + "部"
                sql = "SELECT COUNT(*) as count FROM employees WHERE department = ? AND status = 'active'"
                params = (dept,)
            else:
                return None, ()
        elif "在研项目" in question or "进行中" in question:
            sql = "SELECT name, lead_id, status FROM projects WHERE status = 'active'"
            params = ()
        elif employee_name and ("是谁" in question or "信息" in question):
            sql = "SELECT * FROM employees WHERE name = ? OR employee_id = ?"
            params = (employee_name, employee_name)
        elif employee_id and ("是谁" in question or "信息" in question or "查" in question):
            # 直接用员工ID查询（如 EMP-999）
            sql = "SELECT * FROM employees WHERE employee_id = ?"
            params = (employee_id,)
        elif employee_name:
            # 通用员工查询
            sql = "SELECT * FROM employees WHERE name = ? OR employee_id = ?"
            params = (employee_name, employee_name)
        elif employee_id:
            # 仅有员工ID的查询
            sql = "SELECT * FROM employees WHERE employee_id = ?"
            params = (employee_id,)
        else:
            return None, ()
        
        return sql, params
    
    def generate_manager_query(self, employee_name: str) -> Tuple[str, tuple]:
        """生成上级查询 SQL"""
        sql = """SELECT e.name AS employee_name, m.name AS manager_name, e.manager_id
                  FROM employees e 
                  LEFT JOIN employees m ON e.manager_id = m.employee_id 
                  WHERE e.name = ? OR e.employee_id = ?"""
        return sql, (employee_name, employee_name)
    
    def generate_project_query(self, employee_name: str) -> Tuple[str, tuple]:
        """生成项目查询 SQL"""
        sql = """SELECT p.project_id, p.name, pm.role 
                  FROM projects p
                  JOIN project_members pm ON p.project_id = pm.project_id
                  JOIN employees e ON pm.employee_id = e.employee_id
                  WHERE e.name = ? OR e.employee_id = ?
                  ORDER BY p.start_date DESC"""
        return sql, (employee_name, employee_name)
    
    def generate_promotion_query(self, employee_name: str) -> Tuple[str, tuple]:
        """生成晋升条件查询 SQL"""
        sql = """SELECT e.name, e.level, e.hire_date, e.employee_id
                  FROM employees e
                  WHERE e.name = ? OR e.employee_id = ?"""
        return sql, (employee_name, employee_name)
    
    def generate_performance_query(self, employee_name: str, year: int = 2025) -> Tuple[str, tuple]:
        """生成绩效查询 SQL"""
        sql = """SELECT year, quarter, kpi_score, grade
                  FROM performance_reviews pr
                  JOIN employees e ON pr.employee_id = e.employee_id
                  WHERE e.name = ? AND pr.year = ?
                  ORDER BY year DESC, quarter DESC"""
        return sql, (employee_name, year)
    
    def generate_project_count_query(self, employee_name: str) -> Tuple[str, tuple]:
        """生成项目数量查询 SQL"""
        sql = """SELECT COUNT(*) as project_count, GROUP_CONCAT(p.name, ', ') as project_names
                  FROM project_members pm
                  JOIN projects p ON pm.project_id = p.project_id
                  JOIN employees e ON pm.employee_id = e.employee_id
                  WHERE e.name = ? OR e.employee_id = ?"""
        return sql, (employee_name, employee_name)
