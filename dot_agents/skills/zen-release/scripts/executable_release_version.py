#!/usr/bin/env python3
"""Release flow: commit changes, bump version, tag, push, create GitHub Release."""

import json
import subprocess
import sys
import re
from pathlib import Path


def bail(msg: str):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def sh(*args, dry_run=False):
    cmd = " ".join(str(a) for a in args)
    print(f"+ {cmd}")
    if dry_run:
        return ""
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        bail(f"command failed: {cmd}\n{r.stderr.strip()}")
    if r.stdout:
        print(r.stdout.rstrip())
    return r.stdout.strip()


def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception as e:
        bail(f"cannot read {path}: {e}")


def write_json(path: Path, data):
    path.write_text(json.dumps(data, indent="\t", ensure_ascii=False) + "\n")


def guess_next(current: str, bump: str) -> str:
    parts = current.split(".")
    if len(parts) != 3:
        bail(f"unexpected version format: {current}")
    if bump == "minor":
        parts[2] = str(int(parts[2]) + 1)
    elif bump == "major":
        parts[0] = str(int(parts[0]) + 1)
        parts[1] = "0"
        parts[2] = "0"
    else:
        bail(f"unknown bump type: {bump}")
    return ".".join(parts)


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry_run = "--dry-run" in sys.argv

    if not args or args[0] in ("-h", "--help"):
        print(f"usage: {sys.argv[0]} <version>|minor|major [--dry-run]")
        sys.exit(0)

    root = Path.cwd()
    requested = args[0]

    manifest = load_json(root / "manifest.json")
    current = manifest["version"]

    if requested in ("minor", "major"):
        version = guess_next(current, requested)
        print(f"inferred version: {current} -> {version}")
    else:
        version = requested

    tag_name = f"v{version}"
    remote = "origin"
    branch = sh("git", "branch", "--show-current")

    # 1. Show state
    print(f"\nbranch: {branch}  remote: {remote}  tag: {tag_name}")
    sh("git", "status", "--short", "--branch")

    # 2. Check tag doesn't exist
    r = subprocess.run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag_name}"])
    if r.returncode == 0:
        bail(f"tag already exists locally: {tag_name}")

    # 3. Commit local changes
    status = sh("git", "status", "--porcelain")
    if status:
        sh("git", "add", "-A", dry_run=dry_run)
        sh("git", "commit", "-m", "local changes", dry_run=dry_run)
    else:
        print("no local changes to commit")

    # 4. Update version files
    old_v = manifest["version"]
    manifest["version"] = version
    print(f"manifest.json: {old_v} -> {version}")
    if not dry_run:
        write_json(root / "manifest.json", manifest)

    versions = load_json(root / "versions.json")
    versions[version] = manifest["minAppVersion"]
    print(f"versions.json: added {version} -> {manifest['minAppVersion']}")
    if not dry_run:
        write_json(root / "versions.json", versions)

    pkg = load_json(root / "package.json")
    pkg_v = pkg.get("version")
    pkg["version"] = version
    print(f"package.json: {pkg_v} -> {version}")
    if not dry_run:
        write_json(root / "package.json", pkg)

    # 5. Commit version changes
    if not dry_run:
        sh("git", "diff", "--", "manifest.json", "versions.json", "package.json")
    sh("git", "add", "manifest.json", "versions.json", "package.json", dry_run=dry_run)
    sh("git", "commit", "-m", f"Bump version to {version}", dry_run=dry_run)

    # 6. Tag and push
    sh("git", "tag", tag_name, dry_run=dry_run)
    sh("git", "push", remote, branch, dry_run=dry_run)
    sh("git", "push", remote, tag_name, dry_run=dry_run)

    # 7. Create GitHub Release
    r = subprocess.run(["gh", "release", "view", tag_name], capture_output=True, text=True)
    if r.returncode == 0:
        print(f"release already exists: {tag_name}")
    else:
        sh("gh", "release", "create", tag_name,
           "--title", version,
           "--notes", "",
           "manifest.json",
           "theme.css",
           dry_run=dry_run)


if __name__ == "__main__":
    main()
