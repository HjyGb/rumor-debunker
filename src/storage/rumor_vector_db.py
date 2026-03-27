"""
辟谣知识库向量数据库管理模块
使用 ChromaDB 进行本地向量存储和检索
Embedding 使用阿里百炼云 text-embedding-v4 模型
"""
import os
import json
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from openai import OpenAI


class RumorVectorDB:
    """辟谣知识库向量数据库管理器"""
    
    def __init__(self, persist_directory: str = "assets/rumor_knowledge/chroma_db"):
        """
        初始化向量数据库
        
        Args:
            persist_directory: 向量数据库持久化目录
        """
        self.persist_directory = persist_directory
        
        # 确保目录存在
        os.makedirs(persist_directory, exist_ok=True)
        
        # 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 初始化阿里百炼云 Embedding 客户端
        api_key = os.getenv("DASHSCOPE_API_KEY")
        base_url = os.getenv("DASHSCOPE_BASE_URL")
        
        if not api_key or not base_url:
            raise ValueError("请配置 DASHSCOPE_API_KEY 和 DASHSCOPE_BASE_URL 环境变量")
        
        self.embedding_client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        self.collection_name = "rumor_knowledge_base"
        self.collection = None
        
    def _get_embedding(self, text: str) -> List[float]:
        """
        使用阿里百炼云 text-embedding-v4 模型获取文本向量
        
        Args:
            text: 输入文本
            
        Returns:
            文本的向量表示
        """
        try:
            response = self.embedding_client.embeddings.create(
                model="text-embedding-v4",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ 获取 embedding 失败：{e}")
            raise
    
    def _get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量获取文本向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        embeddings = []
        for i, text in enumerate(texts):
            print(f"正在处理 embedding {i+1}/{len(texts)}...")
            embeddings.append(self._get_embedding(text))
        return embeddings
    
    def get_or_create_collection(self):
        """获取或创建集合"""
        if self.collection is None:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "辟谣知识库"}
            )
        return self.collection
    
    def add_knowledge(
        self, 
        documents: List[str], 
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ):
        """
        添加知识到向量库（使用阿里百炼云 embedding）
        
        Args:
            documents: 文档列表
            metadatas: 元数据列表
            ids: ID列表
        """
        collection = self.get_or_create_collection()
        
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        if metadatas is None:
            metadatas = [{"source": "knowledge_base"} for _ in documents]
        
        # 使用阿里百炼云 embedding 模型生成向量
        print(f"\n📊 正在调用阿里百炼云 text-embedding-v4 模型处理 {len(documents)} 条文档...")
        embeddings = self._get_embeddings_batch(documents)
        
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings
        )
        
        print(f"✅ 成功添加 {len(documents)} 条知识到向量库")
    
    def search(self, query: str, n_results: int = 5) -> Dict:
        """
        搜索相关知识（使用阿里百炼云 embedding）
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            
        Returns:
            搜索结果字典
        """
        collection = self.get_or_create_collection()
        
        # 使用阿里百炼云 embedding 模型生成查询向量
        query_embedding = self._get_embedding(query)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        return results
    
    def get_collection_count(self) -> int:
        """获取集合中的文档数量"""
        collection = self.get_or_create_collection()
        return collection.count()
    
    def reset_collection(self):
        """重置集合"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = None
            print("✅ 集合已重置")
        except Exception as e:
            print(f"⚠️ 重置失败: {e}")


def init_rumor_knowledge_base():
    """
    初始化辟谣知识库
    预置一些常见的谣言和辟谣信息
    """
    db = RumorVectorDB()
    
    # 检查是否已有数据
    if db.get_collection_count() > 0:
        print(f"📚 知识库已存在 {db.get_collection_count()} 条数据")
        return db
    
    # 预置辟谣知识数据
    knowledge_data = [
        # 健康类谣言
        {
            "document": "谣言：喝白酒可以预防新冠病毒。辟谣：酒精并不能杀灭体内的病毒，反而会损害免疫系统。世界卫生组织明确表示，饮酒不能保护您免受COVID-19感染，并可能带来其他健康风险。",
            "metadata": {"category": "健康", "source": "WHO", "credibility": "高"}
        },
        {
            "document": "谣言：微波炉加热食物会产生致癌物质。辟谣：微波炉加热的原理是利用微波使水分子振动产生热，不会改变食物的分子结构。国际癌症研究机构指出，微波加热是安全的烹饪方式。",
            "metadata": {"category": "健康", "source": "IARC", "credibility": "高"}
        },
        {
            "document": "谣言：手机辐射会导致脑癌。辟谣：经过大量研究，没有证据表明手机辐射会导致癌症。世界卫生组织表示，目前没有确认的手机辐射健康风险。",
            "metadata": {"category": "健康", "source": "WHO", "credibility": "高"}
        },
        {
            "document": "谣言：吃碘盐能防辐射。辟谣：碘盐中的碘含量很低，无法达到防辐射的效果。过量食用碘盐反而会导致高血压等健康问题。只有在核事故等极端情况下，才需要在医生指导下服用碘片。",
            "metadata": {"category": "健康", "source": "CDC", "credibility": "高"}
        },
        
        # 科学类谣言
        {
            "document": "谣言：地球是平的。辟谣：地球是球体已被无数科学证据证实，包括卫星照片、环球航行、月食现象等。古希腊科学家埃拉托斯特尼在公元前240年就测量出了地球周长。",
            "metadata": {"category": "科学", "source": "NASA", "credibility": "极高"}
        },
        {
            "document": "谣言：登月是伪造的。辟谣：阿波罗登月计划有大量证据支持，包括带回的月球岩石样本、留在月球上的反射镜、轨道探测器拍摄的照片等。多国航天机构都确认了登月事实。",
            "metadata": {"category": "科学", "source": "NASA", "credibility": "极高"}
        },
        {
            "document": "谣言：5G网络传播病毒。辟谣：5G是无线电波技术，与病毒传播完全无关。病毒需要宿主才能传播，不能通过电磁波传播。这是毫无科学依据的谣言。",
            "metadata": {"category": "科学", "source": "WHO", "credibility": "高"}
        },
        
        # 食品安全类谣言
        {
            "document": "谣言：味精加热会产生有毒物质。辟谣：味精（谷氨酸钠）加热只会分解成谷氨酸和钠，两者都是安全的。谷氨酸是人体必需氨基酸，广泛存在于天然食物中。",
            "metadata": {"category": "食品安全", "source": "FDA", "credibility": "高"}
        },
        {
            "document": "谣言：隔夜菜会致癌。辟谣：隔夜菜中的亚硝酸盐含量很低，远低于安全标准。只要保存得当（冷藏），隔夜菜是安全的。世界卫生组织建议隔夜菜要在24小时内食用。",
            "metadata": {"category": "食品安全", "source": "WHO", "credibility": "高"}
        },
        {
            "document": "谣言：塑料瓶装水会释放致癌物。辟谣：正规厂家生产的塑料瓶（PET材质）在正常使用温度下不会释放有害物质。但要避免高温环境下长时间存放，不要重复使用一次性塑料瓶。",
            "metadata": {"category": "食品安全", "source": "FDA", "credibility": "高"}
        },
        
        # 社会类谣言
        {
            "document": "谣言：打疫苗会改变DNA。辟谣：mRNA疫苗不会改变人类DNA。mRNA疫苗的作用原理是让细胞产生无害的病毒蛋白，从而触发免疫反应。mRNA不会进入细胞核，无法改变DNA。",
            "metadata": {"category": "医疗", "source": "CDC", "credibility": "极高"}
        },
        {
            "document": "谣言：二维码扫描会盗取银行卡信息。辟谣：二维码本身只是一串编码，不能直接盗取信息。风险在于扫描后打开的恶意链接。建议只扫描可信来源的二维码，不随意输入敏感信息。",
            "metadata": {"category": "网络安全", "source": "网安部门", "credibility": "高"}
        },
        
        # AI生成内容识别提示
        {
            "document": "AI生成文本特征：过于流畅和完美、缺乏个人经历细节、重复性表达、逻辑结构过于规整、缺乏情感波动、事实细节可能存在错误、引用来源可能不实。",
            "metadata": {"category": "AI识别", "source": "技术标准", "credibility": "中"}
        },
        {
            "document": "AI生成图像特征：手指数量错误、文字模糊或无意义、背景细节不连贯、对称性异常、光影不一致、眼睛细节不自然、边缘过度平滑。",
            "metadata": {"category": "AI识别", "source": "技术标准", "credibility": "中"}
        }
    ]
    
    # 提取文档、元数据和ID
    documents = [item["document"] for item in knowledge_data]
    metadatas = [item["metadata"] for item in knowledge_data]
    ids = [f"rumor_{i}" for i in range(len(documents))]
    
    # 添加到向量库
    db.add_knowledge(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"📚 辟谣知识库初始化完成，共 {db.get_collection_count()} 条知识")
    return db


if __name__ == "__main__":
    # 初始化知识库
    init_rumor_knowledge_base()
