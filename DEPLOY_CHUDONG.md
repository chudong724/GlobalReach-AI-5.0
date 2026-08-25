# 文美全球AI获客系统 — Windows 部署指南

本仓库已经完成产品品牌化，默认产品名称为 **文美全球AI获客系统**。

## 环境要求

- Windows 10/11
- Python 3.11+
- Node.js 18+
- Git
- 至少一个 LLM API Key
- Tavily 或 Serper 搜索 API Key

## 克隆

```powershell
git clone https://github.com/chudong724/AI_Find_Customer.git
cd AI_Find_Customer
```

## 一键安装

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\windows\setup.ps1
```

该脚本会创建 `backend/.venv`、安装后端依赖、生成 `backend/.env`（如不存在）并安装前端依赖。脚本直接调用 `.venv\Scripts\python.exe`，不依赖 `Activate.ps1`，可避免常见 PowerShell 执行策略问题。

## 配置

编辑：

```text
backend\.env
```

至少配置一个 LLM 提供商，以及 Tavily/Serper 搜索 Key。Google Maps 搜索需要 Serper。

邮件初始测试建议保持：

```env
EMAIL_AUTO_SEND_ENABLED=false
EMAIL_REPLY_DETECTION_ENABLED=false
EMAIL_REQUIRE_APPROVAL_BEFORE_SEND=true
```

## 启动

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\windows\start.ps1
```

默认访问：

- 前端：http://localhost:3000
- API：http://127.0.0.1:8000
- Swagger：http://127.0.0.1:8000/docs

## 安全

不要把真实 `.env`、API Key、SMTP/IMAP 密码提交到 GitHub。外网部署时必须设置 `API_ACCESS_TOKEN`，限制 CORS，并通过 HTTPS/反向代理提供访问。

## 许可

产品品牌统一为“文美全球AI获客系统”。原始 MIT 开源版权与许可声明继续保留在 `LICENSE`；第三方说明见 `THIRD_PARTY_NOTICES.md`。
