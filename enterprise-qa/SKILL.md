---
name: enterprise-qa
description: 企业智能问答助手，可查询 SQLite 数据库和 Markdown 知识库，支持 DB、KB、混合问答和来源标注。
metadata:
  openclaw:
    requires:
      bins:
        - python3
---

# 企业智能问答助手 Skill

能够同时查询**结构化数据**（员工信息、项目记录、考勤数据等）和**非结构化知识**（公司制度、技术文档、会议纪要等），回答员工的各种工作相关问题。

## 触发词

```
/enterprise-qa "张三的部门是什么？"
/qa "年假怎么算？"
@enterprise "王五符合晋升条件吗？"
```

## CLI 调用方式

```bash
python src/cli.py "<用户问题>"
```

示例：
```bash
python src/cli.py "张三的部门是什么？"
python src/cli.py "年假怎么计算？"
python src/cli.py "王五符合 P5 晋升 P6 条件吗？"
```

## 功能特性

- **意图识别**：自动判断问题类型（数据库查询/知识库查询/混合查询）
- **SQL 安全查询**：参数化查询，防 SQL 注入
- **知识库检索**：支持关键词搜索文档
- **多源融合**：综合数据库和知识库信息生成答案
- **来源标注**：清晰标注答案来源

## 支持的问题类型

| 类型 | 示例 | 数据源 |
|------|------|--------|
| 员工信息 | "张三的邮箱是什么？" | DB |
| 项目查询 | "张三负责哪些项目？" | DB |
| 考勤查询 | "张三2月迟到几次？" | DB |
| 制度查询 | "年假怎么计算？" | KB |
| 晋升评估 | "王五符合P5晋升P6条件吗？" | DB+KB |
| 会议查询 | "最近有什么事？" | KB |

## 配置

环境变量：
- `ENTERPRISE_QA_DB_PATH` - 数据库路径
- `ENTERPRISE_QA_KB_PATH` - 知识库路径

当前 CLI 默认支持环境变量配置；config.yaml.example 作为配置示例保留。
