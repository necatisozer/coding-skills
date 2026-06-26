---
name: gradle-conventions
description: Use when running or verifying Gradle builds — capturing pass/fail correctly from a gradle invocation (shell pipe exit-code masking), and the Kotlin Multiplatform iOS resource pipeline serving stale composeResources content after a content-only edit. Prevents false "build passed" claims and shipping stale iOS resources.
user-invocable: false
---

## Never Pipe Gradle Through `tail`/`head` for Pass/Fail
A shell pipeline's exit code is the **last** command's. `./gradlew … | tail -n 80` reports `tail`'s exit code (`0`), so a real `BUILD FAILED` is seen as exit `0` and reads as success.

```bash
# BAD - tail masks gradle's exit code; BUILD FAILED looks like success
./gradlew :app:compileKotlin | tail -n 80

# GOOD - redirect (no pipe), then grep for the literal result
./gradlew :app:compileKotlin > build.log 2>&1
grep -nE "BUILD (SUCCESSFUL|FAILED)|^e: " build.log
```

Always confirm the literal `BUILD SUCCESSFUL` string, not just the reported exit code, before claiming a build passed. If you must pipe, set `-o pipefail` (works in bash and zsh), or capture the first command's status — bash `${PIPESTATUS[0]}`, zsh `${pipestatus[1]}` — or append `; echo "EXIT=$?"` to a non-piped invocation.

## CMP iOS Resource Pipeline Serves Stale Content
After a **content-only edit** to a file under `composeResources/files/` (no rename, no add/remove), the Compose Multiplatform **iOS** resource pipeline can keep shipping the OLD content while reporting `BUILD SUCCESSFUL`: the `assembleIos*MainResources` tasks wrongly stay `UP-TO-DATE` even though the prepared resources refreshed. Every downstream artifact then hashes the stale output and is legitimately up-to-date. The **Android** pipeline picks the change up correctly, so the staleness hides behind green Android builds — and even behind a green iOS framework *link* task, which does not cover the resource sync (the Xcode-invoked `syncFramework` flow does).

After editing any bundled composeResources file, force the chain:

```bash
./gradlew :<module>:assembleIosSimulatorArm64MainResources --rerun \
          :<module>:assembleIosArm64MainResources --rerun
PLATFORM_NAME=iphonesimulator ARCHS=arm64 CONFIGURATION=Debug ./gradlew :<framework-module>:syncFramework
```

(`syncFramework` infers the target arch from the `PLATFORM_NAME`/`ARCHS`/`CONFIGURATION` env vars — without them it fails late on arch inference. `<module>` is whichever module owns the changed composeResources; `<framework-module>` must depend on it so the synced framework picks up the refreshed bytes.) Then verify the new bytes actually landed — grep the edited file inside the framework's synced `compose-resources/` directory before trusting any iOS build.
