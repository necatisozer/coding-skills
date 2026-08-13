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
| `kotlin-conventions` | File organization, idioms, type design, persisted enums → value classes, extensions vs. members, DI helpers, Duration/Instant APIs, expect/actual |
| `kotlin-coroutines-conventions` | Coroutine safety, Flow patterns, runCatching, dispatcher injection, platform dispatch |
| `kotlin-serialization-conventions` | kotlinx.serialization response/request models, value classes instead of serialized enums, typed boundary exceptions |
| `compose-conventions` | Modifiers, state, lazy layouts, lifecycle/one-shot effects, shared components vs. design, navigation routes, iOS dialogs/permissions, UDF, insets |
| `compose-resource-conventions` | Image formats, brand assets vs. glyphs, SVG → ImageVector sizing, icon naming/sizing, string resources, WebP encoding/alpha |
| `android-conventions` | Platform API compatibility, runtime pitfalls |
| `gradle-conventions` | Verifying Gradle builds, CMP iOS resource staleness |
| `git-conventions` | Git stash/pathspec gotchas, binary patches |
| `code-editing-conventions` | Propagating fixes to sibling sites, leaving TODO/placeholder config alone |
| `jira-conventions` | Jira issue handling with comment fetching |
| `figma-conventions` | Token resolution, never authoring design values, icon frame vs. SVG bbox, render-verifying, hi-res asset export, recovering transparent layers |
| `slack-conventions` | Slack message formatting for MCP tools |
| `gws-conventions` | Google Workspace CLI usage |

## Releasing

Bump `version` in `.claude-plugin/plugin.json` — it is the single source of truth.
`.claude-plugin/marketplace.json` is synced from it by `scripts/sync-version.py`,
which the `.githooks/pre-commit` hook runs automatically.

After a fresh clone, point git at the hooks once:

```
git config core.hooksPath .githooks
```
