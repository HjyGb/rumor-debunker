# 🔍 辟谣专家多智能体系统 - 深度项目解析文档

## 📋 文档目的

本文档旨在深入剖析"辟谣专家多智能体系统"的架构设计、模块实现、数据流转和关键技术点，帮助读者全面理解项目运作机制，为面试准备和项目扩展提供系统性知识支撑。

---

## 📖 目录

1. [项目概述](#项目概述)
2. [技术栈详解](#技术栈详解)
3. [系统架构设计](#系统架构设计)
4. [核心模块深度解析](#核心模块深度解析)
5. [数据流转与执行流程](#数据流转与执行流程)
6. [关键技术点分析](#关键技术点分析)
7. [部署与配置](#部署与配置)
8. [面试常见问题准备](#面试常见问题准备)

---

## 项目概述

### 项目定位

基于**多智能体协作架构**的辟谣分析平台，通过 5 个专业智能体的协同工作，对输入的文本或图片内容进行深度分析，判断信息真实性并提供权威辟谣证据。

### 核心价值主张

- **多模态输入支持**：文本 + 图片（OCR）
- **AI 生成内容检测**：识别 AIGC 内容
- **知识库检索**：向量数据库匹配权威辟谣证据
- **结构化报告**：专业、客观、可解释的分析结果
- **可扩展架构**：基于 LangGraph 的智能体编排

### 应用场景

1. 社交媒体谣言验证
2. 新闻真实性核查
3. AI 生成内容识别
4. 健康/科学类谣言粉碎
5. 食品安全谣言验证

---

## 技术栈详解

### 核心框架层

```
┌─────────────────────────────────────┐
│   LangChain 1.0.3                   │  # LLM 应用开发框架
│   LangGraph 1.0.2                   │  # 智能体工作流编排
│   LangChain-OpenAI 1.0.1            │  # LLM API 适配层
└─────────────────────────────────────┘
```

### Web 服务层

```
┌─────────────────────────────────────┐
│   FastAPI >=0.121,<1                │  # 高性能异步 Web 框架
│   Uvicorn >=0.38,<1                 │  # ASGI 服务器
│   Streamlit (app.py)                │  # 交互式 UI 界面
└─────────────────────────────────────┘
```

### 数据存储层

```
┌─────────────────────────────────────┐
│   ChromaDB >=0.5,<1                 │  # 向量数据库（本地持久化）
│   SQLAlchemy >=2.0,<3               │  # ORM 框架
│   PostgreSQL (可选)                 │  # 关系型数据库
└─────────────────────────────────────┘
```

### AI 模型层（阿里云百炼）

```
┌─────────────────────────────────────┐
│   qwen-plus                         │  # 主大语言模型
│   qwen-vl-plus                      │  # 视觉多模态模型
│   text-embedding-v4                 │  # 文本嵌入模型
└─────────────────────────────────────┘
```

### 工具库

- **pydantic**: 数据验证和设置管理
- **Pillow/OpenCV**: 图像处理
- **python-dotenv**: 环境变量管理
- **boto3**: S3 存储兼容（可选）

---

## 系统架构设计

### 整体架构图

```
用户界面层 (Streamlit/FastAPI)
         ↓
工作流编排层 (RumorDebunkerWorkflow)
         ↓
智能体协作层 (5 个 Agent)
├── OrchestratorAgent (调度)
├── ParserAgent (内容解析)
├── AIDetectorAgent (AI 检测)
├── RetrievalAgent (证据检索)
└── ReportAgent (报告生成)
         ↓
基础设施层
├── BaseAgent (统一 LLM 调用接口)
├── RumorVectorDB (向量数据库)
└── 阿里云百炼 API
```

### 设计模式应用

#### 1. **策略模式 (Strategy Pattern)**
- 每个智能体都是独立策略
- 通过 `process()` 方法统一接口
- 易于扩展新的智能体

#### 2. **责任链模式 (Chain of Responsibility)**
- 工作流按顺序执行：Orchestrator → Parser → AI Detector → Retrieval → Report
- 每个环节处理特定任务并传递结果

#### 3. **工厂模式 (Factory Pattern)**
- `init_rumor_knowledge_base()` 初始化知识库
- `build_graph()` 构建工作流图

#### 4. **适配器模式 (Adapter Pattern)**
- `BaseAgent` 适配阿里云百炼 API 到 OpenAI SDK 接口
- 兼容不同 LLM 提供商

---

## 核心模块深度解析

### 1️⃣ BaseAgent - 基础智能体类

**文件路径**: `src/agents/rumor_agents/base_agent.py`

#### 核心职责

- 提供统一的 LLM 调用接口
- 封装阿里云百炼云 API 调用细节
- 支持文本和多模态模型调用

#### 关键代码解析

```python
class BaseAgent(ABC):
    def __init__(self, name: str, description: str):
        # 环境变量检查
        api_key = os.getenv("DASHSCOPE_API_KEY")
        base_url = os.getenv("DASHSCOPE_BASE_URL")
        
        # 初始化 OpenAI 客户端（兼容阿里百炼云）
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    def call_llm(self, messages, temperature=0.7, model=None):
        """调用大语言模型"""
        config = self._get_config()
        model_name = model or config.get("config", {}).get("model", "qwen-plus")
        
        # 转换为 OpenAI 格式
        openai_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                openai_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": msg.content})
        
        response = self.client.chat.completions.create(
            model=model_name,
            messages=openai_messages,
            temperature=temperature
        )
        return response.choices[0].message.content
    
    def call_vision_llm(self, text, image_url, temperature=0.3):
        """调用多模态模型"""
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
        
        response = self.client.chat.completions.create(
            model=vision_model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content
```

#### 设计亮点

1. **抽象基类约束**: 强制子类实现 `process()` 方法
2. **配置集中管理**: 从 `config/agent_llm_config.json` 读取模型参数
3. **错误处理完善**: 捕获异常并输出友好错误信息
4. **灵活模型切换**: 支持通过配置文件或参数指定模型

---

### 2️⃣ OrchestratorAgent - 调度智能体

**文件路径**: `src/agents/rumor_agents/orchestrator_agent.py`

#### 核心职责

- 分析用户输入类型（文本/图片/混合）
- 确定处理工作流
- 协调整个辟谣流程

#### 工作流程

```python
def analyze_input(self, input_data):
    has_text = bool(input_data.get("text"))
    has_image = bool(input_data.get("image_url"))
    
    # 确定输入类型
    if has_text and has_image:
        input_type = "mixed"
    elif has_image:
        input_type = "image"
    else:
        input_type = "text"
    
    # 调用 LLM 分析并返回调度决策
    messages = [
        SystemMessage(content=self.system_prompt),
        HumanMessage(content=f"请分析输入类型：{input_type}")
    ]
    
    response = self.call_llm(messages, temperature=0.3)
    decision = json.loads(response)
    
    return {
        "input_type": input_type,
        "workflow": ["parser", "ai_detector", "retrieval", "report"],
        "priority": "medium"
    }
```

#### Prompt 设计技巧

```python
self.system_prompt = """你是一个专业的辟谣系统调度专家。你的职责是：
1. 分析用户输入的类型（文本、图片或混合）
2. 确定需要调用的智能体序列
3. 处理各智能体的返回结果
4. 协调整个辟谣流程

请以 JSON 格式输出你的调度决策：
{
    "input_type": "text|image|mixed",
    "workflow": ["parser", "ai_detector", "retrieval", "report"],
    "priority": "high|medium|low",
    "notes": "特殊说明"
}"""
```

**关键点**: 
- 明确角色定位
- 列出具体职责
- 规定输出格式（JSON Schema）
- 温度参数较低 (0.3) 保证输出稳定性

---

### 3️⃣ ParserAgent - 内容解析智能体

**文件路径**: `src/agents/rumor_agents/parser_agent.py`

#### 核心职责

- 文本内容分析（提取核心主张、关键词、语气）
- 图片 OCR 和内容理解
- 合并多模态输入的主张

#### 文本解析实现

```python
def parse_text(self, text):
    messages = [
        SystemMessage(content=self.text_system_prompt),
        HumanMessage(content=f"请分析以下文本内容：\n\n{text}")
    ]
    
    response = self.call_llm(messages, temperature=0.3)
    
    # JSON 解析（带容错）
    try:
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        result = json.loads(json_str)
        result["original_text"] = text
    except:
        # 降级处理
        result = {
            "main_claim": text[:100],
            "key_points": [text[:50]],
            "keywords": [],
            "tone": "neutral",
            "category": "其他"
        }
    
    return result
```

#### 图片解析实现（多模态）

```python
def parse_image(self, image_url):
    response = self.call_vision_llm(
        text=f"{self.image_system_prompt}\n\n请分析这张图片：",
        image_url=image_url,
        temperature=0.3
    )
    
    # 同样使用 JSON 解析逻辑
    result = json.loads(response)
    result["image_url"] = image_url
    return result
```

#### 输出结构

```json
{
    "text_analysis": {
        "main_claim": "核心主张",
        "key_points": ["关键点 1", "关键点 2"],
        "keywords": ["关键词 1", "关键词 2"],
        "tone": "alerting|informative|persuasive|neutral",
        "category": "健康 | 科学 | 食品安全 | 社会 | 其他",
        "rumor_indicators": ["谣言特征"]
    },
    "image_analysis": {
        "ocr_text": "OCR 识别文字",
        "image_description": "图片描述",
        "main_claim": "图片核心主张"
    },
    "combined_claim": "合并后的核心主张"
}
```

---

### 4️⃣ AIDetectorAgent - AI 生成检测智能体

**文件路径**: `src/agents/rumor_agents/ai_detector_agent.py`

#### 核心职责

- 检测文本是否为 AI 生成
- 检测图片是否为 AI 生成
- 综合评估置信度

#### AI 文本检测 Prompt 设计

```python
self.text_detection_prompt = """你是一个专业的 AI 生成内容检测专家。

AI 生成文本的常见特征：
1. 过于流畅和完美，缺乏自然的不规则性
2. 缺乏具体的个人经历和细节
3. 重复性表达和固定模式
4. 逻辑结构过于规整
5. 缺乏情感波动和个人观点
6. 事实细节可能存在错误或模糊
7. 引用来源可能不实或无法验证
8. 语言风格单一，缺乏变化

请分析文本并输出 JSON 格式的结果：
{
    "is_ai_generated": true/false,
    "confidence": 0.0-1.0,
    "detected_features": ["检测到的 AI 特征"],
    "human_like_features": ["类似人类的特征"],
    "analysis": "详细分析说明",
    "recommendation": "建议采取的措施"
}"""
```

#### 综合评估逻辑

```python
def process(self, input_data):
    result = {
        "text_detection": None,
        "image_detection": None,
        "overall_assessment": None
    }
    
    # 分别检测文本和图片
    if text_analysis:
        result["text_detection"] = self.detect_text(text)
    if image_analysis:
        result["image_detection"] = self.detect_image(image_url)
    
    # 综合评估
    assessments = []
    if result["text_detection"]:
        assessments.append(result["text_detection"])
    if result["image_detection"]:
        assessments.append(result["image_detection"])
    
    if assessments:
        is_ai = any(a.get("is_ai_generated", False) for a in assessments)
        avg_confidence = sum(a.get("confidence", 0.5) for a in assessments) / len(assessments)
        
        result["overall_assessment"] = {
            "is_ai_generated": is_ai,
            "confidence": avg_confidence,
            "summary": "检测到 AI 生成特征" if is_ai else "未检测到明显 AI 生成特征"
        }
    
    return result
```

**技术要点**:
- 使用**任意原则**: 只要有一个检测结果为 AI 生成，则判定为 AI 生成
- 平均置信度计算提高鲁棒性
- 支持单模态检测（仅文本或仅图片）

---

### 5️⃣ RetrievalAgent - 证据检索智能体（增强版）

**文件路径**: `src/agents/rumor_agents/retrieval_agent.py`

#### 核心职责

- 从向量数据库检索相关辟谣证据
- **新增**: 当向量库证据不足时，调用 LLM 知识库补充权威信息
- 分析证据与主张的相关性
- 评估证据可信度

#### 混合 RAG 架构

**实现流程**:

```python
def process(self, input_data):
    # 步骤 1: 从向量库搜索
    vector_evidence_list = self.search_evidence(combined_claim, n_results=5)
    
    # 步骤 2: 分析向量库证据
    analyzed_evidence = []
    for evidence in vector_evidence_list:
        analysis = self.analyze_evidence(combined_claim, evidence)
        analyzed_evidence.append(analysis)
    
    # 步骤 3: 如果相关性不足，调用 LLM 知识库补充
    has_high_relevance = any(e.get("evidence_relevance") == "high" for e in analyzed_evidence)
    
    if not has_high_relevance:
        llm_knowledge = self.retrieve_from_llm_knowledge(combined_claim)
        # 格式化后加入证据列表
        analyzed_evidence.append(format_llm_evidence(llm_knowledge))
    
    return {
        "vector_db_evidence": vector_evidence_list,
        "llm_knowledge_evidence": llm_knowledge,
        "analyzed_evidence": analyzed_evidence
    }
```

#### LLM 知识库检索 Prompt

```python
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
    "confidence_level": "高 | 中 | 低"
}
"""
```

#### 输出结构（增强版）

```json
{
    "search_query": "待验证主张",
    "vector_db_evidence": [
        {
            "content": "向量库中的辟谣文档",
            "metadata": {"category": "健康", "source": "WHO"},
            "relevance_score": 0.92,
            "source_type": "vector_db"
        }
    ],
    "llm_knowledge_evidence": {
        "verdict": "假",
        "scientific_basis": "酒精不能杀灭体内病毒...",
        "authority_statements": [
            "WHO 明确表示饮酒不能预防新冠",
            "国家卫健委发布相关辟谣声明"
        ],
        "recommended_sources": [
            "https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public",
            "http://www.nhc.gov.cn/xcs/kpjc/list.shtml"
        ],
        "source_type": "llm_knowledge"
    },
    "summary": {
        "total_evidence": 6,
        "vector_db_count": 5,
        "llm_knowledge_count": 1,
        "evidence_sources": "向量库 + LLM 知识库"
    }
}
```

**技术亮点**:

1. **双重检索策略**: 向量库优先，LLM 知识库补充
2. **来源标记**: 每条证据标注 `source_type` 字段
3. **权威性增强**: LLM 提供权威机构声明和官方来源链接
4. **动态降级**: 向量库不足时自动切换到 LLM 知识库

#### 向量数据库集成

```python
class RetrievalAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        # 初始化向量数据库
        self.vector_db = init_rumor_knowledge_base()
    
    def search_evidence(self, query, n_results=5):
        """搜索相关证据"""
        results = self.vector_db.search(query, n_results=n_results)
        
        evidence_list = []
        if results and results.get("documents"):
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]
            
            for i, doc in enumerate(documents):
                evidence = {
                    "content": doc,
                    "metadata": metadatas[i],
                    "relevance_score": 1 - distances[i]  # 距离转相似度
                }
                evidence_list.append(evidence)
        
        return evidence_list
```

#### 证据分析逻辑

```python
def analyze_evidence(self, claim, evidence):
    messages = [
        SystemMessage(content=self.analysis_prompt),
        HumanMessage(content=f"待验证主张：{claim}\n\n证据内容：{evidence['content']}")
    ]
    
    response = self.call_llm(messages, temperature=0.3)
    
    analysis = json.loads(response)
    analysis["original_evidence"] = evidence
    
    return {
        "evidence_relevance": "high|medium|low",
        "evidence_credibility": "high|medium|low",
        "support_conclusion": true/false,
        "analysis": "详细分析",
        "key_facts": ["关键事实"]
    }
```

#### RAG 架构实现（增强版）

这是典型的 **混合 RAG (Hybrid RAG)** 模式:

**架构层次**:
```
1. 第一层：向量库检索 (ChromaDB)
   └─ 优势：精确匹配预置知识，速度快
   └─ 劣势：仅能检索已录入的数据

2. 第二层：LLM 知识库检索 (qwen-plus)
   └─ 优势：覆盖范围广，包含训练数据内的所有知识
   └─ 劣势：可能存在幻觉，时效性受限

3. 融合策略:
   ├─ 向量库相关性高 → 仅使用向量库证据
   └─ 向量库相关性低 → 触发 LLM 知识库补充
```

**解决的问题**:
- ✅ 解决向量库覆盖范围有限的问题
- ✅ 对于新出现的谣言，仍能提供权威信息
- ✅ 结合了两者的优势：向量库的准确性 + LLM 的知识广度
- ✅ 提供可追溯的权威来源（官网链接、机构名称）

**对比纯向量库 RAG**:

| 维度 | 纯向量库 RAG | 混合 RAG (本项目) |
|------|-------------|------------------|
| 覆盖范围 | 仅限预置知识 | LLM 训练数据全量知识 |
| 时效性 | 需手动更新 | 依赖模型训练截止时间 |
| 准确性 | 高（人工审核） | 中高（需验证） |
| 权威性 | 取决于来源 | 提供权威机构背书 |
| 成本 | 低 | 中等（额外 LLM 调用） |
| 适用场景 | 固定领域 | 开放领域谣言 |

---

### 6️⃣ ReportAgent - 报告生成智能体

**文件路径**: `src/agents/rumor_agents/report_agent.py`

#### 核心职责

- 汇总所有前序智能体的分析结果
- 生成结构化辟谣报告
- 提供可读性更好的格式化输出

#### 报告生成 Prompt

```python
self.report_prompt = """你是一个专业的辟谣报告撰写专家。

报告要求：
1. 结构清晰，逻辑严谨
2. 结论明确，有理有据
3. 证据来源清晰可查
4. 语言专业但易懂
5. 给出明确的可信度评级

请生成 JSON 格式的报告：
{
    "title": "报告标题",
    "verdict": "真 | 假 | 部分真实 | 无法判断",
    "confidence": 0.0-1.0,
    "summary": "简要结论（100 字以内）",
    "analysis": "详细分析",
    "key_findings": ["关键发现"],
    "evidence_summary": "证据摘要",
    "recommendations": ["建议"],
    "credibility_level": "高 | 中 | 低",
    "risk_level": "高 | 中 | 低"
}"""
```

#### 信息聚合方法

```python
def _build_input_summary(self, parser_result, ai_detection_result, retrieval_result):
    summary_parts = []
    
    # 内容解析摘要
    if parser_result:
        summary_parts.append("【内容解析结果】")
        summary_parts.append(f"核心主张：{parser_result['combined_claim']}")
        if parser_result.get("text_analysis"):
            ta = parser_result["text_analysis"]
            summary_parts.append(f"文本分类：{ta.get('category')}")
            summary_parts.append(f"关键词：{', '.join(ta['keywords'][:5])}")
    
    # AI 检测摘要
    if ai_detection_result:
        summary_parts.append("\n【AI 生成检测结果】")
        oa = ai_detection_result["overall_assessment"]
        summary_parts.append(f"是否 AI 生成：{'是' if oa.get('is_ai_generated') else '否'}")
        summary_parts.append(f"置信度：{oa.get('confidence', 0):.2%}")
    
    # 证据检索摘要
    if retrieval_result:
        summary_parts.append("\n【证据检索结果】")
        summary_parts.append(f"找到相关证据：{len(retrieval_result['analyzed_evidence'])} 条")
        for i, evidence in enumerate(retrieval_result["analyzed_evidence"][:3]):
            summary_parts.append(f"\n证据{i}: 相关性={evidence.get('evidence_relevance')}")
    
    return "\n".join(summary_parts)
```

#### 双格式输出

```python
def process(self, input_data):
    report = self.generate_report(...)  # 结构化 JSON
    readable_report = self.generate_readable_report(report)  # 人类可读文本
    
    return {
        "structured_report": report,          # 供程序处理
        "readable_report": readable_report    # 供用户阅读
    }
```

**设计优势**:
- **结构化数据**: 便于前端解析和展示
- **自然语言文本**: 提升用户体验
- **元数据追踪**: 记录生成时间和版本

---

### 7️⃣ RumorDebunkerWorkflow - 工作流编排

**文件路径**: `src/agents/rumor_workflow.py`

#### 核心职责

- 初始化所有智能体
- 按顺序协调执行
- 数据在各智能体间流转
- 异常处理和日志记录

#### 执行流程

```python
class RumorDebunkerWorkflow:
    def __init__(self):
        # 初始化所有智能体
        self.orchestrator = OrchestratorAgent()
        self.parser = ParserAgent()
        self.ai_detector = AIDetectorAgent()
        self.retrieval = RetrievalAgent()
        self.report = ReportAgent()
    
    def run(self, text=None, image_url=None):
        start_time = datetime.now()
        result = {
            "success": False,
            "workflow_steps": [],
            "execution_time": None
        }
        
        try:
            # 步骤 1: 调度智能体
            orchestrator_result = self.orchestrator.process(input_data)
            result["workflow_steps"].append("orchestrator")
            
            # 步骤 2: 内容解析
            parser_result = self.parser.process(input_data)
            result["workflow_steps"].append("parser")
            
            # 步骤 3: AI 检测
            ai_detection_result = self.ai_detector.process({
                "parser_result": parser_result
            })
            result["workflow_steps"].append("ai_detector")
            
            # 步骤 4: 证据检索
            retrieval_result = self.retrieval.process({
                "parser_result": parser_result
            })
            result["workflow_steps"].append("retrieval")
            
            # 步骤 5: 报告生成
            report_result = self.report.process({
                "parser_result": parser_result,
                "ai_detection_result": ai_detection_result,
                "retrieval_result": retrieval_result
            })
            result["workflow_steps"].append("report")
            
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
        
        result["execution_time"] = str(datetime.now() - start_time)
        return result
```

#### 数据流转图

```
输入 (text/image_url)
    ↓
[Orchestrator] → 调度决策
    ↓
[Parser] → parser_result (text_analysis, image_analysis, combined_claim)
    ↓
[AIDetector] → ai_detection_result (text_detection, image_detection, overall_assessment)
    ↓
[Retrieval] → retrieval_result (evidence_list, analyzed_evidence)
    ↓
[Report] → report_result (structured_report, readable_report)
    ↓
输出 (完整结果字典)
```

---

### 8️⃣ RumorVectorDB - 向量数据库管理

**文件路径**: `src/storage/rumor_vector_db.py`

#### 核心职责

- 使用 ChromaDB 进行向量存储
- 调用阿里云 embedding 模型
- 支持语义相似度搜索

#### Embedding 生成

```python
class RumorVectorDB:
    def __init__(self, persist_directory="assets/rumor_knowledge/chroma_db"):
        # 初始化 ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False, allow_reset=True)
        )
        
        # 初始化 Embedding 客户端
        self.embedding_client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url=os.getenv("DASHSCOPE_BASE_URL")
        )
    
    def _get_embedding(self, text):
        """获取文本向量"""
        response = self.embedding_client.embeddings.create(
            model="text-embedding-v4",
            input=text
        )
        return response.data[0].embedding
    
    def _get_embeddings_batch(self, texts):
        """批量获取向量"""
        embeddings = []
        for text in texts:
            embeddings.append(self._get_embedding(text))
        return embeddings
```

#### 添加知识

```python
def add_knowledge(self, documents, metadatas=None, ids=None):
    collection = self.get_or_create_collection()
    
    # 批量生成向量
    embeddings = self._get_embeddings_batch(documents)
    
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        embeddings=embeddings  # 使用自定义 embedding
    )
```

#### 相似度搜索

```python
def search(self, query, n_results=5):
    collection = self.get_or_create_collection()
    
    # 生成查询向量
    query_embedding = self._get_embedding(query)
    
    # 余弦相似度搜索
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    return results
```

#### 预置知识库

```python
def init_rumor_knowledge_base():
    db = RumorVectorDB()
    
    if db.get_collection_count() > 0:
        return db  # 已有数据，跳过初始化
    
    # 预置辟谣知识
    knowledge_data = [
        {
            "document": "谣言：喝白酒可以预防新冠病毒。辟谣：酒精并不能杀灭体内的病毒...",
            "metadata": {"category": "健康", "source": "WHO", "credibility": "高"}
        },
        # ... 更多知识条目
    ]
    
    documents = [item["document"] for item in knowledge_data]
    metadatas = [item["metadata"] for item in knowledge_data]
    ids = [f"rumor_{i}" for i in range(len(documents))]
    
    db.add_knowledge(documents=documents, metadatas=metadatas, ids=ids)
    return db
```

**技术亮点**:
- **本地持久化**: SQLite 存储向量数据
- **增量更新**: 支持动态添加新知识
- **元数据过滤**: 可按类别、来源筛选
- **冷启动优化**: 首次运行自动初始化预置知识

---

## 数据流转与执行流程

### 完整请求处理流程

```
1. 用户输入 (app.py - Streamlit)
   ↓
2. 创建工作流实例 (RumorDebunkerWorkflow)
   ↓
3. 执行工作流.run() 方法
   ↓
4. 智能体顺序执行:
   ├─ OrchestratorAgent.analyze_input()
   │   └─ 输入类型识别 → workflow 决策
   ├─ ParserAgent.parse_text()/parse_image()
   │   └─ 提取核心主张、关键词、语气
   ├─ AIDetectorAgent.detect_text()/detect_image()
   │   └─ AI 生成特征检测
   ├─ RetrievalAgent.search_evidence()
   │   └─ 向量数据库检索 + 证据分析
   └─ ReportAgent.generate_report()
       └─ 汇总所有信息生成报告
   ↓
5. 返回结果到前端展示
```

### 数据结构演化

```python
# 初始输入
input_data = {
    "text": "喝白酒可以预防新冠病毒",
    "image_url": None
}

# After Orchestrator
orchestrator_result = {
    "input_type": "text",
    "workflow": ["parser", "ai_detector", "retrieval", "report"],
    "priority": "medium"
}

# After Parser
parser_result = {
    "text_analysis": {
        "main_claim": "喝白酒可以预防新冠病毒",
        "category": "健康",
        "keywords": ["白酒", "新冠病毒", "预防"],
        "tone": "informative"
    },
    "combined_claim": "喝白酒可以预防新冠病毒"
}

# After AI Detector
ai_detection_result = {
    "text_detection": {
        "is_ai_generated": False,
        "confidence": 0.85,
        "detected_features": []
    },
    "overall_assessment": {
        "is_ai_generated": False,
        "confidence": 0.85
    }
}

# After Retrieval
retrieval_result = {
    "search_query": "喝白酒可以预防新冠病毒",
    "evidence_list": [...],  # 5 条相关证据
    "analyzed_evidence": [
        {
            "evidence_relevance": "high",
            "evidence_credibility": "high",
            "support_conclusion": True,
            "key_facts": ["酒精不能杀灭体内病毒"]
        }
    ]
}

# After Report
report_result = {
    "structured_report": {
        "verdict": "假",
        "confidence": 0.95,
        "summary": "该说法无科学依据...",
        "credibility_level": "高",
        "risk_level": "高"
    },
    "readable_report": "格式化文本报告..."
}
```

---

## 关键技术点分析

### 1. LangChain + LangGraph 智能体编排

**LangChain 核心概念应用**:

- **Message 类型**: `SystemMessage`, `HumanMessage`, `AIMessage`
- **LLM 调用**: 统一的 `chat.completions.create()` 接口
- **Prompt 模板**: 通过 system prompt 定义角色和输出格式

**LangGraph 扩展能力** (虽然本项目未直接使用图结构):

- 支持状态管理 (`StateGraph`)
- 条件边和循环
- 节点并行执行

### 2. RAG (检索增强生成) 架构

**实现步骤**:

```
1. 用户查询 → Embedding 模型 → 查询向量
2. 向量数据库 → 余弦相似度搜索 → Top-K 相关文档
3. 查询 + 文档 → LLM → 增强回答
```

**解决的问题**:

- ✅ LLM 幻觉 (Hallucination)
- ✅ 知识时效性
- ✅ 领域专业性
- ✅ 可解释性和可追溯性

### 3. 多模态处理

**技术方案**:

```python
# 文本 + 图片联合输入
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "请分析这张图片"},
            {"type": "image_url", "image_url": {"url": base64_encoded_image}}
        ]
    }
]

response = client.chat.completions.create(
    model="qwen-vl-plus",  # 视觉语言模型
    messages=messages
)
```

**应用场景**:

- OCR 文字识别
- 图片内容理解
- 图文一致性验证

### 4. JSON 结构化输出

**Prompt Engineering 技巧**:

```python
prompt = """请输出 JSON 格式的结果：
{
    "field1": "value1",
    "field2": true,
    "field3": ["array_item1", "array_item2"]
}"""

# 响应后处理
response = llm.invoke(prompt)
if "```json" in response:
    json_str = response.split("```json")[1].split("```")[0].strip()
result = json.loads(json_str)
```

**优势**:

- 便于程序解析
- 字段类型明确
- 支持嵌套复杂结构

### 5. 向量数据库选型

**ChromaDB 特点**:

- 轻量级，无需额外服务
- 本地持久化 (SQLite)
- Python 原生支持
- 支持元数据过滤

**对比其他方案**:

| 方案 | 优势 | 劣势 | 适用场景 |
|------|------|------|----------|
| ChromaDB | 轻量、易部署 | 性能一般 | 小型项目、原型 |
| FAISS | 高性能 | 需自行封装 | 大规模检索 |
| Pinecone | 托管服务 | 成本高 | 生产环境 |
| Milvus | 功能强大 | 部署复杂 | 企业级应用 |

### 6. Embedding 模型选择

**阿里云 text-embedding-v4**:

- 维度：1536 维
- 支持中文优化
- 语义理解能力强
- API 调用便捷

**替代方案**:

- OpenAI `text-embedding-3-large`
- HuggingFace `bge-large-zh` (本地部署)
- Sentence Transformers

### 7. 错误处理与降级策略

**多层容错机制**:

```python
try:
    # 尝试解析 JSON
    if "```json" in response:
        json_str = response.split("```json")[1].split("```")[0]
    result = json.loads(json_str)
except:
    # 降级到默认值
    result = {
        "main_claim": text[:100],
        "confidence": 0.5,
        "verdict": "无法判断"
    }
```

**设计原则**:

- 不中断用户体验
- 提供合理默认值
- 记录详细错误日志

---

## 部署与配置

### 环境要求

- Python 3.12+
- 阿里云百炼 API Key
- 内存 ≥ 4GB (ChromaDB + LLM 调用)

### 安装步骤

```bash
# 1. 克隆项目
git clone <repo_url>
cd rumor-debunker

# 2. 安装依赖 (使用 uv 或 pip)
uv sync
# 或
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑.env 文件，填入 DASHSCOPE_API_KEY

# 4. 运行应用
streamlit run app.py
```

### 配置文件解析

**`.env` 环境变量**:

```bash
DASHSCOPE_API_KEY=sk-your_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

**`config/agent_llm_config.json`**:

```json
{
  "config": {
    "model": "qwen-plus",
    "temperature": 0.7,
    "top_p": 0.9,
    "max_completion_tokens": 10000,
    "timeout": 600,
    "thinking": "disabled"
  },
  "sp": "你是一个专业的辟谣专家系统...",
  "tools": []
}
```

### 性能优化建议

1. **缓存策略**:
   - 缓存高频查询的 embedding
   - 缓存常见谣言的分析结果

2. **批量处理**:
   - Embedding 批量生成而非单个调用
   - 异步并发处理多个请求

3. **数据库优化**:
   - 定期清理无用集合
   - 建立索引加速检索

4. **模型选择**:
   - 开发测试使用 `qwen-turbo` (更快更便宜)
   - 生产环境使用 `qwen-max` (更高精度)

---

## 面试常见问题准备

### Q1: 为什么选择多智能体架构而不是单一 LLM？

**参考答案**:

1. **关注点分离**: 每个智能体专注单一职责，符合 SOLID 原则
2. **可维护性**: 修改某个功能只需调整对应智能体
3. **可解释性**: 每个环节的输出可单独调试和验证
4. **灵活性**: 支持动态调整工作流（如跳过 AI 检测）
5. **性能优化**: 可针对不同环节选择最优模型（如检索用轻量模型，报告用重量模型）

**对比单一模型**:
- ❌ 单一模型：Prompt 过长容易丢失重点，难以调试
- ✅ 多智能体：模块化、可组合、易扩展

---

### Q2: RAG 架构相比纯 LLM 有什么优势？

**参考答案**:

1. **减少幻觉**: 基于检索到的真实证据生成回答，而非完全依赖模型内部知识
2. **知识可更新**: 添加新知识到向量库即可，无需重新训练模型
3. **可追溯性**: 每条结论都有明确的证据来源
4. **领域适应性**: 通过构建领域知识库快速适配垂直场景
5. **成本控制**: 小模型 + RAG 可达到大模型效果，降低 API 调用成本

**本项目的 RAG 实现**:
- 检索：ChromaDB 向量相似度搜索
- 增强：将证据作为上下文拼接到 Prompt
- 生成：LLM 基于证据进行分析

---

### Q3: 如何保证 JSON 输出的稳定性？

**参考答案**:

1. **Prompt 工程**:
   - 明确给出 JSON Schema 模板
   - 使用 few-shot prompting 提供示例
   - 设置较低 temperature (0.3)

2. **后处理解析**:
   ```python
   # 多种格式兼容
   if "```json" in response:
       json_str = extract_markdown_json(response)
   elif "{" in response:
       json_str = extract_brace_content(response)
   
   # 异常降级
   try:
       result = json.loads(json_str)
   except:
       result = get_default_response()
   ```

3. **验证机制**:
   - 使用 Pydantic 验证 JSON 结构
   - 必填字段检查
   - 类型校验

---

### Q4: 向量数据库的工作原理是什么？

**参考答案**:

**核心流程**:

1. **向量化**: 使用 Embedding 模型将文本转换为高维向量
2. **存储**: 将向量和原文存入数据库
3. **检索**: 计算查询向量与库中向量的相似度（余弦相似度）
4. **排序**: 按相似度降序返回 Top-K 结果

**数学原理**:
```
余弦相似度 = cos(θ) = (A·B) / (||A|| × ||B||)
值域：[-1, 1], 越接近 1 越相似
```

**本项目实现**:
- ChromaDB 持久化存储
- 阿里云 text-embedding-v4 生成 1536 维向量
- 支持元数据过滤的混合搜索

---

### Q5: 如何处理多模态输入（文本 + 图片）？

**参考答案**:

**技术栈**:
- 视觉语言模型 (VLM): qwen-vl-plus
- 支持图文联合输入

**实现方式**:
```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "请分析图片内容"},
            {"type": "image_url", "image_url": {"url": base64_image}}
        ]
    }
]
```

**处理流程**:
1. 图片编码为 Base64
2. 拼接图文到 Message Content
3. VLM 模型同时处理视觉和文本信息
4. 输出文本描述和分析结果

**应用场景**:
- OCR 文字提取
- 图片内容理解
- 图文一致性验证（如"有图有真相"类谣言）

---

### Q6: 如果让你优化这个系统，你会从哪些方面入手？

**参考答案**:

**性能优化**:
1. 引入 Redis 缓存热点查询
2. Embedding 批量生成减少 API 调用次数
3. 异步并发处理多个智能体（如 AI 检测和证据检索可并行）

**质量优化**:
1. 增加事实核查工具（接入第三方 API 如 Wikipedia、百度百科）
2. 引入置信度阈值，低置信度时请求人工审核
3. 增加对抗样本检测，防止恶意输入

**用户体验**:
1. 流式输出分析过程（让用户看到进度）
2. 增加可视化证据图谱
3. 支持历史查询记录和对比

**工程化**:
1. 添加单元测试和集成测试
2. CI/CD自动化部署
3. 监控告警（API 调用失败率、响应时间）

**商业模式**:
1. API 开放平台
2. 浏览器插件
3. 企业定制版本（私有化部署）

---

### Q7: 项目中遇到的最大技术挑战是什么？如何解决的？

**参考答案** (可根据实际情况调整):

**挑战 1: JSON 输出不稳定**
- 问题：LLM 偶尔输出非标准 JSON 格式
- 解决：
  - Prompt 中明确 JSON Schema
  - 后处理增加多种格式解析逻辑
  - 设置 temperature=0.3 降低随机性
  - 降级策略保证系统不崩溃

**挑战 2: 向量检索精度不足**
- 问题：简单语义相似度无法捕捉深层逻辑关系
- 解决：
  - 优化 Query 表述（使用核心主张而非全文）
  - 增加重排序环节（Cross-Encoder）
  - 结合元数据过滤（如同类别优先）

**挑战 3: 多模态模型调用失败**
- 问题：图片过大或格式不支持
- 解决：
  - 前端限制上传大小和格式
  - 图片预处理（压缩、格式转换）
  - 超时重试机制

---

### Q8: 如何评估这个系统的效果？

**参考答案**:

**定量指标**:
1. **准确率**: 与人工标注的真实标签对比
2. **召回率**: 成功识别的谣言比例
3. **响应时间**: P95/P99延迟
4. **API 调用成功率**: LLM 和 Embedding 调用稳定性
5. **用户满意度**: 评分或反馈收集

**定性评估**:
1. **报告质量**: 逻辑性、可读性、专业性
2. **证据可靠性**: 来源权威性、时效性
3. **可解释性**: 结论是否有充分理由支撑

**A/B 测试**:
- 不同模型配置对比（qwen-plus vs qwen-max）
- 不同 Prompt 版本效果
- RAG vs 纯 LLM

**持续改进**:
- 收集 bad cases 分析原因
- 定期更新知识库
- 根据用户反馈迭代优化

---

## 总结

### 项目核心技术栈

```
多智能体系统 (Multi-Agent System)
    ├── LangChain (LLM 应用框架)
    └── LangGraph (工作流编排)

RAG 架构 (检索增强生成)
    ├── ChromaDB (向量数据库)
    └── Embedding 模型 (语义表示)

多模态处理
    └── Vision-Language Model (图文理解)

Web 全栈
    ├── FastAPI (后端服务)
    └── Streamlit (前端交互)
```

### 设计模式与架构思想

1. **微服务思想**: 每个智能体独立部署和演进
2. **事件驱动**: 工作流按事件顺序触发
3. **管道 - 过滤器**: 数据依次经过各处理环节
4. **约定优于配置**: 统一接口和输出格式

### 可扩展方向

1. **工具集成**: 接入搜索引擎、事实核查 API
2. **工作流引擎**: 使用 LangGraph 实现条件分支和循环
3. **记忆机制**: 添加长期记忆存储用户历史查询
4. **自我反思**: 增加 Critic 智能体审查报告质量

### 面试加分项

- 能清晰解释 RAG 原理和优势
- 理解向量数据库工作机制
- 掌握 Prompt Engineering 技巧
- 有多智能体系统设计经验
- 熟悉 LangChain 生态工具

---

**文档版本**: v1.0  
**最后更新**: 2026-03-27  
**作者**: AI 助手  

---

*注：本文档基于项目源代码自动生成，如需引用请注明出处。*
