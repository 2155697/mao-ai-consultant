# 教员AI咨询系统 v2.0

> 不是风格模仿，是思维重建。基于McAdams三层人格模型 + CAPS动态图 + 认知结构引擎的深度人格蒸馏。

## 核心理念

当前大多数"角色扮演"AI停留在**特质层**——模仿语言风格、背诵语录。我们的目标是达到**适应性+叙事层**——让AI真正内化和运用教员的底层思维系统。

## 架构设计

五层蒸馏模型：

```
L5 表现层：三层展示架构（思考流 + 认知结构 + 毛选原文）
L4 推理层：Kimi K2.6 + reasoning_content解析引擎
L3 人格建模层：CAPS动态图 + 认知结构引擎 + 思维模板
L2 记忆层：毛选知识库（向量检索 + 原文匹配 + 语境关联）
L1 数据层：毛选四卷结构化（哲学/战略/方法/语言/叙事）
```

### 三层展示架构

| 层级 | 内容 | 展示方式 |
|------|------|----------|
| **思考流** | 教员的内心独白 | 逐字流动，有停顿、顿悟、回退 |
| **认知结构** | 阶段性结论凝结 | 动态思维导图，节点随思考生长 |
| **毛选原文** | 实时匹配的著作引用 | 优雅卡片，AI自行衡量关联度 |

### 动态进度条

反映教员的真实思考节奏——可快可慢可回退可跳跃。

## 核心技术

- **McAdams三层人格模型**：特质 → 适应性 → 叙事
- **CAPS动态图**：if-then情境-行为签名
- **认知结构引擎**：动态演化的思维节点网络
- **System Prompt v2.0**：2115字符深度人格蒸馏
- **毛选知识库**：20+条经典原文精准匹配

## 快速开始

```bash
git clone https://github.com/2155697/mao-ai-consultant.git
cd mao-ai-consultant/backend
pip install fastapi uvicorn sse-starlette openai pydantic
export MOONSHOT_API_KEY="sk-your-api-key"
python main.py
# 浏览器打开 http://localhost:8000
```

## 项目结构

```
backend/
├── main.py                          # FastAPI主入口
├── requirements.txt
├── DESIGN.md                        # 完整架构设计文档
├── static/
│   └── index.html                  # 三层展示架构前端
└── app/
    ├── core/
    │   ├── config.py               # 系统配置
    │   ├── mao_system_prompt.py    # v1 System Prompt
    │   └── mao_persona_v2.py       # ⭐ v2核心引擎
    ├── api/
    │   └── chat.py                 # SSE流式API
    ├── services/
    │   └── kimi_client.py          # v1+v2混合客户端
    └── models/
        └── schemas.py              # 数据模型
```

## License

MIT

> "没有调查就没有发言权" —— 毛泽东
