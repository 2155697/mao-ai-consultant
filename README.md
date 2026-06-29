# 教员AI咨询系统

> 基于 Kimi K2.6 推理模型的毛泽东风格一对一AI咨询平台

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev)
[![Kimi](https://img.shields.io/badge/Kimi-K2.6-red.svg)](https://kimi.moonshot.cn)

## 项目介绍

本项目是一个深度蒸馏毛泽东思想与语言风格的AI咨询系统。不是简单的语录背诵或风格模仿，而是通过**System Prompt工程 + 思维链可视化 + 矛盾分析法**，让AI真正内化了教员的底层思维体系。

### 核心特性

| 特性 | 说明 |
|------|------|
| **5步思考链** | 问题解构 → 矛盾识别 → 深度分析 → 策略构建 → 总结升华 |
| **推理可视化** | 利用Kimi K2.6的reasoning_content，动态展示教员的思考过程 |
| **毛泽东思想注入** | 2655+字符深度System Prompt，覆盖矛盾论、实践论、群众路线 |
| **语言风格蒸馏** | 比喻、排比对偶、先破后立、辩证分析、军事术语政治化 |
| **SSE流式输出** | 逐字显示回答，思考过程实时可视化 |
| **双模式支持** | Mock模式（无需API Key）+ 真实Kimi API模式 |

## 技术架构

```
Frontend (React 18 + Tailwind CSS v3)
    |
    | SSE (EventSource)
    v
Backend (FastAPI + Uvicorn)
    |
    | OpenAI Compatible API
    v
Kimi K2.6 (Moonshot AI)
    reasoning_content + content
```

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/2155697/mao-ai-consultant.git
cd mao-ai-consultant/backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置API Key（可选，不配置则使用Mock模式）
export MOONSHOT_API_KEY="sk-your-api-key"
export MOCK_MODE="false"

# 4. 启动
python main.py

# 5. 访问 http://localhost:8000
```

## API接口

```bash
# 流式对话
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"教员，我最近很迷茫","stream":true}'

# 健康检查
curl http://localhost:8000/api/v1/health
```

## System Prompt 设计

System Prompt是整个系统的灵魂，详见 `backend/app/core/mao_system_prompt.py`，包含：

1. **核心身份特征** - 毛泽东的生平与身份定位
2. **思维体系** - 矛盾分析法、实事求是、群众路线、战略思维
3. **语言风格** - 7大修辞特征 + 语气特征
4. **回答结构模板** - 分析类/建议类的标准回答框架
5. **思考过程规则** - 5步思考链的强制要求
6. **Few-shot示例** - 3个典型对话示例

## 思考过程可视化

```
Step 1 [15%] 问题解构  - "调查就是解决问题"
Step 2 [35%] 矛盾识别  - "主要矛盾决定事物性质"
Step 3 [55%] 深度分析  - "没有调查就没有发言权"
Step 4 [75%] 策略构建  - "战略藐视，战术重视"
Step 5 [100%] 总结升华 - "道路曲折，前途光明"
```

## 项目结构

```
backend/
├── main.py                      # FastAPI主入口
├── requirements.txt             # Python依赖
├── static/
│   └── index.html              # 前端单页应用（React 18 + Tailwind）
└── app/
    ├── core/
    │   ├── config.py           # 系统配置
    │   └── mao_system_prompt.py # System Prompt核心
    ├── api/
    │   └── chat.py             # SSE流式API
    ├── services/
    │   └── kimi_client.py      # Kimi API客户端
    └── models/
        └── schemas.py          # 数据模型
```

## 路线图

- [x] v1.0 基础对话 + Mock模式 + 思考可视化
- [ ] v1.1 接入RAG知识库（毛选向量化检索）
- [ ] v1.2 对话历史持久化
- [ ] v1.3 用户系统 + 登录/支付
- [ ] v1.4 毛选原文引用标注

## License

MIT License

> "没有调查就没有发言权" —— 毛泽东
