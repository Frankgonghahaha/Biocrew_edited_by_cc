#!/usr/bin/env python3
"""
微生物菌剂设计任务
输入：水质净化目标、工程微生物组、菌剂设计提示词
核心功能：遍历工程微生物组，设计最优微生物菌剂
"""

class MicrobialAgentDesignTask:
    def __init__(self, llm):
        self.llm = llm

    def create_task(self, agent, context_task=None, feedback=None, user_requirement=None):
        from crewai import Task
        
        description = """
        根据工程微生物组设计功能微生物菌剂配方。
        
        设计步骤：
        # 1. 分析目标污染物特性和处理要求
        # 2. 遍历工程微生物组，组合功能菌+互补菌形成候选群落
        # 3. 使用ctFBA（协同权衡代谢通量平衡法），以目标污染物为唯一碳源，计算代谢通量（F_take）
        # 4. 选择代谢通量最高的候选群落作为最优菌剂
        # 5. 优化菌剂配比以确保群落稳定性和结构稳定性
        
        # 关键参数：
        # - 权衡系数（0-1，0=保多样性，1=提降解效率）
        """
        
        # 添加用户自定义需求到描述中
        if user_requirement:
            description += f"\n\n用户具体需求：{user_requirement}"
        
        if feedback:
            description += f"\n\n根据评估反馈进行优化设计：\n{feedback}"
        
        expected_output = """
        提供初步的菌剂设计方案，包括：
        # 1. 菌剂组成（微生物种类和比例）
        # 2. 设计原理说明
        # 3. 稳定性保障措施
        # 4. 预期的净化效果
        # 5. 代谢通量计算结果
        
        # TODO: 完善菌剂设计方案的详细内容
        """
        
        # 如果有上下文任务，设置依赖关系
        task_params = {
            'description': description.strip(),
            'expected_output': expected_output.strip(),
            'agent': agent,
            'verbose': True
        }
        
        if context_task:
            task_params['context'] = [context_task]
            
        return Task(**task_params)