# Product Brief

## Problem
Small and medium businesses still automate operations manually or with brittle scripts. Most teams can describe what they want in plain language, but cannot translate that into safe, maintainable workflow automation.

## Vision
Convert natural-language process descriptions into executable workflows with transparent review, deterministic execution, and operational visibility.

## Primary Users
- Operations managers
- Sales/CRM administrators
- Founders and generalists in small teams

## Jobs To Be Done
- "When event X happens, run actions A, B, C in order."
- "If step fails, retry and notify me."
- "Show me what happened in each run and why it failed."

## MVP Use Cases
1. Lead or client signup webhook triggers workflow.
2. Create or update CRM contact record.
3. Send templated welcome email.
4. Call external API (HTTP action) for custom system updates.
5. View run timeline and step logs.

## Success Metrics
- Time from prompt to runnable workflow: under 3 minutes.
- Workflow generation validation pass rate: at least 90 percent for supported intents.
- Step execution success rate (excluding external outages): at least 95 percent.
- Mean time to diagnose failed run: under 10 minutes.

## Constraints
- Free and self-hostable stack.
- Open standards where possible.
- No hard dependency on paid SaaS for core runtime.
