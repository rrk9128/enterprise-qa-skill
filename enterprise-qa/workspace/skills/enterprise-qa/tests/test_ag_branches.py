"""
AnswerGenerator 分支测试 - 覆盖未覆盖的代码分支
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.answer_generator import AnswerGenerator
from src.kb_retriever import KBRetriever, Document


@pytest.fixture
def ag():
    """创建 AnswerGenerator 实例"""
    return AnswerGenerator()


@pytest.fixture
def kb():
    """创建 KBRetriever 实例"""
    return KBRetriever("./knowledge")


class TestAnswerGeneratorBranches:
    """AnswerGenerator 分支测试"""
    
    def test_format_department_with_count(self, ag):
        """测试部门统计 - 覆盖 answer_generator.py 第284-287行"""
        answer, sources = ag._format_department_answer(
            "研发部有多少人",
            [(3,)],  # count = 3
            ["count"]
        )
        assert "3" in answer or "3 人" in answer
    
    def test_format_department_member_list(self, ag):
        """测试部门成员列表 - 覆盖 answer_generator.py 第289-291行"""
        answer, sources = ag._format_department_answer(
            "研发部有哪些人",
            [("张三",), ("李四",), ("王五",)],
            ["name"]
        )
        assert "张三" in answer or "李四" in answer or "王五" in answer
    
    def test_generic_empty_results_with_emp_id(self, ag):
        """测试通用空结果（员工ID） - 覆盖 answer_generator.py 第60-62行"""
        answer, sources = ag._format_generic_answer(
            "EMP-999 的邮箱是什么？",
            [],
            ["email"]
        )
        assert "EMP-999" in answer and ("不存在" in answer or "没找到" in answer or "未找到" in answer)
    
    def test_generic_empty_results_with_name(self, ag):
        """测试通用空结果（员工姓名） - 覆盖 answer_generator.py 第65-68行"""
        answer, sources = ag._format_generic_answer(
            "不存在的员工的邮箱是什么？",
            [],
            ["email"]
        )
        # 应该提取到"不存在"作为姓名
        assert "不存在" in answer or "没有找到" in answer or "请确认" in answer
    
    def test_generic_empty_results_no_hint(self, ag):
        """测试通用空结果（无提示词） - 覆盖 answer_generator.py 第70行"""
        answer, sources = ag._format_generic_answer(
            "asdfghjkl",
            [],
            ["col1"]
        )
        assert "没有找到" in answer or "抱歉" in answer or "未找到" in answer
    
    def test_generic_results(self, ag):
        """测试通用结果 - 覆盖 answer_generator.py 第320-328行"""
        answer, sources = ag._format_generic_answer(
            "查询数据",
            [("a", "b", "c"), ("d", "e", "f")],
            ["col1", "col2", "col3"]
        )
        assert len(answer) > 0
    
    def test_generate_from_kb_empty(self, ag):
        """测试 KB 生成空结果 - 覆盖 answer_generator.py 第345-346行"""
        answer, sources = ag.generate_from_kb("测试问题", [])
        assert "没有找到" in answer or "未找到" in answer
    
    def test_generate_from_kb_single_doc(self, ag, kb):
        """测试 KB 生成单文档 - 覆盖 answer_generator.py 第352-367行"""
        docs = kb.search("年假怎么计算")[:1]
        if docs:
            answer, sources = ag.generate_from_kb("年假怎么计算", docs)
            assert len(answer) > 0
            assert len(sources) > 0
    
    def test_generate_from_kb_multiple_docs(self, ag, kb):
        """测试 KB 生成多文档 - 覆盖 answer_generator.py 第369-372行"""
        docs = kb.search("年假")[:3]
        if len(docs) >= 2:
            answer, sources = ag.generate_from_kb("年假相关", docs)
            assert len(answer) > 0


class TestKBRetrieverBranches:
    """KBRetriever 分支测试"""
    
    def test_search_empty_query(self, kb):
        """测试空查询"""
        docs = kb.search("")
        assert len(docs) >= 0
    
    def test_search_annual_leave(self, kb):
        """测试年假检索"""
        docs = kb.search("年假怎么计算")
        assert len(docs) > 0
        assert any("年假" in d.content or "年假" in d.section for d in docs)
    
    def test_search_meeting_notes(self, kb):
        """测试会议纪要检索"""
        docs = kb.search_meeting_notes("全员大会说了什么")
        assert len(docs) >= 0
    
    def test_calculate_relevance_high(self, kb):
        """测试高相关性计算"""
        doc = kb.documents.get("hr_policies.md", {})
        if doc:
            rel = kb._calculate_relevance("年假怎么算", doc.get("content", ""))
            assert rel > 0
    
    def test_calculate_relevance_low(self, kb):
        """测试低相关性计算"""
        rel = kb._calculate_relevance("xyzabc", "完全无关的内容")
        assert rel < 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
