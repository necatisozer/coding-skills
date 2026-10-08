# KMP and Gradle Tooling

## Build iOS After a Library Bump
Kotlin/Native links klibs with **partial linkage**, which is always on. A symbol that a library expects but no longer finds does not fail the build: the call becomes an `IrLinkageError` at runtime, at the first call site. So a mixed artifact family (two `ktor-client-*` versions) or a third-party Compose library built against another Compose version can compile on Android and crash only on iOS.

- After you bump or add a library, link the iOS framework too, not only Android. One debug arch is enough: `./gradlew :<framework-module>:linkDebugFrameworkIosSimulatorArm64`.
- Read the link output for partial-linkage warnings, such as `can not be called: No function found for symbol` or `No property accessor found`. `-Xpartial-linkage-loglevel=error` turns them into build errors.
- Check that every artifact of one family resolves to the same version.

## KMP CocoaPods: Order Before `pod install`
With `kotlin("native.cocoapods")`, Gradle's own `podInstall` task orders these steps itself. A raw `pod install` (from a script or a fastlane lane) does not, so after a `clean`:

- Run `./gradlew :<module>:generateDummyFramework` before `pod install`.
- Run `./gradlew :<module>:syncPodComposeResourcesForIos` before `pod install`, with the same `PLATFORM_NAME`/`ARCHS`/`CONFIGURATION` env vars as `syncFramework`. CocoaPods reads `build/compose/cocoapods/compose-resources/` at `pod install` time, so an empty folder leaves the Compose resources out of the app.

## SwiftPM Import: Stale Precompiled Modules
With the KMP SwiftPM import (`swiftPMDependencies`), an Xcode or SDK update can make the next build fail with `has been modified since the module file … was built`. That is a stale precompiled-module cache, not an incompatibility. Clear Xcode's DerivedData (Clean Build Folder) and delete only `build/kotlin/swiftPMXcodeDumps`. Do not run `./gradlew clean` for this, because it also deletes `build/kotlin/swiftPMCheckouts`, which can take several GB per repo to download again.

## The Daemon JVM Comes from `gradle-daemon-jvm.properties`
If `gradle/gradle-daemon-jvm.properties` exists, its criteria take precedence over `JAVA_HOME` and `org.gradle.java.home`. Change the daemon JVM with `./gradlew updateDaemonJvm`, not by changing `JAVA_HOME`.

## Host Tests in the KMP `androidLibrary` Plugin
A module on `com.android.kotlin.multiplatform.library` (`androidLibrary {}`) has no `testDebugUnitTest`. Host tests are opt-in (`withHostTest {}`), live in `androidHostTest`, and run with `:<module>:testAndroidHostTest`.

## IDE Sync Needs Gradle 8.8 or Later
Android Studio's Kotlin Multiplatform plugin injects an init script that calls `gradle.lifecycle`, an API added in Gradle 8.8. On an older wrapper the IDE sync fails with `Could not get unknown property 'lifecycle'`, while the command-line build still passes. So a green CLI build proves nothing about IDE sync.

## Iterating on a Library Through `mavenLocal`
Publish a new version (a unique suffix or a `-SNAPSHOT`) for every round, because a consumer can keep using a copy of the same version that it cached from a remote repository. Keep `mavenLocal()` out of committed builds.

- A build-logic that the library includes with `includeBuild` is a separate build. Publish it with its own `publishToMavenLocal`.

## Dependency Updates Report
Use the versions plugin `io.github.ben-manes.versions` 0.55.0 or later. It supports parallel builds and the configuration cache, so `./gradlew dependencyUpdates` needs no extra flags. Older versions fail on Gradle 9 with `Parallel project execution is not supported`.
