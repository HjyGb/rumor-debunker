"""
AI生成检测智能体（AIDetectorAgent）
负责判断内容是否为AI生成
"""
from typing import Dict, Any
from .base_agent import BaseAgent


class AIDetectorAgent(BaseAgent):
    """AI生成检测智能体 - 判断内容是否为AI生成"""
    
    def __init__(self):
        super().__init__(
            name="AI生成检测智能体",
            description="负责判断内容是否为AI生成"
        )
        
        self.text_detection_prompt = """你是一个专业的AI生成内容检测专家。你需要判断文本是否由AI生成。

AI生成文本的常见特征：
1. 过于流畅和完美，缺乏自然的不规则性
2. 缺乏具体的个人经历和细节
3. 重复性表达和固定模式
4. 逻辑结构过于规整
5. 缺乏情感波动和个人观点
6. 事实细节可能存在错误或模糊
7. 引用来源可能不实或无法验证
8. 语言风格单一，缺乏变化

请分析文本并输出JSON格式的结果：
{
    "is_ai_generated": true/false,
    "confidence": 0.0-1.0,
    "detected_features": ["检测到的AI特征1", "特征2", "..."],
    "human_like_features": ["类似人类的特征"],
    "analysis": "详细分析说明",
    "recommendation": "建议采取的措施"
}"""
        
        self.image_detection_prompt = """你是一个专业的AI生成图像检测专家。你需要判断图片是否由AI生成。

AI生成图像的常见特征：
1. 手指数量错误或畸形
2. 文字模糊或无意义
3. 背景细节不连贯
4. 对称性异常（如左右眼睛不对称）
5. 光影不一致
6. 眼睛细节不自然
7. 边缘过度平滑
8. 重复性纹理
9. 物体变形或不合理

请分析图片并输出JSON格式的结果：
{
    "is_ai_generated": true/false,
    "confidence": 0.0-1.0,
    "detected_features": ["检测到的AI特征"],
    "natural_features": ["自然图像特征"],
    "analysis": "详细分析说明",
    "recommendation": "建议采取的措施"
}"""
    
    def detect_text(self, text: str) -> Dict[str, Any]:
        """
        检测文本是否为AI生成
        
        Args:
            text: 待检测文本
            
        Returns:
            检测结果
        """
        from langchain_core.messages import SystemMessage, HumanMessage
        
        messages = [
            SystemMessage(content=self.text_detection_prompt),
            HumanMessage(content=f"请分析以下文本是否为AI生成：\n\n{text}")
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
        except:
            result = {
                "is_ai_generated": False,
                "confidence": 0.5,
                "detected_features": [],
                "human_like_features": [],
                "analysis": "无法准确判断",
                "recommendation": "建议结合其他证据综合判断"
            }
        
        return result
    
    def detect_image(self, image_url: str) -> Dict[str, Any]:
        """
        检测图片是否为AI生成
        
        Args:
            image_url: 图片URL
            
        Returns:
            检测结果
        """
        # 使用视觉模型进行检测
        response = self.call_vision_llm(
            text=f"{self.image_detection_prompt}\n\n请分析这张图片是否为AI生成：",
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
        except:
            result = {
                "is_ai_generated": False,
                "confidence": 0.5,
                "detected_features": [],
                "natural_features": [],
                "analysis": "无法准确判断",
                "recommendation": "建议结合其他证据综合判断"
            }
        
        return result
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据
        
        Args:
            input_data: 包含 parser_result 的字典
            
        Returns:
            检测结果
        """
        result = {
            "text_detection": None,
            "image_detection": None,
            "overall_assessment": None
        }
        
        parser_result = input_data.get("parser_result", {})
        
        # 检测文本
        text_analysis = parser_result.get("text_analysis")
        if text_analysis and text_analysis.get("original_text"):
            result["text_detection"] = self.detect_text(text_analysis["original_text"])
        
        # 检测图片
        image_analysis = parser_result.get("image_analysis")
        if image_analysis and image_analysis.get("image_url"):
            result["image_detection"] = self.detect_image(image_analysis["image_url"])
        
        # 综合评估
        assessments = []
        if result["text_detection"]:
            assessments.append(result["text_detection"])
        if result["image_detection"]:
            assessments.append(result["image_detection"])
        
        if assessments:
            # 计算综合置信度
            is_ai = any(a.get("is_ai_generated", False) for a in assessments)
            avg_confidence = sum(a.get("confidence", 0.5) for a in assessments) / len(assessments)
            
            result["overall_assessment"] = {
                "is_ai_generated": is_ai,
                "confidence": avg_confidence,
                "summary": "检测到AI生成特征" if is_ai else "未检测到明显AI生成特征"
            }
        
        return result
