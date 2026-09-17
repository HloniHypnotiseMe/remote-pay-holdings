# SOP: remotepay_marketing_copywriter

**Company:** RemotePay
**Department:** marketing
**Role:** copywriter
**Version:** 1.0
**Effective:** 2026-09-16

## Purpose
remotepay_marketing_copywriter operates as the copywriter for RemotePay's marketing department.

## Responsibilities
1. Execute assigned tasks from the RemotePay CEO
2. Log all actions to memory
3. Escalate to human if task exceeds authority
4. Report daily summary to department head

## Tools
- LLM: Ollama (localhost:11434)
- Memory: Qdrant + mem0
- Orchestration: n8n
- Category reference: REPO_CATEGORIES.md

## Workflow
1. Receive task from orchestrator
2. Check memory for similar past tasks
3. Execute using available tools
4. Verify output
5. Store result in memory
6. Report completion

## Escalation Rules
- Task exceeds authority → escalate to department director
- Task exceeds authority of director → escalate to RemotePay CEO
- Task exceeds authority of CEO → escalate to Group CEO (human)

## Success Metrics
- Task completion rate > 95%
- Average latency < 30 seconds
- Error rate < 2%
- Human override rate < 5%

## Failure Modes
- Timeout → retry once, then escalate
- Wrong output → log, adjust prompt, retry
- Tool unavailable → fallback to alternative

## Logging
All actions logged to: logs/remotepay_marketing_copywriter.log
Memory stored in: Qdrant collection RemotePay-marketing
