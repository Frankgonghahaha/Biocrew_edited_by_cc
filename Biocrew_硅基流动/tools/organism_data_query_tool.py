#!/usr/bin/env python3
"""
微生物数据查询工具
用于查询指定污染物的微生物数据
"""

from crewai.tools import BaseTool
from config.config import Config
from sqlalchemy import create_engine, text
from typing import Dict, Any, List, Optional
import requests
import json
from pydantic import BaseModel, Field
from tools.pollutant_name_utils import standardize_pollutant_name


class OrganismDataQueryInput(BaseModel):
    """微生物数据查询输入参数"""
    pollutant_name: str = Field(..., description="污染物名称")
    organism_type: Optional[str] = Field(None, description="微生物类型")


class OrganismDataQueryTool(BaseTool):
    """微生物数据查询工具"""
    
    name: str = "OrganismDataQueryTool"
    description: str = "查询指定污染物的微生物数据"
    args_schema: type[BaseModel] = OrganismDataQueryInput
    
    def __init__(self):
        """
        初始化微生物数据查询工具
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
    
    def _run(self, pollutant_name: str, organism_type: Optional[str] = None) -> Dict[Any, Any]:
        """
        查询微生物数据
        
        Args:
            pollutant_name (str): 污染物名称
            organism_type (str, optional): 微生物类型
            
        Returns:
            dict: 微生物数据
        """
        try:
            # 标准化污染物名称
            standardized_name = standardize_pollutant_name(pollutant_name)
            
            with self.db_engine.connect() as connection:
                if organism_type:
                    result = connection.execute(text("""
                        SELECT *
                        FROM organism_data
                        WHERE pollutant_name = :pollutant_name
                        AND organism_type = :organism_type
                        LIMIT 50
                    """), {
                        "pollutant_name": standardized_name,
                        "organism_type": organism_type
                    })
                else:
                    result = connection.execute(text("""
                        SELECT *
                        FROM organism_data
                        WHERE pollutant_name = :pollutant_name
                        LIMIT 50
                    """), {"pollutant_name": standardized_name})
                
                # 转换为字典列表
                columns = result.keys()
                rows = result.fetchall()
                
                organism_data = []
                for row in rows:
                    organism_data.append(dict(zip(columns, row)))
                
                return {
                    "status": "success",
                    "data": organism_data,
                    "count": len(organism_data)
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"查询微生物数据时出错: {str(e)}",
                "pollutant_name": pollutant_name
            }