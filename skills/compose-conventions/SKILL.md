---
name: compose-conventions
description: Enforces Compose UI patterns when writing @Composable functions, Modifier chains, LazyColumn/LazyGrid, mutableStateOf, lifecycle effects, WindowInsets, or Snapshot. Covers UDF, padding, keys, and back handling.
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
Use `GridCells.Adaptive(minSize)` instead of `GridCells.Fixed` for responsive layouts.

## Window Insets
For scrollable content, apply insets as content padding, not outside padding. Components should never reference `WindowInsets` directly — accept `contentPadding: PaddingValues` and let screens pass insets.

## Resources
For image formats, icon naming, and string resource conventions, see the `compose-resource-conventions` skill.
