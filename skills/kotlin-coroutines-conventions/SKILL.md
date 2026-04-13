---
name: kotlin-coroutines-conventions
description: Enforces coroutine safety when writing suspend functions, Flow, runCatching, Dispatchers, coroutineContext, or ensureActive. Prevents CancellationException suppression.
user-invocable: false
paths: "**/*.kt"
---

## runCatching and CancellationException
`runCatching` catches `CancellationException`, which breaks coroutine cancellation. Avoid using `runCatching` around suspending calls — use a cancellation-aware alternative or rethrow `CancellationException`. You can also call `currentCoroutineContext().ensureActive()` after `runCatching` to rethrow if cancelled.

```kotlin
// BAD - breaks coroutine cancellation
val result = runCatching { suspendingOperation() }

// GOOD - ensureActive after runCatching
val result = runCatching { suspendingOperation() }
currentCoroutineContext().ensureActive()
```

## currentCoroutineContext()
Always use `currentCoroutineContext()` over `kotlin.coroutines.coroutineContext`. It avoids ambiguity with `CoroutineScope.coroutineContext` and is the recommended approach per kotlinx.coroutines.

```kotlin
// GOOD
currentCoroutineContext().ensureActive()

// BAD - ambiguous
coroutineContext.ensureActive()
```

## Inject Dispatchers
Don't use `Dispatchers.IO`, `Dispatchers.Default`, etc. directly. Inject dispatchers as a dependency so they can be replaced with `TestDispatcher` in tests.

```kotlin
// GOOD
class MyRepository(private val ioDispatcher: CoroutineDispatcher) {
  fun observeData() = flow { ... }.flowOn(ioDispatcher)
}

// BAD
class MyRepository {
  fun observeData() = flow { ... }.flowOn(Dispatchers.IO)
}
```

## Flow Naming: `observe` Prefix
Use `observe` prefix for `Flow`-returning functions that emit ongoing data updates (e.g., `observeSettings(): Flow<Settings>`). Not needed for one-shot operations that happen to return a `Flow` result.
