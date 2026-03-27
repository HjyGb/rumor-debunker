"""
调度智能体（OrchestratorAgent）
负责任务分发、流程控制和异常处理
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent


class OrchestratorAgent(BaseAgent):
    """调度智能体 - 协调其他智能体的执行流程"""
    
    def __init__(self):
        super().__init__(
            name="调度智能体",
            description="负责任务分发、流程控制和异常处理"
        )
        
        self.system_prompt = """你是一个专业的辟谣系统调度专家。你的职责是：
1. 分析用户输入的类型（文本、图片或混合）
2. 确定需要调用的智能体序列
3. 处理各智能体的返回结果
4. 协调整个辟谣流程

你需要根据输入内容判断：
- 是否需要OCR处理（如果是图片）
- 是否需要AI生成检测
- 是否需要检索相关证据
- 如何生成最终报告

请以JSON格式输出你的调度决策：
{
    "input_type": "text|image|mixed",
    "workflow": ["parser", "ai_detector", "retrieval", "report"],
    "priority": "high|medium|low",
    "notes": "特殊说明"
}"""
    
    def analyze_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析输入数据，确定处理流程
        
        Args:
            input_data: 输入数据，包含 text 和/或 image_url
            
        Returns:
            调度决策
        """
        has_text = bool(input_data.get("text"))
        has_image = bool(input_data.get("image_url"))
        
        # 确定输入类型
        if has_text and has_image:
            input_type = "mixed"
        elif has_image:
            input_type = "image"
        else:
            input_type = "text"
        
        # 构建消息
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"请分析输入类型并确定处理流程：\n输入类型: {input_type}\n文本长度: {len(input_data.get('text', ''))}\n图片: {'有' if has_image else '无'}"}
        ]
        
        # 调用LLM分析
        from langchain_core.messages import SystemMessage, HumanMessage
        llm_messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"请分析输入类型并确定处理流程：\n输入类型: {input_type}\n文本长度: {len(input_data.get('text', ''))}\n图片: {'有' if has_image else '无'}")
        ]
        
        response = self.call_llm(llm_messages, temperature=0.3)
        
        # 解析JSON响应
        import json
        try:
            # 尝试从响应中提取JSON
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "{" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                json_str = response[start:end]
            else:
                json_str = response
            
            decision = json.loads(json_str)
        except:
            # 默认决策
            decision = {
                "input_type": input_type,
                "workflow": ["parser", "ai_detector", "retrieval", "report"],
                "priority": "medium",
                "notes": "使用默认流程"
            }
        
        return decision
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据
        
        Args:
            input_data: 输入数据
            
        Returns:
            调度决策
        """
        return self.analyze_input(input_data)
