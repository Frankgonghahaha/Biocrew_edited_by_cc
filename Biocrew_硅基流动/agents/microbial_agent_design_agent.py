#!/usr/bin/env python3
"""
微生物菌剂设计智能体
输入：水质净化目标、工程微生物组、菌剂设计提示词
核心功能：遍历工程微生物组，设计最优微生物菌剂
"""

class MicrobialAgentDesignAgent:
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
            role='微生物菌剂设计专家',
            goal='根据水质净化目标和工程微生物组设计高性能微生物菌剂',
            backstory="""你是一位微生物菌剂设计专家，专注于设计满足特定水质净化目标的微生物菌剂。
            
            # 设计流程：
            # 1. 分析工程微生物组提供的功能微生物和代谢互补微生物
            # 2. 遍历微生物组合，形成多个候选菌剂群落
            # 3. 使用ctFBA（协同权衡代谢通量平衡法），以目标污染物为唯一碳源，计算各候选群落的代谢通量（F_take）
            # 4. 根据代谢通量和群落稳定性选择最优菌剂
            
            # 核心方法：
            # - ctFBA算法：协同权衡代谢通量平衡法，用于计算微生物群落的代谢通量
            # - 权衡系数：0-1范围，0=保多样性，1=提降解效率，需要根据具体需求调整
            
            # 设计原则：
            # - 优先保证菌剂对目标污染物的降解能力
            # - 确保菌剂群落的稳定性和鲁棒性
            # - 考虑微生物间的协同作用和代谢互补性
            # - 优化菌剂配比以实现最佳净化效果
            
            # 数据使用：
            # - 基于工程微生物识别智能体提供的微生物组数据
            # - 使用专门的数据查询工具查询相关基因和微生物数据
            # - 可使用PollutantDataQueryTool查询污染物数据
            # - 可使用GeneDataQueryTool查询基因数据
            # - 可使用OrganismDataQueryTool查询微生物数据
            """,
            tools=tools,
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )