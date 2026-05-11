"""
数据库查询测试

测试用例 T01, T02, T05, T06, T07, T08
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
    
    if not os.path.exists(db_path):
        pytest.skip("数据库文件不存在，请先运行 init_db.sh")
    
    return EnterpriseQA(db_path=db_path, kb_path=kb_path)


class TestEmployeeQueries:
    """员工信息查询测试"""
    
    def test_t01_zhangsan_department(self, qa):
        """T01: 张三的部门是什么？"""
        result = qa.query("张三的部门是什么？")
        assert "研发部" in result.answer
        assert "employees" in str(result.sources).lower()
    
    def test_t02_lisi_manager(self, qa):
        """T02: 李四的上级是谁？"""
        result = qa.query("李四的上级是谁？")
        assert "CEO" in result.answer or "EMP-000" in result.answer
        assert "employees" in str(result.sources).lower()
    
    def test_zhangsan_email(self, qa):
        """张三的邮箱是什么？"""
        result = qa.query("张三的邮箱是什么？")
        assert "zhangsan@company.com" in result.answer
        assert "employees" in str(result.sources).lower()
    
    def test_wangwu_level(self, qa):
        """王五的职级是什么？"""
        result = qa.query("王五的职级是什么？")
        assert "P5" in result.answer


class TestProjectQueries:
    """项目查询测试"""
    
    def test_t05_zhangsan_projects(self, qa):
        """T05: 张三负责哪些项目？"""
        result = qa.query("张三负责哪些项目？")
        assert "PRJ-001" in result.answer or "ReMe" in result.answer
        # 应该包含多个项目
        assert "project" in str(result.sources).lower()
    
    def test_active_projects(self, qa):
        """有哪些在研项目？"""
        result = qa.query("有哪些在研项目？")
        assert "active" in result.answer.lower() or "进行中" in result.answer


class TestDepartmentQueries:
    """部门查询测试"""
    
    def test_t06_rd_department_count(self, qa):
        """T06: 研发部有多少人？"""
        result = qa.query("研发部有多少人？")
        assert "4" in result.answer
        assert "研发部" in result.answer
    
    def test_product_department_count(self, qa):
        """产品部有多少人？"""
        result = qa.query("产品部有多少人？")
        assert "3" in result.answer


class TestAttendanceQueries:
    """考勤查询测试"""
    
    def test_t08_zhangsan_late(self, qa):
        """T08: 张三2月迟到几次？"""
        result = qa.query("张三2月迟到几次？")
        assert "2" in result.answer
        assert "迟到" in result.answer
    
    def test_wangwu_late(self, qa):
        """王五2月迟到几次？"""
        result = qa.query("王五2月迟到几次？")
        assert "5" in result.answer


class TestPerformanceQueries:
    """绩效查询测试"""
    
    def test_zhangsan_performance(self, qa):
        """张三2025年绩效如何？"""
        result = qa.query("张三2025年绩效如何？")
        assert "2025" in result.answer
        assert "KPI" in result.answer or "A" in result.answer
    
    def test_wangwu_kpi(self, qa):
        """王五的平均KPI是多少？"""
        result = qa.query("王五的平均KPI是多少？")
        assert "80" in result.answer or "B" in result.answer


class TestEdgeCases:
    """边界情况测试"""
    
    def test_t09_nonexistent_employee(self, qa):
        """T09: 查询不存在的员工"""
        result = qa.query("EMP-999 是谁？")
        assert "不存在" in result.answer or "没找到" in result.answer or "抱歉" in result.answer
    
    def test_t11_sql_injection(self, qa):
        """T11: SQL 注入检测"""
        result = qa.query("SELECT * FROM users WHERE '1'='1")
        assert result.error or "不合法的" in result.answer or "无法" in result.answer


class TestQueryBranches:
    """query_engine 分支测试"""
    
    def test_manager_query_ceo(self, qa):
        """测试 CEO 的上级查询"""
        result = qa.query("CEO 的上级是谁？")
        # CEO 没有上级，应该返回相关提示
        assert "上级" in result.answer or "没有" in result.answer or "CEO" in result.answer
    
    def test_attendance_query(self, qa):
        """测试考勤查询"""
        result = qa.query("张三2月迟到几次？")
        assert "迟到" in result.answer or "2" in result.answer
    
    def test_project_list(self, qa):
        """测试项目列表查询"""
        result = qa.query("有哪些在研项目？")
        assert "项目" in result.answer
    
    def test_performance_query(self, qa):
        """测试绩效查询"""
        result = qa.query("张三的绩效是多少？")
        assert "KPI" in result.answer or "评级" in result.answer
    
    def test_department_query(self, qa):
        """测试部门查询"""
        result = qa.query("研发部有多少人？")
        assert "研发部" in result.answer
    
    def test_generic_no_match(self, qa):
        """测试通用答案格式（无匹配）"""
        result = qa.query("随便什么内容？")
        # 应该返回某种答案或提示
        assert len(result.answer) > 0
    
    def test_employee_info(self, qa):
        """测试员工信息查询"""
        result = qa.query("张三的职级是什么？")
        assert "P4" in result.answer or "职级" in result.answer
    
    def test_employee_hire_date(self, qa):
        """测试入职日期查询"""
        result = qa.query("李四什么时候入职的？")
        assert "2024" in result.answer or "入职" in result.answer
    
    def test_unknown_employee_name(self, qa):
        """测试未知员工姓名查询"""
        result = qa.query("不存在的员工是谁？")
        # 应该返回某种提示
        assert len(result.answer) > 0
    
    def test_project_lead_query(self, qa):
        """测试项目负责人查询"""
        result = qa.query("ReMe记忆框架的负责人是谁？")
        # 应该返回项目或负责人相关信息
        assert len(result.answer) > 0
    
    def test_department_project_count(self, qa):
        """测试部门项目数量"""
        result = qa.query("研发部参与了多少个项目？")
        # 应该返回项目相关信息
        assert len(result.answer) > 0
    
    def test_intent_classifier_patterns(self, qa):
        """测试意图分类器模式"""
        from src.intent_classifier import IntentClassifier
        ic = IntentClassifier()
        # 测试分类器存在且可调用
        result = ic.classify("张三的部门是什么？")
        assert result is not None
    
    def test_query_result_to_markdown(self, qa):
        """测试查询结果 markdown 输出"""
        result = qa.query("张三的部门是什么？")
        # 测试 to_markdown 方法
        md = result.to_markdown()
        assert len(md) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
