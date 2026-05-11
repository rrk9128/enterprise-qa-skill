"""
答案生成器

将查询结果转换为自然语言答案
"""

import re
from typing import List, Tuple, Dict, Any, Optional


class AnswerGenerator:
    """答案生成器"""
    
    # 角色映射
    ROLE_MAP = {
        "lead": "lead",
        "core": "core",
        "contributor": "contributor"
    }
    
    # 状态映射
    STATUS_MAP = {
        "active": "进行中",
        "planning": "规划中",
        "on_hold": "暂停",
        "completed": "已完成"
    }
    
    # 考勤状态映射
    ATTENDANCE_STATUS_MAP = {
        "on_time": "正常",
        "late": "迟到",
        "absent": "旷工",
        "on_leave": "请假"
    }
    
    def generate_from_db(
        self, 
        question: str, 
        sql: str, 
        results: List[tuple], 
        columns: List[str]
    ) -> Tuple[str, List[str]]:
        """
        从数据库结果生成答案
        
        Args:
            question: 用户问题
            sql: 执行的 SQL
            results: 查询结果
            columns: 列名
            
        Returns:
            (answer, sources)
        """
        if not results:
            # 检查是否是员工ID查询，提供友好提示
            import re
            emp_id_match = re.search(r'EMP-\d+', question, re.IGNORECASE)
            if emp_id_match:
                emp_id = emp_id_match.group(0).upper()
                return f"不存在员工 {emp_id}，或没找到该员工，请确认员工编号是否正确。", ["employees 表"]
            
            # 检查是否是员工姓名查询
            name_match = re.search(r'([\u4e00-\u9fa5]{2,4})', question)
            if name_match:
                name = name_match.group(1)
                return f"未找到员工 {name}，请确认姓名是否正确。", ["employees 表"]
            
            return "抱歉，数据库中没有找到相关信息。", []
        
        # 分析问题类型
        if self._is_employee_query(question):
            return self._format_employee_answer(question, results, columns)
        elif self._is_project_query(question):
            return self._format_project_answer(question, results, columns)
        elif self._is_attendance_query(question):
            return self._format_attendance_answer(question, results, columns)
        elif self._is_performance_query(question):
            return self._format_performance_answer(question, results, columns)
        elif self._is_department_query(question):
            return self._format_department_answer(question, results, columns)
        else:
            return self._format_generic_answer(question, results, columns)
    
    def _is_employee_query(self, question: str) -> bool:
        keywords = ["员工", "邮箱", "电话", "上级", "领导", "部门", "职级", "入职"]
        return any(kw in question for kw in keywords)
    
    def _is_project_query(self, question: str) -> bool:
        keywords = ["项目", "负责", "参与", "核心", "贡献", "在研", "进行中", "活跃"]
        return any(kw in question for kw in keywords)
    
    def _is_attendance_query(self, question: str) -> bool:
        keywords = ["迟到", "考勤", "打卡", "缺勤"]
        return any(kw in question for kw in keywords)
    
    def _is_performance_query(self, question: str) -> bool:
        keywords = ["绩效", "KPI", "考核", "评分", "等级"]
        return any(kw in question for kw in keywords)
    
    def _is_department_query(self, question: str) -> bool:
        keywords = ["部", "部门", "成员", "多少人"]
        return any(kw in question for kw in keywords)
    
    def _format_employee_answer(
        self, 
        question: str, 
        results: List[tuple], 
        columns: List[str]
    ) -> Tuple[str, List[str]]:
        """格式化员工信息答案"""
        row = results[0]
        row_dict = dict(zip(columns, row))
        
        # 根据问题生成答案
        if "邮箱" in question:
            name = row_dict.get('name', '该员工')
            email = row_dict.get('email', '未知')
            answer = f"{name}的邮箱是 {email}。"
            source = "employees 表 (email)"
        elif "部门" in question:
            name = row_dict.get('name', '该员工')
            dept = row_dict.get('department', '未知')
            answer = f"{name}的部门是 {dept}。"
            source = "employees 表 (department)"
        elif "职级" in question or "级别" in question:
            name = row_dict.get('name', '该员工')
            level = row_dict.get('level', '未知')
            answer = f"{name}的职级是 {level}。"
            source = "employees 表 (level)"
        elif "上级" in question or "领导" in question:
            # T02 特殊格式
            employee_name = row_dict.get('employee_name', row_dict.get('name', ''))
            manager_name = row_dict.get('manager_name', row_dict.get('name', '未知'))
            manager_id = row_dict.get('manager_id', '')
            
            if manager_id:
                answer = f"{employee_name}的上级是 {manager_name}。"
                source = f"employees 表 manager_id 字段，employee_id={manager_id}"
            else:
                answer = f"{employee_name}的上级是 {manager_name}。"
                source = "employees 表 manager_id 字段"
        elif "入职" in question:
            name = row_dict.get('name', '该员工')
            hire_date = row_dict.get('hire_date', '未知')
            answer = f"{name}的入职日期是 {hire_date}。"
            source = "employees 表 (hire_date)"
        else:
            # 通用员工信息
            name = row_dict.get('name', '未知')
            dept = row_dict.get('department', '未知')
            level = row_dict.get('level', '未知')
            answer = f"{name}的信息：\n- 部门：{dept}\n- 职级：{level}\n- 邮箱：{row_dict.get('email', '未知')}"
            source = "employees 表"
        
        return answer, [source]
    
    def _format_project_answer(
        self, 
        question: str, 
        results: List[tuple], 
        columns: List[str]
    ) -> Tuple[str, List[str]]:
        """格式化项目答案 - T05 特殊格式"""
        # 检查是否是简单的在研项目列表查询
        if 'status' in columns and 'project_id' not in columns and 'role' not in columns:
            # 简单的在研项目列表
            projects = []
            for row in results:
                row_dict = dict(zip(columns, row))
                name = row_dict.get('name', '未知')
                status = row_dict.get('status', '')
                projects.append(f"{name} ({status})")
            
            if projects:
                answer = "在研项目：\n" + "\n".join(projects)
                return answer, ["projects 表 status 字段"]
            else:
                return "没有找到相关项目信息。", ["projects 表"]
        
        # 详细项目查询（带 project_id 和 role）
        projects = []
        
        for row in results:
            row_dict = dict(zip(columns, row))
            project_id = row_dict.get('project_id', '')
            name = row_dict.get('name', '未知')
            role = row_dict.get('role', '')
            
            if project_id and name and role:
                projects.append(f"{project_id} {name} {role}")
        
        if not projects:
            return "没有找到相关项目信息。", ["projects + project_members 表"]
        
        # T05 格式：每个项目一行，包含编号、名称、角色
        answer = "\n".join(projects)
        
        return answer, ["projects + project_members 表"]
    
    def _format_attendance_answer(
        self, 
        question: str, 
        results: List[tuple], 
        columns: List[str]
    ) -> Tuple[str, List[str]]:
        """格式化考勤答案"""
        row = results[0]
        row_dict = dict(zip(columns, row))
        
        # 提取月份
        month_match = re.search(r"(\d+)\s*月", question)
        month = month_match.group(1) + "月" if month_match else "该月"
        
        # 迟到次数
        if 'late_count' in row_dict:
            count = row_dict['late_count']
            answer = f"{month}迟到 {count} 次。"
            source = "attendance 表"
        else:
            # 详细考勤记录
            records = []
            for row in results[:5]:  # 只显示最近5条
                record = dict(zip(columns, row))
                date = record.get('date', '')
                status = self.ATTENDANCE_STATUS_MAP.get(record.get('status', ''), '')
                records.append(f"- {date}：{status}")
            
            answer = f"考勤记录：\n" + "\n".join(records)
            source = "attendance 表"
        
        return answer, [source]
    
    def _format_performance_answer(
        self, 
        question: str, 
        results: List[tuple], 
        columns: List[str]
    ) -> Tuple[str, List[str]]:
        """格式化绩效答案"""
        if 'avg_kpi' in dict(zip(columns, results[0])):
            # 平均 KPI
            row = results[0]
            row_dict = dict(zip(columns, row))
            avg_kpi = row_dict.get('avg_kpi')
            if avg_kpi:
                answer = f"平均 KPI 为 {avg_kpi:.1f}。"
            else:
                answer = "没有找到绩效数据。"
            source = "performance_reviews 表"
        else:
            # 详细绩效记录
            records = []
            for row in results:
                record = dict(zip(columns, row))
                year = record.get('year', '')
                quarter = record.get('quarter', '')
                kpi = record.get('kpi_score', '')
                grade = record.get('grade', '')
                records.append(f"- {year} Q{quarter}：KPI {kpi}，评级 {grade}")
            
            if records:
                answer = "\n".join(records)
            else:
                answer = "没有找到绩效数据。"
            source = "performance_reviews 表"
        
        return answer, [source]
    
    def _format_department_answer(
        self, 
        question: str, 
        results: List[tuple], 
        columns: List[str]
    ) -> Tuple[str, List[str]]:
        """格式化部门答案"""
        row = results[0]
        row_dict = dict(zip(columns, row))
        
        dept_match = re.search(r"([^\s]+)部", question)
        dept_name = dept_match.group(1) + "部" if dept_match else "该部门"
        
        if 'count' in row_dict:
            count = row_dict['count']
            answer = f"{dept_name}有 {count} 人。"
            source = "employees 表 (department)"
        else:
            names = [dict(zip(columns, r)).get('name', '') for r in results]
            answer = f"{dept_name}成员：{', '.join(names)}"
            source = "employees 表"
        
        return answer, [source]
    
    def _format_generic_answer(
        self, 
        question: str,
        results: List[tuple], 
        columns: List[str]
    ) -> Tuple[str, List[str]]:
        """格式化通用答案"""
        if not results:
            # 检查是否是员工ID查询
            emp_id_match = re.search(r'EMP-\d+', question, re.IGNORECASE)
            if emp_id_match:
                emp_id = emp_id_match.group(0).upper()
                return f"未找到员工 {emp_id}，请确认员工编号是否正确。", ["employees 表"]
            
            # 检查是否是员工姓名查询
            employee_keywords = ["谁", "信息", "邮箱", "部门", "职级", "上级"]
            if any(kw in question for kw in employee_keywords):
                # 尝试提取姓名
                name_match = re.search(r'([\u4e00-\u9fa5]{2,4})', question)
                if name_match:
                    name = name_match.group(1)
                    return f"未找到员工 {name}，请确认姓名是否正确。", ["employees 表"]
            
            return "没有找到相关信息。", []
        
        rows = []
        for row in results[:5]:
            row_dict = dict(zip(columns, row))
            rows.append(str(row_dict))
        
        answer = "\n".join(rows)
        source = "数据库查询"
        
        return answer, [source]
    
    def generate_from_kb(
        self, 
        question: str, 
        documents: List
    ) -> Tuple[str, List[str]]:
        """
        从知识库文档生成答案
        
        Args:
            question: 用户问题
            documents: 检索到的文档列表
            
        Returns:
            (answer, sources)
        """
        if not documents:
            return "抱歉，我在知识库中没有找到相关信息。", []
        
        # 整理文档内容
        answers = []
        sources = []
        
        for doc in documents:
            if hasattr(doc, 'content'):
                content = doc.content
                source = doc.source
            else:
                content = doc.get('content', '')
                source = doc.get('source', '')
            
            # 提取相关段落
            if len(content) > 500:
                # 如果内容太长，截取关键部分
                answers.append(content[:500] + "...")
            else:
                answers.append(content)
            
            sources.append(source)
        
        # 构建答案
        answer = "\n\n".join(answers)
        
        return answer, sources
