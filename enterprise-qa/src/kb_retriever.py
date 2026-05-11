"""
知识库检索器

基于关键词检索知识库文档
"""

import os
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class Document:
    """文档"""
    title: str
    content: str
    source: str  # 文件路径
    relevance: float = 0.0
    section: Optional[str] = None


class KBRetriever:
    """知识库检索器"""
    
    # 文档类型映射
    DOC_TYPES = {
        "hr_policies.md": {"type": "制度", "category": "人事"},
        "promotion_rules.md": {"type": "制度", "category": "晋升"},
        "finance_rules.md": {"type": "制度", "category": "财务"},
        "tech_docs.md": {"type": "规范", "category": "技术"},
        "faq.md": {"type": "问答", "category": "常见问题"},
        "meeting_notes": {"type": "会议", "category": "会议纪要"}
    }
    
    # 关键词到文档的映射
    KEYWORD_DOC_MAP = {
        # 人事制度
        "年假": "hr_policies.md",
        "病假": "hr_policies.md",
        "事假": "hr_policies.md",
        "请假": "hr_policies.md",
        "调休": "hr_policies.md",
        "加班": "hr_policies.md",
        "考勤": "hr_policies.md",
        "工作制度": "hr_policies.md",
        
        # 晋升规则
        "晋升": "promotion_rules.md",
        "升级": "promotion_rules.md",
        "升职": "promotion_rules.md",
        "职级": "promotion_rules.md",
        "P4": "promotion_rules.md",
        "P5": "promotion_rules.md",
        "P6": "promotion_rules.md",
        "P7": "promotion_rules.md",
        "职级体系": "promotion_rules.md",
        
        # 财务制度
        "报销": "finance_rules.md",
        "差旅": "finance_rules.md",
        "机票": "finance_rules.md",
        "酒店": "finance_rules.md",
        "餐补": "finance_rules.md",
        "费用": "finance_rules.md",
        "财务": "finance_rules.md",
        
        # 技术文档
        "技术": "tech_docs.md",
        "框架": "tech_docs.md",
        "Python": "tech_docs.md",
        "Go": "tech_docs.md",
        "React": "tech_docs.md",
        "代码": "tech_docs.md",
        "开发": "tech_docs.md",
        "规范": "tech_docs.md",
        
        # 常见问题
        "FAQ": "faq.md",
        "常见问题": "faq.md",
        "试用期": "faq.md",
        "五险一金": "faq.md",
        "远程": "faq.md",
        "工资": "faq.md",
        "入职": "faq.md",
        
        # 会议纪要
        "全员大会": "meeting_notes",
        "技术同步": "meeting_notes",
        "大会": "meeting_notes",
        "会议": "meeting_notes",
        "纪要": "meeting_notes",
        "决议": "meeting_notes",
        "3月": "meeting_notes",
        "最近": "meeting_notes"
    }
    
    def __init__(self, kb_path: str = "./knowledge"):
        self.kb_path = Path(kb_path)
        self.documents = {}
        self._load_documents()
    
    def _load_documents(self):
        """加载所有文档"""
        if not self.kb_path.exists():
            return
        
        # 加载根目录下的文档
        for filename in ["hr_policies.md", "promotion_rules.md", "finance_rules.md", 
                         "tech_docs.md", "faq.md"]:
            filepath = self.kb_path / filename
            if filepath.exists():
                self.documents[filename] = self._load_file(filepath)
        
        # 加载会议纪要
        meeting_notes_dir = self.kb_path / "meeting_notes"
        if meeting_notes_dir.exists():
            for filepath in meeting_notes_dir.glob("*.md"):
                filename = f"meeting_notes/{filepath.name}"
                self.documents[filename] = self._load_file(filepath)
    
    def _load_file(self, filepath: Path) -> Dict[str, Any]:
        """加载单个文件"""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {
            "path": str(filepath),
            "content": content,
            "name": filepath.name
        }
    
    def search(self, query: str, top_k: int = 5) -> List[Document]:
        """
        搜索相关文档
        
        Args:
            query: 查询关键词
            top_k: 返回数量
            
        Returns:
            相关文档列表
        """
        query_lower = query.lower()
        results = []
        
        # 1. 精确匹配文档
        matched_files = set()
        for keyword, filename in self.KEYWORD_DOC_MAP.items():
            if keyword.lower() in query_lower:
                matched_files.add(filename)
        
        # 2. 如果 KEYWORD_DOC_MAP 命中了 meeting_notes，遍历所有会议纪要
        if "meeting_notes" in matched_files:
            matched_files.discard("meeting_notes")
            for filename in self.documents:
                if filename.startswith("meeting_notes/"):
                    doc = self.documents[filename]
                    sections = self._extract_relevant_sections(query, doc["content"])
                    for section, content in sections:
                        relevance = self._calculate_relevance(query, content)
                        if relevance > 0:
                            results.append(Document(
                                title=self._get_title(doc["content"]),
                                content=content.strip(),
                                source=filename,
                                relevance=relevance,
                                section=section
                            ))
        
        # 3. 如果没有精确匹配，基于关键词搜索所有文档
        if not matched_files:
            # 从查询中提取关键搜索词
            search_terms = self._extract_search_terms(query)
            for filename, doc in self.documents.items():
                sections = self._extract_relevant_sections(query, doc["content"])
                if sections:
                    for section, content in sections:
                        relevance = self._calculate_relevance(query, content)
                        if relevance > 0:
                            results.append(Document(
                                title=self._get_title(doc["content"]),
                                content=content.strip(),
                                source=filename,
                                relevance=relevance,
                                section=section
                            ))
        
        # 4. 添加精确匹配的文档内容
        for filename in matched_files:
            if filename in self.documents:
                doc = self.documents[filename]
                sections = self._extract_relevant_sections(query, doc["content"])
                
                for section, content in sections:
                    relevance = self._calculate_relevance(query, content)
                    results.append(Document(
                        title=self._get_title(doc["content"]),
                        content=content.strip(),
                        source=filename,
                        relevance=relevance,
                        section=section
                    ))
        
        # 5. 按相关度排序
        results.sort(key=lambda x: x.relevance, reverse=True)
        
        return results[:top_k]
    
    def search_meeting_notes(self, query: str) -> List[Document]:
        """专门搜索会议纪要"""
        results = []
        query_lower = query.lower()
        
        # "最近有什么事" 类查询：直接返回所有会议纪要
        if "最近" in query_lower and any(kw in query_lower for kw in ["什么事", "动态", "事件", "情况"]):
            for filename in self.documents:
                if not filename.startswith("meeting_notes/"):
                    continue
                doc = self.documents[filename]
                results.append(Document(
                    title=self._get_title(doc["content"]),
                    content=doc["content"],
                    source=filename,
                    relevance=100.0,
                    section=""
                ))
            return results
        
        for filename in self.documents:
            if not filename.startswith("meeting_notes/"):
                continue
            
            doc = self.documents[filename]
            sections = self._extract_relevant_sections(query, doc["content"])
            
            for section, content in sections:
                relevance = self._calculate_relevance(query, content)
                if relevance > 0:
                    results.append(Document(
                        title=self._get_title(doc["content"]),
                        content=content.strip(),
                        source=filename,
                        relevance=relevance,
                        section=section
                    ))
        
        results.sort(key=lambda x: x.relevance, reverse=True)
        return results
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """从查询中提取搜索词"""
        # 移除常见疑问词和模式
        stop_words = {'怎么', '如何', '什么', '哪些', '吗', '呢', '的', '是', '有', '没有', '几次', '多少', '说', '了'}
        
        # 如果有空格，按空格分割
        if ' ' in query:
            terms = []
            for word in query.split():
                word = word.strip('?？.,，')
                if word and word not in stop_words and len(word) > 1:  # 过滤单字符
                    terms.append(word)
            return terms if terms else [query]
        
        # 中文查询：移除常见疑问词
        result = query
        for stop in ['怎么', '如何', '什么', '哪些', '吗', '呢', '的', '是', '有', '没有', '几次', '多少', '说', '了']:
            result = result.replace(stop, ' ')
        
        # 清理
        result = result.strip('?？.,， ')
        
        # 如果清理后为空，返回原始查询
        if not result:
            return [query]
        
        # 返回清理后的词
        terms = [t.strip() for t in result.split() if t.strip() and len(t.strip()) > 1]  # 过滤单字符
        return terms if terms else [query]
    
    def _extract_relevant_sections(self, query: str, content: str) -> List[tuple]:
        """提取相关段落"""
        sections = []
        query_lower = query.lower()
        lines = content.split('\n')
        
        # 提取搜索词
        search_terms = self._extract_search_terms(query)
        
        current_section = ""
        current_content = []
        section_matches = False  # 跟踪当前 section 是否匹配
        section_start_idx = -1  # 记录 section 开始的行索引
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # 检测标题
            if stripped.startswith('#'):
                # 保存之前的段落（如果匹配）
                if current_content and section_matches:
                    sections.append((current_section, '\n'.join(current_content)))
                current_section = stripped
                current_content = []
                section_start_idx = i
                # 检查标题是否匹配关键词（使用更宽松的匹配）
                section_matches = self._title_matches(stripped, search_terms)
                # 如果标题匹配，收集从该标题开始的所有内容
                if section_matches:
                    current_content.append(stripped)
                continue
            
            # 检查内容是否匹配
            content_matches = self._content_matches(stripped, search_terms)
            
            # 如果标题匹配，只收集包含搜索词的内容行
            if section_matches:
                # 表格行始终收集（表格需要完整的行）
                if stripped.startswith('|') or stripped.startswith('-') or not stripped:
                    current_content.append(stripped)
                # 内容行需要包含搜索词
                elif content_matches:
                    current_content.append(stripped)
            elif content_matches:
                # 如果内容匹配但标题不匹配，也收集并标记
                current_content.append(stripped)
                section_matches = True
                # 尝试收集上下文（前后几行）
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                for j in range(start, end):
                    if lines[j].strip() and lines[j].strip() not in current_content:
                        current_content.append(lines[j].strip())
        
        # 保存最后一段（如果匹配）
        if current_content and section_matches:
            sections.append((current_section, '\n'.join(current_content)))
        
        # 如果没有找到相关段落，尝试基于标题相似度匹配返回整个文档
        if not sections:
            for i, line in enumerate(lines):
                if line.startswith('#') and self._title_similar(line, search_terms):
                    # 找到了相似的标题，返回从该标题开始的内容
                    title_idx = i
                    relevant_content = '\n'.join(lines[title_idx:])
                    sections.append((line, relevant_content))
                    break
        
        # 如果还是没有，返回整个文档（基于文档类型关键词）
        if not sections:
            sections.append(("", content[:1000]))  # 返回前1000字符
        
        return sections
    
    def _title_matches(self, title: str, search_terms: List[str]) -> bool:
        """检查标题是否匹配搜索词"""
        title_lower = title.lower()
        for term in search_terms:
            term_lower = term.lower()
            # 完整匹配
            if term_lower in title_lower:
                return True
            # 检查搜索词中的每个字符是否在标题中
            term_chars = [c for c in term_lower if c not in ' ，、-']
            if term_chars and all(c in title_lower for c in term_chars):
                return True
        return False
    
    def _content_matches(self, line: str, search_terms: List[str]) -> bool:
        """检查内容是否匹配搜索词"""
        line_lower = line.lower()
        for term in search_terms:
            term_lower = term.lower()
            # 完整匹配
            if term_lower in line_lower:
                return True
            # 检查搜索词中的每个字符是否在内容中
            term_chars = [c for c in term_lower if c not in ' ，、-']
            if term_chars and sum(1 for c in term_chars if c in line_lower) >= len(term_chars) * 0.5:
                return True
        return False
    
    def _title_similar(self, title: str, search_terms: List[str]) -> bool:
        """检查标题是否与搜索词相似"""
        title_lower = title.lower()
        for term in search_terms:
            term_lower = term.lower()
            # 移除搜索词中的 "规则" 等后缀
            core_term = term_lower.replace('规则', '').replace('制度', '').replace('政策', '')
            if core_term and core_term in title_lower:
                return True
        return False
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """计算相关度"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        # 提取搜索词
        search_terms = self._extract_search_terms(query)
        
        # 计算匹配词数
        match_count = 0
        for term in search_terms:
            term_lower = term.lower()
            # 检查完整匹配
            if term_lower in content_lower:
                match_count += 2  # 完整匹配权重更高
            else:
                # 检查每个字符是否在内容中
                term_chars = [c for c in term_lower if c not in ' ，、']
                if term_chars:
                    char_matches = sum(1 for c in term_chars if c in content_lower)
                    match_count += char_matches / len(term_chars)
        
        if not search_terms:
            return 0.0
        
        # 相关度 = 匹配词数 / 总词数 * 100
        relevance = (match_count / len(search_terms)) * 100
        
        # 如果是完整查询匹配标题或开头，给予额外分数
        if query_lower[:5] in content_lower:
            relevance += 20
        
        return min(relevance, 100.0)
    
    def _get_title(self, content: str) -> str:
        """提取文档标题"""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('#'):
                return line.strip('# \n')
        return ""
    
    def get_document(self, filename: str) -> Optional[Dict[str, Any]]:
        """获取指定文档"""
        return self.documents.get(filename)
    
    def search_specific(self, query: str, target_file: str = None) -> List[Document]:
        """
        定向搜索 - 只搜索指定文档或特定类型的相关内容
        
        Args:
            query: 查询关键词
            target_file: 指定文件名（如 hr_policies.md），None 时自动判断
            
        Returns:
            相关文档列表
        """
        results = []
        query_lower = query.lower()
        
        # 自动判断目标文件
        if target_file is None:
            # 优先判断特定查询类型
            if "年假" in query_lower or "请假" in query_lower:
                target_file = "hr_policies.md"
                target_keywords = ["年假", "带薪年假", "计算方式", "年限", "请假"]
            elif "迟到" in query_lower or "考勤" in query_lower:
                target_file = "hr_policies.md"
                target_keywords = ["迟到", "考勤", "扣款", "处理方式"]
            elif "差旅" in query_lower or ("报销" in query_lower and "差旅" not in query_lower):
                target_file = "finance_rules.md"
                target_keywords = ["差旅费标准", "机票", "火车票", "酒店", "住宿费", "餐补"]
            elif "报销" in query_lower:
                target_file = "finance_rules.md"
                target_keywords = ["报销", "差旅费标准", "机票", "火车票", "酒店", "住宿费", "餐补"]
            elif "晋升" in query_lower or "职级" in query_lower:
                target_file = "promotion_rules.md"
                target_keywords = ["晋升", "职级", "P4", "P5", "P6", "P7", "条件"]
            elif "全员大会" in query_lower or "大会" in query_lower:
                # 优先返回全员大会核心事项（过滤 Q&A）
                for filename in self.documents:
                    if "allhands" in filename:
                        doc = self.documents[filename]
                        content = doc["content"]
                        # 过滤 Q&A，只保留核心事项
                        filtered_lines = []
                        in_qa = False
                        for line in content.split('\n'):
                            stripped = line.strip()
                            # 检测 Q&A 块开始
                            if 'Q:' in stripped or stripped.startswith('**Q'):
                                in_qa = True
                            # 检测 Q&A 块结束（遇到空行后的新内容）
                            elif not stripped and in_qa:
                                in_qa = False
                            # 不收集 Q&A 内容
                            if not in_qa and stripped:
                                filtered_lines.append(line)
                        
                        core_content = '\n'.join(filtered_lines)
                        results.append(Document(
                            title=self._get_title(doc["content"]),
                            content=core_content.strip(),
                            source=filename,
                            relevance=1.0,
                            section="全员大会"
                        ))
                return sorted(results, key=lambda x: x.relevance, reverse=True)[:3]
            elif "最近" in query_lower and any(kw in query_lower for kw in ["什么事", "动态", "事件", "情况"]):
                # 最近动态查询 - 返回所有会议纪要
                return self.search_meeting_notes(query)[:5]
            else:
                # 默认返回所有相关
                return self.search(query, top_k=3)
        else:
            target_keywords = self._extract_search_terms(query)
        
        # 搜索指定文档
        if target_file in self.documents:
            doc = self.documents[target_file]
            content = doc["content"]
            
            # 对于 hr_policies.md 和 finance_rules.md 中的表格，需要精确过滤
            if (target_file == "hr_policies.md" and any(kw in query_lower for kw in ["年假", "迟到", "请假", "加班", "调休"])) or \
               (target_file == "finance_rules.md" and "差旅" in query_lower):
                # 提取相关段落后，过滤表格内容
                filtered_lines = []
                lines = content.split('\n')
                in_target_section = False
                section_depth = 0
                section_context = []
                target_section_title = ""
                
                for line in lines:
                    stripped = line.strip()
                    # 检测标题
                    if stripped.startswith('#'):
                        title_level = len(stripped) - len(stripped.lstrip('#'))
                        # 如果遇到更高级的同级或上级标题，结束当前 section
                        if title_level <= section_depth and section_depth > 0:
                            in_target_section = False
                        section_depth = title_level
                        # 检查标题是否包含目标关键词
                        section_match = any(kw in stripped.lower() for kw in target_keywords)
                        if section_match:
                            in_target_section = True
                            filtered_lines = [line]  # 重置，只保留当前 section
                            target_section_title = stripped
                        # 更新上下文
                        section_context = [stripped] if title_level == 3 else section_context[:title_level-1]
                    elif in_target_section:
                        # 对于 hr_policies.md，表格行需要包含关键词
                        # 对于 finance_rules.md 差旅费，收集所有内容直到下一个同级标题
                        if target_file == "hr_policies.md":
                            if stripped.startswith('|'):
                                if any(kw in stripped for kw in target_keywords):
                                    filtered_lines.append(line)
                            elif stripped.startswith('-'):
                                filtered_lines.append(line)  # 保留分隔行
                            elif any(kw in stripped for kw in target_keywords):
                                filtered_lines.append(line)
                            elif not stripped:  # 空行保留
                                filtered_lines.append(line)
                        else:
                            # finance_rules.md: 收集所有内容（表格、分隔符、空行）
                            if stripped.startswith('|') or stripped.startswith('-') or not stripped:
                                filtered_lines.append(line)
                            elif stripped:
                                filtered_lines.append(line)
                
                if filtered_lines:
                    results.append(Document(
                        title=target_section_title or "制度",
                        content='\n'.join(filtered_lines),
                        source=target_file,
                        relevance=1.0,
                        section=target_section_title
                    ))
            else:
                # 默认行为
                sections = self._extract_relevant_sections(query, content)
                for section, section_content in sections:
                    if any(kw.lower() in section_content.lower() for kw in target_keywords):
                        relevance = self._calculate_relevance(query, section_content)
                        if relevance > 0:
                            results.append(Document(
                                title=section if section else self._get_title(content),
                                content=section_content.strip(),
                                source=target_file,
                                relevance=relevance,
                                section=section
                            ))
        
        return sorted(results, key=lambda x: x.relevance, reverse=True)[:3]
