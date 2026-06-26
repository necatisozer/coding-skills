---
name: code-editing-conventions
description: Use when modifying existing code — after adding a guard, null-check, error branch, or fix to one handler/function (grep sibling call sites for the same gap before declaring done), and when encountering an empty or TODO/placeholder config value (don't substitute a guessed value). Prevents half-applied fixes and papered-over placeholders.
user-invocable: false
---

## Propagate Fixes to Sibling Call Sites
When you add a guard — a permission check, a range/bounds check, an error-handling branch, a null-guard — to one event handler or function, the same gap almost always exists in sibling handlers that share the shape. Before declaring the fix complete, grep the surrounding file and the sibling files in the same module for the same pattern.

- `grep` for the sibling function names or the guard condition to surface the same shape elsewhere.
- If the function you fixed mirrors a canonical one (e.g. a retry path that re-does what an initial path sets up), diff the two guard chains line-by-line.
- If two classes in the same module call the same repository/manager method, expect both call sites to need the parallel error-handling shape.

## Leave TODO / Placeholder Config Alone
When a config field is empty or a placeholder with a `// TODO`, do **not** "fix" it by substituting a plausible-but-wrong value. An unset value is usually an intentional pending item — a secret, an API key, or a webhook URL that doesn't exist yet — not a bug to paper over.

- Treat empty/TODO config like a missing secret: leave the TODO.
- Check any project setup checklist (a `TODO.md`, a README setup section, etc.) before flagging or "fixing" a placeholder — if it's listed there, it's an intentional maintainer step, not a defect.
- Before changing any URL/key/id config, check how sibling projects set the same field. A value that looks interchangeable (e.g. a public CDN URL vs. a signed, expiring asset URL) often isn't, and the wrong one silently breaks behavior downstream.
