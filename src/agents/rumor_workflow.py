"""
辟谣专家多智能体协作工作流
协调各智能体的执行顺序和数据流转
"""
from typing import Dict, Any, Optional
from datetime import datetime
import traceback

from .rumor_agents import (
    OrchestratorAgent,
    ParserAgent,
    AIDetectorAgent,
    RetrievalAgent,
    ReportAgent
)


class RumorDebunkerWorkflow:
    """辟谣专家多智能体协作工作流"""
    
    def __init__(self):
        """初始化工作流和所有智能体"""
        # 初始化所有智能体
        self.orchestrator = OrchestratorAgent()
        self.parser = ParserAgent()
        self.ai_detector = AIDetectorAgent()
        self.retrieval = RetrievalAgent()
        self.report = ReportAgent()
        
        print("✅ 辟谣专家多智能体系统初始化完成")
        print(f"   - {self.orchestrator.name}")
        print(f"   - {self.parser.name}")
        print(f"   - {self.ai_detector.name}")
        print(f"   - {self.retrieval.name}")
        print(f"   - {self.report.name}")
    
    def run(
        self,
        text: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行完整的辟谣工作流
        
        Args:
            text: 输入文本
            image_url: 图片URL
            
        Returns:
            完整的分析结果
        """
        # 记录开始时间
        start_time = datetime.now()
        
        # 初始化结果字典
        result = {
            "success": False,
            "error": None,
            "workflow_steps": [],
            "orchestrator_result": None,
            "parser_result": None,
            "ai_detection_result": None,
            "retrieval_result": None,
            "report_result": None,
            "execution_time": None
        }
        
        try:
            # 步骤1: 准备输入数据
            input_data = {
                "text": text,
                "image_url": image_url
            }
            
            if not text and not image_url:
                raise ValueError("请输入文本或上传图片")
            
            print(f"\n{'='*60}")
            print(f"🔍 开始辟谣分析...")
            print(f"{'='*60}")
            
            # 步骤2: 调度智能体分析
            print(f"\n🤖 [1/5] {self.orchestrator.name} 正在分析...")
            orchestrator_result = self.orchestrator.process(input_data)
            result["orchestrator_result"] = orchestrator_result
            result["workflow_steps"].append("orchestrator")
            print(f"   ✅ 调度决策: {orchestrator_result.get('input_type', 'unknown')} 类型输入")
            
            # 步骤3: 内容解析
            print(f"\n📝 [2/5] {self.parser.name} 正在解析...")
            parser_result = self.parser.process(input_data)
            result["parser_result"] = parser_result
            result["workflow_steps"].append("parser")
            
            if parser_result.get("combined_claim"):
                print(f"   ✅ 核心主张: {parser_result['combined_claim'][:100]}...")
            else:
                print(f"   ⚠️ 未能提取核心主张")
            
            # 步骤4: AI生成检测
            print(f"\n🤖 [3/5] {self.ai_detector.name} 正在检测...")
            ai_detection_input = {
                "parser_result": parser_result
            }
            ai_detection_result = self.ai_detector.process(ai_detection_input)
            result["ai_detection_result"] = ai_detection_result
            result["workflow_steps"].append("ai_detector")
            
            if ai_detection_result.get("overall_assessment"):
                oa = ai_detection_result["overall_assessment"]
                print(f"   ✅ AI生成: {'是' if oa.get('is_ai_generated') else '否'} (置信度: {oa.get('confidence', 0):.0%})")
            
            # 步骤5: 证据检索
            print(f"\n🔍 [4/5] {self.retrieval.name} 正在检索...")
            retrieval_input = {
                "parser_result": parser_result
            }
            retrieval_result = self.retrieval.process(retrieval_input)
            result["retrieval_result"] = retrieval_result
            result["workflow_steps"].append("retrieval")
            
            evidence_count = len(retrieval_result.get("analyzed_evidence", []))
            print(f"   ✅ 找到 {evidence_count} 条相关证据")
            
            # 步骤6: 报告生成
            print(f"\n📊 [5/5] {self.report.name} 正在生成报告...")
            report_input = {
                "parser_result": parser_result,
                "ai_detection_result": ai_detection_result,
                "retrieval_result": retrieval_result
            }
            report_result = self.report.process(report_input)
            result["report_result"] = report_result
            result["workflow_steps"].append("report")
            
            if report_result.get("structured_report"):
                sr = report_result["structured_report"]
                print(f"   ✅ 结论: {sr.get('verdict', '未知')} (可信度: {sr.get('credibility_level', '未知')})")
            
            result["success"] = True
            print(f"\n{'='*60}")
            print(f"✅ 辟谣分析完成!")
            print(f"{'='*60}\n")
            
        except Exception as e:
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
            print(f"\n❌ 工作流执行失败: {e}")
            print(traceback.format_exc())
        
        # 计算执行时间
        end_time = datetime.now()
        result["execution_time"] = str(end_time - start_time)
        
        return result
    
    def get_summary(self, result: Dict[str, Any]) -> str:
        """
        生成简洁的结果摘要
        
        Args:
            result: 工作流执行结果
            
        Returns:
            摘要文本
        """
        if not result.get("success"):
            return f"❌ 分析失败: {result.get('error', '未知错误')}"
        
        lines = []
        lines.append("📋 辟谣分析摘要")
        lines.append("=" * 50)
        
        # 核心主张
        if result.get("parser_result", {}).get("combined_claim"):
            lines.append(f"核心主张: {result['parser_result']['combined_claim'][:100]}...")
        
        # AI检测
        if result.get("ai_detection_result", {}).get("overall_assessment"):
            oa = result["ai_detection_result"]["overall_assessment"]
            lines.append(f"AI生成: {'是' if oa.get('is_ai_generated') else '否'} (置信度: {oa.get('confidence', 0):.0%})")
        
        # 结论
        if result.get("report_result", {}).get("structured_report"):
            sr = result["report_result"]["structured_report"]
            lines.append(f"结论: {sr.get('verdict', '未知')}")
            lines.append(f"可信度: {sr.get('credibility_level', '未知')}")
            lines.append(f"摘要: {sr.get('summary', '无')}")
        
        lines.append(f"执行时间: {result.get('execution_time', '未知')}")
        
        return "\n".join(lines)


def run_debunker(text: Optional[str] = None, image_url: Optional[str] = None) -> Dict[str, Any]:
    """
    便捷函数：执行辟谣分析
    
    Args:
        text: 输入文本
        image_url: 图片URL
        
    Returns:
        分析结果
    """
    workflow = RumorDebunkerWorkflow()
    return workflow.run(text=text, image_url=image_url)


if __name__ == "__main__":
    # 测试运行
    test_text = "喝白酒可以预防新冠病毒，这个说法是真的吗？"
    
    workflow = RumorDebunkerWorkflow()
    result = workflow.run(text=test_text)
    
    print("\n" + "="*60)
    print(workflow.get_summary(result))
    print("="*60)
    
    if result.get("report_result", {}).get("readable_report"):
        print("\n" + result["report_result"]["readable_report"])
