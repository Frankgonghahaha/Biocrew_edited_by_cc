#!/usr/bin/env python3
"""
数据库工具工厂
用于创建和管理所有数据库相关的工具
"""

from tools.pollutant_data_query_tool import PollutantDataQueryTool
from tools.gene_data_query_tool import GeneDataQueryTool
from tools.organism_data_query_tool import OrganismDataQueryTool
from tools.pollutant_summary_tool import PollutantSummaryTool
from tools.pollutant_search_tool import PollutantSearchTool


class DatabaseToolFactory:
    """数据库工具工厂类"""
    
    @staticmethod
    def create_all_tools():
        """
        创建所有数据库工具实例
        
        Returns:
            list: 所有数据库工具实例的列表
        """
        tools = [
            PollutantDataQueryTool(),
            GeneDataQueryTool(),
            OrganismDataQueryTool(),
            PollutantSummaryTool(),
            PollutantSearchTool()
        ]
        return tools
    
    @staticmethod
    def get_tool_by_name(tool_name: str):
        """
        根据工具名称获取工具实例
        
        Args:
            tool_name (str): 工具名称
            
        Returns:
            BaseTool: 工具实例，如果未找到则返回None
        """
        tool_map = {
            "PollutantDataQueryTool": PollutantDataQueryTool,
            "GeneDataQueryTool": GeneDataQueryTool,
            "OrganismDataQueryTool": OrganismDataQueryTool,
            "PollutantSummaryTool": PollutantSummaryTool,
            "PollutantSearchTool": PollutantSearchTool
        }
        
        tool_class = tool_map.get(tool_name)
        if tool_class:
            return tool_class()
        return None