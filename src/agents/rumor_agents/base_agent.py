"""
基础智能体类
所有智能体的基类，提供统一的 LLM 调用接口
使用阿里百炼云 API（通过 OpenAI 兼容模式）
"""
import os
import json
from typing import Optional, List, Dict, Any, Union
from abc import ABC, abstractmethod

# 尝试加载 .env 文件中的环境变量
try:
    from dotenv import load_dotenv
    # 尝试从项目根目录加载 .env 文件
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except Exception:
    pass

from openai import OpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


class BaseAgent(ABC):
    """基础智能体抽象类"""
    
    def __init__(self, name: str, description: str):
        """
        初始化基础智能体
        
        Args:
            name: 智能体名称
            description: 智能体描述
        """
        self.name = name
        self.description = description
        
        # 检查是否配置了 API Key 和 Base URL
        api_key = os.getenv("DASHSCOPE_API_KEY")
        base_url = os.getenv("DASHSCOPE_BASE_URL")
        
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
        
        # 初始化 OpenAI 客户端（兼容阿里百炼云）
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
    def _get_config(self) -> Dict[str, Any]:
        """获取配置"""
        workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
        config_path = os.path.join(workspace_path, "config/agent_llm_config.json")
        
        # 如果工作区路径不存在（本地开发），使用相对路径
        if not os.path.exists(config_path):
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "config/agent_llm_config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def call_llm(
        self,
        messages: List[Union[HumanMessage, SystemMessage, AIMessage]],
        temperature: float = 0.7,
        model: Optional[str] = None,
        thinking: str = "disabled",
        streaming: bool = False
    ) -> str:
        """
        调用大语言模型（使用 OpenAI SDK 兼容阿里百炼云）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            model: 模型名称
            thinking: 是否启用思考模式（暂不支持）
            streaming: 是否流式输出
            
        Returns:
            模型响应文本
        """
        config = self._get_config()
        model_name = model or config.get("config", {}).get("model", "qwen-plus")
        
        # 转换为 OpenAI 格式的消息
        openai_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                openai_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": msg.content})
        
        try:
            if streaming:
                # 流式输出
                response_stream = self.client.chat.completions.create(
                    model=model_name,
                    messages=openai_messages,
                    temperature=temperature,
                    stream=True
                )
                response_text = ""
                for chunk in response_stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        response_text += chunk.choices[0].delta.content
                return response_text
            else:
                # 非流式输出
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=openai_messages,
                    temperature=temperature
                )
                return response.choices[0].message.content
        except Exception as e:
            error_msg = f"调用 LLM 失败：{str(e)}"
            print(f"\n❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    def call_vision_llm(
        self,
        text: str,
        image_url: str,
        temperature: float = 0.3,
        model: Optional[str] = None
    ) -> str:
        """
        调用多模态模型（文本 + 图片）
            
        Args:
            text: 文本内容
            image_url: 图片 URL（base64 或 http 链接）
            temperature: 温度参数
            model: 模型名称
                
        Returns:
            模型响应文本
        """
        # 使用视觉模型
        vision_model = model or "qwen-vl-plus"
            
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
            
        try:
            response = self.client.chat.completions.create(
                model=vision_model,
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = f"调用视觉 LLM 失败：{str(e)}"
            print(f"\n❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    @abstractmethod
    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        处理输入数据（子类必须实现）
        
        Args:
            input_data: 输入数据
            
        Returns:
            处理结果字典
        """
        pass
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"
