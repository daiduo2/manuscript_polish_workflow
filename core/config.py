#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责系统配置的集中管理
"""

import os
from typing import Dict, Any
from pathlib import Path


class Config:
    """配置管理类"""

    def __init__(self):
        self.settings = self._load_default_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            # LLM配置
            'llm': {
                'api_key': os.getenv('QWEN_API_KEY') or os.getenv('DASHSCOPE_API_KEY', ''),
                'model': 'qwen-plus',
                'temperature': 0.7,
                'max_tokens': 2000
            },

            # 路径配置
            'paths': {
                'base_dir': Path(__file__).parent.parent,
                'output_dir': Path(__file__).parent.parent / 'output',
                'metadata_dir': Path(__file__).parent.parent / 'output' / 'literature_metadata',
                'log_file': Path(__file__).parent.parent / 'manuscript_polish_workflow.log'
            },

            # 工作流配置
            'workflow': {
                'max_literature_count': 50,
                'passages_per_literature': 2,
                'max_references': 10,
                'context_length_limit': 3000,
                'manuscript_preview_limit': 1500
            },

            # 搜索配置
            'search': {
                'supported_formats': ['.txt', '.md', '.pdf'],
                'tfidf_weight': 0.5,
                'max_keywords': 30
            },

            # 输出配置
            'output': {
                'format': 'markdown',
                'include_citations': True,
                'include_metadata': True
            }
        }

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，如 'llm.api_key'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key_path: 配置键路径
            value: 配置值
        """
        keys = key_path.split('.')
        current = self.settings
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def update_from_env(self) -> None:
        """
        从环境变量更新配置
        """
        # 更新API密钥
        api_key = os.getenv('QWEN_API_KEY') or os.getenv('DASHSCOPE_API_KEY')
        if api_key:
            self.set('llm.api_key', api_key)
        
        # 更新模型名称
        model = os.getenv('QWEN_MODEL')
        if model:
            self.set('llm.model', model)

    @property
    def output_dir(self) -> Path:
        """获取输出目录路径"""
        return self.get('paths.output_dir')
    
    @property
    def metadata_dir(self) -> Path:
        """获取元数据目录路径"""
        return self.get('paths.metadata_dir')
    
    @property
    def log_file(self) -> Path:
        """获取日志文件路径"""
        return self.get('paths.log_file')


# 全局配置实例
config = Config()
config.update_from_env()  # 从环境变量更新配置