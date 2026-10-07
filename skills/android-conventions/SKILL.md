---
name: android-conventions
description: "Enforces Android platform rules when using MutableList, updating compileSdk, targeting API 35+, or running Compose code in Android host (unit) tests. Prevents runtime NoSuchMethodError from removeFirst/removeLast, and host tests that throw \"not mocked\" on every composition."
user-invocable: false
paths: "**/*.kt,**/*.kts,**/*.java"
---

## Never Use removeFirst() / removeLast() on MutableList
Use `removeAt(0)` and `removeAt(list.lastIndex)` instead. Compiling against API 35+ (`compileSdk 35`) causes `NoSuchMethodError` on Android 14 and below.

```kotlin
// BAD - crashes on Android 14 and below when compileSdk 35
list.removeFirst()
list.removeLast()

// GOOD
list.removeAt(0)
list.removeAt(list.lastIndex)
```

## Android Host Tests That Run Compose Code Need `isReturnDefaultValues = true`
Without it, the Compose runtime's `android.os.Trace.beginSection` throws "not mocked" on *every* composition. The report blames `android.util.Log`, but that is only the second throw, raised while it logs the first. The iOS simulator target has neither problem, so a green iOS run proves nothing about Android. Run both.
