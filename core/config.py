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

            # 日志配置
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }

    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的路径"""
        keys = key_path.split('.')
        value = self.settings

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any) -> None:
        """设置配置值"""
        keys = key_path.split('.')
        config = self.settings

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def update_from_env(self) -> None:
        """从环境变量更新配置"""
        # LLM配置
        llm_key = os.getenv('QWEN_API_KEY') or os.getenv('DASHSCOPE_API_KEY')
        if llm_key:
            self.set('llm.api_key', llm_key)

        # 路径配置
        if os.getenv('WORKFLOW_OUTPUT_DIR'):
            self.set('paths.output_dir', Path(os.getenv('WORKFLOW_OUTPUT_DIR')))

        # 工作流配置
        if os.getenv('MAX_LITERATURE_COUNT'):
            self.set('workflow.max_literature_count', int(os.getenv('MAX_LITERATURE_COUNT')))


# 全局配置实例
config = Config()