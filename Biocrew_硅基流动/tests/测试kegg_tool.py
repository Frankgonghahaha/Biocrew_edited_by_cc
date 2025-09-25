# -*- coding: utf-8 -*-
"""
KEGG 工具最小可用性测试（模型优先 + 仅放开 KEGG）
- 彻底移除对项目内 CrewLLM 的依赖，改为文件内内置 CrewLLM Shim
- 优先使用本项目内的 Agent/Task；LLM 后端按顺序尝试：OpenAI SDK -> LiteLLM -> LangChain(ChatOpenAI)
"""

import os
import sys
from pathlib import Path

# ---- 将项目根目录加入 sys.path（优先导入本项目模块）----
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crewai import Crew, Process

# ---- 尝试导入项目内的 Agent / Task ----
from agents.engineering_microorganism_identification_agent import EngineeringMicroorganismIdentificationAgent
from tasks.microorganism_identification_task import MicroorganismIdentificationTask

# ---- Config shim：优先项目内 Config；否则读环境变量 ----
try:
    from config import Config  # 项目内 config.py
except Exception:
    class Config:
        OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE") or os.environ.get("OPENAI_API_BASE_URL") or "https://api.openai.com/v1"
        OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_TOKEN") or ""
        OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME") or os.environ.get("OPENAI_MODEL") or "gpt-4o-mini"

# ---- 环境级基础超时/重试，避免 None/空响应 ----
os.environ.setdefault("LITELLM_MAX_RETRIES", "2")
os.environ.setdefault("LITELLM_TIMEOUT", "60")
os.environ.setdefault("OPENAI_API_TIMEOUT", "60")
os.environ.setdefault("OPENAI_HTTP_CLIENT", "httpx")

# ---- 强化 LiteLLM provider 设置 + 模型前缀（避免 BadRequestError） ----
# 统一给 LiteLLM 明确 provider / base / key（CrewAI 某些分支会用到）
os.environ["LITELLM_PROVIDER"] = "siliconflow"
os.environ["LITELLM_BASE_URL"] = os.environ.get("OPENAI_API_BASE", Config.OPENAI_API_BASE)
os.environ["LITELLM_API_KEY"] = os.environ.get("OPENAI_API_KEY", Config.OPENAI_API_KEY)

# 确保模型名带有提供商前缀：siliconflow/xxx
_model = os.environ.get("OPENAI_MODEL_NAME") or getattr(Config, "OPENAI_MODEL_NAME", "")
if _model and not (_model.lower().startswith("siliconflow/") or _model.lower().startswith("openai/")):
    _model = f"siliconflow/{_model}"
    os.environ["OPENAI_MODEL_NAME"] = _model
    try:
        Config.OPENAI_MODEL_NAME = _model  # 同步回 Config（若可写）
    except Exception:
        pass
print(f"[LiteLLM] provider=siliconflow  base={os.environ['LITELLM_BASE_URL']}  model={os.environ.get('OPENAI_MODEL_NAME')}")

# ---- 内置 CrewLLM Shim：按 OpenAI -> LiteLLM -> LangChain 逐级兜底 ----
class CrewLLM:
    def __init__(self, api_base: str, api_key: str, model: str, temperature: float = 0.2):
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self._openai_client = None
        self._litellm = None
        self._lc = None

        # 尝试 OpenAI 官方 SDK (>=1.x)
        try:
            from openai import OpenAI  # type: ignore
            self._openai_client = OpenAI(base_url=self.api_base, api_key=self.api_key)
            print("[LLM Shim] 使用 OpenAI SDK 作为后端")
        except Exception:
            pass

        # 尝试 LiteLLM
        if self._openai_client is None:
            try:
                import litellm  # type: ignore
                self._litellm = litellm
                print("[LLM Shim] 使用 LiteLLM 作为后端")
            except Exception:
                pass

        # 尝试 LangChain ChatOpenAI（仅用于兜底）
        if self._openai_client is None and self._litellm is None:
            try:
                from langchain_openai import ChatOpenAI  # type: ignore
                self._lc = ChatOpenAI(
                    openai_api_base=self.api_base,
                    openai_api_key=self.api_key,
                    model_name=self.model,
                    temperature=self.temperature,
                )
                print("[LLM Shim] 使用 LangChain ChatOpenAI 作为后端")
            except Exception:
                pass

        if self._openai_client is None and self._litellm is None and self._lc is None:
            raise RuntimeError("没有可用的 LLM 后端：请安装 openai 或 litellm 或 langchain_openai 并设置 OPENAI_API_KEY")

    # 某些 Agent 可能需要拿到底层 LangChain LLM
    def to_langchain(self):
        return self._lc

    # 统一的对话调用接口
    def call(self, messages: list[dict]) -> str:
        # 优先 OpenAI SDK
        if self._openai_client is not None:
            resp = self._openai_client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=messages,
            )
            return (resp.choices[0].message.content or "").strip()

        # 其次 LiteLLM（OpenAI 兼容）
        if self._litellm is not None:
            resp = self._litellm.completion(
                model=self.model,
                api_base=self.api_base,
                api_key=self.api_key,
                temperature=self.temperature,
                messages=messages,
            )
            try:
                return (resp["choices"][0]["message"]["content"] or "").strip()
            except Exception:
                return str(resp)

        # 最后 LangChain：把多轮消息串接为单输入
        if self._lc is not None:
            text = "\n".join(f"{m.get('role')}: {m.get('content')}" for m in messages)
            out = self._lc.invoke(text)
            try:
                return (out.content or "").strip()
            except Exception:
                return str(out)

        return ""

# ---- 构造 LLM 客户端 ----
crew_llm = CrewLLM(
    api_base=Config.OPENAI_API_BASE,
    api_key=Config.OPENAI_API_KEY,
    model=Config.OPENAI_MODEL_NAME,
)

if not Config.OPENAI_API_KEY:
    print("[警告] OPENAI_API_KEY 为空：请在环境变量或 config.py 中设置可用的 API Key。")
print(f"[LLM] base={Config.OPENAI_API_BASE}  model={Config.OPENAI_MODEL_NAME}")

# ---- 初始化 Agent，并仅放开 KEGG 工具 ----
agent = EngineeringMicroorganismIdentificationAgent(crew_llm).create_agent()

# ---- 强制将 Agent 使用 LangChain 后端，绕过 LiteLLM 的 provider 检查 ----
try:
    lc = crew_llm.to_langchain()
    if lc is not None:
        agent.llm = lc
        print("[LLM] 已将 Agent 的 llm 切换为 LangChain ChatOpenAI")
    else:
        # 若没有 LangChain，则沿用上面已设定的 LiteLLM provider 与模型前缀
        print(f"[LLM] 无 LangChain，将使用 LiteLLM（provider={os.environ.get('LITELLM_PROVIDER')}, model={os.environ.get('OPENAI_MODEL_NAME')})")
except Exception as e:
    print(f"[LLM] 切换 Agent LLM 失败：{e}")

# ---- 若未探测到 KEGG 工具，直接注入一个 ----
try:
    from tools.kegg_tool import KeggTool  # 确保该路径正确
    if not any(('kegg' in (getattr(t, 'name', '') or '').lower()) for t in getattr(agent, 'tools', []) or []):
        agent.tools = list(getattr(agent, 'tools', []) or []) + [KeggTool()]
        print("[工具策略] 未检测到 KEGG 工具，已注入本地 KeggTool 1 个")
except Exception as e:
    print(f"[工具策略] 注入本地 KeggTool 失败：{e}")

try:
    all_tools = getattr(agent, 'tools', []) or []
    def _is_kegg_tool(t):
        name = (getattr(t, 'name', '') or '').lower()
        cls  = t.__class__.__name__.lower()
        desc = (getattr(t, 'description', '') or '').lower()
        return ('kegg' in name) or ('kegg' in cls) or ('kegg' in desc)
    kegg_tools = [t for t in all_tools if _is_kegg_tool(t)]
    agent.tools = kegg_tools
    print(f"[工具策略] 已启用 KEGG 工具 {len(kegg_tools)} 个：{[getattr(t, 'name', t.__class__.__name__) for t in kegg_tools]}")
    if not kegg_tools:
        print("[提示] 当前 Agent 没有可用的 KEGG 工具；已尝试自动注入。如仍为 0，请检查 tools/kegg_tool.py 的导入路径与类名。")
except Exception as e:
    print(f"[工具策略] 设置 KEGG 工具失败：{e}")

# ---- 构造任务：模型优先 + 仅一次 KEGG ----
prompt = (
    "【系统约束】本轮模型优先，仅在必要时允许最多 1 次 KEGG 调用；其它工具禁止。\n"
    "调用前先写出 ToolJustification（≤30字），参数需使用双引号。若不用工具也能给出可靠答案，则勿调用。\n"
    "请帮我在 KEGG 查询 glucose 相关的 pathway"
)

task = MicroorganismIdentificationTask(crew_llm).create_task(
    agent=agent,
    user_requirement=prompt
)

# ---- 运行并输出 ----
crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
try:
    result = crew.kickoff()
    print(result if isinstance(result, str) else str(result))
except Exception as e:
    print("[错误] Crew 执行失败：", e)
    print("[兜底] 改为直接 LLM 应答（不使用工具）……")
    try:
        text = crew_llm.call([
            {"role": "user", "content": prompt + "\n\n不要调用任何外部工具，直接回答。"}
        ])
        print(text or "(空响应)")
    except Exception as e2:
        print("[兜底失败] 直连 LLM 仍失败：", e2)