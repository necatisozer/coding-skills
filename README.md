# Coding Skills

A Claude Code plugin with coding-convention and workflow skills for Kotlin, Android, and Compose Multiplatform — plus physical iOS device testing, Git, Gradle, and common tooling (Slack, Figma, Google Workspace).

## Installation

```
/plugin marketplace add necatisozer/coding-skills
/plugin install coding-skills
```

## Skills

| Skill | Description |
|---|---|
| `kotlin-conventions` | File organization, idioms, type design, persisted enums → value classes, extensions vs. members, DI helpers, Duration/Instant APIs, expect/actual |
| `kotlin-coroutines-conventions` | Coroutine safety, Flow patterns, runCatching, dispatcher injection, app-lifetime scopes, platform dispatch |
| `kotlin-serialization-conventions` | kotlinx.serialization response/request models, value classes instead of serialized enums, typed boundary exceptions |
| `compose-conventions` | Modifiers, state, lazy layouts, lifecycle/one-shot effects, shared components vs. design, component defaults, keep-screen-on, navigation routes, iOS dialogs/permissions, UDF, insets |
| `compose-resource-conventions` | Image formats, brand assets vs. glyphs, SVG → ImageVector sizing, icon naming/sizing, string resources, WebP encoding/alpha |
| `molecule-testing-conventions` | In projects that use molecule, testing a `@Composable` effect from `commonTest`: recomposition mode, snapshot notifications, virtual time |
| `android-conventions` | Platform API compatibility, runtime pitfalls, Compose code in Android host tests |
| `ios-device-conventions` | Physical iOS device work from the CLI: devicectl, logs and crash reports, WebDriverAgent driving and runner signing, location simulation, frame measurement, network capture, StoreKit sandbox |
| `gradle-conventions` | Verifying Gradle builds, CMP iOS resource staleness, KMP iOS build pitfalls, Gradle tooling |
| `git-conventions` | Git stash/pathspec gotchas, binary patches, stacked PRs with `gh stack` |
| `code-editing-conventions` | Propagating fixes to sibling sites, leaving TODO/placeholder config alone |
| `figma-conventions` | Token resolution, variables via MCP, never authoring design values, icon frame vs. SVG bbox, render-verifying, hi-res asset export, recovering transparent layers |
| `slack-conventions` | Slack message formatting for MCP tools |
| `gws-conventions` | Google Workspace CLI usage |
