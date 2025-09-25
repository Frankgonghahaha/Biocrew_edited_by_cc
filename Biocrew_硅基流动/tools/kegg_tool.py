#!/usr/bin/env python3
"""
KEGG数据库访问工具
用于查询pathway、ko、genome、reaction、enzyme、genes等信息
"""

from crewai.tools import BaseTool
import requests
import json
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class GetDatabaseInfoRequest(BaseModel):
    database: str = Field(..., description="数据库名称 (pathway, ko, genome, reaction, enzyme, genes)")


class ListEntriesRequest(BaseModel):
    database: str = Field(..., description="数据库名称")
    organism: Optional[str] = Field(None, description="物种代码 (如 hsa 表示人类)")


class FindEntriesRequest(BaseModel):
    database: str = Field(..., description="数据库名称")
    keywords: str = Field(..., description="搜索关键词")


class GetEntryRequest(BaseModel):
    entry_id: str = Field(..., description="条目ID (如 hsa:10458)")
    format_type: str = Field("json", description="返回格式 (json, aaseq, ntseq等)")


class LinkEntriesRequest(BaseModel):
    target_db: str = Field(..., description="目标数据库")
    source_db_entries: str = Field(..., description="源数据库条目 (如 hsa)")


class ConvertIdRequest(BaseModel):
    target_db: str = Field(..., description="目标数据库 (如 ncbi-geneid)")
    source_ids: str = Field(..., description="源ID (如 eco)")


class SearchPathwayByCompoundRequest(BaseModel):
    compound_id: str = Field(..., description="化合物ID (如 C00001)")


class SearchGenesByPathwayRequest(BaseModel):
    pathway_id: str = Field(..., description="pathway ID (如 path:hsa00010)")


class SearchEnzymesByCompoundRequest(BaseModel):
    compound_id: str = Field(..., description="化合物ID")


class KeggTool(BaseTool):
    name: str = "KeggTool"
    description: str = "用于查询pathway、ko、genome、reaction、enzyme、genes等生物代谢信息"
    
    def __init__(self, base_url: str = "https://rest.kegg.jp"):
        """
        初始化KEGG工具
        
        Args:
            base_url (str): KEGG API的基础URL
        """
        super().__init__()  # 调用父类构造函数
        # 使用object.__setattr__来设置实例属性，避免Pydantic验证错误
        object.__setattr__(self, 'base_url', base_url)
        object.__setattr__(self, 'session', requests.Session())
    
    def _run(self, **kwargs) -> Dict[Any, Any]:
        """
        执行指定的KEGG数据库操作
        
        Args:
            **kwargs: 操作参数
            
        Returns:
            dict: 操作结果
        """
        try:
            # 简化参数处理，直接使用kwargs
            if "database" in kwargs and "organism" in kwargs:
                return self.list_entries(kwargs["database"], kwargs.get("organism"))
            elif "database" in kwargs and "keywords" in kwargs:
                return self.find_entries(kwargs["database"], kwargs["keywords"])
            elif "entry_id" in kwargs:
                return self.get_entry(kwargs["entry_id"], kwargs.get("format_type", "json"))
            elif "target_db" in kwargs and "source_db_entries" in kwargs:
                return self.link_entries(kwargs["target_db"], kwargs["source_db_entries"])
            elif "target_db" in kwargs and "source_ids" in kwargs:
                return self.convert_id(kwargs["target_db"], kwargs["source_ids"])
            elif "compound_id" in kwargs and "pathway" in kwargs:
                return self.search_pathway_by_compound(kwargs["compound_id"])
            elif "pathway_id" in kwargs:
                return self.search_genes_by_pathway(kwargs["pathway_id"])
            elif "compound_id" in kwargs:
                # 默认执行search_enzymes_by_compound操作
                return self.search_enzymes_by_compound(kwargs["compound_id"])
            elif "database" in kwargs:
                # 默认执行get_database_info操作
                return self.get_database_info(kwargs["database"])
            else:
                return {"status": "error", "message": "缺少必需参数"}
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"执行操作时出错: {str(e)}"
            }
    
    def get_database_info(self, database: str) -> Dict:
        """
        获取数据库信息
        
        Args:
            database (str): 数据库名称 (pathway, ko, genome, reaction, enzyme, genes)
            
        Returns:
            dict: 数据库信息
        """
        try:
            url = f"{self.base_url}/info/{database}"
            response = self.session.get(url)
            response.raise_for_status()
            
            return {
                "status": "success",
                "data": response.text,
                "database": database
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "database": database
            }
    
    def list_entries(self, database: str, organism: Optional[str] = None) -> Dict:
        """
        列出数据库中的条目
        
        Args:
            database (str): 数据库名称
            organism (str, optional): 物种代码 (如 hsa 表示人类)
            
        Returns:
            dict: 条目列表
        """
        try:
            if organism:
                url = f"{self.base_url}/list/{organism}:{database}"
            else:
                url = f"{self.base_url}/list/{database}"
                
            response = self.session.get(url)
            response.raise_for_status()
            
            # 解析返回的文本数据
            entries = []
            for line in response.text.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        entries.append({
                            "id": parts[0],
                            "description": parts[1]
                        })
                    elif len(parts) == 1:
                        entries.append({
                            "id": parts[0],
                            "description": ""
                        })
            
            return {
                "status": "success",
                "data": entries,
                "database": database,
                "count": len(entries)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "database": database
            }
    
    def find_entries(self, database: str, keywords: str) -> Dict:
        """
        根据关键词搜索条目
        
        Args:
            database (str): 数据库名称
            keywords (str): 搜索关键词
            
        Returns:
            dict: 搜索结果
        """
        try:
            # 将空格替换为+号以符合KEGG API要求
            keywords = keywords.replace(' ', '+')
            url = f"{self.base_url}/find/{database}/{keywords}"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            # 解析返回的文本数据
            entries = []
            for line in response.text.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        entries.append({
                            "id": parts[0],
                            "description": parts[1]
                        })
                    elif len(parts) == 1:
                        entries.append({
                            "id": parts[0],
                            "description": ""
                        })
            
            return {
                "status": "success",
                "data": entries,
                "database": database,
                "keyword": keywords.replace('+', ' '),
                "count": len(entries)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "database": database,
                "keyword": keywords.replace('+', ' ') if 'keywords' in locals() else ""
            }
    
    def get_entry(self, entry_id: str, format_type: str = "json") -> Dict:
        """
        获取特定条目的详细信息
        
        Args:
            entry_id (str): 条目ID (如 hsa:10458)
            format_type (str): 返回格式 (json, aaseq, ntseq等)
            
        Returns:
            dict: 条目详细信息
        """
        try:
            url = f"{self.base_url}/get/{entry_id}/{format_type}"
            response = self.session.get(url)
            response.raise_for_status()
            
            return {
                "status": "success",
                "data": response.text,
                "entry_id": entry_id,
                "format": format_type
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "entry_id": entry_id,
                "format": format_type
            }
    
    def link_entries(self, target_db: str, source_db_entries: str) -> Dict:
        """
        查找相关条目
        
        Args:
            target_db (str): 目标数据库
            source_db_entries (str): 源数据库条目 (如 hsa)
            
        Returns:
            dict: 关联信息
        """
        try:
            url = f"{self.base_url}/link/{target_db}/{source_db_entries}"
            response = self.session.get(url)
            response.raise_for_status()
            
            # 解析返回的文本数据
            links = []
            for line in response.text.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) == 2:
                        links.append({
                            "source": parts[0],
                            "target": parts[1]
                        })
            
            return {
                "status": "success",
                "data": links,
                "target_db": target_db,
                "source": source_db_entries,
                "count": len(links)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "target_db": target_db,
                "source": source_db_entries
            }
    
    def convert_id(self, target_db: str, source_ids: str) -> Dict:
        """
        转换ID格式
        
        Args:
            target_db (str): 目标数据库 (如 ncbi-geneid)
            source_ids (str): 源ID (如 eco)
            
        Returns:
            dict: 转换结果
        """
        try:
            url = f"{self.base_url}/conv/{target_db}/{source_ids}"
            response = self.session.get(url)
            response.raise_for_status()
            
            # 解析返回的文本数据
            conversions = []
            for line in response.text.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) == 2:
                        conversions.append({
                            "source": parts[0],
                            "target": parts[1]
                        })
            
            return {
                "status": "success",
                "data": conversions,
                "target_db": target_db,
                "source": source_ids,
                "count": len(conversions)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "target_db": target_db,
                "source": source_ids
            }
    
    def search_pathway_by_compound(self, compound_id: str) -> Dict:
        """
        根据化合物ID搜索相关代谢路径
        
        Args:
            compound_id (str): 化合物ID (如 C00001)
            
        Returns:
            dict: 相关pathway信息
        """
        return self.link_entries("pathway", compound_id)
    
    def search_genes_by_pathway(self, pathway_id: str) -> Dict:
        """
        根据pathway ID搜索相关基因
        
        Args:
            pathway_id (str): pathway ID (如 path:hsa00010)
            
        Returns:
            dict: 相关基因信息
        """
        return self.link_entries("genes", pathway_id)
    
    def search_enzymes_by_compound(self, compound_id: str) -> Dict:
        """
        根据化合物ID搜索相关酶
        
        Args:
            compound_id (str): 化合物ID
            
        Returns:
            dict: 相关酶信息
        """
        return self.link_entries("enzyme", compound_id)