---
name: figma-conventions
description: Use whenever working with Figma — implementing UI from a Figma URL or design, calling any Figma MCP tool (get_design_context, get_screenshot, get_metadata, get_variable_defs, use_figma), translating designs to code, picking colors/typography/spacing from a design, exporting assets, or verifying a screen against Figma. Covers resolving tokens from the actual node, render-verifying before specing, high-res asset export, and recovering transparent per-layer exports.
user-invocable: false
---

## Resolve Tokens from the Node, Not the Catalog
Always resolve the actual design token instead of guessing theme values from rendered hex colors.

`get_variable_defs` returns the file's **whole token catalog** (every surface tier, every type style) — it does not tell you which token a *specific* container uses. For the color/typography of a given element, pull `get_design_context` on that element's node and read the exact token it references — e.g. a `bg-[var(--surface-elevated,rgba(...))]` line, or the exact font + weight + size. Visually similar shades on a dark background are easy to confuse; the design tokens are the authoritative spec.

## Render and Visually Inspect Before Specing
Don't infer "element X appears here" from the metadata / layer tree alone — **render the frame and look**. A component instance can be present in the layer hierarchy but not paint in the export (set hidden, transparent, or off-canvas).

- For each visual element you plan to spec, render its containing frame via `get_screenshot` at full size and view it.
- For an overlay/badge meant to span multiple frames, verify it actually renders in **every** variant — present in the layer tree of some but painted in none is a layer-tree ghost.
- Small inline icons: metadata is usually trustworthy. Decorative overlays, badges, and ornaments: always render-verify.

## High-Res Asset Export: REST API at `scale=4`
`get_screenshot` is **canvas-capped** — it only downscales, never upscales. An 80×80 component returns at 80×80 even with a large `maxDimension`. For a sharp raster of a small symbol, use Figma's REST API:

```bash
curl -sS -H "X-Figma-Token: $(cat ~/.figma-token)" \
  "https://api.figma.com/v1/images/<fileKey>?ids=<nodeId1>,<nodeId2>&scale=4&format=png"
```

Returns `{"images": {"<nodeId>": "https://…"}}`; each URL is a PNG rendered at 4× the node's canvas size with full vector-overlay fidelity. (The user generates a personal access token at Figma → Settings → Security with "File content: Read-only" scope, stores it in `~/.figma-token` with `chmod 600`, and revokes it when done.) Download each URL (`curl -o asset.png <url>`), then encode it lossless per the `compose-resource-conventions` skill.

**Fallback (no token):** composite from the raw raster URL in `get_design_context` plus per-layer geometry — but this misses Figma-internal vector overlays (inner glows, gradient strokes) that aren't exposed as raster URLs.

## Recover Transparent Per-Layer Exports
For a multi-layer icon (a base shape + a glyph + a count badge, etc.), some per-layer raster URLs from `get_design_context` systematically come back **fully transparent** — the compositing happens at Figma's render time but the per-layer export misses it. The composed render looks correct; the downloaded layer is empty (`Image.getbbox()` is `None`).

Don't recompose from per-layer fills. Recover the composed node directly with `use_figma` (autonomous, true hi-res, no transcription):

```js
// Make a real, addressable, 4x-sized node from the instance child you need
const inst = await figma.getNodeByIdAsync("<instanceId>")
const detached = inst.clone().detachInstance()
const target = detached.findOne(n => n.name === "<child-name>")
detached.parent.appendChild(target); target.rescale(4)
target.x = detached.x; target.y = detached.y - 600; detached.remove()
return { tempNodeId: target.id }
```

Then `get_screenshot(tempNodeId)` → curl the returned URL → encode. **Always delete the temp node afterward** with a second `use_figma` call: `(await figma.getNodeByIdAsync(tempNodeId)).remove()`. (The clone-and-rescale is needed because `get_screenshot` can't upscale past a node's natural size, the node-id regex rejects instance child paths like `I…;…`, and `exportAsync` base64 returned through `use_figma` gets truncated.)
