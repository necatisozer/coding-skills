# Measuring Jank, Freezes and Stutter on Device

Measure frames; don't reason about the code. Tiers, best first — MJPEG is the cheapest but the weakest.

## 1. XCTest Screen Recording via `/wda/video` (Default)
Native, device-side, scriptable, full resolution.

```bash
curl -s -X POST http://localhost:8100/session/<sid>/wda/video/start \
  -H 'Content-Type: application/json' -d '{"fps":60,"codec":0}'   # codec 0 = h264, 1 = HEVC; returns a uuid
# … exercise the app …
curl -s -X POST http://localhost:8100/session/<sid>/wda/video/stop -H 'Content-Type: application/json' -d '{}'

xcrun devicectl device copy from --device <UDID> --domain-type appDataContainer \
  --domain-identifier com.apple.testmanagerd --user mobile \
  --source "tmp/Attachments/<uuid>" --destination rec.mov
```

- The file is named by the `uuid` that `start` returned, and lives in **`tmp/Attachments`, not `Attachments`** — listing the plain one fails with `CoreDevice.ActionError error 3`. If the copy fails, list `tmp/Attachments` with `devicectl device info files … --username mobile --subdirectory tmp/Attachments`.
- **The capture is content-adaptive:** ~60fps while the screen changes, and *no frames at all* while it is static. So **`avg_frame_rate` is meaningless** — a half-idle run reports ~30fps while almost every gap is 16.7 ms.
- **Read the gaps between timestamps instead.** A gap is a motionless period, stated outright: a 1.697 s gap is a 1.697 s freeze. Read `packet=` timestamps, not `frame=` — the same values once sorted, but container-only (0.1 s vs 12.7 s of decoding on a 147 MB file):

```bash
ffprobe -v error -select_streams v:0 -show_entries packet=pts_time -of csv=p=0 rec.mov \
  | tr -d ',' | sort -n | awk 'NR>1{printf "%.4f\n", $1-p} {p=$1}' | sort -rn | head   # largest gaps first
```

- Size scales with motion, not duration: ~147 MB for 62 s half-idle, ~4 s to pull over USB. Reclaim the device space afterwards as in SKILL.md › `devicectl` Essentials.
- Recorded end-to-end on WDA 16.1.7; the endpoints are also present in 16.12.10.

## 2. WDA MJPEG Stream (Live, Coarse)
Its only edge left is being real-time. It delivers ~28fps regardless of the 60 requested, so a one-frame jump or a ~70 ms hitch is below its resolution — trust it only past ~150 ms. To read it programmatically, split on JPEG SOI/EOI and stamp each frame on arrival: consecutive byte-identical frames mean nothing moved. Duplicates also occur naturally when the source content's own frame rate is below the capture rate.

## 3. Camera-Roll Hand Recordings
True 60fps, but manual. `pymobiledevice3 afc ls /DCIM/100APPLE`, then `afc pull`; screen recordings are the highest-numbered `IMG_*.MP4`. When a recording repeats frames while the screen is static, ffmpeg's `freezedetect` prints only the freezes — a handful of lines instead of one per frame:

```bash
ffmpeg -hide_banner -an -i <IMG>.MP4 -vf freezedetect=n=-60dB:d=0.1 -map 0:v -f null - 2>&1 \
  | grep -oE "freeze_(start|duration|end): [0-9.]+"
```

`d` is the shortest freeze reported. `freezedetect` needs repeated frames, so it misses the gaps in a content-adaptive `/wda/video` recording — read timestamp gaps there. For per-frame change magnitude, `-vf "tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-"` writes one value per frame (`YAVG=0` is a static frame); redirect it to a file, and keep `file=-`, which is mandatory once `-loglevel error` is set.

## 4. GPU Counters
`pymobiledevice3 developer dvt graphics --userspace` — one sample per second with `CoreAnimationFramesPerSecond` and `Renderer Utilization %`. Answers "is this expensive", not "when did it hitch".

## Reproduction Gotchas
- Media caches to disk after first play, so a download-caused freeze only reproduces on a cold cache — uninstall and reinstall between runs, and script the walk back to the start screen.
- A consent sheet or other overlay can draw over the screen under test — confirm the screen (SKILL.md › confirm what is on screen) before trusting any capture.
