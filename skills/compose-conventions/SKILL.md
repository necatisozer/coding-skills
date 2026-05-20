---
name: compose-conventions
description: Use when writing or modifying any @Composable, Compose UI, or state — Modifier chains (size/width/height/padding), LazyColumn/LazyRow/LazyGrid, mutableStateOf, rememberSaveable, rememberCoroutineScope, LaunchedEffect, DisposableEffect, LifecycleResumeEffect/StartEffect/EventEffect, BackHandler, WindowInsets/safeDrawing, Snapshot.withMutableSnapshot, IconButton/Surface touch targets (48dp), @Preview composables, UDF state hoisting, and lazy-layout keys.
user-invocable: false
paths: "**/*.kt"
---

## Modifier.size()
Use `Modifier.size()` instead of separate `width()` and `height()` calls. When width and height are equal, use the single-parameter overload (`Modifier.size(58.dp)`).

## Coroutine Scopes
Always name `coroutineScope`, never `scope`:

```kotlin
// GOOD
val coroutineScope = rememberCoroutineScope()

// BAD
val scope = rememberCoroutineScope()
```

## Back Handling
Use `NavigationBackHandler` (from `navigationevent-compose`) instead of `PredictiveBackHandler` or `BackHandler` when the dependency is available.

**Never use `isBackEnabled = false` to block navigation.** Disabling the handler causes the gesture to fall through to the Navigation library's default handler, which pops the screen — the opposite of blocking. Instead, keep the handler enabled and guard inside `onBackCompleted`:

```kotlin
// GOOD - handler intercepts and swallows the gesture
NavigationBackHandler(
  state = rememberNavigationEventState(NavigationEventInfo.None),
  onBackCompleted = { if (canGoBack) onBackClick() },
)

// BAD - disabling handler lets gesture fall through to default pop
NavigationBackHandler(
  state = rememberNavigationEventState(NavigationEventInfo.None),
  isBackEnabled = canGoBack,
  onBackCompleted = { onBackClick() },
)
```

## rememberSaveable for UI State
Use `rememberSaveable` instead of `remember` for UI state that must survive navigation recomposition (e.g., collapsing bar offset, scroll-linked values). Primitive types (`Float`, `Int`, `Boolean`, `String`) are auto-saved — no custom `Saver` needed:

```kotlin
// GOOD - survives navigation recomposition
var offsetPx by rememberSaveable { mutableFloatStateOf(0f) }

// BAD - resets to 0 when composable re-enters composition
var offsetPx by remember { mutableFloatStateOf(0f) }
```

## Batch State Updates
Use `Snapshot.withMutableSnapshot { }` to atomically update multiple `mutableStateOf` variables. Required from background threads. Also useful on the main thread when snapshot observers (e.g., `snapshotFlow`) need to see a consistent combined state.

```kotlin
Snapshot.withMutableSnapshot {
  items = result.items
  isLoading = false
  selectedIndex = 0
}
```

## Component Padding
Components should not include placement padding (margins from screen edges). Only include intrinsic padding (internal to the component's design). Apply placement padding at the call site via `modifier` or `contentPadding`:

```kotlin
// GOOD - placement padding at call site
MyComponent(modifier = Modifier.padding(horizontal = 16.dp))

// BAD - placement padding inside component
@Composable
private fun MyComponent(modifier: Modifier = Modifier) {
  Row(modifier = modifier.padding(horizontal = 16.dp)) { ... }
}
```

## Minimum Interactive Component Size
Material3 interactive components (`Surface(onClick = ...)`, `IconButton`, etc.) enforce a 48dp minimum interactive size via `LocalMinimumInteractiveComponentSize`. The component renders at its visible size but reserves a 48dp layout box, with invisible padding around it. This breaks pixel-perfect design matching:

- A 32dp visible chip occupies 48dp of layout space (8dp invisible padding on each side)
- `Modifier.padding(N.dp)` from a parent edge reads as `(N + 8).dp` visually
- `Arrangement.spacedBy(N.dp)` between chips reads as `(N + 16).dp` between visible edges

When the design requires tight spacing or chips smaller than 48dp, override the local with `Dp.Unspecified` so dp values become visually accurate. Trade-off: the actual touch target shrinks below Material's accessibility floor — accept only when the design explicitly requires it.

```kotlin
// GOOD - 32dp visible chip occupies 32dp of layout, dp values match what's seen
CompositionLocalProvider(LocalMinimumInteractiveComponentSize provides Dp.Unspecified) {
  Surface(onClick = onClick, shape = shape) {
    Box(modifier = Modifier.padding(4.dp)) { Icon(imageVector = icon, contentDescription = null) }
  }
}

// BAD - 32dp visible chip is wrapped in invisible 48dp padding
Surface(onClick = onClick, shape = shape) {
  Box(modifier = Modifier.padding(4.dp)) { Icon(imageVector = icon, contentDescription = null) }
}
```

## Lazy Layout Keys
Provide `key` to lazy layout items for performance. Ensure keys are unique — use `distinctBy` to filter duplicates before passing to `items(key = ...)`, as duplicate keys crash the app.

```kotlin
// GOOD
val uniqueItems = allItems.distinctBy { it.id }
items(uniqueItems, key = { it.id }) { item -> ... }
```

## Lifecycle Effects
Use `LifecycleResumeEffect` / `LifecycleStartEffect` instead of two separate `LifecycleEventEffect` calls for paired start/stop or resume/pause work (e.g., video playback, sensor listeners).

```kotlin
// GOOD
LifecycleResumeEffect(Unit) {
  player.play()
  onPauseOrDispose { player.pause() }
}

// BAD
LifecycleEventEffect(Lifecycle.Event.ON_RESUME) { player.play() }
LifecycleEventEffect(Lifecycle.Event.ON_PAUSE) { player.pause() }
```

## UDF (Unidirectional Data Flow)
State flows down, events flow up. UI event lambdas must be `() -> Unit` — never return data.

## Lazy Grid Columns
Use `GridCells.Adaptive(minSize)` instead of `GridCells.Fixed` — `Fixed` ignores screen width and breaks on tablets, foldables, and landscape.

Derive `minSize` from the target **column count on the smallest supported phone**, not by guessing pixel values. `Adaptive` packs as many columns as fit; if `minSize` is too small, narrow phones gain an extra column and the design breaks.

Given target column count `N`, item horizontal arrangement `S`, and the smallest phone container width `W` after subtracting horizontal content padding (typically `360.dp − 2 × 16.dp = 328.dp`), pick any `minSize` in:

```
((W − N × S) / (N + 1))  <  minSize  ≤  ((W − (N − 1) × S) / N)
```

The lower bound prevents `N + 1` columns from fitting; the upper bound guarantees `N` columns fit. Pick a round number near the **upper** bound so layout cards have headroom.

Reference values for `W = 328.dp` (360-wide phone, 16dp side padding) and `S = 8.dp`:

| Target columns | Valid `minSize` range | Recommended |
|---|---|---|
| 2 | (104, 160] | `160.dp` |
| 3 | (78, 104] | `110.dp` for 390-wide phones; `104.dp` if you must support 360-wide |
| 4 | (62, 76] | `80.dp` for 390-wide; `76.dp` for 360-wide |

If the design spec calls out a fixed card width, use that width as `minSize` and let `LazyVerticalGrid` stretch cells to fill — never hard-code `Modifier.width(...)` on grid items, since adaptive widths must absorb the slack from `(W − content) / N`.

## Window Insets
For scrollable content, apply insets as content padding, not outside padding. Components should never reference `WindowInsets` directly — accept `contentPadding: PaddingValues` and let screens pass insets.

## Previews

Add `@Preview` composables for every screen and every standalone-file composable, one per meaningful visible state (loading, populated, empty, each error, each major variant). Inline helpers (private composables in the same file as their only caller) are covered by the parent's preview and don't need their own.

**Co-locate** previews with the composable they preview — keep them in the same file, not in a sibling `preview/` package. Future readers see all visible states next to the code that renders them, and `private` content composables remain reachable from the preview without relaxing visibility.

### Setup (Compose Multiplatform 1.10+)

In `commonMain` add the new annotation artifact (the old `org.jetbrains.compose.components:components-ui-tooling-preview` is deprecated in CMP 1.10+):

```kotlin
commonMain.dependencies {
  implementation("org.jetbrains.compose.ui:ui-tooling-preview:<compose-version>")
}
```

The tooling library (which Android Studio loads to render the preview) goes on a different configuration depending on the Android target plugin:

- Classic `androidTarget {}` / `com.android.library` → `debugImplementation("org.jetbrains.compose.ui:ui-tooling:<compose-version>")`
- New `androidLibrary {}` / `com.android.kotlin.multiplatform.library` → `androidRuntimeClasspath("org.jetbrains.compose.ui:ui-tooling:<compose-version>")` (the new plugin does NOT expose `debugImplementation` as a top-level configuration; using it produces an "Unresolved reference 'debugImplementation'" script error)

Import `androidx.compose.ui.tooling.preview.Preview` — the `org.jetbrains.compose.ui.tooling.preview.Preview` alias is deprecated and emits a warning.

### Theme wrapper

Don't wrap previews in your app's bare theme composable. App themes typically default to `isSystemInDarkTheme()` (returns `false` in the preview pane regardless of IDE setting) and don't provide `LocalContentColor` / `LocalTextStyle` — those are usually set at the activity root via a separate `CompositionLocalProvider`. The result is a light-theme preview with `Color.Black` content color, leaving icons invisible on dark surfaces.

Create a single `PreviewTheme` helper in your presentation/UI module that mirrors what the activity root does — force the right theme variant, paint the screen background, provide `LocalContentColor` / `LocalTextStyle` — and use it in every preview:

```kotlin
@Suppress("ktlint:compose:modifier-missing-check")
@Composable
fun PreviewTheme(content: @Composable () -> Unit) {
  Theme(darkTheme = true) { // match your app's enforced theme
    Box(modifier = Modifier.background(Theme.colorScheme.background)) {
      CompositionLocalProvider(
        LocalContentColor provides Theme.colorScheme.onBackground,
        LocalTextStyle provides Theme.typography.body14,
        content = content,
      )
    }
  }
}
```

Do NOT add `Modifier.fillMaxSize()` to that outer `Box`. Screen previews already self-expand because the screen's own root usually does `Modifier.fillMaxSize().background(...)`, so the Box wraps that and renders edge-to-edge anyway. But component previews (a button, a card, a section) would inherit the forced full size and render against a full-screen dark backdrop instead of wrapping tightly. With a bare `.background(...)` modifier the Box wraps its content, so screens stay full-size and components render at their intrinsic size with the dark background painted only behind their footprint.

### `showSystemUi`

Do NOT pass `showSystemUi = true` to `@Preview` for screens whose visual depends on a dark background. Android Studio renders the status- and nav-bar zones as opaque light strips that paint over the composable, leaving a pale band above the toolbar that does not match the design (and that does not represent how the app renders edge-to-edge at runtime). There is no per-annotation flag to make those zones transparent.

Use bare `@Preview` — `WindowInsets.safeDrawing` returns zero in that mode, so the toolbar sits flush at the top, matching how design mocks are usually composed (system bar omitted or drawn as a decorative element).

### Sample data

Pull preview inputs into `private` top-level vals, and (for screens with large state objects) a `private fun previewState(...)` helper that fills in defaults. Don't hand-craft a full state object inside each `@Preview` body — the duplication makes it hard to compare what differs between two states. Event lambdas in the state are always `{}` in previews — they're never invoked.

```kotlin
private val previewItem = Item(id = "1", title = "Sample", price = 4.99)

private fun previewState(
  isLoading: Boolean = false,
  items: List<Item> = listOf(previewItem),
  selectedId: String? = null,
) = ScreenState(
  isLoading = isLoading,
  items = items,
  selectedId = selectedId,
  onItemClick = {},
  onBackClick = {},
)

@Preview
@Composable
private fun ScreenLoadingPreview() {
  PreviewTheme { Screen(state = previewState(isLoading = true)) }
}

@Preview
@Composable
private fun ScreenLoadedPreview() {
  PreviewTheme { Screen(state = previewState()) }
}
```

### Cross-platform safety

Even though the new `androidx.compose.ui.tooling.preview.Preview` annotation is multiplatform-safe and no-ops on iOS, the *sample data* you reference still has to compile on every target. Verify with the iOS compile task (e.g., `:<module>:compileKotlinIosSimulatorArm64`) before committing — a `RowScope`-only helper or an Android-only type in your sample data will silently break the iOS build.

## Resources
For image formats, icon naming, and string resource conventions, see the `compose-resource-conventions` skill.
