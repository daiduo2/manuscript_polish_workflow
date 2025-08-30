#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本处理工具函数
"""

import re
import math
from collections import Counter
from typing import List, Set, Dict, Tuple, Any


def clean_text(text: str) -> str:
    """清理文本，移除多余的空格和换行"""
    if not text:
        return ""

    # 移除多余的空格
    text = re.sub(r'\s+', ' ', text)
    # 移除行首行尾空格
    text = text.strip()
    return text


def split_sentences(text: str) -> List[str]:
    """将文本分割成句子"""
    # 使用正则表达式分割句子
    sentences = re.split(r'[。.!?]', text)
    # 过滤空句子并清理
    return [clean_text(s) for s in sentences if clean_text(s)]


def extract_keywords(text: str, max_keywords: int = 20) -> List[str]:
    """从文本中提取关键词（简单实现）"""
    # 移除标点符号
    text = re.sub(r'[^\w\s]', '', text.lower())
    # 分词
    words = re.findall(r'\b\w+\b', text)
    # 统计词频
    word_counts = Counter(words)
    # 过滤停用词（简单版本）
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    filtered_words = {word: count for word, count in word_counts.items()
                     if word not in stop_words and len(word) > 2}
    # 返回最常见的关键词
    return [word for word, _ in Counter(filtered_words).most_common(max_keywords)]


def calculate_tfidf(keywords: List[str], document_text: str, all_documents: List[str]) -> float:
    """计算TF-IDF分数"""
    # 预处理文档文本
    doc_words = re.findall(r'\b\w+\b', document_text.lower())
    doc_word_count = Counter(doc_words)
    total_words = len(doc_words)

    if total_words == 0:
        return 0.0

    tfidf_score = 0.0

    for keyword in keywords:
        keyword_words = re.findall(r'\b\w+\b', keyword.lower())

        for word in keyword_words:
            # 计算TF (Term Frequency)
            tf = doc_word_count.get(word, 0) / total_words

            if tf > 0:
                # 计算IDF (Inverse Document Frequency)
                docs_containing_word = sum(1 for doc in all_documents if word in doc.lower())
                if docs_containing_word > 0:
                    idf = math.log(len(all_documents) / docs_containing_word)
                    tfidf_score += tf * idf

    return tfidf_score


def expand_keywords(keywords: List[str], general_synonyms: Dict[str, List[str]]) -> List[str]:
    """扩展关键词"""
    expanded_keywords = set(keywords)

    # 扩展关键词
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in general_synonyms:
            expanded_keywords.update(general_synonyms[keyword_lower])

    return list(expanded_keywords)


def generate_citation(literature: Dict[str, Any]) -> str:
    """生成文献引用格式"""
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