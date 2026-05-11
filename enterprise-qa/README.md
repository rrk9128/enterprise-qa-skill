# 企业智能问答助手 Skill

能够同时查询**结构化数据**（员工信息、项目记录、考勤数据等）和**非结构化知识**（公司制度、技术文档、会议纪要等），回答员工的各种工作相关问题。

## 功能特性

- 意图识别：自动判断问题类型（数据库查询/知识库查询/混合查询）
- SQL 安全查询：参数化查询，防 SQL 注入
- 知识库检索：支持关键词搜索文档
- 多源融合：综合数据库和知识库信息生成答案
- 来源标注：清晰标注答案来源

## 支持的问题类型

| 类型 | 示例 | 数据源 |
|------|------|--------|
| 员工信息查询 | "张三的邮箱是什么？" | 数据库 |
| 项目查询 | "张三负责哪些项目？" | 数据库 |
| 考勤查询 | "张三2月迟到几次？" | 数据库 |
| 绩效查询 | "王五2025年绩效如何？" | 数据库 |
| 制度查询 | "年假怎么计算？" | 知识库 |
| 晋升评估 | "王五符合P5晋升P6条件吗？" | DB + KB |
| 会议纪要 | "3月全员大会说了什么？" | 知识库 |

## 快速开始

### 1. 环境要求

- Python 3.10+
- SQLite3 或 Python sqlite3

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
# 方式A：使用 sqlite3 命令
chmod +x init_db.sh
./init_db.sh

# 方式B：使用 Python（如果 sqlite3 不可用）
python init_db.py
```

### 4. 运行测试

```bash
# 运行所有测试（预期：全通过）
python -m pytest -q

# 运行测试并查看覆盖率（预期：TOTAL >= 80%）
python -m pytest --cov=src --cov-report=term-missing

# 运行特定测试
python -m pytest tests/test_db_queries.py -v
```

### 5. 命令行使用

```bash
# 基本查询
python src/cli.py "张三的部门是什么？"
python src/cli.py "年假怎么计算？"
python src/cli.py "王五符合P5晋升P6条件吗？"

# SQL 注入检测
python src/cli.py "DROP TABLE employees; SELECT * FROM users WHERE '1'='1"
```

## 项目结构

```
enterprise-qa/
├── SKILL.md              # Skill 说明文档
├── README.md             # 本文件
├── requirements.txt      # Python 依赖
├── config.yaml           # 配置文件
├── config.yaml.example   # 配置示例
├── init_db.sh           # 数据库初始化脚本
├── init_db.py           # Python 初始化脚本
├── enterprise.db         # SQLite 数据库
├── schema.sql           # 数据库表结构
├── seed_data.sql        # 种子数据
├── src/
│   ├── __init__.py
│   ├── query_engine.py   # 查询引擎（主入口）
│   ├── intent_classifier.py  # 意图识别
│   ├── sql_generator.py      # SQL 生成
│   ├── kb_retriever.py       # 知识库检索
│   ├── answer_generator.py   # 答案生成
│   └── cli.py           # 命令行工具
├── tests/
│   ├── __init__.py
│   ├── test_cli.py          # CLI 测试
│   ├── test_db_queries.py   # 数据库测试
│   ├── test_kb_queries.py   # 知识库测试
│   ├── test_intent.py       # 意图识别测试
│   └── test_sql_safety.py   # SQL 安全测试
└── knowledge/
    ├── hr_policies.md        # 人事制度
    ├── promotion_rules.md    # 晋升标准
    ├── tech_docs.md          # 技术规范
    ├── finance_rules.md      # 财务制度
    ├── faq.md                # 常见问题
    └── meeting_notes/        # 会议纪要
```

## 预期结果

```
$ python -m pytest -q
============================== 103 passed in 0.XX s ==============================

$ python -m pytest --cov=src --cov-report=term-missing
TOTAL                        ...   >= 80%
```

## OpenClaw Skill 集成

将 `enterprise-qa` 目录放到 OpenClaw 的 skills 目录下：

```
~/.openclaw/skills/enterprise-qa/
```

触发词：
```
/enterprise-qa "张三的部门是什么？"
/qa "年假怎么算？"
@enterprise "王五符合晋升条件吗？"
```
