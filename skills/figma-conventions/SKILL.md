---
name: figma-conventions
description: Use whenever working with Figma — implementing UI from a Figma URL or design, calling any Figma MCP tool (get_design_context, get_screenshot, get_metadata, get_variable_defs), translating designs to Compose, picking colors/typography/spacing from a design, or verifying a screen against Figma. Enforces resolving design tokens via figma:get_variable_defs instead of guessing hex colors from the rendered design.
user-invocable: false
---

## Design Tokens
Always use the `figma:get_variable_defs` tool to find the actual design token instead of guessing theme colors from hex values.
