# 🔍 辟谣专家多智能体系统

<div align="center">

**一个基于多智能体协作的专业辟谣分析平台**

[快速开始](#-快速开始) • [系统架构](#-系统架构) • [使用指南](#-使用指南) • [部署说明](#-部署说明)

</div>

---

## 📖 项目简介

本系统是一个基于 **多智能体协作架构** 的辟谣分析平台，通过 5 个专业智能体的协同工作，对输入的文本或图片内容进行深度分析，判断信息的真实性并提供权威辟谣证据。

### 🎯 核心能力

- ✅ **多模态输入支持** - 支持文本和图片输入
- ✅ **AI 生成内容检测** - 判断内容是否为 AI 生成
- ✅ **知识库检索** - 从预置知识库检索相关辟谣证据
- ✅ **结构化报告** - 生成专业的辟谣分析报告
- ✅ **Web 界面** - 美观易用的 Streamlit 界面

---

## ✨ 功能特性

### 🤖 五大智能体协作

| 智能体 | 职责 |
|--------|------|
| **调度智能体** | 任务分发、流程控制 |
| **内容解析智能体** | 内容提取和分析 |
| **AI 检测智能体** | AI 生成检测 |
| **证据检索智能体** | 从向量库检索相关辟谣证据 |
| **报告生成智能体** | 生成结构化辟谣分析报告 |

### 📊 分析维度

1. **内容真实性判断** - 真/假/部分真实/无法判断
2. **AI 生成检测** - 判断内容来源
3. **证据关联分析** - 检索相关辟谣证据
4. **风险等级评估** - 高/中/低风险
5. **可信度评级** - 高/中/低可信度

---

## 🏗️ 系统架构

```
用户输入 → 调度智能体 → 内容解析 → AI 检测 & 证据检索 → 报告生成 → 输出结果
```

### 项目结构

```
rumor-debunker/
├── app.py                          # Streamlit 主应用
├── requirements.txt                # 依赖包列表
├── config/                         # 配置目录
├── src/
│   ├── agents/                    # 智能体模块
│   │   └── rumor_agents/          # 辟谣智能体
│   └── storage/                   # 存储模块
├── assets/                        # 知识库数据
└── scripts/                       # 脚本工具
```

---

## 🚀 快速开始

### 环境要求

- Python 3.12+
- pip 或 uv 包管理器

### 安装步骤

#### 1️⃣ 克隆项目

```bash
git clone <项目地址>
cd rumor-debunker
```

#### 2️⃣ 安装依赖

```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -r requirements.txt
```

#### 3️⃣ 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置你的 API Key：
```bash
DASHSCOPE_API_KEY=sk-your_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

#### 4️⃣ 运行应用

```bash
streamlit run app.py
```

应用将在浏览器中自动打开：`http://localhost:8501`

---

## 📖 使用指南

### 文本辟谣

1. 在文本框输入待验证的内容
2. 点击 **"开始分析"** 按钮
3. 等待系统分析完成，查看分析报告

**示例输入：**
```
喝白酒可以预防新冠病毒，这个说法是真的吗？
```

### 图片辟谣

1. 点击 **"上传图片"** 按钮
2. 选择需要分析的图片（支持 PNG、JPG、JPEG、GIF）
3. 系统将自动进行 OCR 文字识别和图片内容分析
4. 查看分析报告

### 结果解读

- **结论**：真/假/部分真实/无法判断
- **可信度**：高/中/低
- **风险等级**：🔴高 / 🟡中 / 🟢低

---

## 🔧 配置说明

### 环境变量

在 `.env` 文件中配置：

```bash
DASHSCOPE_API_KEY=sk-your_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### 应用配置

系统使用阿里云百炼 API，支持多种模型。详细配置请参考代码注释。

---

## 🔒 安全说明

1. **本地部署** - 所有处理都在本地进行，数据不会上传到第三方服务器
2. **API 密钥安全** - 请勿将 API 密钥提交到版本控制系统
3. **免责声明** - 本系统仅供参考，不构成专业建议

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

MIT License

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star！⭐**

Made with ❤️ by 辟谣专家团队

</div>
