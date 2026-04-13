---
name: compose-resource-conventions
description: Guides image format selection and string resource conventions when adding icons, ImageVector, WebP assets, stringResource, or content descriptions in Compose Multiplatform.
user-invocable: false
paths: "**/*.kt,**/*.webp,**/*.png,**/*.xml"
---

## Image Formats
No SVG in Android/CMP compose resources. Use:
- **ImageVector** for simple icons (settings gear, arrows, navigation icons)
- **Lossless WebP** for complex icons/UI assets with gradients and shadows
- **Lossy WebP (80%)** for photos and large images

## PNG → WebP Conversion
Resize to 4x the display dp size and convert in one step:

```bash
# Lossless for sharp UI assets (e.g., 48dp icon → 192px)
cwebp -lossless -resize 192 192 input.png -o output.webp

# Lossy 80% for photos
cwebp -q 80 -resize 640 640 input.png -o output.webp
```

Skip resize if the original is already smaller than the 4x target.

## SVG → ImageVector
Convert SVG path commands to Compose path commands and create `ImageVector`.

## Icon Naming
Match design name, no `ic_` prefix. Create `ImageVector` via `by lazy`.

## Icon Tint
`Icon` uses `LocalContentColor.current` as default tint.

## Icon vs Image Sizing
`Icon` renders at 24.dp by default regardless of the vector's intrinsic dimensions — apply `Modifier.size()` for non-standard sizes. `Image` with `painterResource` also needs explicit `Modifier.size`.

## IconButton Edge Padding
`IconButton` has 48dp touch target with 12dp internal padding. At screen edges, compensate for the internal padding so the icon aligns with the screen margin.

## String Resources
- Always use string resources instead of hardcoded strings.
- Use descriptive names with context: `home_title` (not `title`).
- Suffix accessibility descriptions with `_content_description`.
- Don't reuse strings just because the text is the same — only reuse if semantically connected.
- Use `stringResource(Res.string.key, args)` for formatted values — `%1$d` localizes digits, `%1$s` for strings.
- Never hardcode the app name — use a dynamic source and `%1$s` placeholders in string resources.

## Apostrophes in Compose Multiplatform
Don't escape apostrophes with `\'` in Compose Multiplatform string resources — the backslash renders literally (unlike Android resources).
