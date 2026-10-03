---
name: esl-video-vocab-builder
description: Build a CET-4/6-baselined vocabulary and phrase study guide from a long English video's subtitles, and optionally an interactive local study site (click-to-seek transcript, filterable vocabulary cards, quizzes with progress tracking). Use when an ESL learner asks what words/phrases they need to know to fully understand a specific video, podcast, or lecture — e.g. "提取这个视频的字幕，总结我需要掌握哪些单词和词组" or "把这个内容做成一个网页帮助我学习". Produces a grounded word list (every entry verified present in the transcript), phrase/collocation tables, concept glossary, idiom section, listening-difficulty analysis, a study plan, and optionally a zero-dependency study site generated from the two Markdown deliverables.
---

# ESL Video Vocabulary Builder

Turn one long English video into a **study guide of exactly the words and phrases an ESL learner
needs** to understand it. Two deliverables:

1. `<Video>_逐字稿.md` — full timestamped transcript (+ ASR errata table)
2. `<Video>_词汇与词组精讲.md` — the main deliverable

First run the `video-transcript-extractor` skill (Step 0 → json3 subtitles). Then do the analysis below.

## Core principle

**Every single entry must be verified present in the transcript.** Never ship a "words you'd need for
this topic" list built from intuition — it will contain dozens of expressions the speaker never used,
and the learner wastes hours on non-existent content. In one 3-hour podcast, 11 of 25 plausible idioms
(`rat race`, `sunk cost`, `elephant in the room`, …) turned out **not** to appear. Verify, then write the
rejected ones into an appendix — it demonstrates rigor and tells the learner what *not* to study.

## Step 1 — Establish the learner's baseline

Ask or assume CET-4/6 unless told otherwise. Build the baseline from **two** lists, unioned:

| Source | Fetch via | Caveat |
|---|---|---|
| CET4 + CET6 syllabus words | jsdelivr: `https://cdn.jsdelivr.net/gh/mahavivo/english-wordlists@master/CET4_edited.txt` (and `CET6_edited.txt`) | **Incomplete** — `context`, `media`, `therapy` are missing. Not usable alone. |
| General frequency | jsdelivr: `https://cdn.jsdelivr.net/gh/first20hours/google-10000-english@master/google-10000-english.txt` | Use the first ~4000 lines as "surely known" |

`raw.githubusercontent.com` is blocked in this environment — **always use the jsdelivr CDN mirror.**
Files are formatted `word [phonetic] pos.meaning` or `word pos.meaning`; extract with
`^([A-Za-z][A-Za-z\-'\. ]*?)\s*(?:\[|$)`.

Then clean the candidate list in three passes:

1. **Inflection reduction** — `gotten`/`children`/`said`/`lying` fold into their lemma. Add irregular
   plurals by hand (`children, men, women, feet, data, media, criteria`).
2. **Proper-noun removal** — compute the ratio of occurrences that are capitalized **and not**
   sentence-initial (check the previous token: not `None`, not a sentence-ending mark). Ratio ≥ 0.5 → proper noun.
3. **Non-word removal** — cross-check against `/usr/share/dict/words` + `/usr/share/dict/web2` to drop
   ASR garbage.

Report the surviving counts as a headline stat: *"923 word forms / 1,508 word tokens fall outside the
CET-4/6 baseline — i.e. about X% of the video's tokens."* That number is the whole point: it proves
vocabulary is a bounded, solvable problem and reframes the real difficulty as prosody and speed.

## Step 2 — Count and rank (get the counting口径 right)

**Default to regular inflectional forms only**: `base + (s|es|ed|d|ing|ings)`, plus `y→ies/ied` and
`e→ing/ed/es` handling.

**Do NOT auto-merge derivational relatives via `ion/ity/ment/ness` stem rules.** that silently inflates:

| word | naive stem rule | honest count |
|---|---|---|
| `attention` | 22 (absorbed `attentive`) | 11 |
| `judgment` | 20 (absorbed `judging/judged`) | 10 |
| `societal` | 43 (absorbed `society`) | 11 |

Where the family genuinely is one lemma worth learning together (`ruminate / ruminating / rumination`,
`crave / craving / cravings`), declare it in an explicit hand-checked whitelist and label the column
**"词族出现次数"** with a footnote. Never let the reader mistake a family count for a raw count.

## Step 3 — Anchor every entry to a real example + timestamp

Build a sentence index with `(ms, text)` tuples, then for each entry pick the best example:

```python
def best_sent(pat, maxn=1):
    p = re.compile(pat, re.I)              # re.I is mandatory — see pitfalls
    hits = []
    for ms, s in sents:
        if not p.search(s): continue
        if len(s) < 45 or len(s) > 265: continue   # skip fragments and unreadable run-ons
        if '[ __]' in s: continue                  # profanity-censored auto-caption
        if p.search(s[:14]): continue              # don't let the target word open the sentence
        hits.append((abs(len(s) - 130), ms, s))
    hits.sort()
    return [(ms, clean_ex(s)) for _, ms, s in hits[:maxn]]
```

Fail-soft ladder: strict match → lenient match (`len >= 18`, ignore length caps) → fall back to a
hand-written quote. When auto-extraction keeps grabbing a neighbouring anecdote out of a run-on,
**pin the example manually** with its timestamp — a wrong example is worse than no example.

## Step 4 — Dictionary data (phonetics + Chinese glosses)

**有道 jsonapi is the best available source and is reachable from the host network:**

```
https://dict.youdao.com/jsonapi?q=<word>      # header: User-Agent: Mozilla/5.0
```

Read `ec.word[0]`: `usphone`/`ukphone` (IPA), `trs` (definitions), `wfs` (inflections). Bonus:
`ec.exam_type` returns `["CET6","商务英语"]`-style tags — a free, independent difficulty signal for
cross-checking your tiers.

`api.dictionaryapi.dev` is unreachable here — don't rely on it.

Quality rules for glosses:
- Strip dictionary register tags (`<正式>`, `<美>`, `<旧>`) and leading part-of-speech.
- Truncate to ~34 chars at a sensible punctuation boundary, **then repair unclosed brackets**:
  ```python
  while s.count('（') > s.count('）'):
      s = s[:s.rfind('（')].rstrip('，、； ')
  ```
- Substitute the **video-specific** sense for high-frequency concepts. A dictionary's first gloss for
  `leverage` is "杠杆力"; in Naval's framing it is "借力/放大器" — the framing is what the learner needs.
- Phonetic fallback for plurals: if `<word>` has no IPA, try `word.rstrip('s')`.

## Step 5 — Mine phrases, not just words

Phrasal verbs and discourse markers are where ESL listening actually breaks — `figure out`, `end up`,
`as opposed to` are all made of words the learner knows.

**n-gram frequency is the wrong tool for idioms** (idioms are low-frequency). Instead:

- **Discourse markers** — count them explicitly. In one 3-hour podcast `you know` (266) + `I think` (203)
  = 2.2% of all tokens. Teach the learner to hear them as *background noise* rather than content; that is
  the single highest-leverage listening improvement.
- **Phrasal verbs / prepositional phrases** — write a candidate list with **inflection-aware regexes**
  (`r'figure(?:d|s)? out|figuring out'`) and keep only the ones that hit. Report the count.
- **Argument-signal phrases** — `as opposed to`, `to the extent that`, `I would argue`, `by default`.
  These are structural signposts: hearing one tells the learner a claim or a contrast is coming.
- **Idioms, metaphors, and cultural references** — same treatment, plus a `\b` boundary (bare `hydra`
  matches *hydration*; bare `loser` matches *closer*). Then explain them: they are the speaker's default
  shared knowledge and podcasts never gloss them.

## Step 6 — Add a listening-difficulty section

Vocabulary is rarely the binding constraint. Cover:

- **Speed**: compute words/minute and compare with CET-4 (~120–140) and CET-6 (~140–160) listening material.
- **Reductions**: build a table of `going to→/ˈɡənə/`, `want to→/ˈwɑnə/`, `kind of→/ˈkaɪndə/`,
  `used to→/ˈjuːstə/`, `a lot of→/əˈlɑɾə/` — with real counts from the transcript.
- **ASR errata** — so the learner doesn't learn a misspelling.
- **Where to start**: recommend the chapters with the most everyday vocabulary and clearest argument,
  and note that the chapter list lets them listen out of order.

## Step 7 — Deliverable structure

```
一、结论速览          counts table + 3-tier priority ladder
二、分析口径          baseline definition, cleaning passes, coverage stats
三、核心词汇 (≥3次)   3.1 首轮 40 词 (highest ROI) · 3.2 全表按主题分组
四、进阶词汇 (2次)    compact table
五、拓展低频词 (1次)   决定"完全听懂"上限
六、短语与固定搭配     expression | count | meaning | 原句+时间戳
七、概念术语          the speaker's own framework — comprehension, not vocabulary
八、习语与文化典故     meaning + pinned quote
九、词汇之外的听力障碍  填充词 · 连读弱读 · ASR勘误 · 语速
十、学习计划          3 stages with a 检验标准 per stage
十一、附录            常见但本视频未出现的表达
```

Group core vocabulary **by theme** (psychology / business / biology / society / cognition / philosophy),
not by frequency — thematic clustering is far more memorable, and for a single-topic podcast the themes
map onto the argument's structure. Keep the 频次 column so priority is still visible.

## Step 8 (optional) — Generate an interactive study site

The two Markdown files contain everything a study tool needs: every sentence carries `[MM:SS]` and every
entry carries a first-occurrence timestamp. **That is the whole point of Step 3** — it makes click-to-seek
possible. Ship a study site when the learner wants to *practise*, not just read.

Templates live in `assets/`:

```
assets/generate_data.py      Markdown → data.js  (the only thing you need to edit)
assets/serve.py              Range-capable local server — copy it, do not use http.server
assets/site/index.html       shell
assets/site/style.css        dark + light themes
assets/site/app.js           all interaction logic (vanilla JS, zero dependencies)
```

Copy `assets/site/*` and `assets/serve.py` next to a generated `data.js` and run:

```bash
python3 assets/generate_data.py --vocab <guide>.md --transcript <transcript>.md --out data.js
cp assets/serve.py .            # 与 index.html 同级
python3 serve.py                # http://127.0.0.1:8777/
```

**Never tell the user to run `python3 -m http.server`.** It does not implement Range requests, and once
a real media file is in `media/` that single omission destroys seek: measured on a 286 MB `video.mp4`,
`Range: bytes=0-99` comes back as `200` with the full 286 MB body. Every click-to-seek then re-downloads
the whole video. `serve.py` is ~150 lines and exists solely to fix this.

### Architecture rules (violating these costs hours)

1. **Markdown is the single source of truth.** Never hand-maintain the site's data. The generator parses
   the *deliverables*, so any new video that produces the same two documents gets a study site for free,
   with zero front-end changes.
2. **Emit `data.js`, not `data.json`.** `fetch()` is blocked by CORS under `file://`, but `<script src>` is
   not. Write `window.YOURDATA = {...};` so the page opens by double-click too.
3. **Compute match spans on the server.** The generator outputs `[entityId, startChar, endChar]` per
   sentence. Do **not** re-implement inflection matching in JavaScript — two implementations *will*
   diverge, and the client only needs to slice the string.
4. **The player must degrade gracefully — and YouTube must not be the only source.** Set a load timeout
   (~9s) on the YouTube IFrame API. When it fails, do not just say "network or region issue": read
   `ev.data` and print the code (2/5/100/**101/150 = embed forbidden by the owner**), offer a
   *retry* that re-injects the API without a page reload, and fall back to a **local media backend**.
   Map `playerState 3 → "缓冲中"`, or the user sees "就绪" and thinks the seek failed.
5. **Give the player two interchangeable backends behind one interface** (`yt.ready` / `yt.player.*`):
   YouTube embed and a local `<audio>/<video>`. Local mode is fully offline and must reach feature
   parity (seek, A-B loop, repeat-N, rate, follow-along, listening/cloze questions).
   Auto-detect a `media/` folder (fetch the directory listing, then probe conventional names) and also
   accept a picked/dropped file. Keep **separate duration fields per backend** — one shared `dur` gets
   overwritten by the other side's `onReady` and silently shows the wrong total length.
   When a local file **is** found at boot, switch to it by default instead of waiting for YouTube to
   fail: the user wants a player that works, not a coin flip. Also sort the discovered names by the
   conventional-name list before taking `names[0]` — the directory listing's alphabetical order
   otherwise decides, and you end up playing an arbitrary file.
6. **Layout contract: `body` must be `display:flex; flex-direction:column`** with
   `html{overflow:hidden}`. The CSS keeps the header/dock pinned with `flex:none` and the body with
   `flex:1; min-height:0; overflow:hidden`, and each column scrolls itself. Without the flex container
   the whole page degrades into one document flow: the header scrolls away, the player bar is pushed
   past the fold, and "three independently scrolling columns" silently becomes one page scroll. Measure
   it — `documentElement.scrollHeight - clientHeight` must be exactly `0`, then assert that scrolling
   one column leaves the other two at `scrollTop === 0`. Note `.transcript{scroll-behavior:smooth}`
   makes an immediate `scrollTop` read return the *old* value.
7. **Scope localStorage by video**: `'study.' + meta.videoId + '.v1'`.
8. **The player box shows exactly one layer.** Two independent axes decide it — backend (`mode-yt` /
   `mode-local`) and media kind (`is-video` / `is-audio`) — and *both* must be driven from JS
   (`paintSourceKind()`), never inferred in CSS. A local **video** left with the audio badge visible is
   an opaque full-cover overlay: the video plays behind it and the user sees a black rectangle. The
   inverse matters too — hide `<video>` when an audio-only file is loaded, or you get a dead black box
   where the ♪ badge belongs.
9. **A video with `preload="metadata"` decodes no frame**, so the box is pure black at rest and looks
   broken. Ship a `media/poster.jpg` (convention, optional) referenced from the `<video poster>`
   attribute, and clear it when the user loads a blob (picked/dropped file) so a foreign video doesn't
   wear the bundled poster. Only nudge `currentTime` to force a frame when there is no poster — that
   trick shifts the playback start position, so it must not be the primary mechanism.

10. **Exactly one owner per element decides `style.display`.** The overlay layer (`#ytPh`) is hidden by
   a CSS rule (`.yt-box.mode-local .ph{display:none}`) — but if *any* code path also writes an
   **inline** `style.display='block'` (e.g. an error handler), inline wins and the stale message stays
   painted on top of the working local video/audio forever. Symptom: "I loaded the local file, it plays,
   but it still shows a load error." Route every show/hide through a single `paintPh()` that derives
   visibility from `(backend, phase)`, and call it on every state transition (ready / failed / retry /
   backend switch). Never set the placeholder's `display` at more than one call site.
11. **Play/pause is an icon toggle (▶ / ⏸), not a text label.** A static caption like `播放 / 暂停`
   cannot tell the user what will happen — and they will read it as "half a normal button". Use two
   inline SVGs inside one `<button>`, swap them off a single `.active` class, and drive that class from
   one `setPlayingUI(on)` called by every state source (YT `onStateChange`, local `play`/`pause`/
   `ended`, backend switch). Update `aria-label`/`title` too — it's the accessible name, since the
   button now has no text. Keep the `active` name if the global `button.active` rule already supplies
   the accent styling.
12. **Hit targets: a control the user must click cannot be a 10px hover-only chip.** The per-sentence
   loop button used to be `font-size:10.5px; padding:1px 6px; opacity:0` → ~31×17 px and undiscoverable.
   Ship it at ≥50×25 px, always visible at ~0.4 opacity (1.0 on hover/`:focus-visible`, ~0.9 on the
   active sentence), pill radius. Reserve space with `padding-right` on the text column (button width +
   offset) so the absolute-positioned button never sits on the last words — verify with
   `btnRect.left - (pRect.right - paddingRight) > 0`.

### Verified environment facts

- Under `http://localhost`, the IFrame API's `seekTo` / `playVideo` / `setPlaybackRate` **all work**
  (verified: clicking a sentence moves the playhead to the exact second). Under `file://` the origin is
  `null`, so postMessage control may fail — detect and warn.
- The **video stream itself** may stall on buffering even when the control channel works (no proxy/VPN).
  That is an environment limit, not a bug — hence rule 4.
- **Clicking a chapter entry only switches the transcript view — it does not seek.** Only sentences
  seek. If you "verify" the player by clicking a chapter and the playhead doesn't move, the code is
  fine; this reads as a failure but isn't. Also: only the active chapter's sentences are in the DOM
  (`document.querySelectorAll('.sent')[2400]` is `undefined`), so pick a deep-seek target by first
  clicking the chapter, then its first sentence.
- `agent-browser click` on an element scrolled out of its container silently does nothing (it clicks
  the recorded coordinates). `scrollIntoView({block:'center'})` first, assert
  `0 < rect.top < innerHeight`, then click.
- **To test the offline / YouTube-failed UI, do not try to block the network** — `agent-browser network
  route "*youtube.com/*" --abort` did *not* prevent the player from loading (the script and iframe both
  came back 200), so the run proves nothing. Instead build a throwaway copy: `cp index.html data.js
  serve.py` + `cp -r assets build` into `/tmp/xxx`, **symlink** the big `media/` files (no 286 MB copy),
  then repoint exactly one string — the iframe_api URL — at an unreachable host (`http://127.0.0.1:59999/`).
  Confirm the only diff is that URL, serve on another port, and assert both halves of the invariant:
  `phText` contains the error message **and** `getComputedStyle(ph).display === 'none'` while the video
  is `display:block` with a real `videoWidth`. Checking only one half is how the bug survived the
  previous regression run.

### Fetching the media (this is where yt-dlp bites)

| Symptom | Cause | Fix |
|---|---|---|
| extraction OK, then `SSL: UNEXPECTED_EOF_WHILE_READING` → `HTTP Error 403: Forbidden` | stale yt-dlp; YouTube rotated its player clients | install the standalone `yt-dlp_macos` from GitHub releases (verified working: `2026.08.19`; `2026.06.09` fails) |
| `Requested format is not available` for `-f 18` | newer yt-dlp exposes no progressive 360p; only DASH + HLS | use `-f "134+140" --merge-output-format mp4` (needs ffmpeg) |
| `command not found: timeout` | macOS has no GNU `timeout` | don't build test commands around it |
| `no matches found: /tmp/x.*` kills the whole command line | zsh aborts on an unmatched glob | `rm -f` a literal path, or quote the glob |

Also: **yt-dlp automatically uses the macOS system proxy** (Python reads `scutil` settings), so a
working `--list-formats` does not prove the download path is fine — extraction and download hit
different hosts (`youtube.com` vs `googlevideo.com`).

**Resolution: size the file to the display box, not to your instincts.** Measure the player box first —
here it is `150×84`, so 360p is already 4× oversampled and 1080p would turn a 286 MB file into 2.6 GB
for zero visible gain.

**Verify Range support with two numbers, not by eye:**

```bash
curl -s -o /dev/null -r 0-99  -w "%{http_code} %{size_download}\n" http://127.0.0.1:8777/media/video.mp4
curl -s -o /dev/null -r 0-    -w "%{http_code} %{size_download}\n" http://127.0.0.1:8777/media/video.mp4
```

Expect `206 100` then `206 16777216` (the response cap — see `MAX_RANGE` in `serve.py`). A `200` with
the full file size means Range is unimplemented.

**Then confirm the browser actually seeks cheaply** — the decisive signal is *disjoint* buffered ranges,
not transferred bytes (`performance.getEntriesByType('resource')` under-reports media bodies):

```js
var b = []; for (var i = 0; i < v.buffered.length; i++) b.push([v.buffered.start(i), v.buffered.end(i)]);
```

Two separate small ranges far apart (`[0, 395]` and `[11507, 11779]` out of 11779 s) prove the seek
fetched only its neighbourhood. Total seconds buffered far below the duration is the assertion.

Finally, a browser that seeks asks for `Range: bytes=N-` — "N to the end", hundreds of MB. Streaming
that faithfully produces a burst of `ConnectionResetError` / `BrokenPipeError` tracebacks when the
browser takes what it needs and hangs up. Cap each response (`MAX_RANGE`), catch those two exceptions
in `copyfile()`, and override the server's `handle_error()` to stay silent for them — otherwise the
user's terminal fills with stack traces during normal scrubbing.

Start the server with `NAVAL_LOG_MEDIA=1` when you need to see this; leave it off otherwise.

### Entity-matching rules that are easy to get wrong

Use **`p.finditer(text)`, never `p.search(text)`**, when building the per-sentence span index. `search`
returns only the first occurrence, so a term repeated inside one sentence
(`They come in the moment, they leave in the moment.`) gets highlighted once while the side panel
counts it 3 times — a visible contradiction the learner will notice and circle. Collect every match,
then drop overlaps greedily (sort by `(start, -length)`, keep `start >= lastEnd`).

Inflection must be applied **per token**, with all four of these:

| Case | Rule |
|---|---|
| multi-word phrase inflected on an inner word | `lay out → laid out` — put the alternation on *that* token, not the last |
| plural/singular mismatch | `harsh truths → harsh truth` — trailing `s` must be optional |
| irregular verbs | keep a table; `pay off → paid off`, `stick with → stuck with` |
| apostrophes | subtitles write `prisoners dilemma` — make `'` optional |

Also: a word in the guide's "starter N words" table may be **absent from the master tables** (the baseline
filter classified it as already-known, but it carries the video's core thesis — e.g. `desire`, `suffering`,
`fame`). Append those as entities explicitly, or a "starter list" filter silently shows fewer than N.
Verify coverage by re-reading the starter table and asserting every row is present.

## Pitfalls checklist

- [ ] `re.I` on every sentence/phrase regex (sentence-initial capitals).
- [ ] `finditer` (all occurrences) — assert at least one sentence in the corpus returns 2+ spans for the
      same entity, otherwise the repeated-occurrence path is untested.
- [ ] Layout verified in a real browser: page overflow is 0, header never moves, each column scrolls alone.
- [ ] Coverage check printed and >99% before generating the transcript.
- [ ] Every word/phrase verified present; non-hits either dropped or moved to the appendix.
- [ ] Counting口径 stated in the document; no derivational over-merging.
- [ ] Examples hand-pinned wherever auto-extraction picked a neighbouring anecdote.
- [ ] No unclosed `（）`/`()` from truncation.
- [ ] ASR errata table shipped in both documents.
- [ ] Transcript header numbers (word/sentence counts) regenerated from the final index, not hardcoded.
- [ ] Every entity table you parse actually yielded rows — print the per-table row count and compare with
      the number the document itself claims. A heading inside the block (`### 3.2 …`) will silently
      terminate the block if your parser treats any `###` as a stop marker; slicing the block from
      `idx+1` is mandatory. (This cost 72 of 177 words once.)
- [ ] After writing a multi-word regex helper, re-read the file — if the printed pattern doesn't contain
      the alternation you just wrote, the edit never landed.
- [ ] When editing the same file several times, submit the edits **one at a time** and re-read the file
      between them. Two `Edit` calls to one file in a single message can lose one silently while both
      report success.
- [ ] Served with `serve.py`, never `python3 -m http.server`. Assert `Range: bytes=0-99` → `206` + 100
      bytes; a `200` with the full size means local seek is broken.
- [ ] Local media is auto-detected **and preferred** at boot; verify `#ytBox` carries `mode-local` plus
      `is-video` or `is-audio` matching the actual file.
- [ ] A local video shows its picture, not the opaque ♪ badge, and a non-black box at rest (poster or a
      primed frame). Crop the player box out of a screenshot and check the mean pixel value — "looks
      fine" is how a black rectangle ships.
- [ ] Player state after each action read back from the `video` element itself (`currentTime`,
      `paused`, `playbackRate`, `buffered`), not from the UI labels.
- [ ] While local media is playing, **no failure text is painted over it**: assert
      `getComputedStyle(#ytPh).display === 'none'` *after* forcing the YouTube failure path, then toggle
      YouTube → local → YouTube and check the overlay appears and disappears in step.
- [ ] Play button is an icon whose glyph matches the state (▶ paused / ⏸ playing) — never a static
      `播放 / 暂停` label. Assert both `display` values of the two SVGs plus the `aria-label`.
- [ ] Interactive chips measured, not eyeballed: per-sentence loop button ≥50×25 px, resting opacity > 0,
      and `buttonRect.left > textRightEdge` (no overlap with the sentence text).
