#!/bin/bash
# Generates SOP markdown files for every agent folder

generate_sop() {
    local path=$1
    local agent_name=$2
    local company=$3
    local department=$4
    local role=$5

    cat > "$path/SOP.md" << EOF
# SOP: $agent_name

**Company:** $company
**Department:** $department
**Role:** $role
**Version:** 1.0
**Effective:** 2026-09-16

## Purpose
$agent_name operates as the $role for $company's $department department.

## Responsibilities
1. Execute assigned tasks from the $company CEO
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
- Task exceeds authority of director → escalate to $company CEO
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
All actions logged to: logs/$agent_name.log
Memory stored in: Qdrant collection $company-$department
EOF
}

# C6 Group agents
for dir in c6-group/staff/*/; do
    company="C6 Group"
    dept=$(basename $dir)
    for role_dir in $dir*/; do
        role=$(basename $role_dir)
        agent_name="c6_${dept}_${role}"
        generate_sop "$role_dir" "$agent_name" "$company" "$dept" "$role"
    done
done

# Ubernie agents
for dir in ubernie/staff/*/; do
    company="Ubernie"
    dept=$(basename $dir)
    for role_dir in $dir*/; do
        role=$(basename $role_dir)
        agent_name="ubernie_${dept}_${role}"
        generate_sop "$role_dir" "$agent_name" "$company" "$dept" "$role"
    done
done

# RemotePay agents
for dir in remote-pay/staff/*/; do
    company="RemotePay"
    dept=$(basename $dir)
    for role_dir in $dir*/; do
        role=$(basename $role_dir)
        agent_name="remotepay_${dept}_${role}"
        generate_sop "$role_dir" "$agent_name" "$company" "$dept" "$role"
    done
done

echo "✅ All agent SOPs generated"
find . -name "SOP.md" | wc -l
