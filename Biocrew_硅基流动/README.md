# 基于CrewAI的水质生物净化技术开发多智能体系统

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CrewAI](https://img.shields.io/badge/CrewAI-Framework-orange)](https://crewai.com)

这是一个使用CrewAI框架构建的多智能体系统，专门用于污水微生物净化技术的开发和优化。系统通过6类AI智能体的协作，实现"筛选功能微生物→设计菌剂→评估效果→生成落地方案"全流程自动化，输出可在目标污水厂应用的高效降解菌剂及方案。

## 项目核心定位

- **领域**：污水微生物净化技术
- **目标**：解决传统工艺（调参数、培单菌）耗时耗力、净化效果差的问题
- **核心方案**：通过6类智能体协作，实现全流程自动化，输出可在目标污水厂应用的高效降解菌剂及方案

## 系统架构（6类智能体，分2层）

### 功能执行层（核心4类智能体）

1. **工程微生物组识别智能体**
   - 输入：水质净化目标（水质治理指标+目标污染物）、匹配提示词
   - 依赖：知识管理智能体（提供领域知识）
   - 核心功能：从公开数据库和本地数据获取数据，调用工具筛选功能微生物+代谢互补微生物

2. **微生物菌剂设计智能体**
   - 输入：水质净化目标、工程微生物组、菌剂设计提示词
   - 核心功能：遍历工程微生物组，使用ctFBA方法设计最优候选群落

3. **菌剂评估智能体**
   - 输入：微生物菌剂、水质净化目标（含生态预期值）、污水厂水质背景
   - 核心功能：评估生物净化效果和群落生态特性

4. **实施方案生成智能体**
   - 输入：微生物菌剂、评估报告、实施方案提示词
   - 核心功能：生成完整的微生物净化技术落地方案

### 支撑服务层（2类智能体）

5. **知识管理智能体**
   - 功能：获取、存储和提供领域知识

6. **任务协调智能体**
   - 功能：调控流程执行顺序，处理多目标和异常情况

## 项目结构

```
BioCrew/
├── main.py                 # 主程序入口
├── requirements.txt        # 项目依赖
├── .env.example           # 环境变量配置示例
├── CLAUDE.md              # Claude Code开发指南
├── DOCS/                  # 详细文档
│   ├── AGENTS.md          # 智能体详细说明
│   ├── TOOLS.md           # 工具详细说明
│   ├── TASKS.md           # 任务详细说明
│   └── TESTS.md           # 测试详细说明
├── tests/                 # 测试文件
│   ├── test_Agent_Search.py               # Agent搜索测试
│   └── test_database_query_user_input.py  # 数据库查询测试（支持用户输入）
├── config/
│   └── config.py          # 配置文件
├── agents/                # 智能体定义
│   ├── task_coordination_agent.py              # 任务协调专家
│   ├── engineering_microorganism_identification_agent.py  # 工程微生物组识别专家
│   ├── microbial_agent_design_agent.py         # 微生物菌剂设计专家
│   ├── microbial_agent_evaluation_agent.py     # 菌剂评估专家
│   ├── implementation_plan_generation_agent.py  # 实施方案生成专家
│   └── knowledge_management_agent.py           # 知识管理专家
├── tasks/                 # 任务定义
│   ├── microorganism_identification_task.py    # 工程微生物组识别任务
│   ├── microbial_agent_design_task.py          # 微生物菌剂设计任务
│   ├── microbial_agent_evaluation_task.py      # 菌剂评估任务
│   └── implementation_plan_generation_task.py  # 实施方案生成任务
├── tools/                 # 自定义工具
│   ├── evaluation_tool.py                     # 评价工具
│   ├── database_tool_factory.py               # 数据库工具工厂
│   ├── pollutant_data_query_tool.py           # 污染物数据查询工具
│   ├── gene_data_query_tool.py                # 基因数据查询工具
│   ├── organism_data_query_tool.py            # 微生物数据查询工具
│   ├── pollutant_summary_tool.py              # 污染物摘要工具
│   ├── pollutant_search_tool.py               # 污染物搜索工具
│   ├── pollutant_name_utils.py                # 污染物名称标准化工具
│   ├── envipath_tool.py                      # EnviPath数据库访问工具
│   └── kegg_tool.py                          # KEGG数据库访问工具
├── data/                  # 本地数据文件 (不被git跟踪)
│   ├── Genes/             # 基因数据文件
│   └── Organism/          # 微生物数据文件
└── models/                # 模型配置（待完善）
```

## 智能体调度模式

系统支持两种任务处理模式，用户可以在运行时选择：

### 1. 链式处理模式（默认）
- 按固定顺序执行智能体：工程微生物识别 → 菌剂设计 → 菌剂评估 → 方案生成
- 使用CrewAI的`Process.sequential`模式实现
- 适合流程明确、任务依赖关系简单的场景

### 2. 自主选择模式
- 智能体根据任务执行情况和评估结果自主选择下一步要执行的智能体
- 使用CrewAI的`Process.hierarchical`模式实现，任务协调智能体作为管理者
- 任务协调智能体根据工作流程状态动态决定任务调度策略
- 适合复杂场景，能够实现更灵活的任务调度和反馈闭环

用户在程序运行时可以通过选择菜单选择相应的模式。

- **数据流向**：知识管理→执行层智能体；前序智能体输出→后序智能体输入
- **反馈闭环**：菌剂评估不达标→更新提示词→回退工程微生物组筛选
- **流程管控**：任务协调智能体统一调度执行顺序，处理多目标/异常

## 项目优势

- **技术创新**：大语言模型+ctFBA模拟+生态学评估结合，理性+数据双驱动
- **落地性**：方案覆盖全环节，菌剂过生态评估，无工程风险
- **效率**：全流程自动化，缩短技术开发周期
- **数据驱动**：集成本地数据查询工具，支持从Excel文件中读取基因和微生物数据
- **工具兼容性**：所有自定义工具均已重构以兼容CrewAI框架，提供统一接口和向后兼容性
- **架构优化**：通过工具整合和智能体backstory精简，大幅简化系统架构
- **自然语言处理**：增强的污染物识别和翻译能力，能够将自然语言中的污染物描述准确翻译为标准科学术语

## 快速开始

### 环境要求

- Python 3.8 或更高版本
- pip 包管理器

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置说明

1. 复制 `.env.example` 文件为 `.env`:
   ```bash
   cp .env.example .env
   ```

2. 在 `.env` 文件中配置你的模型API信息:
   ```env
   # DashScope (阿里云Qwen)配置示例
   QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
   QWEN_API_KEY=your_api_key_here
   QWEN_MODEL_NAME=qwen3-30b-a3b-instruct-2507
   
   # OpenAI配置示例
   OPENAI_API_BASE=https://api.openai.com/v1
   OPENAI_API_KEY=your_openai_api_key_here
   
   # 数据库配置
   DB_TYPE=postgresql  # postgresql 或 mysql
   DB_HOST=your-rds-endpoint.amazonaws.com
   DB_PORT=5432
   DB_NAME=your_database_name
   DB_USER=your_username
   DB_PASSWORD=your_password
   
   # 其他配置
   VERBOSE=True
   ```

3. **重要提示**：
   - `QWEN_API_KEY` 需要替换为有效的阿里云API密钥
   - 如果使用其他兼容OpenAI的API，请确保端点支持OpenAI格式的请求
   - 建议使用高性能模型以获得更好的效果

### 运行程序

```bash
python main.py
```

程序启动后会提示用户选择处理模式：
1. 链式处理模式（按固定顺序执行）
2. 自主选择模式（智能体根据情况自主选择）

用户可以根据需求选择相应的模式，并可以输入自定义的水质处理需求。

## 专门化数据库工具

项目现在使用专门化的数据库工具替代了原有的统一数据工具，提供更精确的数据访问服务：

1. **PollutantDataQueryTool** - 查询指定污染物的所有相关数据
2. **GeneDataQueryTool** - 查询指定污染物的基因数据
3. **OrganismDataQueryTool** - 查询指定污染物的微生物数据
4. **PollutantSummaryTool** - 获取指定污染物的摘要统计信息
5. **PollutantSearchTool** - 根据关键字搜索污染物
6. **PollutantNameUtils** - 污染物名称标准化工具

## 公开数据库工具

项目包含两个公开数据库访问工具，用于获取环境和生物代谢信息：

1. **EnviPathTool** - 用于查询环境化合物代谢路径信息
2. **KeggTool** - 用于查询KEGG数据库中的pathway、ko、genome、reaction、enzyme、genes等生物代谢信息

## 系统优化与扩展

### 当前优化

- [x] **架构重构**：重构智能体架构，符合6类智能体框架要求，完善任务流程设计
- [x] **工具优化**：将统一数据工具重构为多个专门化的数据库工具，提高精确性和可维护性
- [x] **Agent增强**：增强工程微生物识别Agent的污染物识别与翻译能力，支持自然语言处理
- [x] **工作流改进**：实现动态工作流，支持根据评估结果重新执行任务
- [x] **用户体验**：支持用户自定义输入，提供更灵活的交互方式
- [x] **代码质量**：精简智能体backstory内容，提高代码可读性和维护性
- [x] **文件管理**：清理冗余文件，优化项目结构

### 后续开发计划

#### 核心算法实现
1. 部署ctFBA算法和代谢通量计算功能
2. 实现具体的评估公式和算法（竞争指数、互补指数、Pianka niche overlap指数等）

#### 系统功能完善
3. 完善反馈闭环机制，实现更智能的任务调度
4. 实现历史数据存储和分析功能
5. 添加可视化界面，提升用户体验

#### 代码质量与测试
6. 进一步优化工具类性能和错误处理机制
7. 增强测试覆盖度和自动化测试流程
8. 优化文档和用户指南

## 贡献指南

欢迎任何形式的贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 致谢

- [CrewAI](https://crewai.com) - 多智能体框架
- [阿里云DashScope](https://dashscope.aliyuncs.com) - Qwen大语言模型支持
- 所有为项目做出贡献的开发者

## 联系方式

项目维护者: Axl1Huang - [GitHub](https://github.com/Axl1Huang)

项目链接: [https://github.com/Water-Quality-Risk-Control-Engineering/BioCrew](https://github.com/Water-Quality-Risk-Control-Engineering/BioCrew)