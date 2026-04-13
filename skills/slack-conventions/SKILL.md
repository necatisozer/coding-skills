---
name: slack-conventions
description: Ensures correct Slack message formatting when sending messages, posting URLs, or composing announcements via MCP Slack tools. Prevents URL parser issues.
user-invocable: false
---

## Message Formatting
When sending Slack messages with URLs via MCP Slack tools, always add a **blank line after each URL**. Without it, Slack's link parser merges the next line's text into the URL, breaking both the link and the text. Always get user confirmation on message format before sending.
