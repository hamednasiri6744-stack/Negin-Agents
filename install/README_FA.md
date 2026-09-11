# Negin Agents Deployment Kit

این پوشه برای نصب، ارتقا و Reconnect مجموعه پنج Agent استفاده می‌شود:

- Negin-Master
- Code-X
- UX-X
- Data-X
- Automation-X
- HAgents Unified Gateway

## نصب روی سیستم جدید

```powershell
git clone https://github.com/hamednasiri6744-stack/Negin-Agents.git
cd Negin-Agents
powershell -executionpolicy bypass -file .\install\install.ps1
```

Installer سورس Agentها را در مسیرهای استاندارد قرار می‌دهد، Secretهای موجود را حفظ می‌کند، روی نصب Fresh توکن محلی جدید می‌سازد و در پایان Health Check می‌گیرد.

## ارتقا

```powershell
powershell -executionpolicy bypass -file .\install\update.ps1
```

فرایند: `git pull --ff-only` → Backup → Sync سورس Canonical → حفظ Runtime Config/Secret → Reconnect → Health Gate 5/5.

## فقط Reconnect

```powershell
powershell -executionpolicy bypass -file .\install\reconnect.ps1
```

Connector در ChatGPT ثابت می‌ماند. اگر Tool جدید اضافه شده باشد، یک Reconnect در ChatGPT برای Refresh فهرست Toolها کافی است.

## Dry Run

```powershell
powershell -executionpolicy bypass -file .\install\install.ps1 -DryRun
```

## مسیرهای پیش‌فرض

- Negin-Master: `C:\enterprise-master-agent`
- Code-X: `C:\code-x`
- UX-X: `C:\code-x\agents\ux-x`
- Specialist Host: `C:\code-x\agents\specialist-host`
- Unified Gateway: `C:\code-x\ops\agent-gateway`

## امنیت

Runtime config، Token، Password، `.env` و فایل‌های private نباید Commit شوند. GitHub فقط Source-of-Truth کد و Skillها است.
