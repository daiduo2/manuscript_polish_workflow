#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文献辅助写作工作流 - 主入口文件

这个模块提供了文献辅助写作工作流的主要接口，
用户可以通过这个模块来执行完整的工作流程。
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 修复相对导入问题
import os
os.chdir(project_root)

try:
    from core.orchestrator import WorkflowOrchestrator
    from core.utils.config import Config
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import importlib.util
    
    # 动态导入 Config
    config_spec = importlib.util.spec_from_file_location(
        "config", project_root / "core" / "utils" / "config.py"
    )
    config_module = importlib.util.module_from_spec(config_spec)
    config_spec.loader.exec_module(config_module)
    Config = config_module.Config
    
    # 对于 WorkflowOrchestrator，我们需要先处理其依赖
    print("警告: 使用简化模式运行，某些功能可能受限")
    WorkflowOrchestrator = None


def create_workflow():
    """
    创建工作流实例
    
    Returns:
        工作流编排器实例或None（如果在简化模式下）
    """
    if WorkflowOrchestrator is None:
        print("错误: 无法加载工作流编排器，请检查依赖是否正确安装")
        return None
    
    try:
        config = Config()
        orchestrator = WorkflowOrchestrator(config)
        return orchestrator
    except Exception as e:
        print(f"创建工作流实例失败: {e}")
        return None


def run_workflow_from_file(
    manuscript_path: str, 
    literature_dir: str,
    preprocess: bool = False
) -> Dict[str, Any]:
    """
    从文件运行工作流
    
    Args:
        manuscript_path: 手稿文件路径
        literature_dir: 文献目录路径
        preprocess: 是否进行预处理
    
    Returns:
        工作流执行结果
    """
    orchestrator = create_workflow()
    if orchestrator is None:
        return {"error": "无法创建工作流实例"}
    
    try:
        # 检查文件是否存在
        manuscript_file = Path(manuscript_path)
        if not manuscript_file.exists():
            return {"error": f"手稿文件不存在: {manuscript_path}"}
        
        literature_path = Path(literature_dir)
        if not literature_path.exists():
            return {"error": f"文献目录不存在: {literature_dir}"}
        
        # 执行工作流
        result = orchestrator.run_workflow(
            manuscript_path=manuscript_path,
            literature_dir=literature_dir,
            preprocess=preprocess
        )
        
        return result
        
    except Exception as e:
        return {"error": f"工作流执行失败: {e}"}


def run_workflow_from_content(
    manuscript_content: str,
    literature_dir: str,
    manuscript_title: str = "untitled",
    preprocess: bool = False
) -> Dict[str, Any]:
    """
    从内容运行工作流
    
    Args:
        manuscript_content: 手稿内容
        literature_dir: 文献目录路径
        manuscript_title: 手稿标题
        preprocess: 是否进行预处理
    
    Returns:
        工作流执行结果
    """
    orchestrator = create_workflow()
    if orchestrator is None:
        return {"error": "无法创建工作流实例"}
    
    try:
        # 检查文献目录是否存在
        literature_path = Path(literature_dir)
        if not literature_path.exists():
            return {"error": f"文献目录不存在: {literature_dir}"}
        
        # 执行工作流
        result = orchestrator.run_workflow_from_content(
            manuscript_content=manuscript_content,
            literature_dir=literature_dir,
            manuscript_title=manuscript_title,
            preprocess=preprocess
        )
        
        return result
        
    except Exception as e:
        return {"error": f"工作流执行失败: {e}"}


def main():
    """
    主函数 - 命令行接口
    """
    parser = argparse.ArgumentParser(
        description="文献辅助写作工作流",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py --manuscript manuscript.md --literature ./literature/
  python main.py --manuscript manuscript.md --literature ./literature/ --preprocess
        """
    )
    
    parser.add_argument(
        "--manuscript", "-m",
        required=True,
        help="手稿文件路径"
    )
    
    parser.add_argument(
        "--literature", "-l",
        required=True,
        help="文献目录路径"
    )
    
    parser.add_argument(
        "--preprocess", "-p",
        action="store_true",
        help="启用预处理"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"手稿文件: {args.manuscript}")
        print(f"文献目录: {args.literature}")
        print(f"预处理: {args.preprocess}")
        print("-" * 50)
    
    # 运行工作流
    result = run_workflow_from_file(
        manuscript_path=args.manuscript,
        literature_dir=args.literature,
        preprocess=args.preprocess
    )
    
    # 输出结果
    if "error" in result:
        print(f"错误: {result['error']}")
        sys.exit(1)
    else:
        print("工作流执行成功!")
        if args.verbose:
            print(f"结果: {result}")
        
        # 显示输出文件信息
        if "output_files" in result:
            print("\n生成的文件:")
            for file_path in result["output_files"]:
                print(f"  - {file_path}")


if __name__ == "__main__":
    main()