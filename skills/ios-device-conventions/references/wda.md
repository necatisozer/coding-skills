# WebDriverAgent: Starting, Signing, Driving

WDA is an XCUITest bundle. iOS only runs one inside a *runner host app*, which Xcode generates by appending `.xctrunner` to the test target's bundle id. Two ids, never to be confused:
- **base id** — what you build with (`PRODUCT_BUNDLE_IDENTIFIER`), e.g. `com.example.wda`
- **runner id** — base id + `.xctrunner`, e.g. `com.example.wda.xctrunner`; what gets installed, launched, and registered as the App ID

## Three Ways to Start the Server
Fastest first. None needs Xcode's GUI.

1. **Installed runner, no source:** the two commands in SKILL.md (`dvt xcuitest <runner-id>`, then `usbmux forward 8100 8100`); `/status` answers in ~12 s. `devicectl device process launch` on the runner starts the app but **not** the HTTP server — only the xcuitest route attaches the test plan. The iOS 17+ developer tunnel opens in-process, with no root.
2. **Built runner, no source:** a hand-written `.xctestrun` (`TestHostPath`, `TestBundlePath`, `IsUITestBundle`, `ProductModuleName`, `UITargetAppPath` pointed at the runner app itself — mandatory — plus `USE_PORT`/`MJPEG_SERVER_PORT` env) run with `xcodebuild test-without-building -xctestrun <file> -destination "id=<UDID>"`, left running.
3. **From source:** shallow-clone `appium/WebDriverAgent` at a pinned tag, then either run `xcodebuild … test` in the background (it *is* the server), or — better when another session is using the phone — build without touching the device and install afterwards:

```bash
git clone --depth 1 --branch <tag> https://github.com/appium/WebDriverAgent.git wda-src
xcodebuild -quiet -project wda-src/WebDriverAgent.xcodeproj -scheme WebDriverAgentRunner \
  -destination 'generic/platform=iOS' -xcconfig ~/.config/wda/wda.xcconfig \
  -derivedDataPath <scratch>/wda-dd build-for-testing
xcrun devicectl device install app --device <UDID> \
  <scratch>/wda-dd/Build/Products/Debug-iphoneos/WebDriverAgentRunner-Runner.app
# then route 1 to launch it
```

With the dedicated profile already installed locally, no network flags are needed. If it still has to be downloaded and no Apple ID is signed into Xcode, add `-allowProvisioningUpdates -authenticationKeyPath <AuthKey_ID.p8> -authenticationKeyID <ID> -authenticationKeyIssuerID <issuer>` — for a manually signed target this only downloads missing profiles.

## When the Runner Dies
It dies on its own sometimes: killed for memory, or `/status` stays 200 while actions fail with "Not authorized for performing UI testing actions". `/status` alone doesn't prove it can drive the phone — probe with a harmless W3C `pointerMove` with no press. Before relaunching, rule out an attached `devicectl … --console` (SKILL.md › Stream Logs) and check the runner is yours (SKILL.md › ownership).

## Signing the Runner

### Never Put `.xctrunner` in `PRODUCT_BUNDLE_IDENTIFIER`
Xcode appends it. Setting `com.example.wda.xctrunner` produces `com.example.wda.xctrunner.xctrunner` — a **second** runner that installs beside the real one. Route 1 keeps launching the old app, `/status` reports the old build, and the upgrade looks like it silently failed. After every build, check what you made:

```bash
/usr/libexec/PlistBuddy -c "Print CFBundleIdentifier" <App>.app/Info.plist
security cms -D -i <App>.app/embedded.mobileprovision   # Name, Entitlements.application-identifier
```

### A Team Wildcard Profile Accepts a Wrong Bundle Id Silently
Automatic signing (`-allowProvisioningUpdates`) matches profiles against the **target's** `PRODUCT_BUNDLE_IDENTIFIER`, while a dedicated profile covers the **generated host** id — so it never matches, and signing falls back to the team wildcard (`<TEAM_ID>.*`). The wildcard accepts any bundle id, which is why the doubled id above signs and installs instead of failing.

Profiles live in `~/Library/Developer/Xcode/UserData/Provisioning Profiles` since Xcode 14. `~/Library/MobileDevice/Provisioning Profiles` is the legacy path; searching only there concludes a profile is missing when it isn't.

### Pin the Dedicated Profile with a Per-Target xcconfig
Command-line build settings apply to **every** target, and `WebDriverAgentLib` fails with *"does not support provisioning profiles"* if one is specified. An `.xcconfig` also applies globally, so key each setting on `$(TARGET_NAME)`: it resolves only for the runner, and every other target sees an empty value, which Xcode treats as unset.

```
DEVELOPMENT_TEAM = <TEAM_ID>
CODE_SIGN_IDENTITY = Apple Development

WDA_STYLE_WebDriverAgentRunner = Manual
CODE_SIGN_STYLE = $(WDA_STYLE_$(TARGET_NAME):default=Automatic)

WDA_PROFILE_WebDriverAgentRunner = <dedicated profile name>
PROVISIONING_PROFILE_SPECIFIER = $(WDA_PROFILE_$(TARGET_NAME))

WDA_BID_WebDriverAgentRunner = <base id — without .xctrunner>
PRODUCT_BUNDLE_IDENTIFIER = $(WDA_BID_$(TARGET_NAME):default=$(inherited))
```

- **`-xcconfig` wins over command-line settings for every key the file sets**, so extra signing flags on the command line are redundant, not dangerous. Check the resolved values with `-showBuildSettings`.
- `PRODUCT_BUNDLE_IDENTIFIER` is keyed on purpose: set globally it would rewrite every target's id.
- The suffix after each `WDA_*_` must match the target name exactly. A typo yields an empty value, which reads as unset and falls back to the wildcard without any error.
- Keep the file outside the clone (e.g. `~/.config/wda/`) so it survives re-cloning — unlike a `fastlane run update_code_signing_settings` patch, which lives in the throwaway clone and must be re-applied on every upgrade.
- Confirm with the PlistBuddy / `security cms` check above: the embedded profile should be the dedicated one, with app-id `<TEAM_ID>.<runner-id>`.

## Driving Gotchas
- **Every `POST /session/<id>/appium/settings` body must be wrapped: `{"settings":{…}}`.** WDA reads `arguments["settings"]`; an unwrapped body is accepted and ignored without any error.
- **A W3C drag that starts on a tappable element fires its `onClick`** — once, that started a paid action. Start drags on inert areas.
- **Empty accessibility labels:** off-screen Compose content often has none, so judge by geometry — after confirming you are reading the right app's tree (SKILL.md › confirm what is on screen); a zero-hit search against the wrong app looks exactly like "unlabelled".
- **Keep synthetic tap presses short** — tens of milliseconds. A longer press can be classified as a long-press or drag: a map view dropped an 80 ms press that a 40 ms one landed.
- **Out-of-process pickers** (PHPicker and the like) ignore synthetic taps until `appium/settings {"settings":{"defaultActiveApplication":"auto"}}`.
- **Lock screen:** a tree with a blank app name and Flashlight/Camera buttons. `POST /session/<id>/wda/unlock` wakes and swipes when no passcode is set.

## Watching the Screen
The runner's MJPEG server (port 9100) serves `multipart/x-mixed-replace` with `image/jpeg` parts, which any browser renders natively:

```bash
pymobiledevice3 usbmux forward 9100 9100 &
open http://localhost:9100
```

Tune it per session through `appium/settings` (`mjpegServerFramerate`, `mjpegServerScreenshotQuality`, `mjpegScalingFactor` — wrapped, as above). They reset with every new WDA session; re-apply them each time. Everything rides the USB cable, so this works with the phone in airplane mode.

### Relaying to Other Players
Transcoding to H.264 only pays off when a player needs WebRTC, HLS or RTSP; for a browser on the same Mac the MJPEG page above is cheaper. When it is needed, publish into a media server such as mediamtx:

```bash
ffmpeg -f mjpeg -use_wallclock_as_timestamps 1 -i http://localhost:9100 \
  -c:v libx264 -preset veryfast -tune zerolatency -r 30 -g 30 -b:v 4000k -pix_fmt yuv420p \
  -f rtsp -rtsp_transport tcp rtsp://localhost:8554/<path>
```

- `-use_wallclock_as_timestamps 1` because MJPEG carries no timestamps; `-g` equal to the frame rate so a player joining mid-stream gets a keyframe within a second.
- **Bind the media server to loopback, turn off every protocol no player uses, and verify with `lsof -nP -a -p <pid> -i` that nothing listens on `*`.** Otherwise anyone on the network can watch the phone, purchase sheets and test accounts included. Stock configs rarely do this: mediamtx's listens on every interface and enables RTMP, SRT, MoQ and RTSP over UDP. There it takes each `*Address` set to `127.0.0.1:<port>`, `rtspTransports: [tcp]`, `webrtcLocalUDPAddress: 127.0.0.1:8189`, and `webrtcIPsFromInterfaces: false` with `webrtcAdditionalHosts: [127.0.0.1]`.
- Run it on demand and stop the forwarder, ffmpeg and the server afterwards — never as a login item.
