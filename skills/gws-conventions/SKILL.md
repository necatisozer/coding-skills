---
name: gws-conventions
description: Provides Google Workspace CLI commands when reading Google Sheets, accessing Docs, or querying Workspace APIs via the gws CLI tool.
user-invocable: false
---

## Google Workspace CLI (`gws`)
Use the `gws` CLI (https://github.com/googleworkspace/cli) to access Google Sheets, Docs, and other Workspace APIs.

### Google Sheets

```bash
# Get sheet names/properties
gws sheets spreadsheets get --params '{"spreadsheetId": "SHEET_ID", "fields": "sheets.properties"}'

# Read all data from a named sheet (no ! needed when using just the sheet name)
gws sheets spreadsheets values get --params "{\"spreadsheetId\": \"SHEET_ID\", \"range\": \"Sheet Name\"}"

# Read a specific range (use double quotes to escape ! from bash history expansion)
gws sheets spreadsheets values get --params "{\"spreadsheetId\": \"SHEET_ID\", \"range\": \"Sheet Name!A1:D10\"}"
```

**Important:** Sheets ranges use `!` which bash interprets as history expansion. Use double-quoted `--params` with escaped inner quotes, or avoid `!` by using just the sheet name as the range.
