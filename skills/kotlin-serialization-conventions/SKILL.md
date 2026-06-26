---
name: kotlin-serialization-conventions
description: Enforces kotlinx.serialization patterns when writing @Serializable data classes, JSON response/request models, or API enum-like fields. Prevents redundant defaults. Also covers throwing typed exceptions for required-but-nullable response fields, and avoiding speculative forward-compat (stray @JsonNames, dead default-null params).
user-invocable: false
paths: "**/*.kt"
---

## No Default Values for Response Fields
Don't add a redundant `= null` to a nullable `@Serializable` field deserialized from an API response — when the JSON is configured with `explicitNulls = false`, a missing field already decodes to `null` (and an explicit JSON `null` does too, by nullable semantics), so the default is just noise. Default values are fine for request models constructed in code. (Exception: a *non-nullable* collection field needs `= emptyList()` to tolerate a missing-or-null array — with `coerceInputValues = true`, a present `null` is then coerced to that `emptyList()` default. See No Speculative Forward-Compat below.)

```kotlin
// GOOD - response model: no defaults
@Serializable
data class Article(
  val title: String?,
  val imageUrl: String?,
)

// BAD - response model with unnecessary defaults
@Serializable
data class Article(
  val title: String? = null,
  val imageUrl: String? = null,
)

// GOOD - request model: defaults for optional fields
@Serializable
data class SearchRequest(
  val query: String,
  val page: Int? = null,
)
```

## Value Classes for API Enum-Like Fields
Use `@JvmInline value class` instead of `enum class` for JSON fields with a set of known values. Define known values in a companion object. This allows unknown values from the API without breaking deserialization.

```kotlin
@JvmInline
@Serializable
value class SortOrder(val value: String) {
  companion object {
    val Newest = SortOrder("newest")
    val Popular = SortOrder("popular")
    val Trending = SortOrder("trending")
  }
}
```

## Typed Exceptions for Required-but-Nullable Response Fields
If a response field is declared nullable but callers treat it as required, do **not** enforce it with `requireNotNull`/`require` — those throw `IllegalArgumentException`, a generic type that collapses into the catch-all bucket alongside decoder failures and programmer bugs. That makes backend contract violations invisible in telemetry, where the exception's `simpleName` is typically the classifier.

Introduce a small typed exception and throw it at the boundary:

```kotlin
class MalformedResponseException(message: String) : RuntimeException(message)

val orderId = response.orderId
  ?: throw MalformedResponseException("createOrder: missing orderId")
```

The caller's existing catch-and-log block then records a distinct, meaningful `error_type` even though the UI shows the same generic error. Worth it even if the type only extends `RuntimeException(message)` — the type name alone is the telemetry win. (Relatedly, when classifying a throwable for analytics, give an unnamed/anonymous throwable a real fallback label rather than an empty string — empty values get dropped by analytics backends.)

## No Speculative Forward-Compat
Match the wire format exactly; don't hedge against imagined future changes.

- Write **one** `@SerialName` that matches the JSON spelling. No `@JsonNames` (and the `@OptIn`/import it drags in) for a snake_case/camelCase variant the backend has never sent. If the spelling actually changes later, a one-line annotation change at that moment costs the same.
- When you delete the only producer of a value, delete the param/field/threading that received it too — don't leave a default-`null` route param or a dead field "for a future entry point" that isn't being designed now.

Not speculative (these are fine): companion constants documenting known JSON values on a value class; `= emptyList()` on a non-nullable `List<T>` response field to tolerate a missing array. And **preserve wire-format types you've spoken before** even if the current client doesn't construct them — a request/response type that documents a real server contract is backward-compat, not speculation. The line: hedging a protocol you don't speak yet is speculative; preserving one you've spoken is correct.
