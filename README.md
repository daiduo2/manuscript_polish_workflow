# Manuscript Polish Workflow

一个基于大语言模型的手稿润色工作流系统，专门用于学术论文和文献的智能化处理与优化。

## 特性

- **智能文献分析**: 自动分析和提取文献关键信息
- **手稿润色**: 基于LLM的智能润色和改进建议
- **工作流自动化**: 完整的处理流程自动化
- **多格式支持**: 支持多种文档格式的处理
- **配置灵活**: 可自定义的配置选项

## 项目结构

```
manuscript_polish_workflow/
├── core/                    # 核心功能模块
│   ├── agents/             # 智能代理模块
│   ├── processors/         # 文档处理器
│   ├── utils/              # 工具函数
│   └── orchestrator.py     # 工作流编排器
├── config/                 # 配置文件
├── examples/               # 示例文件
├── output/                 # 输出目录
├── logs/                   # 日志文件
├── main.py                 # 主入口文件
└── requirements.txt        # 依赖包列表
```

## 安装

1. 克隆仓库:
```bash
git clone https://github.com/daiduo2/manuscript_polish_workflow.git
cd manuscript_polish_workflow
```

2. 安装依赖:
```bash
pip install -r requirements.txt
```

## 配置

1. 复制配置模板:
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，配置必要的环境变量:
```
# LLM API配置
QWEN_API_KEY=your_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 工作流配置
WORKFLOW_MODE=auto
OUTPUT_FORMAT=markdown
```

## 使用方法

### 基本使用

```python
from core.orchestrator import WorkflowOrchestrator

# 创建工作流实例
orchestrator = WorkflowOrchestrator()

# 处理手稿文件
result = orchestrator.process_manuscript(
    manuscript_path="path/to/your/manuscript.md",
    literature_dir="path/to/literature/"
)

print(f"处理结果: {result}")
```

### 命令行使用

```bash
# 处理单个手稿文件
python main.py --manuscript manuscript.md --literature ./literature/

# 使用预处理选项
python main.py --manuscript manuscript.md --literature ./literature/ --preprocess
```

## 核心功能模块

### 1. 文档处理器 (processors/)
- **manuscript_processor.py**: 手稿内容处理
- **literature_processor.py**: 文献资料处理
- **output_processor.py**: 输出格式化处理

### 2. 智能代理 (agents/)
- **analysis_agent.py**: 文献分析代理
- **polish_agent.py**: 润色建议代理
- **review_agent.py**: 审查评估代理

### 3. 工具函数 (utils/)
- **config.py**: 配置管理
- **file_utils.py**: 文件操作工具
- **llm_client.py**: LLM客户端封装

## 工作流程

1. **输入处理**: 读取和解析手稿文件
2. **文献分析**: 分析相关文献和参考资料
3. **内容润色**: 基于LLM的智能润色建议
4. **质量审查**: 自动化质量检查和评估
5. **输出生成**: 生成最终的润色结果

## 性能优化

- **缓存机制**: 智能缓存LLM响应，避免重复调用
- **批处理**: 支持批量处理多个文档
- **异步处理**: 异步I/O操作提升性能
- **内存管理**: 优化内存使用，支持大文件处理

## 输出文件

处理完成后，系统会在 `output/` 目录下生成以下文件:

- `polished_manuscript.md`: 润色后的手稿
- `analysis_report.json`: 详细分析报告
- `suggestions.md`: 改进建议列表
- `metadata.json`: 处理元数据

## 注意事项

1. **API配置**: 确保正确配置LLM API密钥和端点
2. **文件格式**: 支持Markdown、TXT等文本格式
3. **网络连接**: 需要稳定的网络连接访问LLM服务
4. **资源使用**: 大文件处理可能需要较多内存和时间

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

本项目采用MIT许可证。详见 [LICENSE](LICENSE) 文件。