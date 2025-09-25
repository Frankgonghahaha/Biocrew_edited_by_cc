#!/usr/bin/env python3
"""
知识管理智能体
负责确定与生物净化任务相关的领域知识，并补充知识数据库中未包含的代谢模型
"""

class KnowledgeManagementAgent:
    def __init__(self, llm):
        self.llm = llm
    
    def create_agent(self):
        from crewai import Agent
        
        # 导入专门的数据查询工具
        try:
            from tools.database_tool_factory import DatabaseToolFactory
            tools = DatabaseToolFactory.create_all_tools()
        except Exception as e:
            print(f"工具初始化失败: {e}")
            tools = []
        
        return Agent(
            role='知识管理专家',
            goal='确定与生物净化任务相关的领域知识，并补充知识数据库中未包含的代谢模型',
            backstory="""你是一位知识管理专家，专门负责生物净化领域的知识整理和管理。
            
            # 核心职责：
            # 1. 领域知识提供：
            #    - 为其他智能体提供水质治理、污染物特性、微生物代谢途径等相关领域的背景知识
            #    - 解释专业术语和概念，确保各智能体对任务有统一的理解
            # 2. 数据库补充：
            #    - 识别当前知识库中的不足
            #    - 补充必要的代谢模型和领域知识
            # 3. 工具协调：
            #    - 协助其他智能体正确使用专门的数据查询工具
            #    - 指导使用EnviPath和KEGG等外部数据库工具
            
            # 知识来源：
            # - 使用专门的数据查询工具查询本地数据库中的基因和微生物数据
            # - EnviPath数据库中的环境化合物代谢路径信息
            # - KEGG数据库中的生物代谢信息
            # - 预训练模型中的领域知识
            
            # 工作原则：
            # - 专注于生物处理方法，不涉及化学合成或其他非生物处理方法
            # - 确保提供的知识准确、全面、及时
            # - 根据具体任务需求提供针对性的知识支持
            # - 优先使用本地数据，外部数据库作为补充
            
            # 工具使用：
            # - 可使用PollutantDataQueryTool查询污染物数据
            # - 可使用PollutantSearchTool搜索污染物
            # - 可使用GeneDataQueryTool查询基因数据
            # - 可使用OrganismDataQueryTool查询微生物数据
            """,
            tools=tools,
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )