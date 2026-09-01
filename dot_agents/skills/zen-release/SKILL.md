---
name: zen-release
description: Release the Zen repository by committing local changes, updating manifest.json, versions.json, and package.json, creating a version tag, pushing to GitHub, and creating a GitHub Release. Use when the user asks to publish, release, bump, tag, or push a Zen version.
---

# Zen Release

## Overview

1. Commit local changes
2. Update version in `manifest.json`, `versions.json`, `package.json`
3. Create a Git tag (`v<version>`)
4. Push commit + tag to GitHub
5. Create a GitHub Release with `manifest.json` and `theme.css`

## Usage

```bash
# Preview first
python3 /Users/hzd/.agents/skills/zen-release/scripts/release_version.py <version> --dry-run

# Run
python3 /Users/hzd/.agents/skills/zen-release/scripts/release_version.py <version>
```

`<version>` can be:
- **A specific version** like `9.0.11`
- **`minor`** — increments the last part (e.g. `9.0.10` → `9.0.11`)
- **`major`** — increments the first part (e.g. `9.0.10` → `10.0.0`)
- **`--dry-run`** — preview without making any changes

## What happens

| Step | Action |
|---|---|
| 1 | `git add -A && git commit -m "local changes"` (if dirty) |
| 2 | Update `manifest.json:version`, `versions.json`, `package.json:version` |
| 3 | `git tag v<version>` |
| 4 | `git push origin <branch>` + `git push origin v<version>` |
| 5 | `gh release create v<version> --title <version> manifest.json theme.css` |
