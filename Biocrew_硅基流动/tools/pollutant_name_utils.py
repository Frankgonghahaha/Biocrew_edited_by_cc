#!/usr/bin/env python3
"""
污染物名称标准化工具
用于将不同格式的污染物名称转换为数据库中存储的标准化格式
"""

import re
from typing import List, Dict

def standardize_pollutant_name(pollutant_name: str) -> str:
    """
    将污染物名称标准化为数据库中存储的格式
    
    转换规则:
    1. 转换为小写
    2. 将连字符(-)替换为下划线(_)
    3. 将空格替换为下划线(_)
    4. 移除特殊字符
    5. 处理希腊字母(如β -> beta)
    
    Args:
        pollutant_name (str): 原始污染物名称
        
    Returns:
        str: 标准化后的污染物名称
    """
    if not pollutant_name:
        return ""
    
    # 转换为小写
    name = pollutant_name.lower()
    
    # 处理希腊字母
    greek_map = {
        'α': 'alpha',
        'β': 'beta',
        'γ': 'gamma',
        'δ': 'delta',
        'ε': 'epsilon',
        'ζ': 'zeta',
        'η': 'eta',
        'θ': 'theta',
        'ι': 'iota',
        'κ': 'kappa',
        'λ': 'lambda',
        'μ': 'mu',
        'ν': 'nu',
        'ξ': 'xi',
        'ο': 'omicron',
        'π': 'pi',
        'ρ': 'rho',
        'σ': 'sigma',
        'τ': 'tau',
        'υ': 'upsilon',
        'φ': 'phi',
        'χ': 'chi',
        'ψ': 'psi',
        'ω': 'omega'
    }
    
    for greek_char, english_name in greek_map.items():
        name = name.replace(greek_char, english_name)
    
    # 处理常见的缩写
    abbreviations = {
        'hch': 'hexachlorocyclohexane',
        'pcb': 'polychlorinated_biphenyl',
        'pah': 'polycyclic_aromatic_hydrocarbon'
    }
    
    for abbrev, full_name in abbreviations.items():
        # 只有当缩写是独立的词时才替换
        name = re.sub(r'\b' + re.escape(abbrev) + r'\b', full_name, name)
    
    # 将连字符和空格替换为下划线
    name = re.sub(r'[-\s]+', '_', name)
    
    # 移除特殊字符，只保留字母、数字和下划线
    name = re.sub(r'[^\w]', '_', name)
    
    # 合并多个下划线为单个下划线
    name = re.sub(r'_+', '_', name)
    
    # 移除开头和结尾的下划线
    name = name.strip('_')
    
    return name

def generate_pollutant_name_variants(pollutant_name: str) -> List[str]:
    """
    生成污染物名称的多种可能变体，用于搜索和匹配
    
    Args:
        pollutant_name (str): 原始污染物名称
        
    Returns:
        List[str]: 可能的名称变体列表
    """
    variants = set()
    original = pollutant_name
    
    # 原始名称
    variants.add(original)
    
    # 标准化名称
    standardized = standardize_pollutant_name(original)
    variants.add(standardized)
    
    # 小写版本
    variants.add(original.lower())
    
    # 处理连字符和下划线的变体
    with_underscores = original.replace('-', '_').replace(' ', '_')
    variants.add(with_underscores)
    
    with_hyphens = original.replace('_', '-').replace(' ', '-')
    variants.add(with_hyphens)
    
    # 无分隔符版本
    no_separators = re.sub(r'[-_\s]+', '', original)
    variants.add(no_separators)
    
    # 处理希腊字母的变体
    greek_variants = {
        'beta': 'β',
        'alpha': 'α',
        'gamma': 'γ',
        'delta': 'δ'
    }
    
    greek_version = original.lower()
    for english, greek in greek_variants.items():
        greek_version = greek_version.replace(english, greek)
    variants.add(greek_version)
    
    # 返回变体列表
    return list(variants)

# 测试函数
def test_standardize_pollutant_name():
    """测试标准化函数"""
    test_cases = [
        ("Beta-hexachlorocyclohexane", "beta_hexachlorocyclohexane"),
        ("β-Hexachlorocyclohexane", "beta_hexachlorocyclohexane"),
        ("BHC", "bhc"),
        ("Hexachlorocyclohexane", "hexachlorocyclohexane"),
        ("beta-HCH", "beta_hexachlorocyclohexane"),
        ("Alpha-hexachlorocyclohexane", "alpha_hexachlorocyclohexane")
    ]
    
    print("测试标准化函数:")
    for input_name, expected in test_cases:
        result = standardize_pollutant_name(input_name)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_name}' -> '{result}' (期望: '{expected}')")

if __name__ == "__main__":
    test_standardize_pollutant_name()