# Standing the Stack Up on a New Mac, Account or Phone

Budget ~30 minutes, mostly Xcode downloading.

1. **Mac.** Xcode (brings `xcodebuild` and `devicectl`), then `/usr/bin/python3 -m pip install --user pymobiledevice3` and `brew install ffmpeg`. Add mitmproxy, mediamtx or fastlane only if traffic capture, WebRTC streaming or release lanes are needed. `libimobiledevice`/`libusbmuxd` are not required — pymobiledevice3 covers syslog, crash reports, AFC, the iOS 17+ developer tunnel and port forwarding.
2. **Phone.** **Developer Mode must be on (iOS 16+) or nothing works:** `pymobiledevice3 amfi enable-developer-mode`, reboot, confirm `pymobiledevice3 amfi developer-mode-status` prints `true`. Plug in and tap Trust. Then **Settings → Developer → Enable UI Automation** — a separate switch, off by default, without which WDA cannot drive the device. For webview work also turn on Settings → Apps → Safari → Advanced → Web Inspector and Remote Automation. Confirm with `pymobiledevice3 usbmux list`.
3. **Account.** A paid Apple Developer membership is required: a free Personal Team's profiles expire after 7 days, after which the runner stops launching — easy to mistake for an ordinary runner death. Four artifacts: the team id; an App Store Connect API key (`.p8`, key id, issuer id — Users and Access → Integrations); a registered runner id; and a development profile that includes the phone (or let `-allowProvisioningDeviceRegistration` register it on first build).
4. **Build.** Write the per-target xcconfig from `wda.md` with your team id, profile name and base id, clone WDA at a pinned tag, and build and install it (route 3 in `wda.md`). Trust the development certificate once on the phone: Settings → General → VPN & Device Management.
5. **Verify.** `/status` answers `ready`; create a session first (SKILL.md › Drive the UI); confirm the installed runner id (`wda.md` › the `.xctrunner` trap).

Appium is not needed for any of this, and on iOS 18+ its XCUITest driver needs a root-privileged TUN tunnel (`appium-ios-remotexpc`) that this stack avoids.
