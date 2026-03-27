# 🔍 辟谣专家多智能体系统

一个基于多智能体协作的专业辟谣分析平台，通过 5 个专业智能体的协同工作，对输入的文本或图片内容进行深度分析，判断信息的真实性并提供权威辟谣证据。

## ✨ 核心功能

- ✅ **多模态输入支持** - 支持文本和图片输入
- ✅ **AI 生成内容检测** - 判断内容是否为 AI 生成
- ✅ **知识库检索** - 从预置知识库检索相关辟谣证据
- ✅ **结构化报告** - 生成专业的辟谣分析报告
- ✅ **Web 界面** - 美观易用的 Streamlit 界面

## 🚀 快速开始

### 安装依赖

```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的 API Key：

```bash
cp .env.example .env
```

然后在 `.env` 文件中设置：
```bash
DASHSCOPE_API_KEY=sk-your_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 运行应用

**Streamlit Web 界面：**
```bash
streamlit run app.py
```

**命令行模式：**
```bash
bash scripts/local_run.sh -m flow
```

**启动 HTTP 服务：**
```bash
bash scripts/http_run.sh -m http -p 5000
```

## 📖 详细文档

完整的使用说明、系统架构和 API 文档请查看 [README_RUMOR_SYSTEM.md](README_RUMOR_SYSTEM.md)

## ⚠️ 免责声明

本系统仅供参考，不构成专业建议。对于重要决策，请咨询权威机构。

## 📄 许可证

MIT License