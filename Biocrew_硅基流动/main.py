#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于CrewAI的水质生物净化技术开发多智能体系统（硅基流动 OpenAI 兼容）
- 加载 main.py 同目录的 .env / .env.local
- 使用 CrewAI 自带 LLM（底层 LiteLLM），显式 provider=openai 与 api_base
- 自动规范化模型名（Qwen/ 命名空间），避免 “Model does not exist”
- 避免空响应：api_base 正确、max_tokens 2048（可再调大）
- 新增【闲聊/健康检查快通道】：简单输入直接单轮回复，不触发任何 Agent/Task
"""

import os
import sys
import re
from typing import Optional

# 保证导入路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)

# ------------------ 更强的 .env 加载 ------------------
def load_env_hard(project_dir: str) -> Optional[str]:
    from dotenv import load_dotenv, dotenv_values

    # 清理历史残留
    for k in ("OPENAI_API_BASE", "OPENAI_API_KEY", "OPENAI_MODEL_NAME", "MODEL"):
        v = os.environ.get(k, "")
        if v.startswith("https://dashscope.aliyuncs.com") or v.lower().endswith(("api_key", "key_here", "your_api_key")):
            os.environ.pop(k, None)

    candidates = [os.path.join(project_dir, ".env.local"),
                  os.path.join(project_dir, ".env")]

    used = None
    for path in candidates:
        if os.path.exists(path):
            load_dotenv(path, override=True)
            used = path
            break

    if not used:
        return None

    raw = dotenv_values(used)
    for k in ("OPENAI_API_BASE", "OPENAI_API_KEY", "OPENAI_MODEL_NAME"):
        v = raw.get(k)
        if v:
            os.environ[k] = v.strip().strip('"').strip("'")

    return used

used_env = load_env_hard(CURRENT_DIR)

# ------------------ 配置 ------------------
try:
    from config.config import Config
except Exception:
    class Config:
        VERBOSE = True
        MODEL_TEMPERATURE = 0.7
        MODEL_MAX_TOKENS = 8000  # 先保守，避免空响应

from crewai import Crew, Process, LLM as CrewLLM

# agents
from agents.engineering_microorganism_identification_agent import EngineeringMicroorganismIdentificationAgent
from agents.microbial_agent_design_agent import MicrobialAgentDesignAgent
from agents.microbial_agent_evaluation_agent import MicrobialAgentEvaluationAgent
from agents.implementation_plan_generation_agent import ImplementationPlanGenerationAgent
from agents.knowledge_management_agent import KnowledgeManagementAgent
from agents.task_coordination_agent import TaskCoordinationAgent

# tasks
from tasks.microorganism_identification_task import MicroorganismIdentificationTask
from tasks.microbial_agent_design_task import MicrobialAgentDesignTask
from tasks.microbial_agent_evaluation_task import MicrobialAgentEvaluationTask
from tasks.implementation_plan_generation_task import ImplementationPlanGenerationTask
from tasks.task_coordination_task import TaskCoordinationTask

# tools
#from tools.evaluation_tool import EvaluationTool


def _print_env_diag():
    print("====== 环境变量诊断 ======")
    print("工作目录:", os.getcwd())
    print("main.py 目录:", CURRENT_DIR)
    print(".env 使用路径:", used_env or "(未找到)")
    print("OPENAI_API_BASE:", os.environ.get("OPENAI_API_BASE", "(未设置)"))
    key = os.environ.get("OPENAI_API_KEY")
    print("OPENAI_API_KEY:", ("***" + key[-6:]) if key else "(未设置)")
    print("OPENAI_MODEL_NAME:", os.environ.get("OPENAI_MODEL_NAME", "(未设置)"))
    print("MODEL:", os.environ.get("MODEL", "(未设置)"))
    print("=========================")


def _ensure_openai_env() -> tuple[str, str, str]:
    base = os.environ.get("OPENAI_API_BASE", "").strip()
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("OPENAI_MODEL_NAME", "").strip()

    if base.startswith("https://dashscope.aliyuncs.com"):
        raise RuntimeError("检测到 OPENAI_API_BASE 仍指向 DashScope，请改为 https://api.siliconflow.cn/v1。")

    if not base or not key or not model:
        raise RuntimeError("OPENAI_* 未设置完整（OPENAI_API_BASE / OPENAI_API_KEY / OPENAI_MODEL_NAME）。")

    # 规范化模型名：硅基流动常用命名空间 Qwen/...
    if "/" not in model and model.lower().startswith("qwen"):
        print(f"[规范化] 检测到裸模型名 '{model}'，自动规范为命名空间ID")
        model = f"Qwen/{model}"

    return base, key, model


def get_user_input() -> str:
    print("请输入您的水质处理需求（若仅为测试可直接输入：你好 / hi / hello / 测试）:")
    return input("输入: ").strip()


def get_processing_mode() -> int:
    print("\n请选择处理模式:")
    print("1. 链式处理模式（按固定顺序执行）")
    print("2. 自主选择模式（智能体根据情况自主选择）")
    while True:
        s = input("请输入模式选择 (1 或 2): ").strip()
        if s in {"1", "2"}:
            return int(s)
        print("无效输入，请输入 1 或 2")


def analyze_evaluation_result(evaluation_result):
    return EvaluationTool().analyze_evaluation_result(evaluation_result)


def is_smalltalk_or_sanity_check(text: str) -> bool:
    """判断是否是寒暄/探针输入：避免触发大流程"""
    if not text:
        return True
    patterns = [
        r"^\s*你好\s*$",
        r"^\s*您好\s*$",
        r"^\s*hi\s*$",
        r"^\s*hello\s*$",
        r"^\s*测试\s*$",
        r"^\s*hey\s*$",
        r"^\s*哈喽\s*$",
        r"^\s*hello world\s*$",
    ]
    return any(re.match(p, text, flags=re.IGNORECASE) for p in patterns)


def direct_llm_reply(llm: CrewLLM, prompt: str) -> str:
    """
    走一跳直连 LLM 的健康检查/闲聊，不调度任何 Agent/Task。
    注意：CrewLLM.call() 的参数只接受 messages / tools 等，max_tokens/temperature
    已在初始化 CrewLLM(...) 时配置，这里不要重复传入。
    """
    try:
        resp = llm.call(messages=[{"role": "user", "content": prompt or "你好"}])

        # 兼容两种返回：字符串 或 OpenAI 风格 dict
        if isinstance(resp, str):
            return resp.strip()

        if isinstance(resp, dict):
            choices = resp.get("choices") or []
            if choices:
                msg = choices[0].get("message") or {}
                content = (msg.get("content") or "").strip()
                if content:
                    return content

        return "（收到请求，模型已连通，但未返回可读文本）"
    except Exception as e:
        return f"（直连测试失败：{e}）"


def run_autonomous_workflow(user_requirement: str, llm: CrewLLM):
    print("开始自主任务执行流程...")
    identification_agent = EngineeringMicroorganismIdentificationAgent(llm).create_agent()
    design_agent = MicrobialAgentDesignAgent(llm).create_agent()
    evaluation_agent = MicrobialAgentEvaluationAgent(llm).create_agent()
    plan_agent = ImplementationPlanGenerationAgent(llm).create_agent()
    knowledge_agent = KnowledgeManagementAgent(llm).create_agent()
    coordination_agent = TaskCoordinationAgent(llm).create_agent()

    coordination_task = TaskCoordinationTask(llm).create_task(coordination_agent)
    identification_task = MicroorganismIdentificationTask(llm).create_task(identification_agent, user_requirement=user_requirement)
    design_task = MicrobialAgentDesignTask(llm).create_task(design_agent, identification_task, user_requirement=user_requirement)
    evaluation_task = MicrobialAgentEvaluationTask(llm).create_task(evaluation_agent, design_task)
    plan_task = ImplementationPlanGenerationTask(llm).create_task(plan_agent, evaluation_task)

    crew = Crew(
        agents=[identification_agent, design_agent, evaluation_agent, plan_agent, knowledge_agent],
        tasks=[coordination_task, identification_task, design_task, evaluation_task, plan_task],
        process=Process.hierarchical,
        manager_agent=coordination_agent,
        verbose=getattr(Config, "VERBOSE", True),
    )
    return crew.kickoff()


def run_dynamic_workflow(user_requirement: str, llm: CrewLLM):
    print("开始动态任务执行流程...")
    identification_agent = EngineeringMicroorganismIdentificationAgent(llm).create_agent()
    design_agent = MicrobialAgentDesignAgent(llm).create_agent()
    evaluation_agent = MicrobialAgentEvaluationAgent(llm).create_agent()
    plan_agent = ImplementationPlanGenerationAgent(llm).create_agent()
    knowledge_agent = KnowledgeManagementAgent(llm).create_agent()

    crew_agents = [identification_agent, design_agent, evaluation_agent, plan_agent, knowledge_agent]

    identification_result = None
    evaluation_result = None
    plan_result = None

    max_iter = 3
    guidance = (
        "重要数据处理指导：\n"
        "1. 优先使用专门的数据查询工具(PollutantDataQueryTool、GeneDataQueryTool等)\n"
        "2. 缺失数据时继续分析并明确指出缺失\n"
        "3. 调用外部数据库工具(EnviPath、KEGG等)补充\n"
        "4. 最终报告中列出具体微生物与基因，不仅依赖预训练知识"
    )

    for i in range(1, max_iter + 1):
        print(f"执行第 {i} 轮任务流程...")

        if identification_result:
            identification_task = MicroorganismIdentificationTask(llm).create_task(
                identification_agent,
                user_requirement=guidance,
                feedback=f"根据上一轮评估结果重新识别。上一轮结果: {identification_result}\n\n{guidance}"
            )
        else:
            identification_task = MicroorganismIdentificationTask(llm).create_task(
                identification_agent,
                user_requirement=f"{user_requirement}\n\n{guidance}"
            )

        crew1 = Crew(agents=crew_agents, tasks=[identification_task], process=Process.sequential, verbose=getattr(Config, "VERBOSE", True))
        identification_result = crew1.kickoff()
        print("识别任务完成:", identification_result)

        design_task = MicrobialAgentDesignTask(llm).create_task(design_agent, identification_task, user_requirement=user_requirement)
        crew2 = Crew(agents=crew_agents, tasks=[design_task], process=Process.sequential, verbose=getattr(Config, "VERBOSE", True))
        design_result = crew2.kickoff()
        print("设计任务完成:", design_result)

        evaluation_task = MicrobialAgentEvaluationTask(llm).create_task(evaluation_agent, design_task)
        crew3 = Crew(agents=crew_agents, tasks=[evaluation_task], process=Process.sequential, verbose=getattr(Config, "VERBOSE", True))
        evaluation_result = crew3.kickoff()
        print("评估任务完成:", evaluation_result)

        analysis = analyze_evaluation_result(str(evaluation_result))
        core_ok = analysis.get("core_standards_met", False) if isinstance(analysis, dict) else bool(analysis)
        if core_ok:
            print("评估结果达标，进入方案阶段...")
            plan_task = ImplementationPlanGenerationTask(llm).create_task(plan_agent, evaluation_task)
            crew4 = Crew(agents=crew_agents, tasks=[plan_task], process=Process.sequential, verbose=getattr(Config, "VERBOSE", True))
            plan_result = crew4.kickoff()
            print("方案生成任务完成:", plan_result)
            break
        else:
            print("评估未达标，准备下一轮...")

    if plan_result:
        return plan_result
    if evaluation_result:
        return f"最终评估结果: {evaluation_result}"
    return "任务执行失败"


def main():
    print("基于CrewAI的水质生物净化技术开发多智能体系统")
    print("=" * 50)
    _print_env_diag()

    # 明确报错：没有读到 .env
    if not used_env:
        print("错误：未在 main.py 同目录找到 .env 或 .env.local。请将你的 .env 放在：", CURRENT_DIR)
        print("示例内容：\nOPENAI_API_BASE=https://api.siliconflow.cn/v1\nOPENAI_API_KEY=sk-xxx\nOPENAI_MODEL_NAME=Qwen/Qwen3-30B-A3B-Instruct-2507")
        return

    try:
        openai_base, openai_key, openai_model = _ensure_openai_env()
    except Exception as e:
        print("错误：", e)
        return

    # ====== 关键：CrewAI 自带 LLM + 显式 provider/openai 与 api_base ======
    prefixed_model = openai_model if openai_model.startswith(("openai/", "azure/")) else f"openai/{openai_model}"

    # 同步到环境，防止内部其他路径读取
    os.environ["OPENAI_API_BASE"] = openai_base
    os.environ["OPENAI_API_KEY"] = openai_key
    os.environ["OPENAI_MODEL_NAME"] = prefixed_model
    os.environ["MODEL"] = prefixed_model
    os.environ["LLM_PROVIDER"] = "openai"
    os.environ["LITELLM_PROVIDER"] = "openai"

    print(f"[LLM] Using provider=openai, model={prefixed_model}")
    print(f"[LLM] api_base={openai_base}")

    try:
        # ✅ 注意：CrewLLM 里要用 api_base，而不是 base_url
        crew_llm = CrewLLM(
            model=prefixed_model,                 # openai/Qwen/...
            api_key=openai_key,
            api_base=openai_base,                # <— 关键
            temperature=getattr(Config, "MODEL_TEMPERATURE", 0.7),
            max_tokens=getattr(Config, "MODEL_MAX_TOKENS", 2048),
        )
        print("   ✓ CrewLLM 初始化成功")
    except Exception as e:
        print(f"   ✗ CrewLLM 初始化失败: {e}")
        return

    user_requirement = get_user_input()

    # ====== 快通道：闲聊/健康检查，不触发多智能体 ======
    if is_smalltalk_or_sanity_check(user_requirement):
        print("\n[直连测试] 已进入健康检查/闲聊快通道（不调度任何 Agent/Task）")
        reply = direct_llm_reply(crew_llm, user_requirement or "你好")
        print("\n模型回复：\n" + reply)
        return

    # 复杂需求再走工作流
    mode = get_processing_mode()

    if mode == 1:
        print("使用链式处理模式...")
        result = run_dynamic_workflow(user_requirement, crew_llm)
    else:
        print("使用自主选择模式...")
        result = run_autonomous_workflow(user_requirement, crew_llm)

    print("最终结果:")
    print(result)


if __name__ == "__main__":
    main()
