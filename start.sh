#!/bin/bash

# 辟谣专家多智能体系统 - 一键启动脚本

echo "======================================"
echo "  辟谣专家多智能体系统"
echo "  启动脚本 v1.0"
echo "======================================"
echo ""

# 检查Python版本
echo "🔍 检查Python环境..."
if ! command -v python &> /dev/null
then
    echo "❌ 未找到Python，请先安装Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "✅ Python版本: $PYTHON_VERSION"
echo ""

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "🔄 激活虚拟环境..."
    source venv/bin/activate
fi

# 安装依赖
echo "📦 检查并安装依赖..."
pip install -q -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✅ 依赖安装完成"
else
    echo "⚠️ 依赖安装可能存在问题，但继续尝试启动..."
fi
echo ""

# 初始化知识库
echo "📚 初始化知识库..."
python -c "from storage.rumor_vector_db import init_rumor_knowledge_base; init_rumor_knowledge_base()"
echo "✅ 知识库初始化完成"
echo ""

# 启动Streamlit
echo "🚀 启动Web服务..."
echo "   访问地址: http://localhost:8501"
echo "   按 Ctrl+C 停止服务"
echo ""
echo "======================================"

streamlit run app.py
