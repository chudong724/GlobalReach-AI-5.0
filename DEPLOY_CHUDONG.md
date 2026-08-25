# AI Find Customer — Chudong Windows Deployment

This fork keeps the upstream AI Hunter code intact and adds a Windows-friendly setup path that does not require PowerShell virtual-environment activation.

## 1. Requirements

- Windows 10/11
- Python 3.11+
- Node.js 18+
- Git
- At least one LLM API key
- At least one search API key (Tavily or Serper; Serper is required for Google Maps search)

## 2. Clone

```powershell
git clone https://github.com/chudong724/AI_Find_Customer.git
cd AI_Find_Customer
git checkout deploy/chudong-setup
```

## 3. Install

Run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\windows\setup.ps1
```

The script creates `backend/.venv`, installs Python dependencies, creates `backend/.env` if missing, and runs `npm install` for the frontend.

It deliberately calls `backend/.venv/Scripts/python.exe` directly instead of requiring `Activate.ps1`, avoiding the common Windows execution-policy error.

## 4. Configure API keys

Open:

```text
backend/.env
```

At minimum configure:

- one LLM provider key and matching `LLM_MODEL`
- `TAVILY_API_KEY` and/or `SERPER_API_KEY`
- optional `JINA_API_KEY` for web extraction

For email campaigns, also configure SMTP/IMAP fields. Keep these defaults during initial testing:

```env
EMAIL_AUTO_SEND_ENABLED=false
EMAIL_REPLY_DETECTION_ENABLED=false
EMAIL_REQUIRE_APPROVAL_BEFORE_SEND=true
```

Never commit your real `.env` or API keys to GitHub.

## 5. Start

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\windows\start.ps1
```

The script opens two PowerShell windows:

- Backend: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Frontend: http://localhost:3000

## 6. First test

1. Open http://localhost:3000
2. Open Settings and confirm the configured LLM/search providers.
3. Create a small test hunt first (for example 5–10 leads).
4. Keep automatic email sending disabled until SMTP/IMAP tests succeed.
5. After verifying lead quality, increase target lead count and rounds.

## 7. Production safety

For access beyond localhost, set a strong `API_ACCESS_TOKEN` and restrict CORS. Do not expose the FastAPI service directly to the public Internet without authentication and a reverse proxy.

For email, preserve human approval until sender reputation, SPF/DKIM/DMARC, bounce handling, and sending limits are verified.
