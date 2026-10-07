---
name: compose-effect-testing
description: "Use when testing a @Composable effect or Compose state logic from commonTest in a project that already depends on molecule (app.cash.molecule): launchMolecule in backgroundScope, RecompositionMode.Immediate, Snapshot.sendApplyNotifications with runCurrent after each state change, advancing virtual time for effect timers (advanceUntilIdle does not run them)."
user-invocable: false
paths: "**/commonTest/**/*.kt, **/*Test.kt"
---

# Testing Compose effects with molecule

In a project that already has molecule, you can drive a `@Composable` effect straight from `commonTest` with no new dependency, because `molecule-runtime` and `kotlinx-coroutines-test` are already on the test classpath. Look for `app.cash.molecule` in the version catalog or the build files first. This catches real defects before any device run.

If the project does not use molecule, do not add it to write a test. Ask the user first, and test the logic another way until they decide.

- Use `scope.backgroundScope.launchMolecule(RecompositionMode.Immediate) { … }`, and hardcode `Immediate`. The Android actual of a `recompositionMode` expect val is `ContextClock`, which hangs without a frame clock.
- After every state mutation that the test makes, call `Snapshot.sendApplyNotifications()` and then `runCurrent()`. Molecule recomposes off snapshot notifications, and tests must send them. A missing pair is a silent no-op, not a failure.
- **`advanceUntilIdle()` does not run the effect's timers.** The molecule lives in `backgroundScope`, which the scheduler treats as never busy. Advance an explicit `Duration` derived from the production constant (make the constant `internal`).
- **Android host tests that run Compose code need one Gradle setting.** The `android-conventions` skill has it.
