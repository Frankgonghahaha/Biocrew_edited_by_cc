#!/usr/bin/env python3
"""
污染物摘要工具
用于获取指定污染物的数据摘要
"""

from crewai.tools import BaseTool
from config.config import Config
from sqlalchemy import create_engine, text
from typing import Dict, Any, List, Optional
import requests
import json
from pydantic import BaseModel, Field


class PollutantSummaryInput(BaseModel):
    """污染物摘要输入参数"""
    pollutant_name: str = Field(..., description="污染物名称")


class PollutantSummaryTool(BaseTool):
    """污染物摘要工具"""
    
    name: str = "PollutantSummaryTool"
    description: str = "获取指定污染物的数据摘要，包括基因数据和微生物数据的统计信息"
    args_schema: type[BaseModel] = PollutantSummaryInput
    
    def __init__(self):
        """
        初始化污染物摘要工具
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
    
    def _run(self, pollutant_name: str) -> Dict[Any, Any]:
        """
        获取污染物数据摘要
        
        Args:
            pollutant_name (str): 污染物名称
            
        Returns:
            dict: 数据摘要
        """
        try:
            with self.db_engine.connect() as connection:
                # 获取基因数据统计
                gene_result = connection.execute(text("""
                    SELECT COUNT(*) as count, COUNT(DISTINCT enzyme_type) as enzyme_types
                    FROM genes_data
                    WHERE pollutant_name = :pollutant_name
                """), {"pollutant_name": pollutant_name.lower().replace(' ', '_')})
                
                gene_stats = gene_result.fetchone()
                
                # 获取微生物数据统计
                organism_result = connection.execute(text("""
                    SELECT COUNT(*) as count, COUNT(DISTINCT organism_type) as organism_types
                    FROM organism_data
                    WHERE pollutant_name = :pollutant_name
                """), {"pollutant_name": pollutant_name.lower().replace(' ', '_')})
                
                organism_stats = organism_result.fetchone()
                
                return {
                    "status": "success",
                    "pollutant_name": pollutant_name,
                    "gene_data": {
                        "total_records": gene_stats[0] if gene_stats else 0,
                        "enzyme_types": gene_stats[1] if gene_stats else 0
                    },
                    "organism_data": {
                        "total_records": organism_stats[0] if organism_stats else 0,
                        "organism_types": organism_stats[1] if organism_stats else 0
                    }
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"获取污染物摘要时出错: {str(e)}",
                "pollutant_name": pollutant_name
            }