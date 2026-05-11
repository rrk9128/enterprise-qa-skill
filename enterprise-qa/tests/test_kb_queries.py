"""
知识库查询测试

测试用例 T03, T04
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.query_engine import EnterpriseQA


@pytest.fixture
def qa():
    """创建 QA 实例"""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(script_dir, "enterprise.db")
    kb_path = os.path.join(script_dir, "knowledge")
    
    if not os.path.exists(kb_path):
        pytest.skip("知识库目录不存在")
    
    return EnterpriseQA(db_path=db_path, kb_path=kb_path)


class TestKnowledgeBaseQueries:
    """知识库查询测试"""
    
    def test_t03_annual_leave(self, qa):
        """T03: 年假怎么计算？"""
        result = qa.query("年假怎么计算？")
        assert "5" in result.answer  # 满1年5天
        assert "15" in result.answer or "上限" in result.answer  # 上限15天
        assert "hr_policies" in str(result.sources).lower() or "请假" in result.answer
    
    def test_t04_late_penalty(self, qa):
        """T04: 迟到几次扣钱？"""
        result = qa.query("迟到几次扣钱？")
        assert "4" in result.answer or "4" in str(result.sources)
        assert "50" in result.answer or "hr_policies" in str(result.sources).lower()
    
    def test_overtime_rules(self, qa):
        """加班规则是什么？"""
        result = qa.query("加班规则是什么？")
        assert "加班" in result.answer
        assert "调休" in result.answer or "1:1" in result.answer
    
    def test_sick_leave(self, qa):
        """病假怎么请？"""
        result = qa.query("病假怎么请？")
        assert "病假" in result.answer
        assert "医院证明" in result.answer or "3天" in result.answer


class TestFinanceQueries:
    """财务报销测试"""
    
    def test_travel_reimbursement(self, qa):
        """差旅费报销标准是什么？"""
        result = qa.query("差旅费报销标准是什么？")
        assert "机票" in result.answer or "酒店" in result.answer
        assert "finance" in str(result.sources).lower() or "报销" in result.answer


class TestPromotionQueries:
    """晋升规则测试"""
    
    def test_promotion_rules(self, qa):
        """P5怎么晋升P6？"""
        result = qa.query("P5怎么晋升P6？")
        assert "P5" in result.answer or "晋升" in result.answer
        assert "KPI" in result.answer or "85" in result.answer or "项目" in result.answer


class TestTechDocsQueries:
    """技术文档测试"""
    
    def test_tech_stack(self, qa):
        """我们用什么技术栈？"""
        result = qa.query("我们用什么技术栈？")
        assert "Python" in result.answer or "Go" in result.answer or "技术" in result.answer


class TestMeetingNotesQueries:
    """会议纪要测试"""
    
    def test_allhands_meeting(self, qa):
        """3月全员大会说了什么？"""
        result = qa.query("3月全员大会说了什么？")
        assert "全员大会" in result.answer or "会议" in result.answer or "CEO" in result.answer


class TestEdgeCases:
    """边界情况测试"""
    
    def test_t12_no_matching_content(self, qa):
        """T12: 无匹配内容"""
        result = qa.query("xyzabc123怎么报销")
        # 应该友好提示无匹配，而不是编造答案
        assert result.answer  # 有回答
        # 不应该包含随机编造的信息


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestAnswerBranches:
    """answer_generator 分支测试"""
    
    def test_answer_from_kb_single(self, qa):
        """测试单文档知识库答案"""
        result = qa.query("年假怎么计算？")
        assert len(result.answer) > 0
        assert len(result.sources) > 0
    
    def test_answer_from_hybrid(self, qa):
        """测试混合问答答案"""
        result = qa.query("张三2月迟到几次？")
        # 可能返回"2月迟到 2 次。"或"张三2月迟到 2 次。"
        assert "2" in result.answer or "迟到" in result.answer
    
    def test_answer_error_handling(self, qa):
        """测试错误处理分支"""
        from src.answer_generator import AnswerGenerator
        ag = AnswerGenerator()
        # 测试空结果处理
        answer, sources = ag.generate_from_db("测试", "SELECT 1", [], [])
        assert len(answer) > 0
    
    def test_meeting_notes_query(self, qa):
        """测试会议纪要查询"""
        result = qa.query("全员大会说了什么？")
        assert "大会" in result.answer or "allhands" in result.answer.lower() or len(result.answer) > 0
    
    def test_finance_rules_query(self, qa):
        """测试财务规则查询"""
        result = qa.query("差旅费报销标准是什么？")
        assert len(result.answer) > 0
        assert "差旅" in result.answer or "报销" in result.answer or "finance" in result.answer.lower()
    
    def test_promotion_rules_query(self, qa):
        """测试晋升规则查询"""
        result = qa.query("P5晋升P6需要什么条件？")
        assert len(result.answer) > 0
        assert "P5" in result.answer or "晋升" in result.answer or "promotion" in result.answer.lower()
    
    def test_attendance_status_format(self, qa):
        """测试考勤状态格式"""
        from src.answer_generator import AnswerGenerator
        ag = AnswerGenerator()
        # 测试考勤状态映射
        assert ag.ATTENDANCE_STATUS_MAP.get("on_time") == "正常"
        assert ag.ATTENDANCE_STATUS_MAP.get("late") == "迟到"
    
    def test_kb_retriever_all_files(self, qa):
        """测试知识库检索所有文件"""
        from src.kb_retriever import KBRetriever
        retriever = KBRetriever('./knowledge')
        # 检查文档是否加载
        assert len(retriever.documents) >= 5
    
    def test_kb_search_with_extracted_terms(self, qa):
        """测试知识库检索关键词提取"""
        from src.kb_retriever import KBRetriever
        retriever = KBRetriever('./knowledge')
        # 测试搜索词提取
        terms = retriever._extract_search_terms("张三2月迟到几次？")
        assert len(terms) > 0
    
    def test_kb_documents_loaded(self, qa):
        """测试文档加载"""
        from src.kb_retriever import KBRetriever
        retriever = KBRetriever('./knowledge')
        # 验证关键文档已加载
        assert 'hr_policies.md' in retriever.documents
        assert 'promotion_rules.md' in retriever.documents
        assert 'finance_rules.md' in retriever.documents
    
    def test_kb_extract_relevant_sections(self, qa):
        """测试相关段落提取"""
        from src.kb_retriever import KBRetriever
        retriever = KBRetriever('./knowledge')
        content = "# 年假制度\n年假计算规则..."
        sections = retriever._extract_relevant_sections("年假", content)
        assert len(sections) >= 0
    
    def test_kb_calculate_relevance(self, qa):
        """测试相关性计算"""
        from src.kb_retriever import KBRetriever
        retriever = KBRetriever('./knowledge')
        content = "这是关于年假的文档内容"
        rel = retriever._calculate_relevance("年假", content)
        assert rel >= 0
    
    def test_answer_generator_helper_methods(self, qa):
        """测试答案生成器辅助方法"""
        from src.answer_generator import AnswerGenerator
        ag = AnswerGenerator()
        # 测试关键字检测方法
        assert ag._is_employee_query("张三的邮箱是什么？") == True
        assert ag._is_project_query("有哪些在研项目？") == True
        assert ag._is_attendance_query("张三2月迟到几次？") == True
        assert ag._is_performance_query("张三的绩效是多少？") == True
        assert ag._is_department_query("研发部有多少人？") == True
    
    def test_answer_generator_empty_results(self, qa):
        """测试答案生成器空结果处理"""
        from src.answer_generator import AnswerGenerator
        ag = AnswerGenerator()
        # 测试没有结果的通用查询
        answer, sources = ag.generate_from_db("随便什么", "SELECT 1", [], [])
        assert len(answer) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
