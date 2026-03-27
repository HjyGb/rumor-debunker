"""
辟谣专家多智能体系统 - Streamlit Web 界面
"""
import streamlit as st
import os
import sys
import tempfile
import base64
from datetime import datetime
from typing import Optional

# 尝试加载 .env 文件中的环境变量
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except Exception:
    pass

# 添加项目路径到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入工作流
from src.agents.rumor_workflow import RumorDebunkerWorkflow

# 页面配置
st.set_page_config(
    page_title="辟谣专家系统",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #E3F2FD 0%, #BBDEFB 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1565C0;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .info-box {
        background-color: #E3F2FD;
        border-left: 5px solid #1E88E5;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #E8F5E9;
        border-left: 5px solid #43A047;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FFF3E0;
        border-left: 5px solid #FB8C00;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #FFEBEE;
        border-left: 5px solid #E53935;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .agent-card {
        background-color: #F5F5F5;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #E0E0E0;
    }
    .verdict-true {
        background-color: #C8E6C9;
        color: #2E7D32;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
    }
    .verdict-false {
        background-color: #FFCDD2;
        color: #C62828;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
    }
    .verdict-partial {
        background-color: #FFE0B2;
        color: #EF6C00;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
    }
    .verdict-unknown {
        background-color: #E0E0E0;
        color: #616161;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_workflow():
    """初始化工作流（缓存）"""
    return RumorDebunkerWorkflow()


def encode_image_to_base64(image_file):
    """将上传的图片编码为base64"""
    import base64
    return base64.b64encode(image_file.getvalue()).decode()


def get_image_data_url(image_file):
    """获取图片的data URL"""
    image_bytes = image_file.getvalue()
    base64_image = base64.b64encode(image_bytes).decode()
    
    # 根据文件类型设置MIME类型
    file_type = image_file.type
    if "png" in file_type:
        mime_type = "image/png"
    elif "jpg" in file_type or "jpeg" in file_type:
        mime_type = "image/jpeg"
    elif "gif" in file_type:
        mime_type = "image/gif"
    else:
        mime_type = "image/png"
    
    return f"data:{mime_type};base64,{base64_image}"


def main():
    """主函数"""
    # 标题
    st.markdown('<div class="main-header">🔍 辟谣专家多智能体系统</div>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.markdown("### 📖 系统介绍")
        st.markdown("""
本系统是一个基于多智能体协作的辟谣分析平台，采用5个专业智能体协同工作：

1. **调度智能体** - 任务分发与流程控制
2. **内容解析智能体** - 文本分析和图片OCR
3. **AI检测智能体** - 判断是否为AI生成
4. **证据检索智能体** - 检索权威辟谣证据
5. **报告生成智能体** - 生成结构化报告

---

### 💡 使用说明
- 输入需要验证的文本内容
- 或上传可疑图片
- 系统将自动分析并生成辟谣报告

---

### ⚠️ 免责声明
本系统仅供参考，不构成专业建议。对于重要决策，请咨询权威机构。
        """)
        
        st.markdown("---")
        st.markdown(f"🕒 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 初始化工作流
    workflow = init_workflow()
    
    # 主内容区域
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📝 输入待验证内容")
        
        # 文本输入
        user_text = st.text_area(
            "输入文本内容",
            height=150,
            placeholder="请输入需要验证真伪的文本内容...",
            help="粘贴或输入可疑的文字内容"
        )
        
        # 图片上传
        st.markdown("**或上传图片：**")
        uploaded_image = st.file_uploader(
            "上传图片",
            type=["png", "jpg", "jpeg", "gif"],
            help="上传需要分析的图片"
        )
        
        # 显示上传的图片预览
        if uploaded_image:
            st.image(uploaded_image, caption="上传的图片", use_container_width=True)
    
    with col2:
        st.markdown("### ⚙️ 分析设置")
        
        # 分析选项
        enable_ai_detection = st.checkbox("启用AI生成检测", value=True)
        enable_evidence_retrieval = st.checkbox("启用证据检索", value=True)
        
        st.markdown("---")
        
        # 开始分析按钮
        analyze_button = st.button(
            "🔍 开始分析",
            type="primary",
            use_container_width=True
        )
    
    # 处理分析请求
    if analyze_button:
        # 验证输入
        if not user_text and not uploaded_image:
            st.error("❌ 请输入文本或上传图片！")
            return
        
        # 准备图片数据
        image_url = None
        if uploaded_image:
            image_url = get_image_data_url(uploaded_image)
        
        # 显示进度
        with st.spinner("🔄 正在分析中，请稍候..."):
            # 创建进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 执行分析
            status_text.text("🤖 调度智能体正在分析输入...")
            progress_bar.progress(10)
            
            status_text.text("📝 内容解析智能体正在提取关键信息...")
            progress_bar.progress(30)
            
            status_text.text("🤖 AI检测智能体正在判断内容来源...")
            progress_bar.progress(50)
            
            status_text.text("🔍 证据检索智能体正在搜索相关证据...")
            progress_bar.progress(70)
            
            status_text.text("📊 报告生成智能体正在生成分析报告...")
            progress_bar.progress(90)
            
            # 执行工作流
            result = workflow.run(text=user_text, image_url=image_url)
            
            progress_bar.progress(100)
            status_text.text("✅ 分析完成！")
    
        # 显示结果
        st.markdown("---")
        st.markdown("### 📊 分析结果")
        
        if result.get("success"):
            # 创建标签页
            tab1, tab2, tab3, tab4 = st.tabs(["📋 综合报告", "🔍 详细分析", "📚 证据列表", "ℹ️ 系统信息"])
            
            with tab1:
                # 显示结论
                if result.get("report_result", {}).get("structured_report"):
                    report = result["report_result"]["structured_report"]
                    
                    # 结论卡片
                    verdict = report.get("verdict", "无法判断")
                    verdict_class = {
                        "真": "verdict-true",
                        "假": "verdict-false",
                        "部分真实": "verdict-partial"
                    }.get(verdict, "verdict-unknown")
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        st.markdown(f"**结论：**")
                        st.markdown(f'<div class="{verdict_class}">{verdict}</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"**可信度：**")
                        st.markdown(f'<div class="info-box">{report.get("credibility_level", "未知")}</div>', unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"**风险等级：**")
                        risk_level = report.get("risk_level", "未知")
                        risk_emoji = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(risk_level, "⚪")
                        st.markdown(f'<div class="info-box">{risk_emoji} {risk_level}</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # 摘要
                    st.markdown("#### 📌 摘要")
                    st.markdown(f'<div class="success-box">{report.get("summary", "暂无摘要")}</div>', unsafe_allow_html=True)
                    
                    # 详细分析
                    if report.get("analysis"):
                        st.markdown("#### 🔍 详细分析")
                        st.markdown(report["analysis"])
                    
                    # 关键发现
                    if report.get("key_findings"):
                        st.markdown("#### 💡 关键发现")
                        for i, finding in enumerate(report["key_findings"], 1):
                            st.markdown(f"{i}. {finding}")
                    
                    # 建议
                    if report.get("recommendations"):
                        st.markdown("#### ✅ 建议")
                        for i, rec in enumerate(report["recommendations"], 1):
                            st.markdown(f"{i}. {rec}")
            
            with tab2:
                # 显示各智能体的分析结果
                st.markdown("#### 🤖 智能体分析详情")
                
                # 内容解析结果
                if result.get("parser_result"):
                    with st.expander("📝 内容解析结果", expanded=True):
                        parser_result = result["parser_result"]
                        
                        if parser_result.get("text_analysis"):
                            st.markdown("**文本分析：**")
                            ta = parser_result["text_analysis"]
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"- **核心主张：** {ta.get('main_claim', '无')}")
                                st.markdown(f"- **分类：** {ta.get('category', '未知')}")
                            with col2:
                                st.markdown(f"- **语气：** {ta.get('tone', '未知')}")
                                if ta.get("keywords"):
                                    st.markdown(f"- **关键词：** {', '.join(ta['keywords'][:5])}")
                        
                        if parser_result.get("image_analysis"):
                            st.markdown("**图片分析：**")
                            ia = parser_result["image_analysis"]
                            st.markdown(f"- **OCR文字：** {ia.get('ocr_text', '无')[:200]}...")
                            st.markdown(f"- **核心主张：** {ia.get('main_claim', '无')}")
                
                # AI检测结果
                if result.get("ai_detection_result"):
                    with st.expander("🤖 AI生成检测结果", expanded=True):
                        ai_result = result["ai_detection_result"]
                        
                        if ai_result.get("overall_assessment"):
                            oa = ai_result["overall_assessment"]
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                is_ai = oa.get("is_ai_generated", False)
                                icon = "✅" if not is_ai else "⚠️"
                                st.markdown(f"**是否AI生成：** {icon} {'是' if is_ai else '否'}")
                            with col2:
                                st.markdown(f"**置信度：** {oa.get('confidence', 0):.0%}")
                            
                            st.markdown(f"**结论：** {oa.get('summary', '无')}")
            
            with tab3:
                # 显示证据列表
                st.markdown("#### 📚 检索到的证据")
                
                if result.get("retrieval_result", {}).get("analyzed_evidence"):
                    evidence_list = result["retrieval_result"]["analyzed_evidence"]
                    
                    for i, evidence in enumerate(evidence_list, 1):
                        with st.expander(f"证据 {i}", expanded=(i == 1)):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"**相关性：** {evidence.get('evidence_relevance', '未知')}")
                                st.markdown(f"**可信度：** {evidence.get('evidence_credibility', '未知')}")
                            
                            with col2:
                                support = evidence.get("support_conclusion")
                                if support is not None:
                                    support_text = "✅ 支持" if support else "❌ 不支持"
                                    st.markdown(f"**是否支持结论：** {support_text}")
                            
                            if evidence.get("original_evidence"):
                                st.markdown(f"**内容：**")
                                content = evidence["original_evidence"].get("content", "")
                                st.markdown(f"> {content[:300]}{'...' if len(content) > 300 else ''}")
                            
                            if evidence.get("analysis"):
                                st.markdown(f"**分析：** {evidence['analysis']}")
                else:
                    st.info("暂未找到相关证据")
            
            with tab4:
                # 显示系统信息
                st.markdown("#### ℹ️ 系统信息")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**执行状态：** ✅ 成功")
                    st.markdown(f"**执行时间：** {result.get('execution_time', '未知')}")
                    st.markdown(f"**工作流步骤：** {' → '.join(result.get('workflow_steps', []))}")
                
                with col2:
                    st.markdown("**参与的智能体：**")
                    for step in result.get("workflow_steps", []):
                        agent_names = {
                            "orchestrator": "调度智能体",
                            "parser": "内容解析智能体",
                            "ai_detector": "AI检测智能体",
                            "retrieval": "证据检索智能体",
                            "report": "报告生成智能体"
                        }
                        st.markdown(f"- {agent_names.get(step, step)}")
        
        else:
            # 显示错误
            st.markdown(f'<div class="error-box">❌ 分析失败：{result.get("error", "未知错误")}</div>', unsafe_allow_html=True)
            
            with st.expander("查看错误详情"):
                st.code(result.get("traceback", "无详细错误信息"))


if __name__ == "__main__":
    main()
