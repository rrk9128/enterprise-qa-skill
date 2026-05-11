"""
意图识别测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.intent_classifier import IntentClassifier, QueryIntent


@pytest.fixture
def classifier():
    return IntentClassifier()


class TestIntentClassification:
    """意图分类测试"""
    
    def test_db_only_queries(self, classifier):
        """纯数据库查询识别"""
        queries = [
            "张三的部门是什么？",
            "李四的邮箱是什么？",
            "研发部有多少人？",
            "张三2月迟到几次？",
            "张三负责哪些项目？",
            "王五的绩效如何？",
            "EMP-001 是谁？"
        ]
        
        for query in queries:
            intent = classifier.classify(query)
            assert intent == QueryIntent.DB_ONLY, f"Failed for: {query} -> {intent}"
    
    def test_kb_only_queries(self, classifier):
        """纯知识库查询识别"""
        queries = [
            "年假怎么计算？",
            "迟到几次扣钱？",
            "加班规则是什么？",
            "差旅费报销标准是什么？",
            "P5怎么晋升P6？"
        ]
        
        for query in queries:
            intent = classifier.classify(query)
            assert intent in [QueryIntent.KB_ONLY, QueryIntent.HYBRID], f"Failed for: {query} -> {intent}"
    
    def test_hybrid_queries(self, classifier):
        """混合查询识别"""
        queries = [
            "王五符合P5晋升P6条件吗？",
            "张三能达到晋升标准吗？",
            "最近有什么事？"
        ]
        
        for query in queries:
            intent = classifier.classify(query)
            assert intent in [QueryIntent.HYBRID, QueryIntent.DB_ONLY], f"Failed for: {query} -> {intent}"
    
    def test_clarification_queries(self, classifier):
        """需要澄清的查询"""
        queries = [
            "他是谁？",
            "她呢？",
            "吗？",
            "什么？",
            "？"
        ]
        
        for query in queries:
            intent = classifier.classify(query)
            assert intent == QueryIntent.CLARIFICATION, f"Failed for: {query}"
    
    def test_explain_intent(self, classifier):
        """意图解释"""
        query = "张三的部门是什么？"
        explanation = classifier.explain_intent(query)
        assert "employees" in explanation.lower() or "DB" in explanation
        assert "department" in explanation.lower() or "部门" in explanation


class TestConfidenceScore:
    """置信度测试"""
    
    def test_confidence_scores(self, classifier):
        """置信度计算"""
        queries = [
            ("张三的部门", QueryIntent.DB_ONLY),
            ("年假怎么算", QueryIntent.KB_ONLY),
            ("王五符合晋升条件吗", QueryIntent.HYBRID)
        ]
        
        for query, expected_intent in queries:
            intent, confidence = classifier.get_intent_confidence(query)
            assert intent == expected_intent
            assert 0 <= confidence <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
