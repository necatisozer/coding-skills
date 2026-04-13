---
name: kotlin-serialization-conventions
description: Enforces kotlinx.serialization patterns when writing @Serializable data classes, JSON response/request models, or API enum-like fields. Prevents redundant defaults.
user-invocable: false
paths: "**/*.kt"
---

## No Default Values for Response Fields
Don't add `= null` or other defaults to `@Serializable` data class fields deserialized from API responses — the serializer already handles missing/invalid fields via its configuration. Adding defaults is redundant noise. Default values are fine for request models constructed in code.

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
