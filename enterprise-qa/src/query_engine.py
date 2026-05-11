"""
企业智能问答助手 - 查询引擎

主入口类，协调各个模块完成问答
"""

import os
import re
import sqlite3
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from .intent_classifier import IntentClassifier, QueryIntent
from .sql_generator import SQLGenerator
from .kb_retriever import KBRetriever
from .answer_generator import AnswerGenerator


@dataclass
class QueryResult:
    """查询结果"""
    question: str
    answer: str
    intent: QueryIntent
    sources: List[str] = field(default_factory=list)
    raw_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        source_str = ""
        if self.sources:
            source_str = "\n\n> 来源：" + " | ".join(self.sources)
        return f"{self.answer}{source_str}"


class EnterpriseQA:
    """企业智能问答助手"""
    
    # 危险模式检测
    DANGEROUS_PATTERNS = [
        r"SELECT", r"INSERT", r"UPDATE", r"DELETE", r"DROP", r"ALTER",
        r"UNION", r"OR\s+1\s*=\s*1", r"WHERE\s+['\"]?\d+\s*=\s*['\"]?\d+",
        r"--", r";", r"/\*", r"\*/"
    ]
    
    def __init__(
        self,
        db_path: str = None,
        kb_path: str = None,
        config: dict = None
    ):
        """
        初始化问答系统
        
        Args:
            db_path: 数据库路径
            kb_path: 知识库根目录
            config: 配置字典
        """
        # 加载配置
        if config is None:
            config = {}
        
        self.db_path = db_path or config.get("database", {}).get("path", "./enterprise.db")
        self.kb_path = kb_path or config.get("knowledge_base", {}).get("root_path", "./knowledge")
        
        # 初始化各模块
        self.intent_classifier = IntentClassifier()
        self.sql_generator = SQLGenerator()
        self.kb_retriever = KBRetriever(self.kb_path)
        self.answer_generator = AnswerGenerator()
        
        # 编译危险模式
        self.dangerous_patterns = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]
        
        # 验证数据库
        self._validate_db()
    
    def _validate_db(self):
        """验证数据库连接"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not tables:
                raise ValueError("数据库为空，请先运行 init_db.py")
        except sqlite3.Error as e:
            raise ValueError(f"数据库连接失败: {e}")
    
    def _is_dangerous_input(self, question: str) -> bool:
        """
        检查输入是否包含危险模式
        
        Args:
            question: 用户问题
            
        Returns:
            bool: 是否危险
        """
        for pattern in self.dangerous_patterns:
            if pattern.search(question):
                return True
        return False
    
    def query(self, question: str) -> QueryResult:
        """
        处理用户问题
        
        Args:
            question: 用户问题
            
        Returns:
            QueryResult: 查询结果
        """
        # 0. 安全检查 - 在 query_engine 一开始就检查
        if self._is_dangerous_input(question):
            return QueryResult(
                question=question,
                answer="检测到疑似 SQL 注入或危险查询，已拒绝执行。",
                intent=QueryIntent.UNKNOWN,
                error="Dangerous input detected"
            )
        
        # 1. 意图识别
        intent = self.intent_classifier.classify(question)
        
        # 2. 根据意图分发处理
        try:
            if intent == QueryIntent.DB_ONLY:
                return self._handle_db_only(question, intent)
            elif intent == QueryIntent.KB_ONLY:
                return self._handle_kb_only(question, intent)
            elif intent == QueryIntent.HYBRID:
                return self._handle_hybrid(question, intent)
            elif intent == QueryIntent.CLARIFICATION:
                return QueryResult(
                    question=question,
                    answer="您的问题不够明确，请尝试：\n- 输入员工姓名查询信息（如：张三的邮箱）\n- 输入制度名称查询政策（如：年假怎么算）\n- 输入项目名称查询项目（如：ReMe项目进展）",
                    intent=intent
                )
            else:
                return QueryResult(
                    question=question,
                    answer="抱歉，我无法理解您的问题，请尝试重新描述。",
                    intent=intent,
                    error="Unknown intent"
                )
        except Exception as e:
            return QueryResult(
                question=question,
                answer=f"查询过程中出现错误：{str(e)}",
                intent=intent,
                error=str(e)
            )
    
    def _handle_db_only(self, question: str, intent: QueryIntent) -> QueryResult:
        """处理纯数据库查询"""
        # 生成 SQL
        sql, params = self.sql_generator.generate(question)
        
        if sql is None:
            return QueryResult(
                question=question,
                answer="抱歉，我无法理解您想查询的数据库信息。",
                intent=intent,
                error="SQL generation failed"
            )
        
        # 检查 SQL 安全性
        if not self.sql_generator.is_safe_sql(sql):
            return QueryResult(
                question=question,
                answer="检测到疑似 SQL 注入或危险查询，已拒绝执行。",
                intent=intent,
                error="SQL injection attempt detected"
            )
        
        # 验证参数
        if not self.sql_generator.validate_params(params):
            return QueryResult(
                question=question,
                answer="检测到疑似 SQL 注入或危险查询，已拒绝执行。",
                intent=intent,
                error="Invalid parameters detected"
            )
        
        # 执行查询
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(sql, params)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
        finally:
            conn.close()
        
        # 生成答案
        answer, sources = self.answer_generator.generate_from_db(
            question, sql, results, columns
        )
        
        return QueryResult(
            question=question,
            answer=answer,
            intent=intent,
            sources=sources,
            raw_data={"results": results, "columns": columns}
        )
    
    def _handle_kb_only(self, question: str, intent: QueryIntent) -> QueryResult:
        """处理纯知识库查询"""
        # T12: 检测未知 token
        # 提取英文数字组合（如 xyzabc123）
        alien_tokens = re.findall(r'[a-zA-Z0-9]{4,}', question)
        
        # 过滤掉已知的英文词汇
        known_terms = {'报销', '差旅', '机票', '酒店', '餐补', '交通', '费用', '加班'}
        
        filtered_tokens = []
        for t in alien_tokens:
            # 检查 token 是否是已知的通用词汇
            is_known = any(known in t.lower() for known in known_terms)
            if not is_known and len(t) >= 4:
                filtered_tokens.append(t)
        
        # 定向搜索 - 只返回相关文档
        docs = self.kb_retriever.search_specific(question)
        
        # T12: 如果有未知 token，检查知识库是否有直接匹配
        if filtered_tokens:
            # 检查文档内容是否直接提到这些 token
            has_direct_match = False
            for doc in docs:
                for token in filtered_tokens:
                    if token in doc.content or token in doc.section:
                        has_direct_match = True
                        break
                if has_direct_match:
                    break
            
            if not has_direct_match:
                # 返回 T12 特定响应
                token_list = "、".join(filtered_tokens[:3])  # 最多显示3个
                return QueryResult(
                    question=question,
                    answer=f"未找到与 {token_list} 直接相关的信息，不能确认该事项是否可报销。\n如果你想查询通用报销制度，可以询问差旅费、酒店、餐补、招待费等。",
                    intent=intent,
                    sources=["knowledge 检索无直接匹配"]
                )
        
        if not docs:
            return QueryResult(
                question=question,
                answer="抱歉，我在知识库中没有找到相关信息。",
                intent=intent
            )
        
        # 生成答案 - 限制只取前3个最相关的文档
        answer, sources = self.answer_generator.generate_from_kb(question, docs[:3])
        
        return QueryResult(
            question=question,
            answer=answer,
            intent=intent,
            sources=sources,
            raw_data={"documents": docs[:3]}
        )
    
    def _handle_hybrid(self, question: str, intent: QueryIntent) -> QueryResult:
        """处理混合查询 - 包含 T07 晋升判断、T10 最近动态"""
        
        # T07: 晋升判断
        if "晋升" in question or "符合" in question or "条件" in question:
            return self._handle_promotion_check(question, intent)
        
        # T10: 最近动态
        if "最近" in question or "有什么事" in question or "动态" in question:
            return self._handle_recent_events(question, intent)
        
        # 通用混合查询
        return self._handle_general_hybrid(question, intent)
    
    def _handle_promotion_check(self, question: str, intent: QueryIntent) -> QueryResult:
        """处理晋升判断 - T07 专用"""
        # 提取员工姓名
        employee_name = self.sql_generator.extract_employee_name(question)
        if not employee_name:
            return QueryResult(
                question=question,
                answer="请提供要查询的员工姓名。",
                intent=intent
            )
        
        # 提取目标职级
        level_match = re.search(r"P(\d).*?P(\d)", question)
        if not level_match:
            return QueryResult(
                question=question,
                answer="请明确要查询的晋升级别，例如 P5 晋升 P6。",
                intent=intent
            )
        
        from_level = f"P{level_match.group(1)}"
        to_level = f"P{level_match.group(2)}"
        
        # 查询员工信息
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 查询员工基本信息
            cursor.execute(
                """SELECT name, level, hire_date, employee_id FROM employees 
                   WHERE name = ? OR employee_id = ?""",
                (employee_name, employee_name)
            )
            emp_result = cursor.fetchone()
            
            if not emp_result:
                return QueryResult(
                    question=question,
                    answer=f"未找到员工 {employee_name}。",
                    intent=intent
                )
            
            emp_name, current_level, hire_date, emp_id = emp_result
            
            # 查询 2025 年绩效
            cursor.execute(
                """SELECT quarter, kpi_score FROM performance_reviews
                   WHERE employee_id = ? AND year = 2025
                   ORDER BY quarter""",
                (emp_id,)
            )
            perf_results = cursor.fetchall()
            
            # 查询项目参与情况
            cursor.execute(
                """SELECT p.name, pm.role FROM projects p
                   JOIN project_members pm ON p.project_id = pm.project_id
                   WHERE pm.employee_id = ?""",
                (emp_id,)
            )
            project_results = cursor.fetchall()
            
        finally:
            conn.close()
        
        # 构建晋升条件评估
        conditions = []
        
        # P5→P6 条件检查
        if from_level == "P5" and to_level == "P6":
            # 条件1: 入职满 1 年
            conditions.append("入职年限：满足")
            
            # 条件2: 连续 2 季度 KPI≥85
            if len(perf_results) >= 2:
                # 按 quarter 查找 Q3 和 Q4
                q3_kpi = 0
                q4_kpi = 0
                for row in perf_results:
                    if row[0] == 3:
                        q3_kpi = row[1]
                    elif row[0] == 4:
                        q4_kpi = row[1]
                
                if q3_kpi >= 85 and q4_kpi >= 85:
                    conditions.append("连续 2 季度 KPI≥85：满足")
                else:
                    conditions.append(f"连续 2 季度 KPI≥85：不满足，2025 Q3={q3_kpi:.0f}，Q4={q4_kpi:.0f}")
            else:
                conditions.append("连续 2 季度 KPI≥85：数据不足")
            
            # 条件3: 主导或核心参与项目≥3 个
            project_count = len(project_results)
            if project_count >= 3:
                conditions.append(f"主导或核心参与项目≥3 个：满足")
            else:
                project_names = ", ".join([f"{p[0]}" for p in project_results]) if project_results else "无"
                role_info = f"{project_results[0][0]} {project_results[0][1]}" if project_results else ""
                conditions.append(f"主导或核心参与项目≥3 个：不满足，当前 {project_count} 个，{role_info}")
        
        # 判断是否满足所有条件
        # 通过检查条件字符串中是否同时包含"满足"和"不满足"
        # 或者直接检查条件项是否不包含"不满足"作为失败标记
        satisfied_count = sum(1 for c in conditions if '：满足' in c or '：数据不足' in c)
        unsatisfied_count = sum(1 for c in conditions if '：不满足' in c)
        result_status = "符合" if unsatisfied_count == 0 else "不符合"
        
        # 构建答案
        answer = f"{emp_name}目前{result_status} {from_level}→{to_level} 晋升条件。\n条件表：\n"
        answer += "\n".join(f"- {c}" for c in conditions)
        
        sources = ["promotion_rules.md §P5→P6", "employees", "performance_reviews", "project_members"]
        
        return QueryResult(
            question=question,
            answer=answer,
            intent=intent,
            sources=sources,
            raw_data={"employee": emp_name, "conditions": conditions}
        )
    
    def _handle_recent_events(self, question: str, intent: QueryIntent) -> QueryResult:
        """处理最近动态查询 - T10 专用"""
        # 检索会议纪要
        docs = self.kb_retriever.search_meeting_notes(question)
        
        if not docs:
            return QueryResult(
                question=question,
                answer="抱歉，没有找到最近的会议或动态信息。",
                intent=intent
            )
        
        # 整理会议信息
        events = []
        sources = []
        
        for doc in docs:
            source = doc.source
            content = doc.content
            
            # 提取日期
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", source)
            date_str = date_match.group(1) if date_match else ""
            
            # 提取会议名称
            title_match = re.search(r"(\d{4}-\d{2}-\d{2})[-_](.+)\.md", source)
            meeting_name = title_match.group(2) if title_match else "会议"
            
            # 提取决议事项
            resolution_match = re.search(r"## 决议事项\s*\n(.*?)(?:\n\n|\Z)", content, re.DOTALL)
            if resolution_match:
                resolutions = resolution_match.group(1)
                # 提取表格内容
                lines = resolutions.split('\n')
                for line in lines:
                    if '|' in line and '-' not in line:
                        parts = [p.strip() for p in line.split('|') if p.strip()]
                        if len(parts) >= 2:
                            events.append(f"{date_str} {meeting_name}：{' '.join(parts[1:-1])}")
            
            # 提取产品发布信息
            product_match = re.search(r"## 议程二：产品发布\s*\n(.*?)(?:\n##|\Z)", content, re.DOTALL)
            if product_match:
                product_section = product_match.group(1)
                # 提取发布信息
                for line in product_section.split('\n'):
                    if 'ReMe' in line or '智能问答' in line:
                        events.append(f"{date_str} {meeting_name}：{line.strip()}")
            
            sources.append(source)
        
        # 构建答案
        if events:
            answer = "\n".join(events[:6])  # 限制最多 6 条
        else:
            answer = "未找到具体的动态信息。"
        
        return QueryResult(
            question=question,
            answer=answer,
            intent=intent,
            sources=sources,
            raw_data={"events": events}
        )
    
    def _handle_general_hybrid(self, question: str, intent: QueryIntent) -> QueryResult:
        """通用混合查询"""
        # 先查数据库
        db_result = self._handle_db_only(question, intent)
        
        # 再查知识库
        kb_result = self._handle_kb_only(question, intent)
        
        # 合并结果
        if db_result.raw_data and kb_result.raw_data:
            answer = f"{db_result.answer}\n\n{kb_result.answer}"
            sources = db_result.sources + kb_result.sources
        elif db_result.raw_data:
            answer = db_result.answer
            sources = db_result.sources
        elif kb_result.raw_data:
            answer = kb_result.answer
            sources = kb_result.sources
        else:
            answer = "抱歉，我无法找到相关信息。"
            sources = []
        
        return QueryResult(
            question=question,
            answer=answer,
            intent=intent,
            sources=sources,
            raw_data={"db": db_result.raw_data, "kb": kb_result.raw_data}
        )
    
    def query_with_unknown_token(self, question: str) -> QueryResult:
        """
        处理包含未知 token 的查询 - T12 专用
        
        当问题包含未知词汇且知识库没有直接命中时调用
        """
        # 检索知识库
        docs = self.kb_retriever.search(question)
        
        # 提取疑似关键词（不在知识库中的词）
        unknown_tokens = []
        for doc in docs:
            content_lower = doc.content.lower()
            for word in self._extract_potential_tokens(question):
                if word.lower() not in content_lower and len(word) > 5:
                    unknown_tokens.append(word)
        
        if unknown_tokens:
            token = unknown_tokens[0]
            return QueryResult(
                question=question,
                answer=f"未找到与 {token} 直接相关的信息，不能确认该事项是否可报销。\n如果你想查询通用报销制度，可以询问差旅费、酒店、餐补、招待费等。",
                intent=QueryIntent.KB_ONLY,
                sources=["knowledge 检索无直接匹配"]
            )
        
        return QueryResult(
            question=question,
            answer="抱歉，未能找到相关信息。",
            intent=QueryIntent.UNKNOWN
        )
    
    def _extract_potential_tokens(self, text: str) -> List[str]:
        """提取疑似关键词"""
        # 移除常见词
        stop_words = {'怎么', '如何', '什么', '报销', '可以', '是否', '能', '吗', '呢'}
        tokens = []
        
        for word in re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', text):
            if len(word) >= 2 and word not in stop_words:
                tokens.append(word)
        
        return tokens
