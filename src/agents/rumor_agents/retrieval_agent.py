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
            description="负责从向量库检索权威辟谣证据并结合 LLM 知识库生成补充依据"
        )
        
        # 初始化向量数据库
        self.vector_db = init_rumor_knowledge_base()
        
        self.analysis_prompt = """你是一个专业的证据分析专家。你需要分析检索到的辟谣证据，并判断与待验证内容的关联性。

对于每个证据，请分析：
1. 与待验证内容的相关性
2. 证据的可信度
3. 证据的权威性
4. 能否支持辟谣结论

请输出 JSON 格式的分析结果：
{
    "evidence_relevance": "high|medium|low",
    "evidence_credibility": "high|medium|low",
    "support_conclusion": true/false,
    "analysis": "详细分析说明",
    "key_facts": ["关键事实 1", "关键事实 2"]
}"""
        
        # 新增：LLM 知识库检索 Prompt
        self.knowledge_retrieval_prompt = """你是一个专业的辟谣信息检索专家。当向量库中没有相关证据时，你需要基于自己的知识库，提供权威的辟谣信息和科学依据。

请针对以下主张，提供：
1. 明确的真伪判断
2. 科学原理或医学原理解释
3. 权威机构的态度或声明（如 WHO、CDC、国家卫健委等）
4. 相关的科学研究或统计数据
5. 建议的信息来源（官方网站、权威媒体等）

请以 JSON 格式输出：
{
    "verdict": "真 | 假 | 部分真实 | 无法判断",
    "scientific_basis": "科学原理或依据",
    "authority_statements": ["权威机构声明 1", "声明 2"],
    "research_evidence": ["研究证据 1", "证据 2"],
    "recommended_sources": ["推荐信息来源 1", "来源 2"],
    "confidence_level": "高 | 中 | 低",
    "notes": "注意事项或说明"
}

注意：
- 如果该主张超出你的知识范围，请诚实说明"无法判断"
- 优先引用国际知名权威机构（WHO、CDC、NASA 等）
- 区分"科学共识"和"个别研究"
- 标注信息的时效性"""
    
    def search_evidence(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相关证据（从向量库）
        
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
                    "relevance_score": 1 - distances[i] if i < len(distances) else 0.5,
                    "source_type": "vector_db"  # 标记来源类型
                }
                evidence_list.append(evidence)
        
        return evidence_list
    
    def retrieve_from_llm_knowledge(self, claim: str) -> Dict[str, Any]:
        """
        从 LLM 知识库检索权威信息（当向量库证据不足时）
        
        Args:
            claim: 待验证主张
            
        Returns:
            LLM 提供的权威信息
        """
        from langchain_core.messages import SystemMessage, HumanMessage
        
        messages = [
            SystemMessage(content=self.knowledge_retrieval_prompt),
            HumanMessage(content=f"请针对以下主张提供权威的辟谣信息和科学依据：\n\n{claim}")
        ]
        
        response = self.call_llm(messages, temperature=0.3)
        
        # 解析 JSON 响应
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
            result["source_type"] = "llm_knowledge"
            result["query"] = claim
        except:
            result = {
                "verdict": "无法判断",
                "scientific_basis": "暂无足够信息进行判断",
                "authority_statements": [],
                "research_evidence": [],
                "recommended_sources": ["建议咨询权威机构或查阅专业资料"],
                "confidence_level": "低",
                "notes": "LLM 知识库检索失败",
                "source_type": "llm_knowledge",
                "query": claim
            }
        
        return result
    
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
        处理输入数据 - 混合检索策略
        
        Args:
            input_data: 包含 combined_claim 和 parser_result 的字典
            
        Returns:
            检索和分析结果（包含向量库证据 + LLM 知识库证据）
        """
        result = {
            "search_query": None,
            "vector_db_evidence": [],  # 向量库证据
            "llm_knowledge_evidence": None,  # LLM 知识库证据
            "analyzed_evidence": [],
            "summary": None
        }
        
        # 获取待验证的主张
        parser_result = input_data.get("parser_result", {})
        combined_claim = parser_result.get("combined_claim", "")
        
        if not combined_claim:
            text_analysis = parser_result.get("text_analysis", {})
            if text_analysis:
                combined_claim = text_analysis.get("main_claim", "")
        
        if not combined_claim:
            return result
        
        result["search_query"] = combined_claim
        
        # 步骤 1: 从向量库搜索
        print(f"   🔍 正在从向量库检索...")
        vector_evidence_list = self.search_evidence(combined_claim, n_results=5)
        result["vector_db_evidence"] = vector_evidence_list
        
        # 步骤 2: 分析向量库证据
        analyzed_evidence = []
        for evidence in vector_evidence_list:
            analysis = self.analyze_evidence(combined_claim, evidence)
            analyzed_evidence.append(analysis)
        
        # 步骤 3: 如果向量库证据不足，调用 LLM 知识库补充
        has_high_relevance = any(e.get("evidence_relevance") == "high" for e in analyzed_evidence)
        
        if not has_high_relevance:
            print(f"   ⚠️  向量库相关性不足，正在调用 LLM 知识库补充...")
            llm_knowledge = self.retrieve_from_llm_knowledge(combined_claim)
            result["llm_knowledge_evidence"] = llm_knowledge
            
            # 将 LLM 知识转换为统一的证据格式
            if llm_knowledge.get("verdict") != "无法判断":
                llm_evidence_formatted = {
                    "evidence_relevance": "high" if llm_knowledge.get("confidence_level") == "高" else "medium",
                    "evidence_credibility": llm_knowledge.get("confidence_level", "中"),
                    "support_conclusion": llm_knowledge.get("verdict") == "假",
                    "analysis": llm_knowledge.get("scientific_basis", ""),
                    "key_facts": llm_knowledge.get("research_evidence", []),
                    "authority_statements": llm_knowledge.get("authority_statements", []),
                    "recommended_sources": llm_knowledge.get("recommended_sources", []),
                    "original_evidence": {
                        "content": llm_knowledge.get("scientific_basis", ""),
                        "metadata": {"source_type": "llm_knowledge"},
                        "relevance_score": 0.8
                    },
                    "source_type": "llm_knowledge"
                }
                analyzed_evidence.append(llm_evidence_formatted)
        
        result["analyzed_evidence"] = analyzed_evidence
        
        # 步骤 4: 生成摘要
        if analyzed_evidence:
            high_relevance = [e for e in analyzed_evidence if e.get("evidence_relevance") == "high"]
            medium_relevance = [e for e in analyzed_evidence if e.get("evidence_relevance") == "medium"]
            vector_db_count = len([e for e in analyzed_evidence if e.get("source_type") == "vector_db"])
            llm_count = len([e for e in analyzed_evidence if e.get("source_type") == "llm_knowledge"])
            
            result["summary"] = {
                "total_evidence": len(analyzed_evidence),
                "high_relevance_count": len(high_relevance),
                "medium_relevance_count": len(medium_relevance),
                "has_supporting_evidence": len(high_relevance) > 0,
                "top_evidence": analyzed_evidence[0] if analyzed_evidence else None,
                "vector_db_count": vector_db_count,
                "llm_knowledge_count": llm_count,
                "evidence_sources": "向量库" if vector_db_count > 0 else "LLM 知识库" if llm_count > 0 else "无相关证据"
            }
        
        return result
