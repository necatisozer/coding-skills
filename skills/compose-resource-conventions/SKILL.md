---
name: compose-resource-conventions
description: Use whenever adding, editing, or deleting any Compose Multiplatform resource — strings.xml entries, plurals, drawables (WebP/PNG/SVG), ImageVectors, fonts, anything under composeResources/ — or modifying call sites that reference Res.string.*, Res.drawable.*, Res.font.*, stringResource, pluralStringResource, painterResource. Covers image format selection, naming, sizing, apostrophe escaping (don't `\'` in CMP), positional plural specifiers (`%1$d` not `%d`), the per-resource imports CMP requires for every Res.* accessor, brand illustrations vs. ImageVector glyphs, and verifying WebP alpha after encoding.
user-invocable: false
paths: "**/*.kt,**/*.webp,**/*.png,**/*.xml"
---

## Image Formats
No SVG or Android vector XML drawables in Android/CMP compose resources. Use:
- **ImageVector** for simple icons (settings gear, arrows, navigation icons)
- **Lossless WebP** for complex icons/UI assets with gradients and shadows
- **Lossy WebP (80%)** for photos and large images

## Brand Illustrations Stay as Image, Not ImageVector
Designer-rendered raster brand assets — a mascot, a multi-color logo mark, a textured badge, a patterned divider — stay rendered via `Image(painterResource(...))` with a WebP asset. Do **not** substitute a flat `ImageVector` geometric shape, even for a small 24dp marker or a 32dp inline icon; a flat vector loses the gradients, facets, and detail that make the asset on-brand.

Pure UI glyphs (back arrow, check, chevron, close, plus) are the opposite — `ImageVector` is correct for those. The dividing line: if the design node is a named illustration with soft gradient / multi-color detail, it's a brand asset (Image + WebP); if it's a single-color stroked geometric shape, it's a glyph (ImageVector).

## PNG → WebP Conversion
Resize to 4x the display dp size and convert in one step:

```bash
# Lossless for sharp UI assets (e.g., 48dp icon → 192px)
cwebp -lossless -resize 192 192 input.png -o output.webp

# Lossy 80% for photos
cwebp -q 80 -resize 640 640 input.png -o output.webp
```

Skip resize if the original is already smaller than the 4x target.

## Verify Alpha After Encoding
After encoding a WebP that should have transparency, verify it:

```bash
webpmux -info output.webp
```

If `transparency` is absent from the `Features present:` line (e.g. it prints `No features present`), the alpha channel was lost and the asset will render with a visible opaque square backing. This usually means the wrong layer was exported (a parent frame with a fill) rather than the icon-only sub-node; re-export the transparent sub-node and re-encode.

## SVG → ImageVector
Convert SVG path commands to Compose path commands and create `ImageVector`; the SVG file itself is an intermediate and never ships. A design-exported SVG's canvas is the glyph's bounding box, not the icon frame — **load the `figma-conventions` skill before converting one**, for the viewport, scale and translation arithmetic.

## Icon Naming
Match design name, no `ic_` prefix. Create `ImageVector` via `by lazy`.

## Icon Tint
`Icon` uses `LocalContentColor.current` as default tint.

## Icon vs Image Sizing
`Icon` falls back to a 24.dp default size only when the painter's intrinsic size is unspecified; an `ImageVector` with declared dimensions renders at those intrinsic dimensions. Either way, apply `Modifier.size()` to force a specific size. `Image` with `painterResource` also needs an explicit `Modifier.size`.

## IconButton Edge Padding
`IconButton` has 48dp touch target with 12dp internal padding. At screen edges, compensate for the internal padding so the icon aligns with the screen margin.

## String Resources
- Always use string resources instead of hardcoded strings.
- Use descriptive names with context: `home_title` (not `title`).
- Suffix accessibility descriptions with `_content_description`.
- Don't reuse strings just because the text is the same — only reuse if semantically connected.
- Use `stringResource(Res.string.key, args)` for formatted values — `%1$d` localizes digits, `%1$s` for strings.
- Never hardcode the app name — use a dynamic source and `%1$s` placeholders in string resources.

## Per-Resource Imports Are Required
Compose Multiplatform's Resources plugin generates each accessor as a top-level extension property in the `Res` object's package (e.g., `Res.string.home_title` is `<res-package>.home_title`). Unlike Android's `R.string.*` — where importing the `R` class covers every resource — every CMP accessor needs its own import. Adding a `<string>` / drawable / font without also adding `import <res-package>.<name>` in every consumer file produces "Unresolved reference '<name>'" at compile time, which is easy to misdiagnose as a stale resource codegen or Gradle cache problem.

```kotlin
// GOOD — accessor imported alongside the call site
import com.example.app.home_title

stringResource(Res.string.home_title)

// BAD — fails with "Unresolved reference 'home_title'"
stringResource(Res.string.home_title)
```

When adding a resource and a call site in the same change, scan the consumer file for the existing `import <res-package>.<other_resource>` lines and add the new one alphabetically.

## Apostrophes in Compose Multiplatform
Don't escape apostrophes with `\'` in Compose Multiplatform string resources — the backslash renders literally (unlike Android resources).

## Plural Placeholders Must Be Positional
Compose Multiplatform's string formatter only substitutes **positional** specifiers (`%1$d`, `%2$s`). Bare `%d` / `%s` are left as literal text — the UI will render `%d items` instead of `5 items`. This applies to both `stringResource` and `pluralStringResource`.

```xml
<!-- GOOD -->
<plurals name="item_count">
    <item quantity="one">%1$d item</item>
    <item quantity="other">%1$d items</item>
</plurals>

<!-- BAD — %d renders literally -->
<plurals name="item_count">
    <item quantity="one">%d item</item>
    <item quantity="other">%d items</item>
</plurals>
```
