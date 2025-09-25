#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
【简易版】基于CrewAI的水质生物净化技术开发多智能体系统
- 目标：仅执行“工程菌种鉴定”任务，用于调试和验证第一个Agent的输出。
- 保留了完整的环境加载、LLM配置和闲聊快通道逻辑。
- 移除了后续的设计、评估、方案生成等Agent和Task，简化了工作流。
"""

# === 单Agent工作流（已移除任务协调智能体）===
# 本脚本仅保留“工程微生物识别智能体”，不引入任何协调/仲裁 Agent。

import os
import sys
import re
from typing import Optional

# 保证导入路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)

# ------------------ 更强的 .env 加载 (保持不变) ------------------
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

# ------------------ 配置 (保持不变) ------------------
try:
    from config.config import Config
except Exception:
    class Config:
        VERBOSE = True
        MODEL_TEMPERATURE = 0.7
        MODEL_MAX_TOKENS = 8000

from crewai import Crew, Process, LLM as CrewLLM

# ===== 核心简化：只导入需要的Agent和Task =====
from agents.engineering_microorganism_identification_agent import EngineeringMicroorganismIdentificationAgent
from tasks.microorganism_identification_task import MicroorganismIdentificationTask


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

    if "/" not in model and model.lower().startswith("qwen"):
        print(f"[规范化] 检测到裸模型名 '{model}'，自动规范为命名空间ID")
        model = f"Qwen/{model}"

    return base, key, model


def get_user_input() -> str:
    print("请输入您的水质处理需求（若仅为测试可直接输入：你好 / hi / hello / 测试）:")
    return input("输入: ").strip()

# ===== 闲聊/健康检查功能 (保持不变) =====
def is_smalltalk_or_sanity_check(text: str) -> bool:
    if not text:
        return True
    patterns = [
        r"^\s*你好\s*$", r"^\s*您好\s*$", r"^\s*hi\s*$", r"^\s*hello\s*$",
        r"^\s*测试\s*$", r"^\s*hey\s*$", r"^\s*哈喽\s*$", r"^\s*hello world\s*$",
    ]
    return any(re.match(p, text, flags=re.IGNORECASE) for p in patterns)


def direct_llm_reply(llm: CrewLLM, prompt: str) -> str:
    try:
        resp = llm.call(messages=[{"role": "user", "content": prompt or "你好"}])
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

# ===== 对话缓冲与拼接工具 =====
CHAT_HISTORY = []  # [("user", text), ("assistant", text), ...]
HISTORY_MAX_TURNS = 6  # 仅携带最近 N 轮，避免上下文过长

def build_history_prompt(user_input: str) -> str:
    """将最近的对话历史拼接到当前需求中，便于形成连续对话。"""
    if not CHAT_HISTORY:
        return user_input
    # 仅取最近 N 轮（用户 + 助手合计 2N 条）
    pairs = []
    u, a = None, None
    # 从尾部反向扫描，收集最近的用户-助手成对轮次
    tmp = []
    for role, text in reversed(CHAT_HISTORY):
        tmp.append((role, text))
        if len(tmp) >= 2 and tmp[-2][0] == 'user' and tmp[-1][0] == 'assistant':
            pairs.append((tmp[-2][1], tmp[-1][1]))
            if len(pairs) >= HISTORY_MAX_TURNS:
                break
    pairs.reverse()
    history_lines = []
    for i, (uu, aa) in enumerate(pairs, 1):
        history_lines.append(f"[历史第{i}轮]\n用户: {uu}\n助手: {aa}")
    history_block = "\n\n".join(history_lines)
    return (
        "【对话历史（可作为上下文参考）】\n" + history_block +
        "\n\n【当前用户输入】\n" + user_input +
        "\n\n【要求】请在充分理解历史语境的基础上连续回答。若需外部工具，仅在必要时最小化调用。"
    )

# ===== 交互式对话循环 =====
HELP_TEXT = (
    "\n指令：/exit 退出；/reset 清空上下文；/help 查看帮助。"\
    "\n直接输入业务问题即可与智能体连续对话。\n"
)

def chat_loop(crew_llm: CrewLLM):
    print("\n[对话模式] 已启动。" + HELP_TEXT)
    
    # 1) 初始化需要的Agent（只建一次，复用）
    identification_agent = EngineeringMicroorganismIdentificationAgent(crew_llm).create_agent()
    # === 渐进放开：仅允许 KEGG 小工具，其余禁用 ===
    try:
        all_tools = getattr(identification_agent, 'tools', []) or []
        def _is_kegg_tool(t):
            name = (getattr(t, 'name', '') or '').lower()
            cls  = t.__class__.__name__.lower()
            desc = (getattr(t, 'description', '') or '').lower()
            return ('kegg' in name) or ('kegg' in cls) or ('kegg' in desc)
        kegg_tools = [t for t in all_tools if _is_kegg_tool(t)]
        identification_agent.tools = kegg_tools
        names = [getattr(t, 'name', t.__class__.__name__) for t in kegg_tools]
        print(f"[工具策略] 已启用 KEGG 工具 {len(kegg_tools)} 个：{names if names else '[]'}；其余全部禁用")
    except Exception as e:
        print(f"[工具策略] 设置 KEGG 工具失败：{e}")
    
    while True:
        try:
            user_text = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[对话模式] 已退出。")
            break
        if not user_text:
            continue
        if user_text.lower() in {"/exit", ":q", "quit", "exit"}:
            print("[对话模式] 再见！")
            break
        if user_text.lower() in {"/help", "help", "?"}:
            print(HELP_TEXT)
            continue
        if user_text.lower() in {"/reset", "reset"}:
            CHAT_HISTORY.clear()
            print("[对话模式] 已清空上下文。")
            continue

        # 快通道：寒暄/健康检查
        if is_smalltalk_or_sanity_check(user_text):
            reply = direct_llm_reply(crew_llm, user_text)
            print("助手:\n" + reply)
            CHAT_HISTORY.append(("user", user_text))
            CHAT_HISTORY.append(("assistant", reply))
            continue

        # 2) 将历史拼接到当前需求，构造任务输入
        merged_requirement = build_history_prompt(user_text)
        merged_requirement = (
            "【系统约束】本轮模型优先，仅允许在必要时调用 1 次 KEGG 工具；其它工具禁止。\n"
            "调用前先在答案中写出 ToolJustification（≤30字），并仅使用标准双引号参数。若不用工具也能给出可靠答案，则勿调用。\n"
            + merged_requirement
        )

        # 3) 为本轮创建 Task 与 Crew，并执行
        identification_task = MicroorganismIdentificationTask(crew_llm).create_task(
            agent=identification_agent,
            user_requirement=merged_requirement
        )
        # 单Agent Crew：只包含工程微生物识别智能体，无任务协调者
        crew = Crew(
            agents=[identification_agent],
            tasks=[identification_task],
            process=Process.sequential,
            verbose=getattr(Config, "VERBOSE", True)
        )
        try:
            result = crew.kickoff()
            text = result if isinstance(result, str) else str(result)
        except Exception as e:
            text = f"（执行出错：{e}）"
        
        print("助手:\n" + text)
        CHAT_HISTORY.append(("user", user_text))
        CHAT_HISTORY.append(("assistant", text))


def main():
    print("【简易版】水质生物净化技术开发多智能体系统")
    print(">> 模式：仅执行第一步“工程菌种鉴定” <<")
    print("=" * 50)
    _print_env_diag()

    if not used_env:
        print("错误：未在 main.py 同目录找到 .env 或 .env.local。")
        return

    try:
        openai_base, openai_key, openai_model = _ensure_openai_env()
    except Exception as e:
        print("错误：", e)
        return

    prefixed_model = openai_model if openai_model.startswith(("openai/", "azure/")) else f"openai/{openai_model}"
    os.environ["OPENAI_API_BASE"] = openai_base
    os.environ["OPENAI_API_KEY"] = openai_key
    os.environ["OPENAI_MODEL_NAME"] = prefixed_model
    os.environ["MODEL"] = prefixed_model
    os.environ["LLM_PROVIDER"] = "openai"
    os.environ["LITELLM_PROVIDER"] = "openai"

    print(f"[LLM] Using provider=openai, model={prefixed_model}")
    print(f"[LLM] api_base={openai_base}")

    try:
        crew_llm = CrewLLM(
            model=prefixed_model,
            api_key=openai_key,
            api_base=openai_base,
            temperature=getattr(Config, "MODEL_TEMPERATURE", 0.7),
            max_tokens=getattr(Config, "MODEL_MAX_TOKENS", 8000),
        )
        print("   ✓ CrewLLM 初始化成功")
    except Exception as e:
        print(f"   ✗ CrewLLM 初始化失败: {e}")
        return

    print("[模式] 单Agent：仅工程微生物识别智能体（无任务协调）")

    # 进入对话模式（默认）
    chat_loop(crew_llm)


if __name__ == "__main__":
    main()