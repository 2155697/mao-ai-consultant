# 教员AI咨询系统 v2.0

> 不是风格模仿，是思维重建。基于McAdams三层人格模型 + CAPS动态图 + 认知结构引擎的深度人格蒸馏。

## 核心理念

当前大多数"角色扮演"AI停留在**特质层**——模仿语言风格、背诵语录。我们的目标是达到**适应性+叙事层**——让AI真正内化和运用教员的底层思维系统。

## 系统架构：五层蒸馏模型

```
L5 表现层：三层展示架构（思考流 + 认知结构 + 毛选原文）
L4 推理层：Kimi K2.6 + reasoning_content解析引擎
L3 人格建模层：CAPS动态图 + 认知结构引擎 + 思维模板库
L2 记忆层：毛选知识库（20+条经典原文精准匹配）
L1 数据层：毛选四卷结构化（哲学/战略/方法/语言/叙事）
```

## 三层展示架构（核心体验）

| 层级 | 内容 | 动态特征 |
|------|------|---------|
| **💭 思考流** | 教员的内心独白 | 逐字流动、停顿、顿悟💡、回退修正🔄 |
| **🧠 认知结构** | 阶段性结论凝结 | 动态思维导图，节点从无到有生长 |
| **📖 毛选原文** | 实时匹配的著作引用 | AI自行衡量关联度，有价值时才展示 |

## 核心技术栈

- **McAdams三层人格模型**：特质 → 适应性 → 叙事
- **CAPS动态图**：6个if-then情境-行为签名
- **认知模板库**：5套思维方法（矛盾分析/调查研究/形势分析/群众路线/军事辩证法）
- **认知结构引擎**：动态演化的思维节点网络
- **System Prompt v2.0**：2115字符深度人格蒸馏
- **毛选知识库**：20+条经典原文，概念+语义双重匹配

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/2155697/mao-ai-consultant.git
cd mao-ai-consultant/backend
```

### 2. 安装依赖

```bash
pip install fastapi uvicorn sse-starlette openai pydantic
```

### 3. 配置API Key（必须）

```bash
# 使用你的Kimi API Key
export MOONSHOT_API_KEY="sk-ttvmoQuD7rSXb3jolIUdkwkoI5LIi2ca33fdChWnr2Q0gmL9"
```

### 4. 启动服务

```bash
python main.py
```

### 5. 打开浏览器

访问 `http://localhost:8000`

## 项目结构

```
mao-ai-consultant/
├── README.md                          # 本文件
├── DESIGN.md                          # 完整架构设计文档（21KB）
├── backend/
│   ├── main.py                        # FastAPI主入口（v2.0）
│   ├── requirements.txt               # Python依赖
│   ├── static/
│   │   └── index.html                 # 前端：三层展示架构（纯JS）
│   └── app/
│       ├── core/
│       │   ├── config.py              # 系统配置（kimi-k2.6）
│       │   ├── mao_system_prompt.py   # v1 System Prompt
│       │   └── mao_persona_v2.py      # ⭐ v2核心引擎（27KB）
│       ├── api/
│       │   └── chat.py                # SSE流式API（支持v2三层输出）
│       ├── services/
│       │   └── kimi_client.py         # v1+v2混合客户端（句子缓冲）
│       └── models/
│           └── schemas.py             # 数据模型（扩展v2 chunk类型）
```

## v2.0 新增文件说明

| 文件 | 大小 | 功能 |
|------|------|------|
| `app/core/mao_persona_v2.py` | 27KB | McAdams三层 + CAPS + 认知结构 + 毛选知识库 |
| `app/services/kimi_client.py` | 8KB | v1架构 + v2三层SSE输出 + 句子缓冲 |
| `static/index.html` | 12KB | 三层展示架构前端（思考流+认知图+毛选卡片） |
| `DESIGN.md` | 21KB | 完整架构设计文档 |

## API接口

### 流式对话（SSE）

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"教员，我最近工作压力大","stream":true}'
```

返回事件类型：
- `thinking_stream` - 思考流事件（内心独白）
- `cognitive_structure` - 认知结构数据（思维导图）
- `mao_quote` - 毛选原文引用
- `content` - 回答内容片段
- `done` - 完成

### 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

## License

MIT

> "没有调查就没有发言权" —— 毛泽东