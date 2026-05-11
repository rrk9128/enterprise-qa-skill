"""
意图分类器

识别用户问题的意图类型
"""

import re
from enum import Enum
from typing import List, Tuple


class QueryIntent(Enum):
    """查询意图类型"""
    DB_ONLY = "db_only"           # 纯数据库查询
    KB_ONLY = "kb_only"           # 纯知识库查询
    HYBRID = "hybrid"             # 混合查询
    CLARIFICATION = "clarification"  # 需要澄清
    UNKNOWN = "unknown"           # 未知


class IntentClassifier:
    """意图分类器"""
    
    # 数据库关键词模式
    DB_PATTERNS = [
        # 员工相关
        r"(?:张三|李四|王五|赵六|钱七|孙八|周九|吴十|CEO|离职员工|EMP-\d+)",
        # 员工属性查询
        r"(?:员工|同事|某人).{0,4}?(?:名字|姓名|邮箱|邮件|电话|手机|部门|职位|职级|级别|入职|上级|领导|老板|经理)",
        r".{0,4}的(?:名字|姓名|邮箱|邮件|电话|手机|部门|职位|职级|级别|入职|上级|领导|老板|经理)",
        # 项目相关（有具体人名）
        r"(?:张三|李四|王五|赵六|钱七|孙八|周九|吴十).{0,10}?(?:项目|负责|参与)",
        # 绩效相关
        r"(?:张三|李四|王五|赵六|钱七|孙八|周九|吴十).{0,10}?(?:绩效|KPI|考核)",
        r"(?:张三|李四|王五|赵六|钱七|孙八|周九|吴十).{0,10}?(?:迟到|早退|旷工)",
        # 部门统计
        r"[^\s]+部.{0,5}?(?:多少人|有.*人|人数|总数)",
        # 项目统计（无具体人名，但在研项目、进行中项目是 DB 查询）
        r"(?:在研项目|进行中.*项目|活跃.*项目|有哪些.{0,3}项目)",
        # 考勤统计
        r"(?:张三|李四|王五|赵六|钱七|孙八|周九|吴十)\d*月.{0,5}?(?:迟到|早退)",
    ]
    
    # 知识库关键词模式
    KB_PATTERNS = [
        # 制度类
        r"(?:制度|规定|规则|标准|政策|流程|规范|准则)",
        # 假期类
        r"(?:年假|病假|事假|婚假|产假|陪产假|丧假|调休|请假)",
        # 报销类
        r"(?:报销|差旅|机票|酒店|餐补|交通|费用)",
        # 福利类
        r"(?:福利|体检|保险|奖金|薪酬|工资|调薪)",
        # 加班类
        r"(?:加班|宵夜|打车|补助)",
        # 迟到扣款类（不需要具体人名的规则查询）
        r"(?:迟到|早退|旷工).{0,10}?(?:扣钱|扣款|规则|如何|怎么)",
        # 技术类
        r"(?:技术|框架|语言|工具|架构|代码|开发|规范|栈)",
        # 会议类
        r"(?:大会|全员|同步会|会议|纪要|决议|3月)",
        # 晋升规则类（无具体人名）
        r"(?:P\d怎么|P\d→P\d|P\d晋升|怎么晋升)",
    ]
    
    # 混合查询关键词
    HYBRID_PATTERNS = [
        r"(?:符合|满足|可以.*晋升|能.*晋升|达到.*条件)",
        r"(?:最近有什么事|最近.*动态)",
    ]
    
    # 需要澄清的模式（更严格）
    CLARIFICATION_PATTERNS = [
        r"^(?:他|她|它|这个|那个|该|其)(?:是|的|呢)?[\?？]?$",  # 他是谁？、她呢？
        r"^(?:吗|呢|吧|呀|啊|么|什么)[\?？]?$",  # 吗？、呢？、什么？
        r"^[\?？]$",  # 单独的？
        r"^$",  # 空字符串
        r"^(?:他|她|它)(?:是|的)",  # 他是谁、她是
        r"^吗[\?？]$",  # 吗？
    ]
    
    def __init__(self):
        self.db_patterns = [re.compile(p, re.IGNORECASE) for p in self.DB_PATTERNS]
        self.kb_patterns = [re.compile(p, re.IGNORECASE) for p in self.KB_PATTERNS]
        self.hybrid_patterns = [re.compile(p, re.IGNORECASE) for p in self.HYBRID_PATTERNS]
        self.clarification_patterns = [re.compile(p) for p in self.CLARIFICATION_PATTERNS]
    
    def classify(self, question: str) -> QueryIntent:
        """
        分类用户问题
        
        Args:
            question: 用户问题
            
        Returns:
            QueryIntent: 识别的意图
        """
        question = question.strip()
        
        if not question:
            return QueryIntent.UNKNOWN
        
        # 检查是否需要澄清
        for pattern in self.clarification_patterns:
            if pattern.match(question):
                return QueryIntent.CLARIFICATION
        
        # 匹配各类模式
        db_matches = self._count_matches(question, self.db_patterns)
        kb_matches = self._count_matches(question, self.kb_patterns)
        hybrid_matches = self._count_matches(question, self.hybrid_patterns)
        
        # 判断意图
        if hybrid_matches > 0 or (db_matches > 0 and kb_matches > 0):
            return QueryIntent.HYBRID
        elif db_matches > kb_matches:
            return QueryIntent.DB_ONLY
        elif kb_matches > 0:
            return QueryIntent.KB_ONLY
        else:
            # 默认尝试数据库查询
            return QueryIntent.DB_ONLY
    
    def _count_matches(self, text: str, patterns: List[re.Pattern]) -> int:
        """计算匹配的模式数量"""
        count = 0
        for pattern in patterns:
            if pattern.search(text):
                count += 1
        return count
    
    def get_intent_confidence(self, question: str) -> Tuple[QueryIntent, float]:
        """
        获取意图及置信度
        
        Returns:
            (intent, confidence)
        """
        question = question.strip()
        
        db_matches = self._count_matches(question, self.db_patterns)
        kb_matches = self._count_matches(question, self.kb_patterns)
        hybrid_matches = self._count_matches(question, self.hybrid_patterns)
        
        total = db_matches + kb_matches + hybrid_matches
        
        if total == 0:
            return QueryIntent.UNKNOWN, 0.0
        
        if hybrid_matches > 0 or (db_matches > 0 and kb_matches > 0):
            return QueryIntent.HYBRID, hybrid_matches / total
        elif db_matches > kb_matches:
            return QueryIntent.DB_ONLY, db_matches / total
        else:
            return QueryIntent.KB_ONLY, kb_matches / total
    
    def explain_intent(self, question: str) -> str:
        """解释意图判断原因"""
        intent, confidence = self.get_intent_confidence(question)
        
        reasons = []
        
        # 数据库匹配原因
        db_keywords = ["员工", "项目", "绩效", "考勤", "部门", "邮箱"]
        for kw in db_keywords:
            if kw in question:
                reasons.append(f"检测到DB关键词: {kw}")
        
        # 知识库匹配原因
        kb_keywords = ["年假", "报销", "加班", "晋升", "制度", "会议"]
        for kw in kb_keywords:
            if kw in question:
                reasons.append(f"检测到KB关键词: {kw}")
        
        return f"意图: {intent.value}, 置信度: {confidence:.2f}\n原因: " + "; ".join(reasons) if reasons else f"意图: {intent.value}"
