#!/usr/bin/env python3
"""
配置文件，用于设置模型URL和Token
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # QWEN3模型配置
    QWEN_API_BASE = os.getenv('QWEN_API_BASE', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    QWEN_API_KEY = os.getenv('QWEN_API_KEY', 'YOUR_API_KEY')
    QWEN_MODEL_NAME = os.getenv('QWEN_MODEL_NAME', 'qwen3-next-80b-a3b-thinking')
    
    # OpenAI兼容配置（CrewAI需要）
    OPENAI_API_BASE = os.getenv('OPENAI_API_BASE', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'YOUR_API_KEY')
    
    # 其他配置
    VERBOSE = os.getenv('VERBOSE', 'True').lower() == 'true'
    
    # 模型参数配置
    MODEL_TEMPERATURE = float(os.getenv('MODEL_TEMPERATURE', '0.7'))
    MODEL_MAX_TOKENS = int(os.getenv('MODEL_MAX_TOKENS', '2048'))
    
    # 系统配置
    PROJECT_NAME = "BioCrew"
    VERSION = "1.0.0"
    
    # 数据库配置
    DB_TYPE = os.getenv('DB_TYPE', 'postgresql')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '5432'))
    DB_NAME = os.getenv('DB_NAME', 'Bio_data')
    DB_USER = os.getenv('DB_USER', 'nju_bio')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '980605Hyz')