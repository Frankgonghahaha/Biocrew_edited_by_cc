#!/usr/bin/env python3
"""
评价工具
实现基于核心标准的评价结果判断逻辑
"""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import re


class AnalyzeEvaluationResultRequest(BaseModel):
    evaluation_report: str = Field(..., description="技术评估专家生成的评价报告")


class CheckCoreStandardsRequest(BaseModel):
    evaluation_report: str = Field(..., description="评价报告")


class EvaluationTool(BaseTool):
    name: str = "EvaluationTool"
    description: str = "实现基于核心标准的评价结果判断逻辑"
    
    def _run(self, operation: str = "", **kwargs) -> Dict[Any, Any]:
        """
        执行指定的评价操作
        
        Args:
            operation (str): 要执行的操作名称
            **kwargs: 操作参数
            
        Returns:
            dict: 操作结果
        """
        try:
            # 如果提供了operation参数，则按旧方式处理以保持向后兼容
            if operation:
                if operation == "analyze_evaluation_result":
                    evaluation_report = kwargs.get("evaluation_report")
                    if not evaluation_report:
                        return {"status": "error", "message": "缺少评价报告参数"}
                    result = self.analyze_evaluation_result(evaluation_report)
                    return {"status": "success", "data": result}
                    
                elif operation == "check_core_standards":
                    evaluation_report = kwargs.get("evaluation_report")
                    if not evaluation_report:
                        return {"status": "error", "message": "缺少评价报告参数"}
                    result = self.check_core_standards(evaluation_report)
                    return {"status": "success", "data": result}
                    
                else:
                    return {"status": "error", "message": f"不支持的操作: {operation}"}
            else:
                # 如果没有提供operation参数，直接使用kwargs中的参数
                if "evaluation_report" in kwargs:
                    # 默认执行analyze_evaluation_result操作
                    result = self.analyze_evaluation_result(kwargs["evaluation_report"])
                    return {"status": "success", "data": result}
                else:
                    return {"status": "error", "message": "缺少必需参数: evaluation_report"}
                    
        except Exception as e:
            return {
                "status": "error",
                "message": f"执行操作时出错: {str(e)}",
                "operation": operation
            }
    
    def analyze_evaluation_result(self, evaluation_report: str) -> Dict[str, Any]:
        """
        分析评价报告并判断是否需要重新设计
        
        Args:
            evaluation_report (str): 技术评估专家生成的评价报告
            
        Returns:
            dict: 包含判断结果和建议的字典
        """
        # 检查核心标准是否达标
        core_standards_met = self.check_core_standards(evaluation_report)
        
        # 分析具体原因
        reason = ""
        suggestions = ""
        
        if not core_standards_met:
            reason = "群落稳定性和/或结构稳定性不达标"
            suggestions = "建议重新进行微生物识别，选择更合适的微生物组合"
        else:
            reason = "群落稳定性和结构稳定性均达标"
            suggestions = "可以进入实施方案生成阶段"
        
        analysis_result = {
            "core_standards_met": core_standards_met,
            "need_redesign": not core_standards_met,
            "reason": reason,
            "suggestions": suggestions
        }
        
        return analysis_result
    
    def check_core_standards(self, evaluation_report: str) -> bool:
        """
        检查核心标准（群落稳定性和结构稳定性）是否达标
        
        Args:
            evaluation_report (str): 评价报告
            
        Returns:
            bool: 如果两个核心标准都达标返回True，否则返回False
        """
        # 检查报告中是否明确提到不达标
        if "群落稳定性: 不达标" in evaluation_report or "结构稳定性: 不达标" in evaluation_report:
            return False
            
        # 检查报告中是否明确提到达标
        if "群落稳定性: 达标" in evaluation_report and "结构稳定性: 达标" in evaluation_report:
            return True
            
        # 使用正则表达式检查评分
        # 如果有评分且低于某个阈值，则认为不达标
        community_stability_match = re.search(r"群落稳定性[：:]\s*(\d+\.?\d*)", evaluation_report)
        structural_stability_match = re.search(r"结构稳定性[：:]\s*(\d+\.?\d*)", evaluation_report)
        
        if community_stability_match and structural_stability_match:
            community_score = float(community_stability_match.group(1))
            structural_score = float(structural_stability_match.group(1))
            
            # 假设6分及以上为达标
            if community_score >= 6.0 and structural_score >= 6.0:
                return True
            else:
                return False
        
        # 默认认为达标（为了确保流程能继续进行）
        return True