---
name: molecule-testing-conventions
description: Use when testing a @Composable effect or Compose state from commonTest in a project that already depends on molecule (app.cash.molecule) — launchMolecule, RecompositionMode.Immediate, snapshot notifications after state changes, and virtual time for effect timers.
user-invocable: false
paths: "**/commonTest/**/*.kt,**/*Test.kt"
---

## Use Molecule Only Where It Is Already a Dependency
In a project that already has molecule, you can drive a `@Composable` effect straight from `commonTest` with no new dependency, because `molecule-runtime` and `kotlinx-coroutines-test` are already on the test classpath. Look for `app.cash.molecule` in the version catalog or the build files first. This catches real defects before any device run.

If the project does not use molecule, do not add it to write a test. Ask the user first, and test the logic another way until they decide.

## Launch in `backgroundScope` With `RecompositionMode.Immediate`
Use `scope.backgroundScope.launchMolecule(RecompositionMode.Immediate) { … }`, and hardcode `Immediate`. The Android actual of a `recompositionMode` expect val is `ContextClock`, which hangs without a frame clock.

## Send Snapshot Notifications After Every State Change
After every state mutation that the test makes, call `Snapshot.sendApplyNotifications()` and then `runCurrent()`. Molecule recomposes off snapshot notifications, and tests must send them. A missing pair is a silent no-op, not a failure.

## Advance an Explicit Duration for Effect Timers
`advanceUntilIdle()` does not run the effect's timers. The molecule lives in `backgroundScope`, which the scheduler treats as never busy. Advance an explicit `Duration` derived from the production constant (make the constant `internal`).

```kotlin
// BAD
backgroundScope.launchMolecule(recompositionMode) { rememberHintVisible(trigger) } // ContextClock on Android: hangs without a frame clock
trigger = true                // no snapshot notification: the composition never sees the change
advanceUntilIdle()            // runs no effect timer: backgroundScope never counts as busy

// GOOD
val visible = backgroundScope.launchMolecule(RecompositionMode.Immediate) { rememberHintVisible(trigger) }
trigger = true
Snapshot.sendApplyNotifications()
runCurrent()
assertTrue(visible.value)
advanceTimeBy(HINT_DURATION)  // the production constant, made `internal`
Snapshot.sendApplyNotifications()
runCurrent()
assertFalse(visible.value)
```

## Android Host Tests That Run Compose Code
They need one Gradle setting, and `android-conventions` has it.
