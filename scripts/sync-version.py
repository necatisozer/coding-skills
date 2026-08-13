#!/usr/bin/env python3
"""Copy the version from plugin.json into every plugin entry of marketplace.json.

plugin.json is the source of truth — bump it, and this keeps the marketplace
manifest matching. Run directly, or let the pre-commit hook in .githooks run it.
Exits 0 and prints nothing when already in sync.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLUGIN = ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"


def main() -> int:
    version = json.loads(PLUGIN.read_text())["version"]

    original = MARKETPLACE.read_text()
    manifest = json.loads(original)
    for entry in manifest.get("plugins", []):
        if entry.get("source") == "./":
            entry["version"] = version

    updated = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if updated == original:
        return 0

    MARKETPLACE.write_text(updated)
    print(f"synced marketplace.json to version {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
