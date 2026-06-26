# Coding Skills

A Claude Code plugin with coding-convention and workflow skills for Kotlin, Android, and Compose Multiplatform — plus Git, Gradle, and common tooling (Jira, Slack, Figma, Google Workspace).

## Installation

```
/plugin marketplace add necatisozer/coding-skills
/plugin install coding-skills
```

## Skills

| Skill | Description |
|---|---|
| `kotlin-conventions` | File organization, idioms, type design, extensions vs. members, DI helpers, Duration/Instant APIs, expect/actual |
| `kotlin-coroutines-conventions` | Coroutine safety, Flow patterns, runCatching, dispatcher injection, platform dispatch |
| `kotlin-serialization-conventions` | kotlinx.serialization response/request models, value classes for API enums, typed boundary exceptions |
| `compose-conventions` | Modifiers, state, lazy layouts, lifecycle/one-shot effects, navigation routes, iOS dialogs/permissions, UDF, insets |
| `compose-resource-conventions` | Image formats, brand assets vs. glyphs, icon naming/sizing, string resources, WebP encoding/alpha |
| `android-conventions` | Platform API compatibility, runtime pitfalls |
| `gradle-conventions` | Verifying Gradle builds, CMP iOS resource staleness |
| `git-conventions` | Git stash/pathspec gotchas, binary patches |
| `code-editing-conventions` | Propagating fixes to sibling sites, leaving TODO/placeholder config alone |
| `jira-conventions` | Jira issue handling with comment fetching |
| `figma-conventions` | Token resolution, render-verifying, hi-res asset export, recovering transparent layers |
| `slack-conventions` | Slack message formatting for MCP tools |
| `gws-conventions` | Google Workspace CLI usage |
