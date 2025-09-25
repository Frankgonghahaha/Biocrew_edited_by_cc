#!/usr/bin/env python3
"""
工程微生物组识别任务
负责根据水质净化目标识别工程微生物组
"""

class MicroorganismIdentificationTask:
    def __init__(self, llm):
        self.llm = llm

    def create_task(self, agent, context_task=None, feedback=None, user_requirement=None):
        from crewai import Task
        
        description = """
        【任务目标】
        在给定水质净化目标下，识别候选功能微生物与代谢互补微生物，并形成可执行的组合建议。

        【总原则（模型优先 + 工具为辅）】
        1) 先由模型进行专业分析与初选（不依赖工具），给出直答与关键假设；
        2) 仅在以下情形调用工具进行“佐证/补全/编号检索”：
           - 需要精确编号/链接（NCBI accession、DOI、KEGG/EnviPath条目等）；
           - 关键信息不确定，模型自评置信度较低；
           - 用户明确要求“查库/给出最新数据”；
           - 需要聚合结构化表格或跨多源比对；
        3) 工具调用需最小化，遵循系统级 TOOL_BUDGET 和严格模式；
        4) 工具异常/空结果时，不得中断；必须走回退路径并明确说明。

        【识别步骤】
        # A. 目标理解与污染物标准化（不使用工具）
        - 解析水质治理指标、目标污染物与工况限制（温度、pH、盐度、溶氧、是否厌氧等）；
        - 对用户输入中的污染物进行“名称标准化”：
          · 统一全/半角、大小写、空格/连字符；
          · 生成同义词/缩写/常见别名的候选（如 PAHs、PCBs、TCE、DEHP/DBP 等）；
          · 得到“标准科学术语(英文)”与“原始表达(中文/英文)”的映射；
        - 输出模型直答的初版候选菌群与互补思路，并给出置信度(0–1)与关键假设清单。

        # B. 本地数据库与外部数据（必要时，才调用工具）
        - 仅在需要时调用：
          · pollutant_data_query_tool._run({"pollutant_name": "标准名", "data_type": "both"})
          · pollutant_summary_tool._run({"pollutant_name": "标准名"})
          · envipath_tool._run({"operation": "search_compound", "compound_name": "标准名"})
          · kegg_tool._run({"operation": "find_entries", "database": "genes", "keywords": "标准关键词"})
        - 调用前先在答案中写出：ToolJustification（≤30字），并严格使用双引号；
        - 对单一污染物，最多尝试 2–3 个名称变体（原文/翻译/常见别名）。

        # C. 证据整合与回退策略
        - 若工具返回空/错误：
          · 记录失败原因（工具名/参数/错误信息）；
          · 给出上位类别（如“多环芳烃/有机氯/邻苯二甲酸酯”等）与可替代的通路/基团级微生物与基因（如脱卤、加氧酶、单加氧酶等）；
          · 明确可执行的替代方案（例如：用通路级基因/菌属做先导试验）；
        - 若工具不可用：仍需产出“最小有用”方案（模型直答 + 假设 + 实验建议）。

        【结果应包含的计算/判断要点】
        - 目标污染物的降解途径假设（关键反应、可能的酶/基因族、需氧/厌氧条件）；
        - 候选功能微生物清单；
        - 代谢互补设计：
          · 中间体/共代谢依赖关系、电子受体/供体、维生素/辅因子互补；
          · 温度、pH、盐度、溶氧等工况兼容性；
        - 竞争/互补的定性评分（若缺数据，说明假设来源与不确定性）。

        【数据查询与格式要求】
        - pollutant_name 参数必须使用“翻译后的标准科学术语(英文)”；
        - 所有参数使用双引号；
        - 报告中同时给出：原始污染物表达 × 标准术语映射表；
        - 在“数据来源与可信度”中，逐条列出：是否来自工具、工具名、检索词、命中条目、链接/编号、失败原因（若有）。
        """
        
        # 添加用户自定义需求到描述中
        if user_requirement:
            description += f"\n\n用户具体需求：{user_requirement}"
        
        if feedback:
            description += f"\n\n根据评估反馈进行优化设计：\n{feedback}"
        
        expected_output = """
        【交付物：工程微生物组识别报告】
        一、模型直答（不依赖工具）
          - 结论摘要（≤10行）：候选功能微生物 + 互补思路
          - 关键假设与边界条件
          - 自评置信度(0–1)
          - 是否调用工具：是/否（次数）

        二、污染物名称标准化
          - 原始表达 → 标准科学术语（表格）
          - 常见同义词/缩写/别名（若有）

        三、（若调用）工具查询纪要
          - ToolJustification：调用原因（≤30字）
          - 每次调用：工具名、参数、命中条目、核心数据摘录、链接/编号
          - 失败或为空时：失败原因与处理（变体检索/回退策略）

        四、候选功能微生物与代谢互补设计
          - 功能微生物列表（来源：模型/工具，分别标注）
          - 代谢互补关系（中间体/电子受体供体/辅因子）
          - 工况兼容性（温度、pH、氧条件、盐度等）
          - 竞争/互补指数（若缺数据，给出定性判断与不确定性）

        五、降解途径假设与基因/酶族
          - 关键反应步骤与候选酶/基因（如加氧酶、单加氧酶、脱卤酶等）
          - 需氧/厌氧通路分歧与判据

        六、数据完整性与可信度评估
          - 哪些结论来自工具数据，哪些来自模型推理
          - 数据缺口清单与下一步计划（实验/补数/替代表）

        （可选）附录：若需结构化输出，请同时给出一个 JSON 块，键包括：
          {"pollutants": [...], "candidates": [...], "complements": [...], "evidence": [...], "limitations": [...], "next_steps": [...]}。
        """
        
        # 如果有上下文任务，设置依赖关系
        task_params = {
            'description': description.strip(),
            'expected_output': expected_output.strip(),
            'agent': agent,
            'verbose': True
        }
        
        if context_task:
            task_params['context'] = [context_task]
            
        return Task(**task_params)