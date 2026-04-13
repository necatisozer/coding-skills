---
name: android-conventions
description: Enforces Android platform rules when using MutableList, updating compileSdk, or targeting API 35+. Prevents runtime NoSuchMethodError from removeFirst/removeLast.
user-invocable: false
paths: "**/*.kt,**/*.java"
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
