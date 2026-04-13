---
name: kotlin-conventions
description: Enforces Kotlin file organization, idioms, and type design when writing data classes, sealed interfaces, enums, value classes, delegation, Duration/Instant APIs, or organizing files.
user-invocable: false
paths: "**/*.kt,**/*.kts"
---

## File Naming
One file per top-level model, named after it. Related sub-models (e.g., value classes, sealed interfaces) go in the same file. Shared types used by multiple models get their own file. Mappers belong in their related model file, not in separate mapper files.

## Imports
Always use import statements — never use fully qualified package paths inline in code.

## Pairs
Use `to` infix function instead of `Pair()` constructor.

## Annotations
Place `@OptIn` and `@Suppress` on the narrowest scope (function/class), not at file level (`@file:`). Only use `@file:` for ktlint rules that apply to the whole file.

## List Construction
Prefer `List(size) { index -> ... }` constructor over `collection.mapIndexed { index, _ -> ... }` when the original elements are unused.

## Explicit Backing Fields (Experimental)
When enabled, use Kotlin 2.3+ explicit backing fields instead of the `_foo` / `foo` pattern when exposing a read-only public type backed by a mutable private one. Requires `-Xexplicit-backing-fields` compiler flag.

```kotlin
// GOOD - explicit backing field
val isMuted: StateFlow<Boolean>
  field = MutableStateFlow(false)

// BAD - underscore-prefixed backing field
private val _isMuted = MutableStateFlow(false)
val isMuted: StateFlow<Boolean> = _isMuted.asStateFlow()
```

## Enum vs Sealed Interface
Prefer `enum class` when all subtypes are singleton `data object`s with no properties. Use `sealed interface` (not `sealed class`) when subtypes carry different data.

```kotlin
// GOOD - all entries are simple singletons
enum class ValidationError { TooSmall, NotFound, InvalidFormat }

// GOOD - sealed interface when subtypes carry different data
sealed interface Result {
  data class Success(val data: String) : Result
  data class Error(val message: String) : Result
}
```

## Value Classes
Use `@JvmInline value class` instead of `data class` for single-property wrappers (identifiers, typed strings).

## Interface Delegation
Use Kotlin's `by` keyword instead of manually forwarding methods.

```kotlin
// GOOD
class LoggingRepository(private val delegate: Repository) : Repository by delegate {
  override fun observeData() = delegate.observeData().onEach { println(it) }
}
```

## Throw Instead of Result Types
For simple success/failure operations, throw exceptions instead of wrapping return types in `Result`, `Either`, or custom sealed classes when there are only two outcomes.

Exception: in KMP shared code consumed by Swift, `Result` wrappers may be preferred since Kotlin exceptions require explicit handling at the Swift boundary.

## Kotlin Time
- Use `kotlin.time.Duration` API (`delay(1.seconds)`) instead of raw milliseconds (`delay(1000L)`). Requires Kotlin 1.6+.
- Use `kotlin.time.Clock` and `kotlin.time.Instant` instead of `kotlinx.datetime.Clock` and `kotlinx.datetime.Instant` when available. Requires Kotlin 2.1.20+. Other datetime types (`LocalDate`, `LocalDateTime`, `TimeZone`, etc.) remain in `kotlinx-datetime`.

## Kotlin/Native Generic Type Erasure
On KMP, multiple parameters with the same erased type (e.g., `List<String>`, `List<Int>`) become indistinguishable on iOS. Wrap in distinct types (`value class`) to give each a unique identity.

```kotlin
// BAD - indistinguishable on iOS
fun process(names: List<String>, ids: List<Int>)

// GOOD
@JvmInline value class Names(val value: List<String>)
@JvmInline value class Ids(val value: List<Int>)
fun process(names: Names, ids: Ids)
```
