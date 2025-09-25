#!/usr/bin/env python3
"""
实施方案生成任务
负责生成完整的微生物净化技术落地方案
"""

class ImplementationPlanGenerationTask:
    def __init__(self, llm):
        self.llm = llm

    def create_task(self, agent, context_task=None):
        from crewai import Task
        
        description = """
        根据微生物菌剂和评估报告生成完整的微生物净化技术落地方案。
        
        # 生成步骤：
        # 1. 分析微生物菌剂特性和评估结果
        # 2. 基于微调大语言模型生成方案
        # 3. 覆盖全落地环节
        
        # 方案内容应包括：
        # - 菌剂获取：合法渠道（CGMCC/ATCC采购、实验室分离、合作授权）
        # - 制剂储运：液体浓缩剂（10⁹ CFU/mL，2-8℃存1-3月）、冻干粉（10¹⁰ CFU/g，常温存6-12月）
        # - 投加策略：启动期分阶段投、稳定期定期投、应急补投
        # - 监测应急：周期测水质/群落，异常调参数
        """
        
        expected_output = """
        提供初步的《微生物净化技术方案评估报告》，包括：
        # 1. 菌剂详细组成和特性
        # 2. 获取和制备方法
        # 3. 储运要求
        # 4. 投加策略和操作指南
        # 5. 监测和应急处理方案
        # 6. 预期效果和风险控制措施
        
        # TODO: 完善实施方案的详细内容
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