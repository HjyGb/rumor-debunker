@echo off
chcp 65001 >nul
REM 辟谣专家多智能体系统 - Windows一键启动脚本

echo ======================================
echo   辟谣专家多智能体系统
echo   启动脚本 v1.0
echo ======================================
echo.

REM 检查Python
echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python版本: %PYTHON_VERSION%
echo.

REM 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 🔄 激活虚拟环境...
    call venv\Scripts\activate.bat
)

REM 安装依赖
echo 📦 检查并安装依赖...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ⚠️ 依赖安装可能存在问题，但继续尝试启动...
) else (
    echo ✅ 依赖安装完成
)
echo.

REM 初始化知识库
echo 📚 初始化知识库...
python -c "from storage.rumor_vector_db import init_rumor_knowledge_base; init_rumor_knowledge_base()"
echo ✅ 知识库初始化完成
echo.

REM 启动Streamlit
echo 🚀 启动Web服务...
echo    访问地址: http://localhost:8501
echo    按 Ctrl+C 停止服务
echo.
echo ======================================

streamlit run app.py
