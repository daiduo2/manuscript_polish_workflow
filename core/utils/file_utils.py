#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理工具函数
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional


def ensure_directory(path: Path) -> None:
    """确保目录存在，如果不存在则创建"""
    path.mkdir(parents=True, exist_ok=True)


def save_json(data: Dict[str, Any], file_path: Path, indent: int = 2) -> None:
    """保存数据为JSON文件"""
    ensure_directory(file_path.parent)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """从JSON文件加载数据"""
    if not file_path.exists():
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def get_supported_files(directory, extensions: List[str]) -> List[Path]:
    """获取指定目录下支持的文件"""
    # 确保 directory 是 Path 对象
    if isinstance(directory, str):
        directory = Path(directory)
    
    supported_files = []
    if not directory.exists():
        return supported_files

    for ext in extensions:
        supported_files.extend(directory.rglob(f"*{ext}"))

    return sorted(supported_files)


def read_file_content(file_path, encoding: str = 'utf-8') -> Optional[str]:
    """读取文件内容"""
    # 确保 file_path 是 Path 对象或字符串
    if isinstance(file_path, Path):
        file_path = str(file_path)
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except (UnicodeDecodeError, FileNotFoundError):
        return None


def write_file_content(content: str, file_path: Path, encoding: str = 'utf-8') -> None:
    """写入文件内容"""
    ensure_directory(file_path.parent)
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(content)


def generate_timestamp_filename(prefix: str, extension: str) -> str:
    """生成带时间戳的文件名"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"