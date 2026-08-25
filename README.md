# 文美全球AI获客系统

> 面向外贸与 B2B 场景的 AI 客户开发、线索挖掘、联系人发现、开发信生成与自动跟进系统。

## 产品定位

文美全球AI获客系统用于帮助外贸团队从目标市场与产品信息出发，自动完成客户画像理解、关键词生成、网页与地图搜索、企业线索提取、联系人与邮箱发现、线索评估、AI 开发信生成、Campaign 管理与回信检测。

## 核心能力

- 多 Agent 获客流水线：Insight → KeywordGen → Search → LeadExtract → Evaluate
- 支持官网 URL、PDF、Excel、CSV、Word、Markdown、TXT 与关键词输入
- Google / Google Maps / B2B 场景搜索
- 官网与公开网页信息抓取
- 企业名称、官网、邮箱、电话、地址与社媒信息提取
- AI 线索分析与继续挖掘
- AI 开发信与多步骤跟进序列
- Campaign 持久化发送
- SMTP 发信与 IMAP 回信检测
- FastAPI + SSE 实时任务进度
- React + Vite 管理界面
- LiteLLM 多模型接入
- Langfuse 可选观测
- Windows 一键安装与启动脚本

## 技术架构

- Backend：Python 3.11+ / FastAPI / LangGraph
- Frontend：React 18 / TypeScript / Vite
- LLM：LiteLLM 统一模型接口
- Search：Tavily / Serper
- Reader：Jina Reader
- Storage：SQLite / JSON
- Email：SMTP / IMAP

## Windows 快速部署

```powershell
git clone https://github.com/chudong724/AI_Find_Customer.git
cd AI_Find_Customer
powershell -ExecutionPolicy Bypass -File .\deploy\windows\setup.ps1
```

安装完成后编辑：

```text
backend\.env
```

然后启动：

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\windows\start.ps1
```

默认地址：

- 前端：http://localhost:3000
- 后端：http://127.0.0.1:8000
- API 文档：http://127.0.0.1:8000/docs

## API 与模型配置

至少配置一个 LLM API Key，以及 Tavily 或 Serper 搜索 Key。Google Maps 搜索需要 Serper。

邮件自动发送建议初期保持：

```env
EMAIL_AUTO_SEND_ENABLED=false
EMAIL_REPLY_DETECTION_ENABLED=false
EMAIL_REQUIRE_APPROVAL_BEFORE_SEND=true
```

先完成 SMTP / IMAP 测试，再逐步开启自动化发送与回信检测。

## 安全建议

- 不要把真实 `.env`、API Key、SMTP 密码提交到 GitHub。
- 外网部署时设置强 `API_ACCESS_TOKEN`。
- 限制 CORS 来源。
- 使用反向代理与 HTTPS。
- 邮件发送保留人工审核，直到域名信誉、SPF、DKIM、DMARC 与发送限额验证完成。

## 品牌与版权

当前产品品牌：**文美全球AI获客系统**。

本项目包含基于 MIT License 获得授权的开源代码。原始 MIT 版权与许可声明保留在 `LICENSE` 中；文美全球AI获客系统后续新增的品牌、配置、界面与自有模块可独立维护。

Copyright © 2026 文美全球AI获客系统。自有新增内容保留相应权利。
