# Oral AI 实时口语练习应用 - 项目记忆

## 项目地址
- (待补充)

## 项目概述
打造一款可以24小时在线的AI口语陪练应用。应用的核心定位是“面向未来的私人语言导师”，专注于为用户提供“深度个性化”和“实时反馈”的练习体验。项目旨在通过融合“人机协同”的理念，在Duolingo和Babbel等主流应用之间，开拓一个高价值的细分市场。

## 核心技术栈
采用“可扩展实时口语（Scalable Real-time Oral Practice, SROP）”微服务架构。
- **前端**: React / 移动应用 (iOS/Android)
- **后端**: 微服务架构 (Node.js, Go, Python)
- **通信协议**:
    - **WebSocket (WSS) / WebRTC**: 用于客户端与服务器之间的实时音频流传输。
    - **HTTPS**: 用于处理用户注册、登录、查询历史记录等业务逻辑的 RESTful API。
- **数据库与缓存**:
    - **业务数据库**: PostgreSQL / MongoDB (存储用户信息、订阅状态等)
    - **对话历史库**: MongoDB / DynamoDB (存储海量对话记录)
    - **缓存**: Redis (缓存用户会话、热点数据)
- **基础设施**:
    - **API 网关**: Nginx / Kong (作为所有请求的统一入口，负责路由、认证、限流)
    - **对象存储**: AWS S3 / Aliyun OSS (存储录制的音频文件)
- **第三方服务 (AI引擎)**:
    - **流式ASR**: Google Speech-to-Text, AWS Transcribe Streaming, Deepgram
    - **核心LLM**: Coze, OpenAI, Anthropic Claude, Google Gemini
    - **流式TTS**: ElevenLabs, PlayHT, AWS Polly, Google Text-to-Speech

## 关键文件与目录结构
```
oral_app/
├── docker-compose.yml   # Local development environment services
├── client/              # Frontend application (React/Mobile)
├── api-gateway/         # API Gateway configuration
├── services/            # Backend microservices
│   ├── user-service/
│   │   └── docs/
│   │       └── schema.md  # User service database schema
│   ├── conversation-service/
│   ├── history-analytics-service/
│   └── media-processing-service/
└── docs/                # Project documentation
```

# SROP (Scalable Real-time Oral Practice) Architecture Diagram

```
+------------------+      +---------------------+      +-----------------------+
|   Client App     |      |    API Gateway      |      |   Backend Services    |
| (React/Mobile)   |----->| (e.g., Nginx, Kong) |----->| (Microservices Arch)  |
+------------------+      +---------------------+      +-----------------------+
        |
        | (WebRTC/WSS for Audio Stream)                         | (Internal RPC/Events)
        | (HTTPS for REST API)                                  |
        |
        v                                                       v
+--------------------------+      +--------------------+      +-------------------------+
| Real-time Comms Layer    |      |   AI Service Layer |      |   Data Persistence Layer|
| (e.g., WebSocket Server) |<---->| (AI Engine)        |<---->| (Databases & Caching)   |
+--------------------------+      +--------------------+      +-------------------------+
```


## 核心业务逻辑

### 1. SROP 核心架构设计理念
- **流式处理优先 (Streaming First)**: 客户端通过 `AudioWorklet` 等技术实时采集音频PCM数据流，并通过WSS/WebRTC协议实时传输至后端，彻底抛弃“录音-上传-处理-返回”的传统模式，实现端到端的流式处理，将交互延迟降至秒级。
- **服务化与解耦 (Service-Oriented & Decoupled)**: 后端拆分为用户、对话、历史分析、媒体处理等多个独立的微服务。各服务可独立迭代和扩展，从而实现精细化的成本控制。
- **数据驱动个性化 (Data-Driven Personalization)**: 引入数据库和数据分析管道，为每个用户建立动态画像（如学习进度、目标、常犯错误），为LLM提供上下文，使其回应更具个性化和针对性。
- **AI引擎抽象化 (Abstracted AI Engine)**: 将ASR、LLM、TTS等AI能力封装成独立的“AI引擎”层，不与任何单一供应商绑定，未来可以根据成本和性能灵活切换或组合使用不同的AI服务。
- **提示词工程模块 (Prompt Engineering Module)**: 在AI引擎内部，建立一个专门的提示词管理模块。该模块负责动态构建发送给LLM的最终Prompt。它会将定义AI导师角色的**基础指令**（Base Prompt）与用户的**动态上下文**（如个人学习目标、历史对话摘要、常犯错误等）相结合，确保AI的每一次回应都具有高度的个性化和教学相关性。

### 2. 核心实时对话流程
1.  **客户端**：实时采集用户音频流，通过WebSocket发送至后端的“实时通信层”。
2.  **实时通信层**：接收音频流并实时转发给“AI服务层”。
3.  **AI服务层 (AI引擎)**：执行核心编排任务：
    - 音频流进入 **流式ASR**，实时转换为文本流。
    - 识别出的文本被发送给 **核心LLM**。
    - LLM生成的回应文本块，被立即送入 **流式TTS**。
    - 流式TTS将文本实时转换为音频流。
4.  **实时通信层**：接收AI引擎生成的音频流，并立即通过WebSocket转发回客户端。
5.  **客户端**：接收音频流并实时播放，实现“边生成边播放”的低延迟体验。

### 3. 用户画像与自适应学习
- **异步分析**: “历史与分析服务”会异步处理存储在对象存储和对话历史库中的完整对话记录，进行分析，提取用户学习的关键指标（如流利度、常用词、语法弱点），并持续更新用户画像。
- **个性化交互**: “对话服务”在与LLM交互时，会附上用户的画像摘要。这使得LLM能够真正扮演“私人导师”的角色，提供高度个性化的反馈和指导。
- **动态调整**: 系统可以基于分析结果，为用户生成学习报告，并动态调整未来的练习目标和内容，实现千人千面的自适应学习路径。

## 开发与运行
- **本地环境启动**:
    - 运行 `docker-compose up -d` 来启动项目所需的 PostgreSQL, MongoDB, Redis和 user-service 服务。

## 关键环境变量与配置
(待补充)

## Gemini Added Memories
- 项目已配置专属的今日开发工作收尾命令 `finish_today`，其具体操作如下: "作为AI助手，我的目标是完成今日的收尾工作。我将执行以下4项操作：
  \n1. Update the development plan in @docs/TODO.md using the mcp-tasks tool.
  \n2. Append a summary of the day's work to the development log at @docs/development_log.md if exists.
  \n3. Update the GEMINI.md project memory file to reflect the current project state, don't change the ##Gemini Added Memories.
  \n4. Commit and push all changes to the origin/master branch of the remote repository using the commit message ser {{今日日期}}."