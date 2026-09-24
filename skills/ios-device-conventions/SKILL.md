---
name: ios-device-conventions
description: Use when working with a physical iOS device from the command line — installing or launching builds with `xcrun devicectl`, streaming logs, pulling crash reports or app-container files, driving the UI with WebDriverAgent (WDA) over plain HTTP without Appium, building or signing the WDA runner, recording on-device frames for jank/freeze/stutter reports, capturing device traffic with mitmproxy, or StoreKit sandbox testing via the App Store Connect API. Covers pymobiledevice3, the `.xctrunner` bundle-id signing trap, and `/wda/video` 60fps recording. Prevents simulator-based false verification, silently-wrong build artifacts, and misread capture results.
user-invocable: false
---

Machine-specific values — device UDID, team id, the WDA runner id, profile name, sandbox tester accounts — are deliberately not in this skill. Look for them in the user's own instructions before running anything below, and ask when they are missing.

Two shell rules every snippet depends on:
- `pip install --user` leaves `pymobiledevice3` off PATH. Snippets write it bare; call `~/Library/Python/<ver>/bin/pymobiledevice3` or `/usr/bin/python3 -m pymobiledevice3`. Bare `python3 -m` may resolve to Homebrew's Python and fail with `No module named pymobiledevice3`.
- Quote every argument containing `?`, `*` or `[...]` — URLs with query strings, `--include` patterns, bracketed API parameters. In zsh an unmatched glob aborts the whole command with `no matches found` before the program runs, which reads like a legitimate empty result.

Detail lives in reference files; load the one you need:
- `references/wda.md` — starting the WDA server, a dead runner, signing the runner, driving gotchas, watching the screen
- `references/measuring-frames.md` — jank/freeze measurement: 60fps XCTest recording, MJPEG, camera roll, GPU counters
- `references/network-capture.md` — mitmproxy against a device, and the StoreKit-pinning trap
- `references/storekit-sandbox.md` — sandbox testers, App Store Connect API and JWT signing, intro-offer and storefront traps
- `references/setup.md` — standing the whole stack up on a new Mac, account, or phone

## Verify on the Physical Device, Not the Simulator
Reproduce, investigate and verify on the real iPhone by default — not only for final sign-off. Camera and photo library, face detection, StoreKit and real network conditions all differ in the simulator, so a simulator repro can confirm or deny the wrong thing. If no device is connected, say so and ask rather than substituting a simulator or an Android build.

## Stream Logs Whenever the App Runs
The screen shows a generic symptom; backend 500s, purchase/verify failures and data-gated UI are only visible in logs. Both streams run until killed — start them in the background with output redirected to a file, then search the file.

```bash
# the app's own stdout — e.g. a networking layer's request/response lines
xcrun devicectl device process launch --device <UDID> --console <bundleId> > <scratch>/console.log 2>&1

# os_log, several processes interleaved in one stream
pymobiledevice3 syslog live -e "(<ProcessName>|storekitd|appstored|itunesstored)" > <scratch>/syslog.log
```

- A `print`/`println`/`NSLog` added ad hoc for diagnosis has not shown up in these streams in practice — don't spend a build round on one; lean on logging the app already emits.
- `--process-name` takes **one exact name**. For a multi-process union use `-e`/`--regex`, which matches the whole rendered line rather than the process field — anchor the pattern if a process name can also appear inside message bodies.
- `os_log` redacts URLs and bodies as `<private>`, but CFNetwork task summaries still expose `response_status` and `request_bytes`/`response_bytes` — enough to spot a failing call.
- Syslog output contains binary bytes: plain `grep` returns nothing, always use **`grep -a`**. The device clock can run seconds behind the Mac, so correlate by event order and log growth, not wall-clock.
- **`devicectl --console`, WDA's xcuitest start and syslog share one device tunnel and disturb each other.** Start WDA first and syslog after it — starting WDA stalls a running syslog stream — and detach `--console` before taking WDA screenshots, which fail while it is attached.

## `devicectl` Essentials
`xcrun devicectl` is Apple's own device CLI (CoreDevice). It is the only tool here that reaches **system-daemon containers** (e.g. `com.apple.testmanagerd`); pymobiledevice3's house_arrest route only reaches installed apps and fails with `AppNotInstalledError`.

```bash
xcrun devicectl device info files --device <UDID> --domain-type appDataContainer \
  --domain-identifier <bundleId> --username mobile
xcrun devicectl device copy from --device <UDID> --domain-type appDataContainer \
  --domain-identifier <bundleId> --user mobile --source "Documents/x.json" --destination /tmp/x.json
```

- `info files` takes `--username`, `copy from`/`copy to` take `--user`. The wrong one exits 64, and redirecting stdout swallows the error — pipe to `grep` instead.
- **There is no delete.** To reclaim space, `copy to` an empty file over the target.
- A dev-signed app's whole sandbox is readable and writable, which is the cheap way past a slow precondition. A DataStore Preferences file is plain protobuf (`PreferenceMap{map<string,Value>=1}`, `Value{bool=1, string=5}`), so a flag is a one-byte flip. Kill the app first — it overwrites the file from memory on its next write.

## Install and Launch a Debug Build by Default
```bash
xcodebuild -quiet -project <App>.xcodeproj -scheme <Scheme> -configuration Debug \
  -destination 'id=<UDID>' -allowProvisioningUpdates -derivedDataPath <scratch>/dd build
xcrun devicectl device install app --device <UDID> "<scratch>/dd/Build/Products/Debug-iphoneos/<App>.app"
xcrun devicectl device process launch --device <UDID> --console <bundleId>
```

`-quiet` prints only warnings and errors, so judge the build by its exit code — don't pipe it through `tail` (see gradle-conventions on pipes masking exit codes). Debug is signed with `get-task-allow = true`, so `devicectl … launch` works and `--console` streams stdout. Use an ad-hoc IPA only when the ad-hoc artifact itself is under test: its `get-task-allow = false` makes `devicectl … launch` fail ("invalid code signature… not explicitly trusted") — don't chase that, **launch it through WDA** (`POST /session/<sid>/wda/apps/launch {"bundleId":"<id>"}`), which doesn't attach as a debugger.

- Installing over an existing app keeps its container; uninstall first when a clean container is the point.
- **Launch denied after a reinstall** is usually certificate trust, not the network: uninstalling the last app signed by a development cert drops the device's trust entry. Re-trust in Settings → General → VPN & Device Management. Check provisioning with `security cms -D -i <App>.app/embedded.mobileprovision` (`ProvisionedDevices`, `ExpirationDate`).

## Crash Reports
`pymobiledevice3 crash ls` (`ls`, not `list`), then `crash pull <outdir> --erase`. An `.ips` file is two concatenated JSON documents — split on the first newline. For permission crashes read `termination`, not `exception`: `termination.namespace == "TCC"` names the missing Info.plist usage key.

## Drive the UI with WebDriverAgent over Plain HTTP
No Appium needed: WDA is an HTTP server inside an XCUITest runner on the phone, and `curl` is the whole client.

```bash
pymobiledevice3 developer dvt xcuitest <runner-id> &    # the installed ….xctrunner id
pymobiledevice3 usbmux forward 8100 8100 &
curl -s http://localhost:8100/status
```

- **Recent WDA (verified on 16.12.10) no longer auto-creates a session.** `/status` returns `sessionId: null`; `POST /session {"capabilities":{"alwaysMatch":{"platformName":"iOS"}}}` first, then use the returned id for every `/session/<id>/…` call.
- Taps and swipes are W3C actions at `POST /session/<id>/actions`. `GET /source?format=json` returns the accessibility tree with every rect **already in points** — measure layout from rects, not from screenshot pixels.
- **Confirm what is on screen before acting on it.** Before any tap, and before trusting a label search or a capture, check in the current tree which app is in front and which screen it's on, using a label only that screen has. The foreground can change under you — another session, an app switch, the lock screen, a consent sheet — and a stale coordinate lands on another app's control. Locate targets by label and recompute geometry from the current tree.
- **Never enter a password, passcode or any other credential through automation.** Drive up to the prompt, hand it to the human, then carry on.
- **Never expose 8100 (or the MJPEG port 9100) beyond localhost.** WDA has no authentication: anything that can reach the port can screenshot, read and drive the phone. The legacy `iproxy 8100 8100` form binds every interface; the `pymobiledevice3` forwarder binds loopback by default.
- **Check ownership before claiming the device.** If `/status` answers, something is already driving the phone. Find the owner with `pgrep -fl "xcuitest|xcodebuild"` — the fastest start route leaves a `pymobiledevice3 … dvt xcuitest` process, so grepping for `xcodebuild` alone reports a busy device as free. Ask the owning session before interrupting, and ask again each time: permission to interrupt describes the moment it was given, not the next ten minutes.

Starting from source, a dead runner, signing, and driving gotchas: `references/wda.md`.

## Measure Frames Instead of Reasoning About Jank
For "it stutters / freezes / snaps", record and measure. Default to WDA's native XCTest recording (`/wda/video`, ~60fps at native resolution, scriptable), and read **inter-frame timestamp gaps**, never `avg_frame_rate` — the recorder emits no frames while the screen is static, so a gap *is* a freeze. Full recipe and the other capture tiers: `references/measuring-frames.md`.
