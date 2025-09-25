#!/usr/bin/env python3
"""
测试脚本：支持用户输入的数据库查询测试
用户可以输入污染物名称，系统将查询相关的基因和微生物数据
"""
import os, sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入数据库工具
from tools.database_tool_factory import DatabaseToolFactory
from tools.pollutant_data_query_tool import PollutantDataQueryTool
from tools.gene_data_query_tool import GeneDataQueryTool
from tools.organism_data_query_tool import OrganismDataQueryTool
from tools.pollutant_search_tool import PollutantSearchTool

def get_user_input():
    """获取用户输入的污染物名称"""
    print("请输入要查询的污染物名称:")
    print("例如: Alpha-hexachlorocyclohexane, Lindane, Benzene 等")
    pollutant_name = input("污染物名称: ").strip()
    return pollutant_name

def check_pollutant_data(pollutant_name):
    """检查指定污染物相关的基因和微生物数据"""
    print(f"检查 {pollutant_name} 相关数据...")
    print("=" * 50)
    
    # 使用数据库工具查询数据
    print("1. 查询基因数据...")
    gene_tool = GeneDataQueryTool()
    gene_result = gene_tool._run(pollutant_name)
    
    if gene_result.get("status") == "success":
        gene_data = gene_result.get("data", [])
        print(f"   ✓ 基因数据查询成功，共有 {len(gene_data)} 条数据")
        if gene_data:
            # 显示前几行数据
            print("   前5条基因数据:")
            for i, record in enumerate(gene_data[:5]):
                print(f"     {i+1}. {record}")
    else:
        print(f"   ✗ 基因数据查询失败: {gene_result.get('message')}")
    
    print("\n" + "-" * 30 + "\n")
    
    # 检查微生物数据
    print("2. 查询微生物数据...")
    organism_tool = OrganismDataQueryTool()
    organism_result = organism_tool._run(pollutant_name)
    
    if organism_result.get("status") == "success":
        organism_data = organism_result.get("data", [])
        print(f"   ✓ 微生物数据查询成功，共有 {len(organism_data)} 条数据")
        if organism_data:
            # 显示前几行数据
            print("   前5条微生物数据:")
            for i, record in enumerate(organism_data[:5]):
                print(f"     {i+1}. {record}")
    else:
        print(f"   ✗ 微生物数据查询失败: {organism_result.get('message')}")

def search_similar_pollutants(pollutant_name):
    """搜索相似污染物的数据"""
    print("\n" + "=" * 50)
    print("搜索相似污染物...")
    
    # 使用污染物搜索工具
    search_tool = PollutantSearchTool()
    search_result = search_tool._run(pollutant_name)
    
    if search_result.get("status") == "success":
        matches = search_result.get("data", [])
        print(f"找到 {len(matches)} 个匹配的污染物:")
        for i, match in enumerate(matches[:10], 1):  # 只显示前10个
            print(f"   {i}. {match}")
        if len(matches) > 10:
            print(f"   ... 还有 {len(matches) - 10} 个匹配项")
    else:
        print(f"搜索失败: {search_result.get('message')}")

def list_available_pollutants():
    """列出所有可用的污染物数据（使用搜索工具模拟）"""
    print("\n" + "=" * 50)
    print("可用的污染物数据:")
    
    # 使用污染物搜索工具列出一些常见污染物
    common_pollutants = [
        "Alpha-hexachlorocyclohexane",
        "Lindane", 
        "Benzene",
        "Toluene",
        "Xylene",
        "Chlorobenzene",
        "Phenol",
        "Aniline",
        "Naphthalene",
        "Anthracene"
    ]
    
    print("常见污染物:")
    for i, pollutant in enumerate(common_pollutants, 1):
        print(f"   {i}. {pollutant}")

if __name__ == "__main__":
    print("数据库查询测试脚本（支持用户输入）")
    print("=" * 50)
    
    # 列出所有可用的污染物
    list_available_pollutants()
    
    # 获取用户输入
    print("\n" + "=" * 50)
    pollutant_name = get_user_input()
    
    # 如果用户没有输入，则使用默认值
    if not pollutant_name:
        print("未输入污染物名称，使用默认值: Alpha-hexachlorocyclohexane")
        pollutant_name = "Alpha-hexachlorocyclohexane"
    
    # 检查数据
    check_pollutant_data(pollutant_name)
    search_similar_pollutants(pollutant_name)
    
    print("\n" + "=" * 50)
    print("查询完成")