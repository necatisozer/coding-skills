---
name: kotlin-coroutines-conventions
description: Enforces coroutine safety when writing suspend functions, Flow, runCatching, Dispatchers, coroutineContext, or ensureActive. Prevents CancellationException suppression. Also covers platform implementations owning their own thread dispatch, not re-wrapping suspend functions that are already main-safe, and avoiding async work in constructors/`init` (including ViewModel `init`).
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
Use `observe` prefix for `Flow`-returning functions that emit ongoing data updates (e.g., `observeNetworkStatus(): Flow<NetworkStatus>`). Not needed for one-shot operations that happen to return a `Flow` result.

## Platform Implementations Own Their Dispatch
A platform-specific implementation (an `expect`/`actual` class, an `iosMain`/`androidMain` body) must handle its own thread/dispatcher requirements internally. Callers should not need to know which thread a platform API requires.

Some iOS APIs require the main thread. If the implementation doesn't wrap the call, every caller has to remember `withContext(Dispatchers.Main)` — error-prone, and it leaks a platform detail into shared code. Wrap the thread-sensitive call inside the platform body instead. Using `Dispatchers.Main` directly *there* is fine — it's an implementation detail of that platform body, not shared logic that needs an injected dispatcher (contrast "Inject Dispatchers" above, which is about testable shared code).

## Don't Re-Wrap an Already Main-Safe Suspend Function
Before wrapping a library's suspend call in `withContext(Dispatchers.IO)`, check whether it's already **main-safe** — callable from the main thread without blocking it. A suspend function can be main-safe either because it switches to a background dispatcher internally (`withContext(Dispatchers.IO) { … }`) *or* because it does non-blocking async I/O (many network clients never touch `Dispatchers.IO` at all — and `Dispatchers.IO` doesn't even exist on Kotlin/Native). Re-wrapping an already-main-safe call is a redundant scope hop (plus an extra thread switch only when the inner dispatcher differs), and it misleadingly implies the call was main-unsafe.

Check the library's documented threading (or source) before wrapping — and don't grep solely for `Dispatchers.IO` and conclude a non-blocking client is main-unsafe.

## No Async Work in Constructors / `init`
Keep constructors and `init` blocks side-effect-free — don't launch coroutines or kick off async work at construction time. It makes the class hard to test: the work starts the moment the object is created, before a test can arrange timing, fakes, or a `TestDispatcher`. This bites hardest with ViewModels, which a factory constructs outside your control. Start async work from an explicit trigger function, a lifecycle/Compose effect (`LaunchedEffect`/`produceState`), or a lazily-collected `Flow` — not from `init`.
