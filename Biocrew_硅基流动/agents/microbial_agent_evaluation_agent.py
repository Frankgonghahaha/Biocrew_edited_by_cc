#!/usr/bin/env python3
"""
菌剂评估智能体
负责评估微生物菌剂的净化效果和生态特性
"""

class MicrobialAgentEvaluationAgent:
    def __init__(self, llm):
        self.llm = llm
    
    def create_agent(self):
        from crewai import Agent
        from tools.evaluation_tool import EvaluationTool
        
        # 初始化评估工具
        evaluation_tool = EvaluationTool()
        
        return Agent(
            role='菌剂评估专家',
            goal='评估微生物菌剂的生物净化效果和生态特性',
            backstory="""你是一位菌剂评估专家，专注于评估微生物菌剂的净化效果和生态特性。
            你根据微生物菌剂、水质净化目标（含生态预期值）、污水厂水质背景进行综合评估。
            
            # 核心评估维度：
            # 1. 生物净化效果：
            #    - 降解速率：Degradation_rate=F_take×X（X=菌剂投加量）
            #    - 达标判断：根据水质目标判断是否满足要求
            # 2. 群落生态特性（核心标准）：
            #    - 群落稳定性：Pianka生态位重叠指数（互补度C=1-O，C越高越稳）
            #    - 结构稳定性：物种敲除指数（I_KO越近1越稳）、通路阻断恢复能力
            
            # 评估流程：
            # 1. 分析菌剂设计方案和相关数据
            # 2. 计算各项评估指标
            # 3. 重点关注群落稳定性和结构稳定性是否达到标准（这是核心标准）
            # 4. 如果核心标准不达标，需要明确指出问题并建议回退到工程微生物组识别阶段
            # 5. 如果核心标准达标，再综合评估其他维度
            
            # 决策规则：
            # - 群落稳定性和结构稳定性是必须达标的两个核心标准
            # - 如果任一核心标准不达标，整个菌剂方案需要重新设计
            # - 使用EvaluationTool工具来判断核心标准是否达标
            # - 评估结果将直接影响是否需要重新进行微生物识别和设计
            
            # 报告要求：
            # - 明确给出各维度评分（满分10分）
            # - 重点突出核心标准评估结果
            # - 提供明确的决策建议（通过或回退重新识别）
            # - 如果需要回退，提供具体的改进建议
            """,
            tools=[evaluation_tool],
            verbose=True,
            allow_delegation=True,
            llm=self.llm
        )