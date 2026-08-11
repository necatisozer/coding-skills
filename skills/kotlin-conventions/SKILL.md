---
name: kotlin-conventions
description: Use when writing or modifying any Kotlin code — data classes, sealed interfaces/classes, enums (and never relying on `.name` for persistence), value classes, interface delegation, annotations, `Pair` construction, list construction (`List(size) { }` vs `mapIndexed`), explicit backing fields (`-Xexplicit-backing-fields`) vs the `_foo`/`foo` pattern, wildcard or unused imports, `throw` vs `Result<T>` for error handling, `kotlin.time` Duration/Instant APIs, KMP native-SDK wrappers, Kotlin/Native generic type erasure of same-typed parameters at the iOS boundary, file naming, where to put mappers, extension functions on stdlib types, derived members vs. top-level extensions, DI-injected helper classes, code comments that reference other modules, formatter (ktfmt) preferences, and `expect`/`actual` class constructors.
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
val isConnected: StateFlow<Boolean>
  field = MutableStateFlow(false)

// BAD - underscore-prefixed backing field
private val _isConnected = MutableStateFlow(false)
val isConnected: StateFlow<Boolean> = _isConnected.asStateFlow()
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

## Never Rely on Enum `.name` for Persistence
`Enum.name` returns the source-code identifier and changes the moment someone renames an entry. Never use it for analytics events/properties, serialization, wire formats, database storage, file paths, or anything else that outlives a build. Declare an explicit stable string per entry — a refactor of the entry name then can't silently break dashboards, payloads, or stored rows.

```kotlin
// BAD - rename Failed → FailedRetryable silently breaks dashboards/stored rows
enum class OrderStatus { Pending, Shipped, Delivered, Cancelled }
analytics.log("status" to status.name)

// GOOD - explicit serial name decouples source identifier from persisted string
enum class OrderStatus(val serialName: String) {
  Pending("pending"),
  Shipped("shipped"),
  Delivered("delivered"),
  Cancelled("cancelled"),
}
analytics.log("status" to status.serialName)
```

A rename is not the only way this breaks. **Obfuscation renames entries for you** — an R8/ProGuard release build can write or read a different string than the one the source was written against, so a debug build passes and the shipped one silently stops matching.

**Read it back through a total lookup, never `valueOf`.** `valueOf` throws on any unknown string, and inside a `Flow` or state producer that exception kills whatever collects it. A downgrade to a build that predates a newer entry is enough to trigger it.

```kotlin
// BAD - throws on an unknown or older stored value
val status = OrderStatus.valueOf(stored)

// GOOD - total, null for anything unrecognised; add to the enum declared above
companion object {
  fun fromSerialName(value: String?) = entries.firstOrNull { it.serialName == value }
}
```

**Return `null`, don't bake in a fallback.** A default inside the lookup hides the miss from every caller and makes an unrecognised value indistinguishable from a genuine one. Let the caller decide what an unknown value means — `?: Pending` at the one call site where that is actually the right answer, or a branch that reports the miss.

When adding stable strings to an enum that already persists `.name`, spell the literals to match what a **non-obfuscated** build wrote, so those stored values keep resolving without a migration. Values an obfuscated release build wrote are per-build minified identifiers that no literal can match — ship a migration, or accept that they miss the lookup and reset.

For kotlinx.serialization, use `@SerialName` to pin the JSON key — see the kotlin-serialization-conventions skill.

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

## Native SDK Wrappers (KMP)
When wrapping a platform SDK in `commonMain` with `expect`/`actual`:

1. Mirror the SDK's public API surface. Expose the same method names and overloads the native SDK offers — don't invent convenience methods the SDK doesn't have.
2. Delegate constants to the SDK via `expect`/`actual`. Don't declare `const val` with string literals in `commonMain` — the SDK is the source of truth, and a wrapper should pick up value changes automatically.

```kotlin
// BAD - hardcoded literal duplicates the SDK's constant
public object VendorConstants {
  public const val SOME_NAME: String = "some-value"
}

// GOOD - common expect delegates to the SDK in each actual
// commonMain
public expect object VendorConstants {
  public val SOME_NAME: String
}

// androidMain
public actual object VendorConstants {
  public actual val SOME_NAME: String = com.vendor.sdk.VendorConstants.SOME_NAME
}

// iosMain
public actual object VendorConstants {
  public actual val SOME_NAME: String
    get() = cocoapods.VendorFramework.VendorSdkSomeName!!
}
```

## Don't Add Domain Behavior to Stdlib Types
Never add domain-specific extension functions to common/stdlib types (`String`, `Int`, collections). Model the concept as a `@JvmInline value class` and put the operation on it as a member.

```kotlin
// BAD - leaks a URL-joining concern onto every String in scope
fun String.appendPath(path: String): String = ...

// GOOD - a value class owns the behavior; a raw String can't be mistaken for it
@JvmInline value class UrlPrefix(val value: String) {
  fun resolve(path: String): String = ...
}
```

Flow the wrapper type through the codebase, including as the field type on the owning `@Serializable` model — a `@Serializable @JvmInline value class` serializes inline as its wrapped value, so JSON keys are unchanged. (Distinct from the next rule: this one is about not extending *stdlib* types; the next is about not bloating data holders with *derived* helpers — a value class's own *defining* operation, like `resolve` here, rightly stays a member.)

## Keep Classes Minimal — Derived Behavior as Extensions
Data classes, value classes, response/DTO models, and UI state classes should hold only their primary data. Anything **derived** from that state — helper functions, computed convenience values — belongs **outside** the class body as a top-level extension function/property in the same file, not as a member.

```kotlin
// BAD - derived helper as a member bloats the data holder
data class OrderResponse(val lines: List<Line>, val status: String) {
  fun failedLineOrNull(): Line? = lines.firstOrNull { it.failed }
}

// GOOD - pure data holder; the derivation lives next to it
data class OrderResponse(val lines: List<Line>, val status: String)

internal fun OrderResponse.failedLineOrNull(): Line? = lines.firstOrNull { it.failed }
```

- **Match the member's effective visibility.** If a caller lives in another module, the extension must be `public` (no modifier) — `internal` only resolves same-module. The call site then needs an explicit `import <pkg>.<name>` (extension imports are per-symbol) unless caller and class share a package.
- **Caveat — eager-cached hot-path vals may stay members.** An extension property has no backing field, so it recomputes on every access. A derived `val` that is effectively part of the type's primary data *and* read on a hot path (e.g. a palette's alpha-tint tokens, computed once at construction and read pervasively during composition) should stay a member val. Apply the convention to behavioral derivations on data holders, not to palette/token data.

## Inject Dependencies Into a Class, Don't Thread Them Through Helpers
If a top-level helper takes repository/manager dependencies as positional args, and callers have to inject those deps just to pass them through, convert the helper into a DI-injected class. Callers then inject the wrapper instead of the leaf deps.

```kotlin
// BAD - every caller injects the leaf deps just to forward them
suspend fun submitOrder(orderRepository: OrderRepository, analytics: Analytics, cart: Cart): OrderId

// GOOD - a class owns the deps; callers inject it (annotate per your DI container)
@Inject @Singleton
class OrderSubmitter(
  private val orderRepository: OrderRepository,
  private val analytics: Analytics,
) {
  suspend fun submit(cart: Cart): OrderId { ... }
}
```

A class constructor-injected into a public class must itself be public, and so must the return types of its public methods (Kotlin's "public function exposes its internal parameter type" rule). Don't convert pure functions — extension utilities and pure transformations with no injectable dependency stay top-level.

## Comments Describe Code on Its Own Terms
Never reference an unrelated module, feature, or SDK by name in a file's comments or KDoc just because the code was modeled on it. When a file borrows a pattern from elsewhere, describe the *pattern* generically — not the other module's concrete type names.

```kotlin
// BAD - names another module's types; rots when that module changes
// Built like the sync module's RemoteClient + ClientFactory pair.

// GOOD - describes the pattern on its own terms
// expect interface bridged to platform code via an expect factory function.
```

Cross-module references in comments couple unrelated domains, go stale when the other module changes, and confuse readers who have no reason to know its internals. A generic framework/convention reference is fine; a specific unrelated-feature type name is not.

## Don't Fight the Formatter
A formatter like ktfmt (Google style) actively reformats certain patterns; don't waste edits "simplifying" them, because the next format run reverts the change and churns the diff:

- Single-statement `when` branches get braced: `is Foo -> doThing()` becomes `is Foo -> { doThing() }`.
- `?.let { return it }` chains stay expanded across lines even when the body is one expression.

These are formatter preferences, not simplification opportunities. What *can* be simplified safely (and survives formatting): extracting duplicated branches into helpers, inlining single-use locals, removing dead fields/params/imports, consolidating multi-line comments. When a reviewer flags a formatter-owned pattern, skip it with the rationale "formatter preference."

## KMP `expect class` Is Constructor-less
Declare `expect class` bodies **without a constructor**. Each `actual class` declares its own platform-specific primary constructor, where platform dependencies are injected, and is constructed only in per-platform DI providers (androidMain/iosMain) — never in commonMain.

**Never add a constructor parameter to an `expect class`** (in this pattern). The actuals' implicit primary constructor then fails to pair with it, producing a compile error like `Declaration must be marked with 'actual'` at the actual's constructor. (Kotlin *does* allow an `expect class` constructor when every `actual` declares a matching `actual constructor` — but keeping the expect no-arg and injecting platform deps on the `actual` keeps them out of common code. Common auto-fix trap: adding an injected dependency to the `actual` and "helpfully" mirroring it onto the `expect`.)

```kotlin
// commonMain - no constructor
expect class FileStore {
  suspend fun save(bytes: ByteArray, name: String)
}

// androidMain - platform deps on the actual constructor only
actual class FileStore(private val context: Context) {
  actual suspend fun save(bytes: ByteArray, name: String) { ... }
}
// + a per-platform DI provider: fun provideFileStore(context: Context) = FileStore(context)
```

Also: don't move a per-platform provider that builds an `expect class` into commonMain — commonMain can't call the platform constructor (`Expected class … does not have default constructor`).
