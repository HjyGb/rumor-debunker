"""
辟谣专家 Agent - 主入口
符合 Coze Agent 规范的标准实现
"""
import os
import json
from typing import Annotated

# 尝试加载 .env 文件中的环境变量
try:
    from dotenv import load_dotenv
    # 尝试从项目根目录加载 .env 文件
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except Exception:
    pass

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from storage.memory.memory_saver import get_memory_saver

from .rumor_workflow import RumorDebunkerWorkflow

# 配置文件路径
LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]


class AgentState(MessagesState):
    """Agent 状态"""
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """
    构建辟谣专家 Agent
    
    Args:
        ctx: 运行时上下文
        
    Returns:
        Agent 实例
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)
    
    # 如果工作区路径不存在（本地开发），使用相对路径
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', LLM_CONFIG)

    # 加载配置
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在：{config_path}")
        
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    # 获取 API 配置
    api_key = os.getenv("DASHSCOPE_API_KEY")
    base_url = os.getenv("DASHSCOPE_BASE_URL")
    
    # 检查 API Key 是否配置
    if not api_key:
        raise ValueError(
            "未配置 DASHSCOPE_API_KEY 环境变量。\n"
            "请在项目根目录创建 .env 文件，并设置：\n"
            "DASHSCOPE_API_KEY=sk-your_api_key_here\n"
            "DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    
    if not base_url:
        raise ValueError(
            "未配置 DASHSCOPE_BASE_URL 环境变量。\n"
            "请在项目根目录创建 .env 文件，并设置：\n"
            "DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

    # 创建 LLM 实例
    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        }
    )

    # 创建 Agent
    agent = create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=[],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )

    return agent


# 初始化工作流实例（用于直接调用）
_workflow = None


def get_workflow():
    """获取工作流实例（延迟初始化）"""
    global _workflow
    if _workflow is None:
        _workflow = RumorDebunkerWorkflow()
    return _workflow


def analyze_rumor(text: str = None, image_url: str = None):
    """
    便捷函数：分析谣言
    
    Args:
        text: 输入文本
        image_url: 图片URL
        
    Returns:
        分析结果
    """
    workflow = get_workflow()
    return workflow.run(text=text, image_url=image_url)


if __name__ == "__main__":
    # 测试运行
    test_text = "喝白酒可以预防新冠病毒，这个说法是真的吗？"
    
    print("="*60)
    print("辟谣专家多智能体系统 - 测试运行")
    print("="*60)
    print(f"\n输入文本: {test_text}\n")
    
    result = analyze_rumor(text=test_text)
    
    if result.get("success"):
        print("\n✅ 分析成功!")
        if result.get("report_result", {}).get("readable_report"):
            print(result["report_result"]["readable_report"])
    else:
        print(f"\n❌ 分析失败: {result.get('error')}")
