# C6 GROUP – STANDARD OPERATING PROCEDURES & MANUAL

**Version:** 1.0
**Effective Date:** 16 September 2026
**Owner:** RemotePay Fintech Services Pty Ltd
**Classification:** Internal – Strategic

---

## PART 1: STANDARD OPERATING MANUAL (SOM)

### 1.1 CORPORATE IDENTITY

**Registered Entity:** RemotePay Fintech Services Pty Ltd
**Jurisdiction:** South Africa
**Structure:** Holding company with three trading brands

| Brand | Purpose | Domain |
|-------|---------|--------|
| C6 Group | AI business intelligence, audits, tools | c6group.co.za |
| Ubernie | Business directory, ads, discovery | ubernie.co.za |
| RemotePay | Payment gateway, merchant services | remote-pay.co.za |

### 1.2 CORPORATE STRUCTURE

- **Group CEO:** You + AI Digital Twin
- **C6 CEO:** AI agent, 18 staff agents
- **Ubernie CEO:** AI agent, 17 staff agents
- **RemotePay CEO:** AI agent, 23 staff agents
- **Total AI Staff:** 58 agents

### 1.3 THE FLYWHEEL

1. Scraper discovers SA businesses (daily)
2. Ubernie auto-creates free listings
3. Alert sent to owners (email/WhatsApp/SMS)
4. Owners click C6 audit link
5. Audit runs (Ollama) → report + bundle offers
6. Owner chooses bundle (Ubernie discount applied)
7. RemotePay processes payment
8. All three platforms activate
9. Loop repeats

### 1.4 REVENUE MODEL

| Package | Price | Cost | Margin |
|---------|-------|------|--------|
| Start | R0 | R0.03 | -R0.03 |
| Diamond | R4,995 | R50-450 | R4,545-4,945 |
| Gold | R9,995 | R150-500 | R9,495-9,845 |
| Platinum | R24,995 | R350-1,000 | R23,995-24,645 |

**Only feasible with local Ollama. Cloud AI = bankruptcy.**

### 1.5 TECHNOLOGY STACK

- Orchestration: agency-agents + agency-orchestrator
- Multi-Agent: crewAI, hermes-agent, langgraph
- Memory: mem0, LightRAG, Qdrant
- Email: BillionMail
- WhatsApp: Whatomate
- SMS: Arkesel
- Scraping: Scrapling, crawl4ai, browser-use
- Voice: Voicebox, F5-TTS, fish-speech
- Content: MoneyPrinterV2, paperclip, ComfyUI
- Payments: RemotePay + PayGate
- LLM: Ollama (local)
- VPS: Contabo Cloud VPS 4 (8GB)
- Frontend: Cloudflare Pages

---

## PART 2: STANDARD OPERATING PROCEDURES

### SOP-001: DAILY HUMAN SUPERVISION
- Morning check (10 min): Control Room, CEO decisions, financials
- Mid-day check (5 min): manual review queue, alerts
- End-of-day check (15 min): approve reviews, backup, document

### SOP-002: CEO AGENT OPERATIONS
- Start: `python agents/ceo/ceo_v3.py`
- Kill switch: `touch control/STOP_ALL.flag`
- Remove: `rm control/STOP_ALL.flag`

### SOP-003: UBERNIE SCRAPING
- Trigger: `php artisan scavenger:seek`
- Verify: `Business::latest()->take(10)->get()`

### SOP-004: C6 AUDIT DELIVERY
- Form → FastAPI → n8n → Ollama → BillionMail
- Verify: n8n log + BillionMail sent folder

### SOP-005: REMOTEPAY TRANSACTIONS
- Merchant onboarding: KYC → PayGate → merchant ID
- Payment: link → PayGate → webhook → receipt
- Failure: retry 3x → notify merchant

### SOP-006: AD SPACE MANAGEMENT
- Inventory: home-top, home-sidebar, directory-top, directory-sidebar, business-top, search-featured
- Booking: upload → duration → RemotePay → activate

### SOP-007: EMAIL OPERATIONS
- Setup per brand: MX, SPF, DKIM, DMARC
- Campaigns: BillionMail → track → report

### SOP-008: WHATSAPP OPERATIONS
- Onboarding: register number → Whatomate → test
- Message flow: receive → n8n → Ollama → reply
- Quota: 500/2000/10000 per tier

### SOP-009: INCIDENT RESPONSE
- P1: immediate, activate kill switch
- P2: < 4 hours
- P3: < 24 hours
- P4: next business day

### SOP-010: SECURITY OPERATIONS
- Daily: fail2ban, suspicious activity
- Weekly: firewall, packages, logs
- Monthly: full audit, key rotation

### SOP-011: COMPLIANCE & POPIA
- Daily: consent, retention, cross-border
- Monthly: access logs, subject requests
- Annually: full audit, IR registration

### SOP-012: FINANCIAL REPORTING
- Daily: transactions, signups, ads
- Weekly: P&L per brand
- Monthly: full report, tax provision

### SOP-013: AI AGENT LIFECYCLE
- Deploy: define role → sandbox → register → production
- Monitor: success, latency, cost, errors
- Retire: confirm no deps → archive → remove

### SOP-014: HUMAN-IN-THE-LOOP OVERRIDE
- Trigger: > R10k, new market, legal, P1
- Procedure: pause → review → decide → document → resume

### SOP-015: VPS DEPLOYMENT
- Provision Contabo Cloud VPS 4
- Install Docker, Ollama, n8n
- Clone repos, docker compose up
- Configure DNS, Cloudflare Tunnel
- Import n8n workflows
- Verify all endpoints

---

## PART 3: RESPONSIBILITY MATRIX

| Task | Human | C6 CEO | Ubernie CEO | RemotePay CEO |
|------|-------|--------|-------------|---------------|
| Strategy | ✅ | – | – | – |
| Daily CEO run | – | ✅ | ✅ | ✅ |
| Audit delivery | – | ✅ | – | – |
| Scraping | – | – | ✅ | – |
| Ad management | – | – | ✅ | – |
| Payment processing | – | – | – | ✅ |
| Security audits | ✅ | – | – | – |
| Compliance | ✅ | – | – | – |
| Emergency response | ✅ | – | – | – |
| Financial reporting | ✅ | – | – | – |

---

## PART 4: EXECUTION CALENDAR

| Time | Task | Owner |
|------|------|-------|
| 6:00 AM | Scraper runs | Ubernie CEO |
| 8:00 AM | Daily CEO cycles | All CEOs |
| 9:00 AM | Human morning check | Group CEO |
| 12:00 PM | Mid-day check | Group CEO |
| 5:00 PM | Human end-of-day | Group CEO |
| 2:00 AM | Backups | Infra |
| 3:00 AM | Security scan | Infra |

---

## PART 5: CHANGE LOG

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 1.0 | 2026-09-16 | Initial SOM + SOP | Group CEO |

All future changes logged here before implementation.
