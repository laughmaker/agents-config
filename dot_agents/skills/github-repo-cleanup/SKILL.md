---
name: github-repo-cleanup
description: "Safely audit and clean up a GitHub account's repositories. Use when the user wants to review, organize, archive, or delete GitHub repos — e.g. \"整理我的 GitHub\", \"总结一下我的 repo\", \"删除这些仓库\", \"which repos should I archive\". Covers: enumerating all repos via gh CLI, clustering them into buckets, computing storage/activity distributions, verifying content coverage before deletion, mirror-backing-up repos, and executing archive/delete with the delete_repo scope. Emphasizes the non-obvious traps: delete_repo scope is not granted by default, HTTPS cloning fails behind a proxy, and the user's 'content is already migrated' premise is usually only ~85% true."
agent_created: true
---

# GitHub Repository Cleanup

## Overview

Audit a GitHub account's repos, present a clustered summary, then execute cleanup
(archive / delete) with a verifiable safety net.

The two failure modes this skill exists to prevent:

1. **Deleting a repo that holds unique content**, because the user asserted it was "already migrated".
2. **Deleting without a restorable copy**, because the repo's only remote was the one being deleted.

Read [references/procedures.md](references/procedures.md) for the exact commands.

## Non-negotiable order

Never reorder these. Each step gates the next.

1. **Enumerate** all repos (including private) and cluster them.
2. **Check the token scope.** Deletion needs `delete_repo`, which is NOT in the default `gh` scope set.
   Discover this *before* promising the user a deletion.
3. **Verify the coverage claim.** If the user says "X is already covered by Y", test it. See `references/procedures.md`.
4. **Mirror-backup every repo you intend to delete.** `git clone --mirror` + `git fsck` + record the HEAD SHA.
5. **Delete**, then verify each with a 404 probe.

## Rules

- **Backup precedes deletion, always.** Mirror backups are cheap; a deleted repo without a mirror is gone.
- **Do not accept the coverage premise unverified.** In practice "已覆盖" measures ~83–87% by title and
  ~1–4% by content hash. Surface the gap and let the user decide with real numbers.
- **Report the size math.** If the repos being deleted total 31 MB out of 2.86 GB, say so — it usually
  changes the decision. Archiving does NOT reclaim storage; only deletion does.
- **Do not push back more than once.** Surface the evidence, ask, then execute what the user chooses.
- **Use SSH for cloning.** HTTPS through the user's proxy fails with `HTTP2 framing layer` / `CONNECT tunnel 502`.
- **Never touch unrelated repos.** Only act on the explicit target list.

## Clustering heuristic

`gh repo list` output is dominated by age, not purpose. Sort by `pushedAt` to find the live tier,
then group the tail by origin story rather than by language:

- live/active (pushed this year)
- knowledge-base / note-vault generations (look for `.obsidian`, `00 Inbox`, PARA dirs)
- one employer or product era (look for a shared name prefix, e.g. `mmgg.*`, `pawbby_*`)
- personal open-source portfolio (a shared library prefix, e.g. `TW*` — these often carry the stars)
- docs / forks / empty

Portfolio repos are the highest-leverage finding: they frequently have real stars **and no LICENSE**,
which makes them legally unusable. Flag this.

## Local Environment Notes

Verified on this machine (macOS, Chinese-locale user):

- `gh` at `/opt/homebrew/bin/gh`; check scope via `gh auth status 2>&1 | grep -i scopes`.
- Granting delete rights non-interactively:
  `echo | gh auth refresh -h github.com -s delete_repo`
  Piping `echo` auto-confirms the "Press Enter to open browser" prompt. It prints a one-time code
  (format `XXXX-XXXX`) and `https://github.com/login/device`; **the user must complete it in a browser**,
  so surface the code prominently and wait. The command re-writes the keyring token in place.
- GitHub SSH is already authorized on this machine (`ssh -T git@github.com` → `Hi laughmaker!`).
- Skill convention: real directories live in `~/.agents/skills/<name>/`; agent dirs hold symlinks only
  (`~/.workbuddy/skills/<name>` → `~/.agents/skills/<name>`).
  `ln -sfn` fails under `.cursor/skills-cursor` and `.qwenworkcn/skills`; use Python
  `os.remove(t) if exists; os.symlink(src, t)` instead.
