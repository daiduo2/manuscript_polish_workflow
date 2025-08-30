# -*- coding: utf-8 -*-
"""
文献服务模块
负责文献的提取、搜索和处理，包含完整的文献搜索、元数据提取、段落召回功能
"""

import os
import json
import re
import logging
import math
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ..config import config
from ..models.literature import LiteratureMetadata, Passage
from ..utils.file_utils import read_file_content, save_json, load_json, get_supported_files
from ..utils.algorithm_utils import AlgorithmUtils
from .llm_service import LLMService


class LiteratureService:
    """
    文献服务类
    负责文献的提取、搜索和处理
    """

    def __init__(self, metadata_cache_dir: str = "./cache/metadata", llm_service=None):
        """
        初始化文献服务
        
        Args:
            metadata_cache_dir: 元数据缓存目录
            llm_service: LLM服务实例（用于智能段落提取）
        """
        self.metadata_cache_dir = Path(metadata_cache_dir)
        self.metadata_cache_dir.mkdir(parents=True, exist_ok=True)
        self.llm_service = llm_service
        self.logger = logging.getLogger(__name__)
        self.algorithm_utils = AlgorithmUtils()
        
        # 支持的文件格式
        self.supported_formats = ['.txt', '.md', '.pdf']

    def extract_metadata_fast(self, file_path: str) -> Dict[str, Any]:
        """
        快速提取文献元信息（本地解析，不依赖LLM）
        
        Args:
            file_path: 文献文件路径
            
        Returns:
            Dict[str, Any]: 文献元信息
        """
        self.logger.info(f"快速提取文献元信息: {file_path}")

        try:
            content = read_file_content(file_path)
            if not content:
                return {'file_path': str(file_path)}

            # 初始化元信息
            metadata = {
                'title': "",
                'authors': [],
                'abstract': "",
                'keywords': [],
                'year': "",
                'file_path': str(file_path),
                'extraction_time': datetime.now().isoformat(),
                'extraction_method': "fast_local"
            }

            lines = content.split('\n')
            content_lower = content.lower()

            # 提取标题
            if lines:
                for line in lines[:10]:
                    line = line.strip()
                    if line and not line.startswith('#') and len(line) > 5:
                        if not any(skip in line.lower() for skip in ['author', 'date', '@', 'http', 'doi']):
                            metadata['title'] = line
                            break

                if not metadata['title']:
                    metadata['title'] = Path(file_path).stem.replace('_', ' ')

            # 提取摘要
            abstract_patterns = ['abstract', '摘要', 'summary', '概 要']
            for i, line in enumerate(lines):
                if any(pattern in line.lower() for pattern in abstract_patterns):
                    abstract_lines = []
                    for j in range(i + 1, min(i + 20, len(lines))):
                        if lines[j].strip():
                            if lines[j].startswith('#'):
                                break
                            abstract_lines.append(lines[j])
                        elif len(abstract_lines) > 0:
                            break
                    metadata['abstract'] = ' '.join(abstract_lines).strip()
                    break

            # 提取关键词
            keyword_patterns = ['keywords', '关键词', 'key words', '关键字']
            for i, line in enumerate(lines):
                if any(pattern in line.lower() for pattern in keyword_patterns):
                    keyword_text = ' '.join(lines[i + 1: i + 5]).strip()
                    keywords = [kw.strip() for kw in keyword_text.replace('，', ',').split(',') if kw.strip()]
                    metadata['keywords'] = keywords[:10]
                    break

            # 提取作者信息
            author_patterns = ['author', '作者', '@']
            for line in lines[:15]:
                if any(pattern in line.lower() for pattern in author_patterns):
                    author_text = line.replace('author:', '').replace('作者:', '').replace('@', '').strip()
                    if author_text:
                        authors = [author.strip() for author in author_text.replace('，', ',').replace(' and ', ',').split(',') if author.strip()]
                        metadata['authors'] = authors[:5]
                    break

            # 提取年份
            year_match = re.search(r'\b(19|20)\d{2}\b', content)
            if year_match:
                metadata['year'] = year_match.group()

            # 如果摘要为空，使用前几段作为摘要
            if not metadata['abstract']:
                paragraphs = [line.strip() for line in lines if line.strip() and len(line) > 20]
                if paragraphs:
                    metadata['abstract'] = ' '.join(paragraphs[:3])[:500]

            return metadata

        except Exception as e:
            self.logger.error(f"快速提取文献元信息失败: {e}")
            return {'file_path': str(file_path)}

    def search_literature(self, keywords: List[str], literature_dir: str, max_results: int = 50, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        搜索相关文献
        
        Args:
            keywords: 搜索关键词
            literature_dir: 文献目录
            max_results: 最大返回结果数
            use_cache: 是否使用缓存的元数据
            
        Returns:
            List[Dict[str, Any]]: 匹配的文献列表，按相关性排序
        """
        self.logger.info(f"开始搜索文献，关键词: {keywords[:5]}...")

        try:
            matched_literature = []
            all_documents = []

            literature_path = Path(literature_dir)
            if not literature_path.exists():
                self.logger.error(f"文献目录不存在: {literature_dir}")
                return matched_literature

            # 获取所有支持的文件
            supported_files = get_supported_files(literature_dir, self.supported_formats)

            # 第一遍：收集所有文档内容用于TF-IDF计算
            for file_path in supported_files:
                try:
                    content = read_file_content(file_path)
                    if content:
                        all_documents.append(content)
                except Exception as e:
                    self.logger.warning(f"读取文档失败 {file_path}: {e}")

            # 扩展关键词
            expanded_keywords = self.algorithm_utils.expand_keywords_with_synonyms(keywords, self.algorithm_utils.get_general_synonyms())

            # 第二遍：计算匹配度和TF-IDF评分
            for file_path in supported_files:
                try:
                    content = read_file_content(file_path)
                    if not content:
                        continue

                    # 获取或提取元数据
                    metadata = self._get_or_extract_metadata(str(file_path), use_cache)
                    
                    if not metadata:
                        continue

                    # 计算关键词匹配度
                    keyword_score = self.algorithm_utils.calculate_keyword_match_score(expanded_keywords, content)
                    
                    # 计算TF-IDF评分
                    tfidf_score = self.algorithm_utils.calculate_relevance_score(expanded_keywords, content, all_documents)
                    
                    # 计算综合评分
                    combined_score = (keyword_score * 0.6 + tfidf_score * 0.4)
                    
                    # 只保留有一定相关性的文献
                    if combined_score > 0.1:
                        literature_info = {
                            **metadata,
                            'keyword_score': keyword_score,
                            'tfidf_score': tfidf_score,
                            'combined_score': combined_score,
                            'matched_keywords': self._find_matched_keywords(expanded_keywords, content)
                        }
                        matched_literature.append(literature_info)

                except Exception as e:
                    self.logger.warning(f"处理文献文件失败 {file_path}: {e}")

            # 按综合评分排序
            matched_literature.sort(key=lambda x: x['combined_score'], reverse=True)
            
            # 限制返回数量
            result = matched_literature[:max_results]
            
            self.logger.info(f"搜索完成，匹配到 {len(result)} 篇相关文献")
            return result

        except Exception as e:
            self.logger.error(f"文献搜索失败: {e}")
            raise
    
    def extract_metadata_with_llm(self, file_path: str) -> Dict[str, Any]:
        """
        使用LLM提取文献元信息（更准确但需要API调用）
        
        Args:
            file_path: 文献文件路径
            
        Returns:
            Dict[str, Any]: 文献元信息
        """
        if not self.llm_service:
            self.logger.warning("LLM服务未配置，使用快速提取方法")
            return self.extract_metadata_fast(file_path)
        
        try:
            content = read_file_content(file_path)
            metadata = self.llm_service.extract_metadata(content)
            metadata['file_path'] = file_path
            return metadata
        except Exception as e:
            self.logger.error(f"LLM元数据提取失败，回退到快速方法: {e}")
            return self.extract_metadata_fast(file_path)
    
    def extract_relevant_passages(self, literature_list: List[Dict[str, Any]], keywords: List[str], 
                                max_literature: int = 50, passages_per_literature: int = 2) -> List[Dict[str, Any]]:
        """
        从检索到的文献中提取相关段落
        
        Args:
            literature_list: 文献列表
            keywords: 检索关键词
            max_literature: 最多处理多少篇文献
            passages_per_literature: 每篇文献提取多少个段落
            
        Returns:
            包含相关段落和引用信息的列表
        """
        self.logger.info(f"开始提取相关文献段落，最多处理 {max_literature} 篇文献")
        
        try:
            relevant_passages = []
            process_count = min(max_literature, len(literature_list))
            
            for i, literature in enumerate(literature_list[:process_count]):
                try:
                    # 读取文献全文
                    content = read_file_content(literature['file_path'])
                    
                    # 尝试使用LLM智能提取
                    if self.llm_service:
                        passages = self._extract_passages_with_llm(
                            content, keywords, literature, passages_per_literature
                        )
                    else:
                        # 使用备用方法
                        passages = self._extract_passages_fallback(
                            content, keywords, literature, passages_per_literature
                        )
                    
                    relevant_passages.extend(passages)
                    
                except Exception as e:
                    self.logger.warning(f"处理文献段落提取失败 {literature.get('title', 'unknown')}: {e}")
                    continue
            
            # 按综合评分排序（相关性 + 文献匹配度）
            relevant_passages.sort(
                key=lambda x: (x['relevance_score'] + x.get('combined_score', 0) * 0.1), 
                reverse=True
            )
            
            # 限制返回数量
            max_return = min(20, len(relevant_passages))
            relevant_passages = relevant_passages[:max_return]
            
            self.logger.info(f"成功提取 {len(relevant_passages)} 个相关段落")
            return relevant_passages
            
        except Exception as e:
            self.logger.error(f"提取相关段落失败: {e}")
            raise
    
    def _extract_passages_with_llm(self, content: str, keywords: List[str], 
                                 literature: Dict[str, Any], max_passages: int = 2) -> List[Dict[str, Any]]:
        """
        使用LLM智能提取相关段落
        
        Args:
            content: 文献内容
            keywords: 关键词列表
            literature: 文献元信息
            max_passages: 最多提取段落数
            
        Returns:
            段落信息列表
        """
        try:
            # 控制上下文长度：摘要 + 前2000字符内容
            abstract = literature.get('abstract', '')
            content_preview = content[:2000] if len(content) > 2000 else content
            
            if abstract:
                context_text = f"摘要：{abstract}\n\n正文预览：{content_preview}"
            else:
                context_text = content_preview
            
            # 构建段落提取提示词
            prompt = f"""
请从以下文献中提取与关键词最相关的{max_passages}个段落：

关键词：{', '.join(keywords[:10])}

文献标题：{literature.get('title', '未知')}

文献内容：
{context_text}

要求：
1. 选择与关键词最相关的段落
2. 每个段落80-200字
3. 保持段落的完整性和上下文
4. 按相关性排序
5. 确保段落内容完整，不要截断句子

请以以下JSON格式返回：
{{
    "passages": [
        {{
            "text": "段落内容",
            "relevance_score": 0.9,
            "related_keywords": ["相关关键词"]
        }}
    ]
}}

只返回JSON，不要其他内容。
            """
            
            response = self.llm_service.chat(
                prompt,
                "你是一个专业的文献分析助手，擅长从学术文献中提取相关段落。"
            )
            
            # 解析响应
            passages_data = self.llm_service.parse_json_response(response)
            
            passages = []
            for passage in passages_data.get('passages', []):
                passage_info = {
                    'text': passage['text'],
                    'source_title': literature.get('title', '未知'),
                    'source_authors': literature.get('authors', []),
                    'source_year': literature.get('year', ''),
                    'relevance_score': passage.get('relevance_score', 0.5),
                    'related_keywords': passage.get('related_keywords', []),
                    'citation': self._generate_citation(literature),
                    'source_file': literature.get('file_path', ''),
                    'combined_score': literature.get('combined_score', 0)
                }
                passages.append(passage_info)
            
            return passages
            
        except Exception as e:
            self.logger.warning(f"LLM段落提取失败，使用备用方法: {e}")
            return self._extract_passages_fallback(content, keywords, literature, max_passages)
    
    def _extract_passages_fallback(self, content: str, keywords: List[str], 
                                 literature: Dict[str, Any], max_passages: int = 2) -> List[Dict[str, Any]]:
        """
        备用段落提取方法（不使用LLM）
        
        Args:
            content: 文献内容
            keywords: 关键词列表
            literature: 文献元信息
            max_passages: 最多提取段落数
            
        Returns:
            段落信息列表
        """
        passages = []
        sentences = re.split(r'[。.!?]', content)
        
        # 计算每个句子的关键词匹配度
        sentence_scores = []
        for i, sentence in enumerate(sentences):
            if len(sentence.strip()) < 10:  # 跳过太短的句子
                continue
            
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in sentence.lower():
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                sentence_scores.append({
                    'sentence': sentence.strip(),
                    'score': score,
                    'matched_keywords': matched_keywords,
                    'index': i
                })
        
        # 按匹配度排序
        sentence_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # 提取最相关的段落
        for i, item in enumerate(sentence_scores[:max_passages]):
            # 尝试包含上下文（前后句子）
            start_idx = max(0, item['index'] - 1)
            end_idx = min(len(sentences), item['index'] + 2)
            context_sentences = sentences[start_idx:end_idx]
            
            passage_text = '。'.join([s.strip() for s in context_sentences if s.strip()])
            
            passage_info = {
                'text': passage_text[:300],  # 限制长度
                'source_title': literature.get('title', '未知'),
                'source_authors': literature.get('authors', []),
                'source_year': literature.get('year', ''),
                'relevance_score': min(1.0, item['score'] / len(keywords)),
                'related_keywords': item['matched_keywords'][:5],
                'citation': self._generate_citation(literature),
                'source_file': literature.get('file_path', ''),
                'combined_score': literature.get('combined_score', 0)
            }
            passages.append(passage_info)
        
        return passages
    
    def preprocess_literature_metadata(self, literature_dir: str, force_update: bool = False) -> None:
        """
        批量预处理文献目录中的所有文献元信息
        
        Args:
            literature_dir: 文献目录路径
            force_update: 是否强制更新已存在的元数据
        """
        self.logger.info(f"开始批量预处理文献元信息: {literature_dir}")
        
        try:
            literature_path = Path(literature_dir)
            if not literature_path.exists():
                self.logger.error(f"文献目录不存在: {literature_dir}")
                return
            
            literature_files = get_supported_files(literature_dir, self.supported_formats)
            processed_count = 0
            
            for file_path in literature_files:
                try:
                    metadata_file = self.metadata_cache_dir / (Path(file_path).stem + "_metadata.json")
                    
                    # 如果已存在且不强制更新，跳过
                    if metadata_file.exists() and not force_update:
                        continue
                    
                    # 使用快速提取方法
                    metadata = self.extract_metadata_fast(file_path)
                    
                    # 保存元信息
                    save_json(metadata, str(metadata_file))
                    
                    processed_count += 1
                    
                    if processed_count % 10 == 0:
                        self.logger.info(f"已处理 {processed_count} 篇文献...")
                
                except Exception as e:
                    self.logger.warning(f"处理文献失败 {file_path}: {e}")
                    continue
            
            self.logger.info(f"批量预处理完成，共处理 {processed_count} 篇文献")
            
        except Exception as e:
            self.logger.error(f"批量预处理失败: {e}")
            raise
    
    def _generate_citation(self, literature: Dict[str, Any]) -> str:
        """
        生成文献引用格式
        
        Args:
            literature: 文献元信息
            
        Returns:
            格式化的引用字符串
        """
        authors = literature.get('authors', [])
        title = literature.get('title', '未知标题')
        year = literature.get('year', '')
        
        if authors:
            author_str = ', '.join(authors[:3])  # 最多显示3个作者
            if len(authors) > 3:
                author_str += ' et al.'
        else:
            author_str = '未知作者'
        
        return f"{author_str} ({year}). {title}"
    
    def _get_or_extract_metadata(self, file_path: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        获取或提取文献元数据
        
        Args:
            file_path: 文献文件路径
            use_cache: 是否使用缓存
            
        Returns:
            文献元数据或None
        """
        try:
            metadata_file = self.metadata_cache_dir / (Path(file_path).stem + "_metadata.json")
            
            # 尝试从缓存加载
            if use_cache and metadata_file.exists():
                try:
                    metadata = load_json(str(metadata_file))
                    if metadata and 'title' in metadata:
                        return metadata
                except Exception:
                    pass  # 缓存损坏，重新提取
            
            # 提取新的元数据
            metadata = self.extract_metadata_fast(file_path)
            
            # 保存到缓存
            if metadata:
                try:
                    save_json(metadata, str(metadata_file))
                except Exception as e:
                    self.logger.warning(f"保存元数据缓存失败: {e}")
            
            return metadata
            
        except Exception as e:
            self.logger.warning(f"获取元数据失败 {file_path}: {e}")
            return None
    
    def _find_matched_keywords(self, keywords: List[str], content: str) -> List[str]:
        """
        查找在内容中匹配的关键词
        
        Args:
            keywords: 关键词列表
            content: 文档内容
            
        Returns:
            匹配的关键词列表
        """
        matched = []
        content_lower = content.lower()
        
        for keyword in keywords:
            if keyword.lower() in content_lower:
                matched.append(keyword)
        
        return matched