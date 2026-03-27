"""
报告生成智能体（ReportAgent）
负责生成结构化辟谣报告
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from datetime import datetime


class ReportAgent(BaseAgent):
    """报告生成智能体 - 生成结构化辟谣报告"""
    
    def __init__(self):
        super().__init__(
            name="报告生成智能体",
            description="负责生成结构化辟谣报告"
        )
        
        self.report_prompt = """你是一个专业的辟谣报告撰写专家。你需要基于收集到的所有信息，生成一份专业、客观、清晰的辟谣报告。

报告要求：
1. 结构清晰，逻辑严谨
2. 结论明确，有理有据
3. 证据来源清晰可查
4. 语言专业但易懂
5. 给出明确的可信度评级

请生成JSON格式的报告：
{
    "title": "报告标题",
    "verdict": "真|假|部分真实|无法判断",
    "confidence": 0.0-1.0,
    "summary": "简要结论（100字以内）",
    "analysis": "详细分析",
    "key_findings": ["关键发现1", "关键发现2", "..."],
    "evidence_summary": "证据摘要",
    "recommendations": ["建议1", "建议2", "..."],
    "credibility_level": "高|中|低",
    "risk_level": "高|中|低"
}"""
    
    def generate_report(
        self,
        parser_result: Dict[str, Any],
        ai_detection_result: Dict[str, Any],
        retrieval_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成辟谣报告
        
        Args:
            parser_result: 内容解析结果
            ai_detection_result: AI检测结果
            retrieval_result: 证据检索结果
            
        Returns:
            完整的辟谣报告
        """
        from langchain_core.messages import SystemMessage, HumanMessage
        
        # 构建输入信息摘要
        input_summary = self._build_input_summary(parser_result, ai_detection_result, retrieval_result)
        
        messages = [
            SystemMessage(content=self.report_prompt),
            HumanMessage(content=f"请基于以下信息生成辟谣报告：\n\n{input_summary}")
        ]
        
        response = self.call_llm(messages, temperature=0.5)
        
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
            
            report = json.loads(json_str)
        except:
            report = {
                "title": "辟谣分析报告",
                "verdict": "无法判断",
                "confidence": 0.5,
                "summary": "由于信息不足，无法做出明确判断",
                "analysis": response,
                "key_findings": [],
                "evidence_summary": "暂无相关证据",
                "recommendations": ["建议咨询权威机构", "等待更多信息"],
                "credibility_level": "中",
                "risk_level": "中"
            }
        
        # 添加元数据
        report["metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "agent": "ReportAgent",
            "version": "1.0"
        }
        
        return report
    
    def _build_input_summary(
        self,
        parser_result: Dict[str, Any],
        ai_detection_result: Dict[str, Any],
        retrieval_result: Dict[str, Any]
    ) -> str:
        """构建输入信息摘要"""
        
        summary_parts = []
        
        # 内容解析摘要
        if parser_result:
            summary_parts.append("【内容解析结果】")
            if parser_result.get("combined_claim"):
                summary_parts.append(f"核心主张: {parser_result['combined_claim']}")
            if parser_result.get("text_analysis"):
                ta = parser_result["text_analysis"]
                summary_parts.append(f"文本分类: {ta.get('category', '未知')}")
                summary_parts.append(f"语气: {ta.get('tone', '未知')}")
                if ta.get("keywords"):
                    summary_parts.append(f"关键词: {', '.join(ta['keywords'][:5])}")
            if parser_result.get("image_analysis"):
                ia = parser_result["image_analysis"]
                summary_parts.append(f"图片OCR: {ia.get('ocr_text', '无')[:100]}...")
        
        # AI检测摘要
        if ai_detection_result and ai_detection_result.get("overall_assessment"):
            summary_parts.append("\n【AI生成检测结果】")
            oa = ai_detection_result["overall_assessment"]
            summary_parts.append(f"是否AI生成: {'是' if oa.get('is_ai_generated') else '否'}")
            summary_parts.append(f"置信度: {oa.get('confidence', 0):.2%}")
            summary_parts.append(f"结论: {oa.get('summary', '无')}")
        
        # 证据检索摘要
        if retrieval_result and retrieval_result.get("analyzed_evidence"):
            summary_parts.append("\n【证据检索结果】")
            summary_parts.append(f"找到相关证据: {len(retrieval_result['analyzed_evidence'])} 条")
            
            for i, evidence in enumerate(retrieval_result["analyzed_evidence"][:3], 1):
                summary_parts.append(f"\n证据{i}:")
                summary_parts.append(f"相关性: {evidence.get('evidence_relevance', '未知')}")
                summary_parts.append(f"可信度: {evidence.get('evidence_credibility', '未知')}")
                if evidence.get("original_evidence"):
                    summary_parts.append(f"内容: {evidence['original_evidence'].get('content', '')[:200]}...")
        
        return "\n".join(summary_parts)
    
    def generate_readable_report(self, report: Dict[str, Any]) -> str:
        """
        生成可读性更好的报告文本
        
        Args:
            report: 结构化报告
            
        Returns:
            格式化的报告文本
        """
        lines = []
        
        # 标题
        lines.append("=" * 60)
        lines.append(f"📋 {report.get('title', '辟谣分析报告')}")
        lines.append("=" * 60)
        
        # 结论框
        verdict = report.get('verdict', '无法判断')
        confidence = report.get('confidence', 0)
        credibility = report.get('credibility_level', '中')
        
        lines.append("\n┌──────────────────────────────────────────────────────┐")
        lines.append(f"│  结论: {verdict:<12}  可信度: {credibility:<6}  置信度: {confidence:.0%}  │")
        lines.append("└──────────────────────────────────────────────────────┘")
        
        # 摘要
        lines.append(f"\n📌 摘要:")
        lines.append(f"   {report.get('summary', '暂无摘要')}")
        
        # 详细分析
        lines.append(f"\n🔍 详细分析:")
        analysis = report.get('analysis', '')
        for line in analysis.split('\n'):
            lines.append(f"   {line}")
        
        # 关键发现
        key_findings = report.get('key_findings', [])
        if key_findings:
            lines.append(f"\n💡 关键发现:")
            for i, finding in enumerate(key_findings, 1):
                lines.append(f"   {i}. {finding}")
        
        # 证据摘要
        lines.append(f"\n📚 证据摘要:")
        evidence_summary = report.get('evidence_summary', '暂无相关证据')
        lines.append(f"   {evidence_summary}")
        
        # 建议
        recommendations = report.get('recommendations', [])
        if recommendations:
            lines.append(f"\n✅ 建议:")
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"   {i}. {rec}")
        
        # 风险等级
        risk_level = report.get('risk_level', '中')
        risk_emoji = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(risk_level, "⚪")
        lines.append(f"\n⚠️  风险等级: {risk_emoji} {risk_level}")
        
        # 时间戳
        if report.get('metadata'):
            lines.append(f"\n⏰ 生成时间: {report['metadata'].get('generated_at', '未知')}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据
        
        Args:
            input_data: 包含所有前序处理结果的字典
            
        Returns:
            完整的辟谣报告
        """
        parser_result = input_data.get("parser_result", {})
        ai_detection_result = input_data.get("ai_detection_result", {})
        retrieval_result = input_data.get("retrieval_result", {})
        
        report = self.generate_report(parser_result, ai_detection_result, retrieval_result)
        readable_report = self.generate_readable_report(report)
        
        return {
            "structured_report": report,
            "readable_report": readable_report
        }
