#!/usr/bin/env python3
"""
污染物搜索工具
用于根据关键词搜索污染物
"""

from crewai.tools import BaseTool
from config.config import Config
from sqlalchemy import create_engine, text
from typing import Dict, Any, List, Optional
import requests
import json
from pydantic import BaseModel, Field
from tools.pollutant_name_utils import generate_pollutant_name_variants


class PollutantSearchInput(BaseModel):
    """污染物搜索输入参数"""
    keyword: str = Field(..., description="搜索关键词")


class PollutantSearchTool(BaseTool):
    """污染物搜索工具"""
    
    name: str = "PollutantSearchTool"
    description: str = "根据关键词搜索污染物"
    args_schema: type[BaseModel] = PollutantSearchInput
    
    def __init__(self):
        """
        初始化污染物搜索工具
        """
        super().__init__()
        # 初始化数据库连接
        object.__setattr__(self, 'db_engine', self._get_database_connection())
    
    def _get_database_connection(self):
        """
        创建数据库连接
        """
        db_type = Config.DB_TYPE
        db_host = Config.DB_HOST
        db_port = Config.DB_PORT
        db_name = Config.DB_NAME
        db_user = Config.DB_USER
        db_password = Config.DB_PASSWORD
        
        if db_type == 'postgresql':
            database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        elif db_type == 'mysql':
            database_url = f"mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
        
        engine = create_engine(database_url)
        return engine
    
    def _run(self, keyword: str) -> Dict[Any, Any]:
        """
        搜索污染物
        
        Args:
            keyword (str): 搜索关键词
            
        Returns:
            dict: 搜索结果
        """
        try:
            # 生成关键词的多种变体
            keyword_variants = generate_pollutant_name_variants(keyword)
            
            with self.db_engine.connect() as connection:
                all_pollutants = set()
                
                # 对每个变体进行搜索
                for variant in keyword_variants:
                    # 搜索基因数据中的污染物
                    gene_result = connection.execute(text("""
                        SELECT DISTINCT pollutant_name
                        FROM genes_data
                        WHERE pollutant_name ILIKE :keyword
                        LIMIT 20
                    """), {"keyword": f"%{variant}%"})
                    
                    gene_pollutants = [row[0] for row in gene_result.fetchall()]
                    all_pollutants.update(gene_pollutants)
                    
                    # 搜索微生物数据中的污染物
                    organism_result = connection.execute(text("""
                        SELECT DISTINCT pollutant_name
                        FROM organism_data
                        WHERE pollutant_name ILIKE :keyword
                        LIMIT 20
                    """), {"keyword": f"%{variant}%"})
                    
                    organism_pollutants = [row[0] for row in organism_result.fetchall()]
                    all_pollutants.update(organism_pollutants)
                
                # 转换为列表
                pollutants_list = list(all_pollutants)
                
                return {
                    "status": "success",
                    "keyword": keyword,
                    "variants_searched": keyword_variants[:5],  # 只显示前5个变体
                    "pollutants": pollutants_list,
                    "count": len(pollutants_list)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"搜索污染物时出错: {str(e)}",
                "keyword": keyword
            }