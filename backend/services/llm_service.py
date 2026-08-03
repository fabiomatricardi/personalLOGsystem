"""
LLM service with primary/fallback API support.
"""
import httpx
from backend.services.config import load_config
from datetime import datetime


async def call_llm(messages: list[dict], use_fallback: bool = False) -> str:
    config = load_config()
    llm_key = "primary" if not use_fallback else "fallback"
    llm_config = config["llm"][llm_key]

    if not llm_config.get("api_key"):
        if not use_fallback:
            return await call_llm(messages, use_fallback=True)
        raise ValueError("No LLM API configured. Please configure an LLM API in Settings.")

    base_url = llm_config.get("base_url", "").rstrip("/")
    api_key = llm_config["api_key"]

    try:
        async with httpx.AsyncClient(timeout=llm_config.get("timeout", 60)) as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            url = f"{base_url}/chat/completions"

            payload = {
                "model": llm_config["model"],
                "messages": messages,
                "max_tokens": llm_config.get("max_tokens", 4096)
            }

            response = await client.post(
                url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        error_detail = ""
        try:
            error_detail = e.response.text[:500]
        except Exception:
            pass
        if not use_fallback:
            return await call_llm(messages, use_fallback=True)
        raise Exception(f"LLM API error {e.response.status_code}: {error_detail}")
    except Exception as e:
        if not use_fallback:
            return await call_llm(messages, use_fallback=True)
        raise Exception(f"LLM API error: {str(e)}")


async def generate_weekly_summary(entries: list[dict], week_label: str = "Weekly") -> str:
    system_prompt = """You are a personal log analyst for an instrumentation engineer working on a FLNG project.
Generate a concise weekly summary of activities in markdown format.

Format:
## {Week Label} Summary

### Key Activities
- Bullet list of main activities completed

### Tasks Progress
- Tasks that were worked on or completed

### Pending Items
- Items awaiting action or follow-up

### Recommendations
- 2-3 suggested next steps based on the activities

Keep the summary professional and focused on work accomplishments."""

    entries_text = "\n".join([
        f"- [{e.get('type', 'LOG')}] {e.get('timestamp', 'N/A')[:16]}: {e.get('activity', '')[:300]}"
        for e in entries
    ])

    user_prompt = f"""Generate a summary for {week_label} based on these log entries:

{entries_text}

Period: {week_label}
Total entries: {len(entries)}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    return await call_llm(messages)


async def generate_comprehensive_report(
    all_entries: list[dict],
    stats: dict,
    pending: list[dict],
    completed: list[dict]
) -> str:
    system_prompt = """You are a personal log analyst for an instrumentation engineer on a FLNG project.
Generate a comprehensive report covering all logged activities.

Format:
## Comprehensive Activity Report

### Executive Summary
Brief overview of overall status and key achievements.

### Statistics Overview
- Total entries, breakdown by type
- Completion rates
- Task distribution

### Completed Items
Key accomplishments from completed tasks.

### Pending/In-Progress Items
Items still requiring attention, organized by priority.

### Trends & Patterns
Observations about work patterns, common themes.

### Recommendations
Strategic next steps and priorities.

Be thorough but concise. Focus on actionable insights."""

    entries_summary = "\n".join([
        f"- [{e.get('type', 'LOG')}] {e.get('status', 'N/A')} | {e.get('timestamp', 'N/A')[:10]}: {e.get('activity', '')[:200]}"
        for e in all_entries[:100]
    ])

    pending_summary = "\n".join([
        f"- [{e.get('type')}] {e.get('activity', '')[:150]}"
        for e in pending[:20]
    ])

    completed_summary = "\n".join([
        f"- {e.get('activity', '')[:150]}"
        for e in completed[:20]
    ])

    user_prompt = f"""Generate a comprehensive report based on this data:

## Statistics
- Total entries: {stats.get('total_entries', 0)}
- Logs: {stats.get('total_logs', 0)}
- TODOs: {stats.get('total_todos', 0)}
- Tasks: {stats.get('total_tasks', 0)}
- Pending: {stats.get('pending_tasks', 0)}
- Assigned: {stats.get('assigned_tasks', 0)}
- Ongoing: {stats.get('ongoing_tasks', 0)}
- Completed: {stats.get('completed_tasks', 0)}

## Recent Entries
{entries_summary}

## Pending Items
{pending_summary if pending_summary else "None"}

## Completed Items
{completed_summary if completed_summary else "None"}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    return await call_llm(messages)


async def detect_overdue_tasks(entries: list[dict]) -> str:
    if not entries:
        return "## Overdue Tasks\n\nNo overdue tasks found. All items are on track!"

    system_prompt = """You are a task management assistant for an instrumentation engineer.
Analyze overdue tasks and suggest actions.

Format:
## Overdue Tasks Analysis

### Overdue Items
List each overdue item with:
- Description
- Original ETA and how many days overdue
- Current status

### Suggested Actions
For each overdue item, suggest a specific action.

### Risk Assessment
Overall risk level (Low/Medium/High) and justification.

Be specific and actionable."""

    now = datetime.now()
    entries_text = "\n".join([
        f"- [{e.get('type')}] ID:{e.get('id')} ETA:{e.get('eta', 'N/A')[:10]} Status:{e.get('status')} - {e.get('activity', '')[:200]}"
        for e in entries
    ])

    user_prompt = f"""Analyze these overdue items:

Current Date: {now.strftime('%Y-%m-%d')}

{entries_text}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    return await call_llm(messages)


async def suggest_next_steps(recent_entries: list[dict], pending_entries: list[dict]) -> str:
    system_prompt = """You are a productivity assistant for an instrumentation engineer on an FLNG project.
Based on recent activities and pending items, suggest prioritized next steps.

Format:
## Recommended Next Steps

### Priority 1 (Urgent)
- Items requiring immediate attention

### Priority 2 (Important)
- Items to address this week

### Priority 3 (When possible)
- Items for upcoming weeks

Be specific, actionable, and consider project context."""

    recent_text = "\n".join([
        f"- {e.get('timestamp', 'N/A')[:10]}: {e.get('activity', '')[:250]}"
        for e in recent_entries[:10]
    ])

    pending_text = "\n".join([
        f"- [{e.get('type')}] {e.get('activity', '')[:200]}"
        for e in pending_entries[:15]
    ])

    user_prompt = f"""Based on these activities and pending items, suggest next steps:

## Recent Activities
{recent_text}

## Pending Items
{pending_text if pending_text else "None"}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    return await call_llm(messages)


async def analyze_patterns(entries: list[dict]) -> str:
    system_prompt = """You are a data analyst for an instrumentation engineer.
Identify patterns and insights from log entries.

Format:
## Pattern Analysis

### Activity Distribution
- Breakdown of activity types

### Time Patterns
- When most work is happening
- Weekly trends

### Common Themes
- Recurring topics or tasks

### Productivity Insights
- Observations about work patterns

### Recommendations
- Suggestions based on identified patterns

Use bullet points and be concise."""

    entries_text = "\n".join([
        f"- [{e.get('type', 'LOG')}] {e.get('timestamp', 'N/A')[:10]}: {e.get('activity', '')[:150]}"
        for e in entries
    ])

    user_prompt = f"""Analyze patterns in these {len(entries)} log entries:

{entries_text}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    return await call_llm(messages)
