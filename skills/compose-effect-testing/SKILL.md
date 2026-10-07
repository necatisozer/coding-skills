---
name: compose-effect-testing
description: "Use when testing a @Composable effect or Compose state logic from commonTest with molecule: launchMolecule in backgroundScope, RecompositionMode.Immediate, Snapshot.sendApplyNotifications with runCurrent after each state change, advancing virtual time for effect timers (advanceUntilIdle does not run them), and the Android host test isReturnDefaultValues trap."
user-invocable: false
paths: "**/commonTest/**/*.kt, **/*Test.kt"
---

# Testing Compose effects with molecule

You can drive a `@Composable` effect straight from `commonTest` with no new dependency, where `molecule-runtime` and `kotlinx-coroutines-test` are already on the test classpath. This catches real defects before any device run.

- Use `scope.backgroundScope.launchMolecule(RecompositionMode.Immediate) { … }`, and hardcode `Immediate`. The Android actual of a `recompositionMode` expect val is `ContextClock`, which hangs without a frame clock.
- After every state mutation that the test makes, call `Snapshot.sendApplyNotifications()` and then `runCurrent()`. Molecule recomposes off snapshot notifications, and tests must send them. A missing pair is a silent no-op, not a failure.
- **`advanceUntilIdle()` does not run the effect's timers.** The molecule lives in `backgroundScope`, which the scheduler treats as never busy. Advance an explicit `Duration` derived from the production constant (make the constant `internal`).
- **Android host tests need `isReturnDefaultValues = true`.** Without it, the Compose runtime's `android.os.Trace.beginSection` throws "not mocked" on *every* composition. The report blames `android.util.Log`, but that is only the second throw, raised while it logs the first. The iOS simulator target has neither problem, so a green iOS run proves nothing about Android. Run both.
