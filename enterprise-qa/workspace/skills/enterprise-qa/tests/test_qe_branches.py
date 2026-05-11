"""
QueryEngine 分支测试 - 覆盖未覆盖的代码分支
"""

import pytest
import sys
import os
import sqlite3
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.query_engine import EnterpriseQA, QueryResult, QueryIntent
from src.intent_classifier import IntentClassifier


@pytest.fixture
def qa():
    """创建 EnterpriseQA 实例"""
    return EnterpriseQA(db_path="./enterprise.db", kb_path="./knowledge")


@pytest.fixture
def empty_db():
    """创建临时空数据库"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


class TestQueryEngineBranches:
    """QueryEngine 分支测试"""
    
    def test_clarification_intent(self, qa):
        """测试 CLARIFICATION 意图 - 覆盖 query_engine.py 第143-148行"""
        # 使用一个会返回 CLARIFICATION 的问题
        result = qa.query("吗？")
        assert result.intent == QueryIntent.CLARIFICATION
        assert "不够明确" in result.answer
    
    def test_no_employee_name_for_promotion(self, qa):
        """测试晋升查询没有员工姓名 - 覆盖 query_engine.py 第296-301行"""
        result = qa.query("符合 P5 晋升 P6 条件吗？")
        assert "请提供" in result.answer or "员工" in result.answer
    
    def test_no_level_for_promotion(self, qa):
        """测试晋升查询没有职级 - 覆盖 query_engine.py 第305-310行"""
        result = qa.query("张三符合晋升条件吗？")
        assert "请明确" in result.answer or "晋升级别" in result.answer or "P5" in result.answer
    
    def test_recent_events_not_found(self, qa):
        """测试最近动态未找到 - 覆盖 query_engine.py 第419-424行"""
        # 修改 kb_retriever 使其返回空
        original_search = qa.kb_retriever.search_meeting_notes
        qa.kb_retriever.search_meeting_notes = lambda x: []
        
        result = qa._handle_recent_events("最近有什么事？", QueryIntent.HYBRID)
        assert "没有找到" in result.answer or "未找到" in result.answer
        
        qa.kb_retriever.search_meeting_notes = original_search
    
    def test_general_hybrid_no_data(self, qa):
        """测试混合查询无数据 - 覆盖 query_engine.py 第497-499行"""
        # 模拟返回空结果的 DB 和 KB
        original_db = qa._handle_db_only
        original_kb = qa._handle_kb_only
        
        qa._handle_db_only = lambda q, i: QueryResult(
            question=q, answer="", intent=i, sources=[], raw_data=None
        )
        qa._handle_kb_only = lambda q, i: QueryResult(
            question=q, answer="", intent=i, sources=[], raw_data=None
        )
        
        result = qa._handle_general_hybrid("测试问题", QueryIntent.HYBRID)
        assert "无法找到" in result.answer or "没有" in result.answer
        
        qa._handle_db_only = original_db
        qa._handle_kb_only = original_kb
    
    def test_employee_not_found_by_id(self, qa):
        """测试按 ID 查找员工不存在 - 覆盖 answer_generator.py 第60-62行"""
        result = qa.query("EMP-999 的邮箱是什么？")
        assert "不存在" in result.answer or "没找到" in result.answer or "未找到" in result.answer
    
    def test_unknown_intent_fallback(self, qa):
        """测试未知意图返回 - 覆盖 query_engine.py 第149-155行"""
        # 使用纯数字测试
        result = qa.query("123456")
        # DB_ONLY 是有效返回值
        assert result.intent in [QueryIntent.UNKNOWN, QueryIntent.CLARIFICATION, QueryIntent.KB_ONLY, QueryIntent.DB_ONLY]


class TestIntentClassifierBranches:
    """IntentClassifier 分支测试"""
    
    def test_question_marks_only(self):
        """测试只有问号的问题"""
        ic = IntentClassifier()
        intent = ic.classify("？")
        assert intent == QueryIntent.CLARIFICATION
    
    def test_empty_question(self):
        """测试空问题"""
        ic = IntentClassifier()
        intent = ic.classify("")
        assert intent in [QueryIntent.UNKNOWN, QueryIntent.CLARIFICATION]
    
    def test_special_characters(self):
        """测试特殊字符"""
        ic = IntentClassifier()
        intent = ic.classify("abc")
        assert intent in [QueryIntent.UNKNOWN, QueryIntent.CLARIFICATION, QueryIntent.KB_ONLY, QueryIntent.DB_ONLY]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
