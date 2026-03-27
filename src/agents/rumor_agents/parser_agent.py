"""
内容解析智能体（ParserAgent）
负责提取文本、图片OCR、提取谣言主张
"""
from typing import Dict, Any
from .base_agent import BaseAgent


class ParserAgent(BaseAgent):
    """内容解析智能体 - 提取和分析输入内容"""
    
    def __init__(self):
        super().__init__(
            name="内容解析智能体",
            description="负责提取文本、图片OCR、提取谣言主张"
        )
        
        self.text_system_prompt = """你是一个专业的内容分析专家。你的任务是：
1. 提取输入文本中的核心主张或观点
2. 识别文本中的关键信息点
3. 判断文本的语气和意图（是否为传播性内容）
4. 提取可能的谣言特征

请以JSON格式输出分析结果：
{
    "main_claim": "核心主张（一句话概括）",
    "key_points": ["关键点1", "关键点2", "..."],
    "keywords": ["关键词1", "关键词2", "..."],
    "tone": "alerting|informative|persuasive|neutral",
    "rumor_indicators": ["可能的谣言特征"],
    "category": "健康|科学|食品安全|社会|其他"
}"""
        
        self.image_system_prompt = """你是一个专业的图片内容分析专家。你的任务是：
1. 识别图片中的所有文字（OCR）
2. 描述图片的主要内容
3. 识别图片中可能的谣言特征（如夸张的标题、不可信的来源标识等）
4. 提取图片中的核心主张

请以JSON格式输出分析结果：
{
    "ocr_text": "图片中识别到的所有文字",
    "image_description": "图片内容描述",
    "main_claim": "核心主张",
    "visual_elements": ["视觉元素1", "视觉元素2"],
    "rumor_indicators": ["可能的谣言特征"],
    "credibility_signals": ["可信度信号（如水印、来源标识等）"]
}"""
    
    def parse_text(self, text: str) -> Dict[str, Any]:
        """
        解析文本内容
        
        Args:
            text: 输入文本
            
        Returns:
            解析结果
        """
        from langchain_core.messages import SystemMessage, HumanMessage
        
        messages = [
            SystemMessage(content=self.text_system_prompt),
            HumanMessage(content=f"请分析以下文本内容：\n\n{text}")
        ]
        
        response = self.call_llm(messages, temperature=0.3)
        
        # 解析JSON响应
        import json
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "{" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                json_str = response[start:end]
            else:
                json_str = response
            
            result = json.loads(json_str)
            result["original_text"] = text
        except:
            result = {
                "main_claim": text[:100] if len(text) > 100 else text,
                "key_points": [text[:50]],
                "keywords": [],
                "tone": "neutral",
                "rumor_indicators": [],
                "category": "其他",
                "original_text": text
            }
        
        return result
    
    def parse_image(self, image_url: str) -> Dict[str, Any]:
        """
        解析图片内容（OCR + 理解）
        
        Args:
            image_url: 图片URL
            
        Returns:
            解析结果
        """
        # 使用视觉模型进行分析
        response = self.call_vision_llm(
            text=f"{self.image_system_prompt}\n\n请分析这张图片：",
            image_url=image_url,
            temperature=0.3
        )
        
        # 解析JSON响应
        import json
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "{" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                json_str = response[start:end]
            else:
                json_str = response
            
            result = json.loads(json_str)
            result["image_url"] = image_url
        except:
            result = {
                "ocr_text": response,
                "image_description": response,
                "main_claim": response[:100],
                "visual_elements": [],
                "rumor_indicators": [],
                "credibility_signals": [],
                "image_url": image_url
            }
        
        return result
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据
        
        Args:
            input_data: 包含 text 和/或 image_url 的字典
            
        Returns:
            解析结果
        """
        result = {
            "text_analysis": None,
            "image_analysis": None,
            "combined_claim": None
        }
        
        # 解析文本
        if input_data.get("text"):
            result["text_analysis"] = self.parse_text(input_data["text"])
        
        # 解析图片
        if input_data.get("image_url"):
            result["image_analysis"] = self.parse_image(input_data["image_url"])
        
        # 合并核心主张
        claims = []
        if result["text_analysis"]:
            claims.append(result["text_analysis"].get("main_claim", ""))
        if result["image_analysis"]:
            claims.append(result["image_analysis"].get("main_claim", ""))
        
        if claims:
            result["combined_claim"] = " | ".join([c for c in claims if c])
        
        return result
