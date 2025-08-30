#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文献数据模型
定义文献相关的实体类和数据结构
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class LiteratureMetadata:
    """文献元数据"""

    title: str = ""
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    keywords: List[str] = field(default_factory=list)
    year: str = ""
    file_path: str = ""
    extraction_time: str = ""
    extraction_method: str = "unknown"

    # 匹配相关
    match_score: float = 0.0
    tfidf_score: float = 0.0
    combined_score: float = 0.0
    matched_keywords: List[str] = field(default_factory=list)
    title_matches: int = 0
    abstract_matches: int = 0
    total_keywords_checked: int = 0

    # 匹配详情
    match_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'keywords': self.keywords,
            'year': self.year,
            'file_path': self.file_path,
            'extraction_time': self.extraction_time,
            'extraction_method': self.extraction_method,
            'match_score': self.match_score,
            'tfidf_score': self.tfidf_score,
            'combined_score': self.combined_score,
            'matched_keywords': self.matched_keywords,
            'title_matches': self.title_matches,
            'abstract_matches': self.abstract_matches,
            'total_keywords_checked': self.total_keywords_checked,
            'match_details': self.match_details
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LiteratureMetadata':
        """从字典创建实例"""
        return cls(**data)


@dataclass
class Passage:
    """文献段落"""

    text: str = ""
    source_title: str = ""
    source_authors: List[str] = field(default_factory=list)
    source_year: str = ""
    relevance_score: float = 0.0
    related_keywords: List[str] = field(default_factory=list)
    citation: str = ""
    source_file: str = ""
    combined_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'text': self.text,
            'source_title': self.source_title,
            'source_authors': self.source_authors,
            'source_year': self.source_year,
            'relevance_score': self.relevance_score,
            'related_keywords': self.related_keywords,
            'citation': self.citation,
            'source_file': self.source_file,
            'combined_score': self.combined_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Passage':
        """从字典创建实例"""
        return cls(**data)


@dataclass
class WorkflowResult:
    """工作流执行结果"""

    timestamp: str = ""
    input_manuscript: str = ""
    literature_directory: str = ""
    generated_keywords: List[str] = field(default_factory=list)
    matched_literature_count: int = 0
    relevant_passages_count: int = 0
    output_manuscript: str = ""
    preprocessing_enabled: bool = False
    matched_literature: List[Dict[str, Any]] = field(default_factory=list)
    relevant_passages: List[Dict[str, Any]] = field(default_factory=list)
    optimized_content: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp,
            'input_manuscript': self.input_manuscript,
            'literature_directory': self.literature_directory,
            'generated_keywords': self.generated_keywords,
            'matched_literature_count': self.matched_literature_count,
            'relevant_passages_count': self.relevant_passages_count,
            'output_manuscript': self.output_manuscript,
            'preprocessing_enabled': self.preprocessing_enabled,
            'matched_literature': self.matched_literature,
            'relevant_passages': self.relevant_passages,
            'optimized_content': self.optimized_content
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowResult':
        """从字典创建实例"""
        return cls(**data)