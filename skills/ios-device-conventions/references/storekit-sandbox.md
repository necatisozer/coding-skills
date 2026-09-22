# StoreKit Sandbox Testing

## On the Device
- Sandbox testers sign in under **Settings → Developer → Sandbox Apple Account**, not Settings → App Store. Past a 2FA upgrade wall: **Other options → Do not upgrade**.
- **The purchase sheet is where the no-credentials rule (SKILL.md) bites** — and automation fails there anyway: a WDA-typed password produced "Verification Failed — There was a problem connecting to the server" while a hand-typed one went straight through. Drive Subscribe and Confirm, hand the password prompt to the human, then carry on. Say so *before* they tap: a subscription-only paywall leaves the app entitled until you go through the reset below.
- **Check the storefront before trusting any price- or offer-dependent result.** The currency on the paywall is the proof (`₺699,99` vs `$12,99`).
- **Entitlement can outlive the Apple ID.** If the backend keys entitlement off a user id the app keeps in the keychain, it survives app deletion — uninstalling, switching Apple ID, or waiting all come back subscribed. Capture instrumentation *before* buying.
- **Back to unsubscribed without the tester's password:** clear the tester's purchase history over the App Store Connect API, **then uninstall and reinstall.** The clear alone changes nothing on device — it stops renewals and restores trial eligibility, but the running app keeps its state until a fresh install forces a re-sync.
- **Reaching a gate without real spending:** change the client-side input the gate reads, not server state — e.g. if the gate reads a bundled config, raise the item's price above the live balance; the backend still charges its own price. Pick a value a purchase can clear, or any resume-after-purchase path never fires. Revert before committing; for Compose Multiplatform bundled files, gradle-conventions › CMP iOS Resource Pipeline Serves Stale Content covers confirming the edit actually shipped to iOS.

## Traps
- **`isEligibleForIntroOffer` answers for the subscription *group*, not the product.** A product with no introductory offer still reports `true` when the account is eligible within the group — reading `false` as "this product has no offer" is a wrong diagnosis.
- **A tester's territory is editable**, the way to test per-territory pricing without new accounts — but **the device keeps serving the old storefront until the sandbox account is signed out and back in.** Reinstalling is not enough. Sign-out can be automated; sign-in cannot.
- **Testers are shared test state.** Ask before clearing anyone's purchase history or changing a territory, and put a changed territory back.

## App Store Connect API
Credentials usually sit in the app's `fastlane/` folder: `AuthKey_<KEY_ID>.p8` (the key id is in the filename) and the issuer id in `fastlane/.env` — a dotfile, easy to miss with a glob (see SKILL.md's quoting rule).

**Sign the ES256 JWT with openssl** — no PyJWT or `cryptography` install needed, and those can fail to load on the system Python. The DER signature must be repacked into JWS's raw `r‖s`, each half left-padded to 32 bytes:

```python
import base64, json, time, subprocess, pathlib
KEY, KID, ISS = "AuthKey_<KEY_ID>.p8", "<KEY_ID>", "<ISSUER_ID>"
b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=")
now = int(time.time())
msg = (b64(json.dumps({"alg": "ES256", "kid": KID, "typ": "JWT"}, separators=(",", ":")).encode()) + b"." +
       b64(json.dumps({"iss": ISS, "iat": now, "exp": now + 900, "aud": "appstoreconnect-v1"}, separators=(",", ":")).encode()))
der = subprocess.run(["openssl", "dgst", "-sha256", "-sign", KEY], input=msg, capture_output=True, check=True).stdout
assert der, "openssl produced no signature - check the key path"
i = 2 if der[1] < 0x80 else 3
r = der[i + 2:i + 2 + der[i + 1]]; j = i + 2 + der[i + 1]; s = der[j + 2:j + 2 + der[j + 1]]
sig = r.lstrip(b"\0").rjust(32, b"\0") + s.lstrip(b"\0").rjust(32, b"\0")
pathlib.Path("jwt.txt").write_text((msg + b"." + b64(sig)).decode())
```

- Send `-H "Authorization: Bearer $(cat jwt.txt)"` so the token never lands in argv.
- Tokens live at most 20 minutes — regenerate rather than debug a sudden 401.
- Use `curl`; Python `urllib` has timed out against this API.
- Transient `HTTP 000` happens — retry two or three times.

| Task | Call |
|---|---|
| List sandbox testers | `GET /v2/sandboxTesters` (collection only; fetching one instance 403s). Match on `attributes.acAccountName` — `appleId`/`email` come back null |
| Clear purchase history | `POST /v2/sandboxTestersClearPurchaseHistoryRequest` → 201, body `{"data":{"type":"sandboxTestersClearPurchaseHistoryRequest","relationships":{"sandboxTesters":{"data":[{"type":"sandboxTesters","id":"<id>"}]}}}}`. Every `v1` spelling in older docs 404s |
| Change territory | `PATCH /v2/sandboxTesters/<id>` with `{"data":{"type":"sandboxTesters","id":"<id>","attributes":{"territory":"TUR"}}}` |
| Audit signing assets | `GET /v1/bundleIds`, `GET /v1/profiles` (`profileContent` is the base64 `.mobileprovision`), `GET /v1/certificates` |
