from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
import json
from datetime import datetime
import sys
import os

# 确保能够导入模块
if __name__ == '__main__' or 'core.orchestrator' in sys.modules:
    # 添加项目根目录到路径
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

try:
    from .services.llm_service import LLMService
    from .services.literature_service import LiteratureService
    from .utils.config import Config
except ImportError:
    # 备用导入方式
    from core.services.llm_service import LLMService
    from core.services.literature_service import LiteratureService
    from core.utils.config import Config


class WorkflowOrchestrator:
    """
    工作流编排器 - 协调各个服务完成完整的文献辅助写作流程
    """
    
    def __init__(self, config: Config):
        """
        初始化工作流编排器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化各个服务
        self.llm_service = self._create_llm_service()
        self.literature_service = LiteratureService(llm_service=self.llm_service)
        
        # 确保输出目录存在
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_llm_service(self) -> LLMService:
        """
        创建LLM服务实例
        
        Returns:
            LLMService: LLM服务实例
        """
        try:
            from .services.llm_service import QwenService
            return QwenService(
                api_key=self.config.get('llm.api_key'),
                model=self.config.get('llm.model', 'qwen-plus'),
                max_retries=3,
                timeout=60
            )
        except Exception as e:
            self.logger.error(f"创建LLM服务失败: {e}")
            raise
    
    def run_workflow(self, manuscript_path: str, literature_dir: str) -> Dict[str, Any]:
        """
        运行完整的工作流程
        
        Args:
            manuscript_path: 手稿文件路径
            literature_dir: 文献目录路径
            
        Returns:
            Dict[str, Any]: 工作流执行结果
        """
        try:
            # 读取手稿内容
            manuscript_file = Path(manuscript_path)
            if not manuscript_file.exists():
                raise FileNotFoundError(f"手稿文件不存在: {manuscript_path}")
            
            with open(manuscript_file, 'r', encoding='utf-8') as f:
                manuscript_content = f.read()
            
            manuscript_title = manuscript_file.stem
            
            # 调用内容处理方法
            return self.run_workflow_with_content(
                manuscript_content=manuscript_content,
                literature_dir=literature_dir,
                manuscript_title=manuscript_title
            )
            
        except Exception as e:
            self.logger.error(f"工作流执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def run_workflow_with_content(
        self, 
        manuscript_content: str, 
        literature_dir: str, 
        manuscript_title: str = "untitled"
    ) -> Dict[str, Any]:
        """
        使用手稿内容运行工作流
        
        Args:
            manuscript_content: 手稿内容
            literature_dir: 文献目录路径
            manuscript_title: 手稿标题
            
        Returns:
            Dict[str, Any]: 工作流执行结果
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"开始处理手稿: {manuscript_title}")
            
            # 1. 生成检索关键词
            self.logger.info("生成检索关键词...")
            keywords = self.llm_service.generate_keywords(manuscript_content)
            self.logger.info(f"生成关键词: {keywords}")
            
            # 2. 检索相关文献
            self.logger.info("检索相关文献...")
            literature_results = self.literature_service.search_literature(
                literature_dir=literature_dir,
                keywords=keywords,
                max_count=self.config.get('workflow.max_literature_count', 50)
            )
            self.logger.info(f"找到 {len(literature_results)} 篇相关文献")
            
            # 3. 提取文献元数据
            self.logger.info("提取文献元数据...")
            literature_metadata = []
            for lit in literature_results[:self.config.get('workflow.max_references', 10)]:
                try:
                    metadata = self.literature_service.extract_literature_metadata(lit['content'])
                    metadata['file_path'] = lit['file_path']
                    metadata['relevance_score'] = lit.get('relevance_score', 0.0)
                    literature_metadata.append(metadata)
                except Exception as e:
                    self.logger.warning(f"提取文献元数据失败 {lit['file_path']}: {e}")
                    continue
            
            # 4. 优化手稿
            self.logger.info("优化手稿内容...")
            optimized_content = self.llm_service.optimize_manuscript(
                manuscript_content=manuscript_content,
                references=literature_metadata,
                max_references=self.config.get('workflow.max_references', 10)
            )
            
            # 5. 保存结果
            timestamp = start_time.strftime("%Y%m%d_%H%M%S")
            
            # 保存优化后的手稿
            output_file = self.output_dir / f"optimized_{manuscript_title}_{timestamp}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(optimized_content)
            
            # 保存工作流结果
            result_data = {
                "manuscript_title": manuscript_title,
                "timestamp": start_time.isoformat(),
                "keywords": keywords,
                "literature_count": len(literature_results),
                "references_used": len(literature_metadata),
                "output_file": str(output_file),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
            
            result_file = self.output_dir / f"workflow_result_{manuscript_title}_{timestamp}.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"工作流完成，结果保存到: {output_file}")
            
            return {
                "success": True,
                "output_file": str(output_file),
                "result_file": str(result_file),
                "metadata": result_data
            }
            
        except Exception as e:
            self.logger.error(f"工作流执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def run_workflow_with_preprocessing(
        self, 
        manuscript_content: str, 
        literature_dir: str, 
        manuscript_title: str = "untitled",
        preprocess_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        运行带预处理的工作流
        
        Args:
            manuscript_content: 手稿内容
            literature_dir: 文献目录路径
            manuscript_title: 手稿标题
            preprocess_metadata: 是否预处理元数据
            
        Returns:
            Dict[str, Any]: 工作流执行结果
        """
        try:
            if preprocess_metadata:
                self.logger.info("预处理文献元数据...")
                self.literature_service.preprocess_literature_metadata(literature_dir)
            
            return self.run_workflow_with_content(
                manuscript_content=manuscript_content,
                literature_dir=literature_dir,
                manuscript_title=manuscript_title
            )
            
        except Exception as e:
            self.logger.error(f"预处理工作流执行失败: {e}")
            raise