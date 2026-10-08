# Faking the Device Location
On iOS 17 and later, pymobiledevice3 sets a device-wide location over DVT:

```bash
pymobiledevice3 developer dvt simulate-location set --udid <UDID> -- <lat> <lon>
pymobiledevice3 developer dvt simulate-location play --udid <UDID> route.gpx
pymobiledevice3 developer dvt simulate-location clear --udid <UDID>
```

- **`set` and `play` never exit on their own.** They wait for SIGINT or SIGTERM, and `play` keeps holding the last point of the route. Run them like the log streams in SKILL.md (background, output to a file), and stop them by PID.
- **Run `clear` afterwards.** It is the command that stops the simulation, so do not rely on killing `set` or `play` to end it.
- With two phones, pass `--udid` to every call, and stop only the process for that UDID. A bare `pkill` also ends the other phone's replay.
