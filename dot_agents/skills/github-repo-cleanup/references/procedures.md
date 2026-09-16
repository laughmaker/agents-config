# Procedures

Exact commands, verified working. Adapt the account name (`laughmaker`) and paths.

---

## 1. Enumerate everything

`gh repo list` includes private repos the token can see; `public_repos` from `gh api user` does not,
so the two numbers will disagree. Trust the list.

```bash
gh repo list <account> --limit 300 \
  --json name,description,visibility,isFork,isArchived,primaryLanguage,diskUsage,updatedAt,pushedAt,createdAt,stargazerCount,forkCount,isEmpty,licenseInfo,repositoryTopics \
  > /tmp/gh_repos.json
```

Useful derived metrics from that JSON:

- storage total: `sum(r["diskUsage"])` (units are KB)
- age buckets: `(today - pushedAt)` → `<6mo / 6-12mo / 1-3y / 3-5y / >5y`
- metadata gaps: repos lacking `description`, `repositoryTopics`, `licenseInfo`
- read-only probes: `gh api repos/<acct>/<repo>/contents` and `.../commits?per_page=5` for the live tier

## 2. Check delete scope BEFORE planning deletions

```bash
gh auth status 2>&1 | grep -i scopes
```

Default here is `gist, read:org, repo, workflow` — **no `delete_repo`**.
Deleting without it returns:

```
HTTP 403: Must have admin rights to Repository.
This API operation needs the "delete_repo" scope.
```

Grant it (user completes the browser step):

```bash
echo | gh auth refresh -h github.com -s delete_repo
```

Output to surface verbatim to the user:

```
! First copy your one-time code: XXXX-XXXX
Open this URL to continue in your web browser: https://github.com/login/device
```

Then re-check `gh auth status` and confirm `delete_repo` appears before proceeding.

## 3. Verify a coverage claim

The user will say "these are already migrated, safe to delete". Test it. Three probes, weakest to strongest:

### 3a. Title match (fairest — tolerates edits during migration)

```bash
cd <mirror-dir>
git -C <old>.git -c core.quotepath=false ls-tree -r --name-only HEAD
```

Compare `os.path.splitext(basename(f))[0]` for `*.md` against the stems of the target vault's `*.md`.
Report hit rate. A real migration typically lands at **83–88%**, not 100%.
Split misses into `YYYY-MM-DD` daily notes vs everything else — daily notes from uncovered
date ranges are expected; missing *topical* notes are the ones worth reporting.

### 3b. Content hash (strict — detects any edit)

Git blob SHA *is* a content hash, so compare it directly without any hashing library:

```python
import hashlib, os
def git_blob_sha(path):
    data = open(path, "rb").read()
    h = hashlib.sha1()
    h.update(b"blob %d\0" % len(data))
    h.update(data)
    return h.hexdigest()
```

Build a set of these for the surviving vault's working tree, then check each
`git ls-tree -r HEAD` SHA in the old mirror against it.

Expect a brutal result — migration rewrites frontmatter and renames, so identical-content
rates land at **1–4%**. Do NOT present this as "the content is missing"; present it as
"nothing is byte-identical". 3a is the number that answers the user's actual question.

### 3c. Filter nested-repo noise first

Before drawing any conclusion, drop paths containing `.git.nosync/`:

```python
blobs = [b for b in blobs if '.git.nosync/' not in b[1]]
```

Vaults often committed a nested `.git` directory. In the observed case this was **6271 of 8856
files (and ~700 MB of 755 MB)** — pure noise that makes the "unique content" number meaningless
if left in. Always report this, since it is usually the true bulk of a bloated repo.

## 4. Mirror-backup before deleting

Use SSH, not HTTPS.

```bash
mkdir -p <backup-dir> && cd <backup-dir>
for r in repo1 repo2; do
  git clone --mirror "git@github.com:<account>/$r.git" "$r.git"
done

# verify + record exactly what was captured
for d in *.git; do
  printf "%-26s " "$d"
  git -C "$d" rev-parse --short HEAD
  git -C "$d" fsck --no-progress --no-dangling >/dev/null 2>&1 && echo "  OK" || echo "  CORRUPT"
done
```

A mirror records *every* ref, tag and branch — restore is `git clone <name>.git` or push it back
up with `git push --mirror`.

**HTTPS failures seen behind a proxy** (abandon HTTPS immediately, do not retry it):

```
fatal: unable to access '...': Error in the HTTP2 framing layer
fatal: unable to access '...': CONNECT tunnel failed, response 502
```

Large mirrors are slow over SSH (~755 MB took ~20 min). Run the loop with `run_in_background`.

## 5. Delete and verify

```bash
for r in repo1 repo2; do gh repo delete "<account>/$r" --yes; sleep 1; done
```

`gh repo delete` prints nothing on success — do not read silence as failure. Verify independently:

```bash
for r in repo1 repo2; do
  printf "%-24s " "$r"
  gh api "repos/<account>/$r" --silent -i 2>/dev/null | head -1 | grep -q 404 \
    && echo "deleted" || echo "STILL EXISTS"
done
gh repo list <account> --limit 300 --json name --jq 'length'
```

## 6. Fork-specific pre-check

A fork is safe to delete with no backup when it carries no local commits:

```bash
gh api "repos/<upstream-owner>/<upstream-repo>/compare/<branch>...<account>:<fork-repo>:<branch>" \
  --jq '{ahead:.ahead_by,behind:.behind_by}'
```

`ahead: 0` means it is a pristine snapshot — re-forking costs nothing, so no mirror is needed.
Skip the backup for these. (`repos/<acct>/<fork>/compare/...` returns 404 — you must call it on the
**upstream** repo.)

---

## Reporting shape

Lead with the three things that change decisions:

1. totals (count, public/private split, storage)
2. the storage concentration (usually 2–5 repos hold ~90%) and which one is *growing*
3. the metadata gaps (missing LICENSE on starred repos is the highest-leverage fix)

Then the cluster table, then a P0→P4 recommendation list ordered by benefit/risk.
Close with the specific questions that block execution — not a generic "shall I proceed?".
