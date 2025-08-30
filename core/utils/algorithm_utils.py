#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
算法工具类
"""

import math
from collections import Counter
from typing import List, Dict, Set, Tuple


class AlgorithmUtils:
    """算法工具类"""
    
    @staticmethod
    def expand_keywords_with_synonyms(keywords: List[str], general_synonyms: Dict[str, List[str]]) -> List[str]:
        """基于通用同义词映射扩展关键词"""
        expanded_keywords = set(keywords)
        
        # 扩展关键词
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in general_synonyms:
                expanded_keywords.update(general_synonyms[keyword_lower])
        
        return list(expanded_keywords)
    
    @staticmethod
    def calculate_relevance_score(keywords: List[str], document_text: str, all_documents: List[str]) -> float:
        """基于TF-IDF计算相关性评分"""
        import re
        
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
    
    @staticmethod
    def calculate_keyword_match_score(keywords: List[str], text: str) -> float:
        """计算关键词匹配分数"""
        import re
        
        if not keywords or not text:
            return 0.0
        
        text_lower = text.lower()
        matched_keywords = 0
        
        for keyword in keywords:
            # 使用正则表达式进行单词边界匹配
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_lower):
                matched_keywords += 1
        
        return matched_keywords / len(keywords) if keywords else 0.0
    
    @staticmethod
    def get_general_synonyms() -> Dict[str, List[str]]:
        """获取通用同义词映射"""
        return {
            'research': ['study', 'investigation', 'analysis', 'examination'],
            'method': ['approach', 'technique', 'methodology', 'procedure'],
            'result': ['outcome', 'finding', 'conclusion', 'output'],
            'analysis': ['examination', 'evaluation', 'assessment', 'study'],
            'data': ['information', 'dataset', 'statistics', 'evidence'],
            'model': ['framework', 'system', 'structure', 'design'],
            'algorithm': ['method', 'procedure', 'technique', 'approach'],
            'performance': ['efficiency', 'effectiveness', 'capability', 'quality'],
            'evaluation': ['assessment', 'analysis', 'examination', 'review'],
            'experiment': ['test', 'trial', 'study', 'investigation'],
            'application': ['use', 'implementation', 'deployment', 'utilization'],
            'development': ['creation', 'construction', 'building', 'design'],
            'improvement': ['enhancement', 'optimization', 'refinement', 'upgrade'],
            'comparison': ['contrast', 'evaluation', 'analysis', 'assessment'],
            'validation': ['verification', 'confirmation', 'testing', 'proof']
        }