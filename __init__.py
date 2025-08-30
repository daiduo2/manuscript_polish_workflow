#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manuscript Polish Workflow - 手稿润色工作流系统

一个基于大语言模型的手稿润色工作流系统，专门用于学术论文和文献的智能化处理与优化。
"""

__version__ = "1.0.0"
__author__ = "Manuscript Polish Workflow Team"
__email__ = "support@manuscript-polish.com"
__description__ = "A workflow system for manuscript polishing and literature assistance"

# 导出主要接口
from .main import run_workflow_from_file, run_workflow_from_content, create_workflow

__all__ = [
    "run_workflow_from_file",
    "run_workflow_from_content", 
    "create_workflow",
    "__version__",
    "__author__",
    "__email__",
    "__description__"
]