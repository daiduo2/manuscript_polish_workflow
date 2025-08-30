#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文献辅助写作工作流 - 模块主入口

这个模块作为包的主入口，支持 python -m core.main 方式运行
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# 确保能够导入相对模块
if __name__ == '__main__':
    # 添加父目录到路径
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))

from .orchestrator import WorkflowOrchestrator
from .config import config


def create_workflow() -> WorkflowOrchestrator:
    """
    创建工作流实例
    
    Returns:
        工作流编排器实例
    """
    # 从环境变量更新配置
    config.update_from_env()
    
    # 验证配置
    if not config.get('llm.api_key'):
        raise ValueError("未设置 LLM API Key，请设置 QWEN_API_KEY 或 DASHSCOPE_API_KEY 环境变量")
    
    return WorkflowOrchestrator(config)


def run_workflow_from_file(
    manuscript_path: str, 
    literature_dir: str,
    preprocess: bool = False
) -> Dict[str, Any]:
    """
    从文件执行工作流
    
    Args:
        manuscript_path: 手稿文件路径
        literature_dir: 文献目录路径
        preprocess: 是否预处理文献元数据
        
    Returns:
        工作流执行结果
    """
    workflow = create_workflow()
    
    if preprocess:
        # 读取手稿内容
        with open(manuscript_path, 'r', encoding='utf-8') as f:
            manuscript_content = f.read()
        
        manuscript_title = Path(manuscript_path).stem
        
        return workflow.run_workflow_with_preprocessing(
            manuscript_content=manuscript_content,
            literature_dir=literature_dir,
            manuscript_title=manuscript_title,
            preprocess_metadata=True
        )
    else:
        return workflow.run_workflow(
            manuscript_path=manuscript_path,
            literature_dir=literature_dir
        )


def run_workflow_from_content(
    manuscript_content: str,
    literature_dir: str,
    manuscript_title: str = "untitled",
    preprocess: bool = False
) -> Dict[str, Any]:
    """
    从内容执行工作流
    
    Args:
        manuscript_content: 手稿内容
        literature_dir: 文献目录路径
        manuscript_title: 手稿标题
        preprocess: 是否预处理文献元数据
        
    Returns:
        工作流执行结果
    """
    workflow = create_workflow()
    
    if preprocess:
        return workflow.run_workflow_with_preprocessing(
            manuscript_content=manuscript_content,
            literature_dir=literature_dir,
            manuscript_title=manuscript_title,
            preprocess_metadata=True
        )
    else:
        return workflow.run_workflow_with_content(
            manuscript_content=manuscript_content,
            literature_dir=literature_dir,
            manuscript_title=manuscript_title
        )


def main():
    """
    主函数 - 处理命令行参数并执行工作流
    """
    parser = argparse.ArgumentParser(
        description='文献辅助写作工作流',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python -m core.main --manuscript manuscript.md --literature ./papers
  python -m core.main --manuscript manuscript.md --literature ./papers --preprocess
        """
    )
    
    parser.add_argument(
        '--manuscript', '-m',
        required=True,
        help='手稿文件路径'
    )
    
    parser.add_argument(
        '--literature', '-l',
        required=True,
        help='文献目录路径'
    )
    
    parser.add_argument(
        '--preprocess', '-p',
        action='store_true',
        help='是否预处理文献元数据'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )
    
    args = parser.parse_args()
    
    try:
        print("=== 文献辅助写作工作流 ===")
        print(f"手稿文件: {args.manuscript}")
        print(f"文献目录: {args.literature}")
        print(f"预处理模式: {'启用' if args.preprocess else '禁用'}")
        print()
        
        # 检查文件是否存在
        if not Path(args.manuscript).exists():
            print(f"错误: 手稿文件不存在: {args.manuscript}")
            return 1
            
        if not Path(args.literature).exists():
            print(f"错误: 文献目录不存在: {args.literature}")
            return 1
        
        # 执行工作流
        result = run_workflow_from_file(
            manuscript_path=args.manuscript,
            literature_dir=args.literature,
            preprocess=args.preprocess
        )
        
        # 输出结果
        print("=== 执行结果 ===")
        if 'error' in result:
            print(f"执行失败: {result['error']}")
            return 1
        else:
            print(f"生成关键词数量: {len(result.get('keywords', []))}")
            print(f"匹配文献数量: {len(result.get('matched_literature', []))}")
            print(f"召回段落数量: {len(result.get('relevant_passages', []))}")
            
            if 'optimized_manuscript' in result:
                print(f"优化后手稿长度: {len(result['optimized_manuscript'])} 字符")
                
                # 保存优化后的手稿
                output_path = Path(args.manuscript).with_suffix('.optimized.md')
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result['optimized_manuscript'])
                print(f"优化后手稿已保存到: {output_path}")
            else:
                print("优化后手稿: N/A")
        
        print("\n工作流执行成功！")
        return 0
        
    except Exception as e:
        print(f"执行失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())