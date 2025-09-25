#!/usr/bin/env python3
"""
EnviPath数据库访问工具
用于查询环境pathway数据和化合物代谢信息
基于enviPath-python库实现
"""

from crewai.tools import BaseTool
from enviPath_python import enviPath
import json
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SearchCompoundRequest(BaseModel):
    compound_name: str = Field(..., description="化合物名称")


class GetPathwayInfoRequest(BaseModel):
    pathway_id: str = Field(..., description="pathway ID")


class GetCompoundPathwaysRequest(BaseModel):
    compound_id: str = Field(..., description="化合物ID")


class SearchPathwaysByKeywordRequest(BaseModel):
    keyword: str = Field(..., description="搜索关键词")


class EnviPathTool(BaseTool):
    name: str = "EnviPathTool"
    description: str = "用于查询环境pathway数据和化合物代谢信息，基于enviPath-python库实现"
    
    def __init__(self, base_url: str = "https://envipath.org"):
        """
        初始化EnviPath工具
        
        Args:
            base_url (str): EnviPath API的基础URL
        """
        super().__init__()  # 调用父类构造函数
        # 使用object.__setattr__来设置实例属性，避免Pydantic验证错误
        object.__setattr__(self, 'base_url', base_url)
        try:
            object.__setattr__(self, 'client', enviPath(base_url))
        except Exception as e:
            object.__setattr__(self, 'client', None)
            print(f"警告: 无法初始化EnviPath客户端: {e}")
    
    def _run(self, **kwargs) -> Dict:
        """
        执行指定的EnviPath操作
        
        Args:
            **kwargs: 操作参数
            
        Returns:
            dict: 操作结果
        """
        try:
            # 使用object.__getattribute__获取实例属性
            client = object.__getattribute__(self, 'client')
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"解析参数时出错: {str(e)}"
            }
        
        if not client:
            return {
                "status": "error",
                "message": "EnviPath客户端未初始化",
                "suggestion": "请检查网络连接或使用KEGG工具或其他本地数据源"
            }
        
        try:
            # 简化参数处理，直接使用kwargs
            if "compound_name" in kwargs:
                return self.search_compound(kwargs["compound_name"])
            elif "pathway_id" in kwargs:
                return self.get_pathway_info(kwargs["pathway_id"])
            elif "compound_id" in kwargs:
                return self.get_compound_pathways(kwargs["compound_id"])
            elif "keyword" in kwargs:
                return self.search_pathways_by_keyword(kwargs["keyword"])
            else:
                return {"status": "error", "message": "缺少必需参数"}
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"执行操作时出错: {str(e)}"
            }
    
    def search_compound(self, compound_name: str) -> Dict:
        """
        搜索化合物信息
        
        Args:
            compound_name (str): 化合物名称
            
        Returns:
            dict: 化合物搜索结果
        """
        try:
            client = object.__getattribute__(self, 'client')
            package = client.get_package('https://envipath.org/package/32de3cf4-e3e6-4168-956e-32fa5ddb0ce1')
            result = package.search(compound_name)
            return {"status": "success", "data": result, "query": compound_name}
        except Exception as e:
            return {
                "status": "error",
                "message": f"搜索化合物时出错: {str(e)}",
                "compound_name": compound_name
            }
    
    def get_pathway_info(self, pathway_id: str) -> Dict:
        """
        获取特定pathway的详细信息
        
        Args:
            pathway_id (str): pathway ID
            
        Returns:
            dict: pathway信息
        """
        try:
            client = object.__getattribute__(self, 'client')
            pathway = client.get_pathway(pathway_id)
            return {"status": "success", "data": pathway, "pathway_id": pathway_id}
        except Exception as e:
            return {
                "status": "error",
                "message": f"获取pathway信息时出错: {str(e)}",
                "pathway_id": pathway_id
            }
    
    def get_compound_pathways(self, compound_id: str) -> Dict:
        """
        获取与特定化合物相关的代谢路径
        
        Args:
            compound_id (str): 化合物ID
            
        Returns:
            dict: 相关pathway信息
        """
        try:
            client = object.__getattribute__(self, 'client')
            compound = client.get_compound(compound_id)
            # 注意：这里可能需要根据实际API返回结构进行调整
            pathways = []
            return {"status": "success", "data": pathways, "compound_id": compound_id}
        except Exception as e:
            return {
                "status": "error",
                "message": f"获取化合物路径时出错: {str(e)}",
                "compound_id": compound_id
            }
    
    def search_pathways_by_keyword(self, keyword: str) -> Dict:
        """
        根据关键词搜索pathway
        
        Args:
            keyword (str): 搜索关键词
            
        Returns:
            dict: 搜索结果
        """
        try:
            client = object.__getattribute__(self, 'client')
            package = client.get_package('https://envipath.org/package/32de3cf4-e3e6-4168-956e-32fa5ddb0ce1')
            result = package.search(keyword)
            return {"status": "success", "data": result, "keyword": keyword}
        except Exception as e:
            return {
                "status": "error",
                "message": f"搜索pathway时出错: {str(e)}",
                "keyword": keyword
            }