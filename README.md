# 教员AI咨询系统 v3.0 - 极致蒸馏版

> 不是角色扮演，是思维重建。
> 基于毛选98万字原文，从数据中客观提取教员的思维系统。

---

## 核心特性

### 与传统角色扮演的区别

| 维度 | 普通角色扮演 | 本系统（极致蒸馏） |
|------|------------|------------------|
| 数据来源 | 人为编写的Prompt | 毛选全四卷98万字原文 |
| 思维方法 | 人为设定"步骤1→步骤2" | 从原文统计提取真实模式 |
| 知识引用 | 背下来的几十条 | 3,571个原文段落动态检索 |
| 概念网络 | 无 | 661个概念+2,238条共现关系 |
| 认知签名 | 无 | 9种if-then情境-行为签名 |
| 人格画像 | 简单描述 | 完整YAML（12个维度） |
| Prompt架构 | 单层静态 | CharLoRA双层动态+PCL自检 |

### 四层架构

```
Layer 1: 原文层 (98万字 → 3,571 chunks → 向量库)
Layer 2: 概念层 (661概念 → 2,238共现 → 图数据库)
Layer 3: Persona层 (完整人格画像 YAML)
Layer 4: Prompt层 (双层动态架构 + PCL自检)
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 20+（前端）
- 支持OpenAI兼容格式的推理模型API

### 1. 克隆项目

```bash
git clone https://github.com/2155697/mao-ai-consultant.git
cd mao-ai-consultant
```

### 2. 准备数据

由于数据文件较大，需要手动放入 `backend/data/` 目录：

```bash
# 下载数据文件（从Release或网盘）
# 放入 backend/data/ 目录，包含：
# - vol1-4_clean.txt (清洗后毛选原文)
# - knowledge_base.json (知识库: chunks+倒排索引)
# - concept_network.json (概念网络: 661概念+共现关系)
# - cognitive_signatures.json (9种认知签名)
# - persona.yaml (完整人格画像)
```

### 3. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务（Mock模式，无需API Key）
python main.py
```

服务启动后访问：http://localhost:8000

### 4. 配置API Key（可选）

```bash
cp .env.example .env
# 编辑.env填入API配置
```

### 5. 启动前端

```bash
cd ../frontend
npm install
npm run dev
```

---

## 项目结构

```
mao-ai-consultant/
├── README.md
├── backend/
│   ├── main.py                 # FastAPI入口
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py       # 配置管理
│   │   │   └── persona_engine.py  # 核心引擎(460行)
│   │   ├── models/schemas.py   # 数据模型
│   │   ├── api/chat.py         # API路由
│   │   └── services/llm_client.py  # LLM客户端
│   └── data/                   # 数据资产(需手动放入)
└── frontend/
    ├── index.html
    ├── vite.config.ts
    ├── tailwind.config.js
    └── src/
        ├── App.tsx
        ├── types.ts
        ├── components/
        │   ├── ChatInterface.tsx     # 核心界面
        │   ├── ThinkingStream.tsx    # 思考流
        │   ├── CognitiveGraph.tsx    # 认知结构图
        │   ├── MaoQuoteCard.tsx      # 毛选卡片
        │   ├── MessageBubble.tsx     # 消息气泡
        │   └── WelcomeScreen.tsx     # 欢迎界面
```

---

## 技术栈

**后端**: FastAPI, jieba, PyYAML, networkx
**前端**: React 19, TypeScript, Vite, Tailwind CSS, Framer Motion
**模型**: 支持OpenAI兼容格式

---

## License

MIT

> "没有调查就没有发言权" —— 《反对本本主义》
