## نسخه 1.0.2
- اصلاح routing احراز هویت Negin-Master از طریق `/mcp/<token>`.
- upgrade درجا با `upgrade.ps1`.
- rotate خودکار Token خارجی Gateway چون URL قبلی در گفتگو نمایش داده شده است.
- هیچ Agent یا فولدر دیگری حذف یا جابه‌جا نمی‌شود.

## نسخه 1.0.1
سازگار با Windows PowerShell 5.1 برای تولید Token.

# HAgents Unified Gateway

هدف: به‌جای ۵ Connector مستقل در ChatGPT، فقط یک Connector ثابت داشته باشیم.

## نصب

PowerShell را باز کن و از فولدر Extract شده اجرا کن:

```powershell
powershell -executionpolicy bypass -file .\install.ps1
```

نصب:
- Gateway را روی `127.0.0.1:8791` اجرا می‌کند.
- Token ثابت Gateway را یک بار می‌سازد و نگه می‌دارد.
- Startup را در HKCU Run ثبت می‌کند.
- با Tailscale Funnel مسیر `/agents` را به Gateway وصل می‌کند.
- `CONNECTOR.txt` را می‌سازد که Server URL نهایی داخل آن است.
- هیچ Agent، Connector قدیمی یا فولدری را حذف نمی‌کند.

## تست

```powershell
powershell -executionpolicy bypass -file C:\code-x\ops\agent-gateway\test-gateway.ps1
```

باید `AGENTS=5/5` ببینی.

## Connector جدید ChatGPT

فقط **یک Connector** بساز:

- Name: `HAgents Unified Gateway`
- Server URL: مقدار داخل `C:\code-x\ops\agent-gateway\CONNECTOR.txt`
- Authentication: `No authentication`

Token داخل URL است؛ URL را عمومی نکن.

پس از اینکه این Connector تست شد، Connectorهای مستقل قدیمی را می‌توانیم disable کنیم. حذفشان قبل از تست Gateway توصیه نمی‌شود.

## Inventory فولدرهای Agent

```powershell
powershell -executionpolicy bypass -file C:\code-x\ops\agent-gateway\inventory-agents.ps1
```

این فقط `KEEP` و `REVIEW` می‌سازد؛ هیچ چیزی حذف نمی‌کند. بعد از reconciliation و تأیید مسیرهای دقیق، فولدرهای legacy را حذف می‌کنیم.
