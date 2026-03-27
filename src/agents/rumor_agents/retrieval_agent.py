"""
证据检索智能体（RetrievalAgent）
负责从向量库检索权威辟谣证据
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from ...storage.rumor_vector_db import RumorVectorDB, init_rumor_knowledge_base


class RetrievalAgent(BaseAgent):
    """证据检索智能体 - 检索相关辟谣证据"""
    
    def __init__(self):
        super().__init__(
            name="证据检索智能体",
            description="负责从向量库检索权威辟谣证据"
        )
        
        # 初始化向量数据库
        self.vector_db = init_rumor_knowledge_base()
        
        self.analysis_prompt = """你是一个专业的证据分析专家。你需要分析检索到的辟谣证据，并判断与待验证内容的关联性。

对于每个证据，请分析：
1. 与待验证内容的相关性
2. 证据的可信度
3. 证据的权威性
4. 能否支持辟谣结论

请输出JSON格式的分析结果：
{
    "evidence_relevance": "high|medium|low",
    "evidence_credibility": "high|medium|low",
    "support_conclusion": true/false,
    "analysis": "详细分析说明",
    "key_facts": ["关键事实1", "关键事实2"]
}"""
    
    def search_evidence(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关证据
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        # 从向量库搜索
        results = self.vector_db.search(query, n_results=n_results)
        
        # 格式化结果
        evidence_list = []
        
        if results and results.get("documents"):
            documents = results["documents"][0] if results["documents"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []
            distances = results["distances"][0] if results["distances"] else []
            
            for i, doc in enumerate(documents):
                evidence = {
                    "content": doc,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "relevance_score": 1 - distances[i] if i < len(distances) else 0.5
                }
                evidence_list.append(evidence)
        
        return evidence_list
    
    def analyze_evidence(
        self, 
        claim: str, 
        evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析单个证据与主张的关联性
        
        Args:
            claim: 待验证主张
            evidence: 证据内容
            
        Returns:
            分析结果
        """
        from langchain_core.messages import SystemMessage, HumanMessage
        
        messages = [
            SystemMessage(content=self.analysis_prompt),
            HumanMessage(content=f"待验证主张：{claim}\n\n证据内容：{evidence['content']}\n\n请分析这个证据的相关性和可信度：")
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
            
            analysis = json.loads(json_str)
            analysis["original_evidence"] = evidence
        except:
            analysis = {
                "evidence_relevance": "medium",
                "evidence_credibility": "medium",
                "support_conclusion": None,
                "analysis": "无法准确分析",
                "key_facts": [],
                "original_evidence": evidence
            }
        
        return analysis
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据
        
        Args:
            input_data: 包含 combined_claim 和 parser_result 的字典
            
        Returns:
            检索和分析结果
        """
        result = {
            "search_query": None,
            "evidence_list": [],
            "analyzed_evidence": [],
            "summary": None
        }
        
        # 获取待验证的主张
        parser_result = input_data.get("parser_result", {})
        combined_claim = parser_result.get("combined_claim", "")
        
        if not combined_claim:
            # 尝试从文本分析中获取
            text_analysis = parser_result.get("text_analysis", {})
            if text_analysis:
                combined_claim = text_analysis.get("main_claim", "")
        
        if not combined_claim:
            return result
        
        result["search_query"] = combined_claim
        
        # 搜索相关证据
        evidence_list = self.search_evidence(combined_claim, n_results=5)
        result["evidence_list"] = evidence_list
        
        # 分析每个证据
        analyzed_evidence = []
        for evidence in evidence_list:
            analysis = self.analyze_evidence(combined_claim, evidence)
            analyzed_evidence.append(analysis)
        
        result["analyzed_evidence"] = analyzed_evidence
        
        # 生成摘要
        if analyzed_evidence:
            high_relevance = [e for e in analyzed_evidence if e.get("evidence_relevance") == "high"]
            medium_relevance = [e for e in analyzed_evidence if e.get("evidence_relevance") == "medium"]
            
            result["summary"] = {
                "total_evidence": len(analyzed_evidence),
                "high_relevance_count": len(high_relevance),
                "medium_relevance_count": len(medium_relevance),
                "has_supporting_evidence": len(high_relevance) > 0,
                "top_evidence": analyzed_evidence[0] if analyzed_evidence else None
            }
        
        return result
