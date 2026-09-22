# Capturing a Device's Network Traffic

**Clear the device's Wi-Fi proxy before any paywall or network testing.** A proxy still pointed at a mitmdump that is no longer running kills all app traffic and looks exactly like an app bug.

**When the question is what the app actually sent or received, capture it — don't infer it from call sites.** Setup takes ~10 minutes and settles in one run what reading code only makes plausible. It matters most for device-scoped traffic: auth tokens, StoreKit receipts, user-scoped responses, bodies built on-device. Two cheaper checks first:
- Does the endpoint answer a plain `curl`? Some APIs need no user context at all.
- Does the app already log requests and responses? `devicectl device process launch --console` streams the app's stdout, which often carries full request/response bodies.

```bash
mitmdump -s capture.py --listen-port 8080 --allow-hosts '(<api-host-1>|<api-host-2>)'
```

- **`--allow-hosts` is mandatory.** Intercepting everything breaks Apple's certificate-pinned StoreKit endpoints: product queries never return and the paywall hangs in Loading, which reads as an app bug. Allow-listing tunnels every other host as raw TCP.
- **Don't express this as a negative lookahead in `--ignore-hosts`** (`'^(?!.*(host))'`) — it silently ignores *everything*, including the hosts you want, and captures nothing.

Verify the split before trusting a run:

```bash
echo | openssl s_client -proxy <mac-ip>:8080 -connect <api-host>:443 -servername <api-host> 2>/dev/null \
  | openssl x509 -noout -issuer
# expect issuer=CN=mitmproxy — and a REAL Apple issuer for buy.itunes.apple.com
```

Don't verify with macOS system `curl`: its native TLS backend ignores `--cacert` and returns 200 against a passthrough connection, falsely implying interception works.

Device side, each time: Wi-Fi → proxy Manual; install the CA from `http://mitm.it`; then Settings → General → About → **Certificate Trust Settings** → enable it. Trusting is a separate step from installing the profile and easy to miss. Revoke the trust and clear the proxy when finished.
