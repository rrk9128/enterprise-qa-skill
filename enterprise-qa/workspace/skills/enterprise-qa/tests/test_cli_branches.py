"""
CLI 测试 - 覆盖 src/cli.py 的分支
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCLIBranches:
    """CLI 分支测试"""
    
    def test_cli_no_args(self):
        """测试无参数调用 - 覆盖 cli.py 第21-23行"""
        # 保存原始 argv
        original_argv = sys.argv
        
        try:
            sys.argv = ['cli.py']  # 没有问题参数
            from src.cli import main
            
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        finally:
            sys.argv = original_argv
    
    def test_cli_file_not_found(self):
        """测试 FileNotFoundError 处理 - 覆盖 cli.py 第55-58行"""
        original_argv = sys.argv
        original_env = os.environ.get('ENTERPRISE_QA_DB_PATH')
        
        try:
            sys.argv = ['cli.py', '测试问题']
            os.environ['ENTERPRISE_QA_DB_PATH'] = '/nonexistent/path/enterprise.db'
            
            from src.cli import main
            
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        finally:
            sys.argv = original_argv
            if original_env:
                os.environ['ENTERPRISE_QA_DB_PATH'] = original_env
            elif 'ENTERPRISE_QA_DB_PATH' in os.environ:
                del os.environ['ENTERPRISE_QA_DB_PATH']
    
    def test_cli_normal_execution(self):
        """测试正常执行 - 覆盖 cli.py 第39-54行"""
        from src.cli import main
        import io
        from contextlib import redirect_stdout
        
        original_argv = sys.argv
        try:
            sys.argv = ['cli.py', '张三的部门是什么？']
            
            # 正常执行会输出到 stdout
            f = io.StringIO()
            with redirect_stdout(f):
                main()
            
            output = f.getvalue()
            assert '问题:' in output
            assert '答案:' in output
        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
