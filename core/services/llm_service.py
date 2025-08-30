#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM服务模块
负责与大语言模型的交互，包括文本生成、关键词提取、元数据提取等功能
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
import json
import re
from datetime import datetime

# 导入具体的LLM客户端
try:
    from ..clients.qwen_client import QwenClient
except ImportError:
    from core.clients.qwen_client import QwenClient


class LLMService(ABC):
    """
    LLM服务抽象基类
    定义了与大语言模型交互的标准接口
    """
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        与LLM进行对话
        
        Args:
            messages: 对话消息列表
            **kwargs: 其他参数
            
        Returns:
            str: LLM的回复
        """
        pass
    
    @abstractmethod
    def generate_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        从文本中生成关键词
        
        Args:
            text: 输入文本
            max_keywords: 最大关键词数量
            
        Returns:
            List[str]: 关键词列表
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        从文献内容中提取元数据
        
        Args:
            content: 文献内容
            
        Returns:
            Dict[str, Any]: 提取的元数据
        """
        pass
    
    @abstractmethod
    def optimize_manuscript(self, manuscript_content: str, references: List[Dict[str, Any]], max_references: int = 10) -> str:
        """
        优化手稿内容
        
        Args:
            manuscript_content: 原始手稿内容
            references: 参考文献列表
            max_references: 最大参考文献数量
            
        Returns:
            str: 优化后的手稿内容
        """
        pass


class QwenService(LLMService):
    """
    通义千问LLM服务实现
    """
    
    def __init__(self, api_key: str, model: str = "qwen-plus", max_retries: int = 3, timeout: int = 60):
        """
        初始化通义千问服务
        
        Args:
            api_key: API密钥
            model: 模型名称
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
        """
        self.client = QwenClient(
            api_key=api_key,
            model=model,
            max_retries=max_retries,
            timeout=timeout
        )
        self.logger = logging.getLogger(__name__)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        与通义千问进行对话
        
        Args:
            messages: 对话消息列表
            **kwargs: 其他参数
            
        Returns:
            str: LLM的回复
        """
        try:
            response = self.client.chat(messages, **kwargs)
            return response
        except Exception as e:
            self.logger.error(f"LLM对话失败: {e}")
            raise
    
    def generate_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        从文本中生成关键词
        
        Args:
            text: 输入文本
            max_keywords: 最大关键词数量
            
        Returns:
            List[str]: 关键词列表
        """
        try:
            # 限制输入文本长度
            if len(text) > 3000:
                text = text[:3000] + "..."
            
            prompt = f"""
请从以下文本中提取{max_keywords}个最重要的关键词，用于文献检索。
要求：
1. 关键词应该是学术术语或专业概念
2. 优先选择名词和名词短语
3. 避免过于通用的词汇
4. 每个关键词用逗号分隔
5. 只返回关键词，不要其他解释

文本内容：
{text}

关键词：
"""
            
            messages = [{"role": "user", "content": prompt}]
            response = self.chat(messages)
            
            # 解析关键词
            keywords = [kw.strip() for kw in response.split(',') if kw.strip()]
            keywords = [kw for kw in keywords if len(kw) > 1 and not kw.isdigit()]
            
            return keywords[:max_keywords]
            
        except Exception as e:
            self.logger.error(f"生成关键词失败: {e}")
            # 返回基于文本频率的备用关键词
            return self._extract_keywords_fallback(text, max_keywords)
    
    def _extract_keywords_fallback(self, text: str, max_keywords: int) -> List[str]:
        """
        备用关键词提取方法（基于词频）
        
        Args:
            text: 输入文本
            max_keywords: 最大关键词数量
            
        Returns:
            List[str]: 关键词列表
        """
        # 简单的词频统计
        words = re.findall(r'\b[a-zA-Z\u4e00-\u9fff]{2,}\b', text.lower())
        word_freq = {}
        for word in words:
            if len(word) > 2:  # 过滤短词
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序并返回前N个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        从文献内容中提取元数据
        
        Args:
            content: 文献内容
            
        Returns:
            Dict[str, Any]: 提取的元数据
        """
        try:
            # 限制输入长度
            if len(content) > 2000:
                content = content[:2000] + "..."
            
            prompt = f"""
请从以下文献内容中提取元数据信息，以JSON格式返回。
要求的字段：
- title: 文献标题
- authors: 作者列表（数组）
- abstract: 摘要
- keywords: 关键词列表（数组）
- year: 发表年份

如果某个字段无法提取，请设为空字符串或空数组。
只返回JSON，不要其他解释。

文献内容：
{content}
"""
            
            messages = [{"role": "user", "content": prompt}]
            response = self.chat(messages)
            
            # 尝试解析JSON
            try:
                metadata = json.loads(response)
                return metadata
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试从响应中提取信息
                return self._parse_metadata_from_text(response)
                
        except Exception as e:
            self.logger.error(f"提取元数据失败: {e}")
            return {}
    
    def _parse_metadata_from_text(self, text: str) -> Dict[str, Any]:
        """
        从文本中解析元数据（备用方法）
        
        Args:
            text: 包含元数据的文本
            
        Returns:
            Dict[str, Any]: 解析的元数据
        """
        metadata = {
            "title": "",
            "authors": [],
            "abstract": "",
            "keywords": [],
            "year": ""
        }
        
        # 简单的正则表达式提取
        title_match = re.search(r'title["\s]*:["\s]*([^"\n]+)', text, re.IGNORECASE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()
        
        year_match = re.search(r'year["\s]*:["\s]*(\d{4})', text, re.IGNORECASE)
        if year_match:
            metadata["year"] = year_match.group(1)
        
        return metadata
    
    def optimize_manuscript(self, manuscript_content: str, references: List[Dict[str, Any]], max_references: int = 10) -> str:
        """
        优化手稿内容
        
        Args:
            manuscript_content: 原始手稿内容
            references: 参考文献列表
            max_references: 最大参考文献数量
            
        Returns:
            str: 优化后的手稿内容
        """
        try:
            # 限制手稿长度
            if len(manuscript_content) > 2000:
                manuscript_preview = manuscript_content[:2000] + "..."
            else:
                manuscript_preview = manuscript_content
            
            # 准备参考文献信息
            ref_info = []
            for i, ref in enumerate(references[:max_references]):
                ref_summary = f"{i+1}. {ref.get('title', 'Unknown Title')}"
                if ref.get('authors'):
                    ref_summary += f" - {', '.join(ref['authors'][:2])}"
                if ref.get('year'):
                    ref_summary += f" ({ref['year']})"
                if ref.get('abstract'):
                    ref_summary += f"\n   摘要: {ref['abstract'][:200]}..."
                ref_info.append(ref_summary)
            
            references_text = "\n".join(ref_info)
            
            prompt = f"""
请根据提供的参考文献，优化以下学术手稿。要求：

1. 保持原文的核心观点和结构
2. 根据参考文献补充相关的理论支撑和实证证据
3. 在适当位置添加引用（格式：[作者, 年份]）
4. 改进表达的学术性和准确性
5. 确保逻辑清晰，论证充分
6. 保持中文表达的流畅性

原始手稿：
{manuscript_preview}

参考文献：
{references_text}

优化后的手稿：
"""
            
            messages = [{"role": "user", "content": prompt}]
            response = self.chat(messages)
            
            return response
            
        except Exception as e:
            self.logger.error(f"优化手稿失败: {e}")
            return manuscript_content  # 返回原始内容


def create_llm_service(service_type: str = "qwen", **kwargs) -> LLMService:
    """
    创建LLM服务实例
    
    Args:
        service_type: 服务类型
        **kwargs: 服务配置参数
        
    Returns:
        LLMService: LLM服务实例
    """
    if service_type.lower() == "qwen":
        return QwenService(**kwargs)
    else:
        raise ValueError(f"不支持的LLM服务类型: {service_type}")
