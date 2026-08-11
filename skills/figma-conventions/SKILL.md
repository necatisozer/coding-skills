---
name: figma-conventions
description: Use whenever working with Figma — implementing UI from a Figma URL or design, calling any Figma MCP tool (get_design_context, get_screenshot, get_metadata, get_variable_defs, use_figma), translating designs to code, picking colors/typography/spacing from a design, exporting assets, or verifying a screen against Figma. Covers resolving tokens from the actual node, never authoring an icon/colour/size/spacing that isn't in the design node, converting an exported SVG into an ImageVector sized to the design's icon frame, render-verifying before specing, high-res asset export, and recovering transparent per-layer exports.
user-invocable: false
---

## Resolve Tokens from the Node, Not the Catalog
Always resolve the actual design token instead of guessing theme values from rendered hex colors.

`get_variable_defs` returns the file's **whole token catalog** (every surface tier, every type style) — it does not tell you which token a *specific* container uses. For the color/typography of a given element, pull `get_design_context` on that element's node and read the exact token it references — e.g. a `bg-[var(--surface-elevated,rgba(...))]` line, or the exact font + weight + size. Visually similar shades on a dark background are easy to confuse; the design tokens are the authoritative spec.

**A design token does not map to the app theme token of the same name.** Check the app token's actual value before substituting it — a design's `text/primary` at `#121212` and an app `textPrimary` at `#0D0D0D` are not the same colour.

## Never Author an Icon, Colour, Size or Spacing Yourself
Every drawable path, hex value, frame size and gap comes from the design node or from an asset already in the repo. A hand-picked value looks plausible and is wrong in a way nothing catches — a geometric star where the design has a soft-cornered one, `#FFC107` where the design says `#FFCC00`, 36dp where the node says 32.

- **Icons: export, never draw.** Pull the node's SVG (`get_design_context` returns the asset URL), `curl` it, and convert its path commands, stroke width and caps **verbatim** into an `ImageVector`; the SVG is an intermediate you read, not an artifact you ship. Which assets become an `ImageVector` at all, and which stay raster, is `compose-resource-conventions`' call — check it before converting.
- **Colours: read them, don't match them.** Take the hex from the node's token or the exported SVG's `fill`/`stroke` — never from how a screenshot looks.
- **Sizes and spacing: from the node.** Frame size, icon frame, gaps, padding, button height are all stated in `get_design_context`. If a number is not in the design, it is not yours to pick — ask for the node.
- **An existing repo asset proves nothing about how to use it.** The file being there says nothing about the size, tint or frame the design draws it at. Check the component, not just the asset.

### The Exported SVG Is the Glyph's Bounding Box, Not the Icon Frame
`get_design_context` gives three numbers for one icon, and they are measured against **two different boxes**:

- the **frame** — `size-[32px]`
- the vector's **insets** inside that frame — `inset-[16.67%_14.82%_16.67%_14.35%]`, as percentages of the frame (top, right, bottom, left)
- the **stroke bleed** on the `img` wrapper — `inset-[-4.69%_-4.42%]`, printed **negative** and measured against the *vector box*, not the frame

The downloaded SVG canvas is *vector box + bleed*, which is smaller than the frame — so carrying its `viewBox` into the `ImageVector` viewport makes the glyph fill the whole cell, and every call site that then uses the design's own numbers renders too large.

Three numbers settle it: viewport = the frame in px, `scale` = SVG canvas px / `viewBox` units, `translation` = the SVG canvas origin relative to the frame. When the node reports percentages, recover them like this — converting to frame units first, never subtracting one percentage from the other:

```
insetLeftPx   = insetLeft%  × frame                        // 14.35% × 32   = 4.59
vectorWidthPx = frame × (1 − insetLeft% − insetRight%)     // 32 × 0.7083   = 22.67
bleedXPx      = |bleedX%| × vectorWidthPx                  // 4.42% × 22.67 = 1.00
translationX  = insetLeftPx − bleedXPx                     //  4.59 − 1.00  = 3.59
scale         = (vectorWidthPx + 2 × bleedXPx) / svgViewBoxWidth
```

Repeat with the top/bottom values for `translationY` (here `5.33 − 1.00 = 4.33`). `scale` is `1f` only when the SVG's `viewBox` is already in frame pixels — a `0 0 24 24` viewBox on a 32px frame is not, and pasting its coordinates unscaled renders the glyph at 75% with a stroke to match.

```kotlin
ImageVector.Builder(
  name = "StarOutline",
  defaultWidth = 32.dp, defaultHeight = 32.dp,
  viewportWidth = 32f, viewportHeight = 32f,   // the frame, NOT the SVG viewBox
).apply {
  // pivot defaults to 0,0: the path is scaled about the origin, then translated
  group(scaleX = SCALE, scaleY = SCALE, translationX = 3.59f, translationY = 4.33f) {
    // path commands and strokeLineWidth stay in the SVG's own units — the group scales both
    path(stroke = SolidColor(Color.Black), strokeLineWidth = 1.5f) { /* SVG path commands, unchanged */ }
  }
}.build()
```

The call site can then use the design's own numbers (`size(32.dp)`, `spacedBy(8.dp)`) and have them mean what the design means.

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

## Name Code Assets After Their Figma Components
When creating a code asset (an `ImageVector`, drawable, or similar) that implements a Figma component, derive its name from the Figma component's name — e.g. `icon/back` → `Back`, `icon/expand-right` → `ExpandRight`, `swap-item` → `SwapItem`, `icon/home-filled` → `HomeFilled`. Don't invent a descriptive synonym (`ChevronLeft` for `icon/back`, `Loading` for `icon/spinner`): designers file bugs and discuss icons using the Figma names, and a synonym forces a mental mapping on every conversation and invites duplicate look-alike assets.

Documented deviations are fine when the literal name can't work in code — identifiers can't start with a digit (`icon/3d-view`), the name collides with a framework symbol (`icon/image` vs a UI-framework `Image` function), or the Figma name carries a variant/state suffix (`icon/settings-default` → `Settings`). Deviate deliberately, not by habit — and when auditing, verify glyph identity by usage slot in the design (which instance sits where) or geometry, not by name similarity alone.
