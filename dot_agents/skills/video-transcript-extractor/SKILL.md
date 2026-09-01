---
name: video-transcript-extractor
description: Download video/audio from Bilibili, YouTube, Twitter/X, and 1000+ platforms, then transcribe to text with timestamps using Whisper. Use when the user asks to extract transcripts, subtitles, or逐字稿 from video URLs, or wants to convert video/audio to text/markdown.
---

# Video Transcript Extractor

Extract transcripts (逐字稿) from any video platform — Bilibili, YouTube, Twitter/X, TikTok, and more. Outputs a timestamped Markdown file.

## Prerequisites

### yt-dlp
A command-line video downloader (active fork of youtube-dl). Supports 1000+ sites.

- **Check**: `which yt-dlp` or `/Users/hzd/.local/bin/yt-dlp --version`
- **Install**: `pip install yt-dlp` or `brew install yt-dlp`
- **Update**: `pip install -U yt-dlp` (update regularly — sites change their APIs constantly)

### OpenAI Whisper
Open-source speech recognition model by OpenAI. Runs locally on CPU or GPU.

- **Check**: `which whisper` or `/Users/hzd/.workbuddy/binaries/python/versions/3.13.12/bin/whisper --version`
- **Install**: `pip install openai-whisper`
- **Models** (by size/accuracy tradeoff):
  - `tiny` (~39MB) — fastest, lowest accuracy
  - `base` (~74MB) — fast, decent accuracy for clear English
  - `small` (~244MB) — good accuracy, slower
  - `medium` (~769MB) — high accuracy, slow on CPU
  - `large` (~1.5GB) — best accuracy, very slow on CPU
- **Recommendation**: Use `base` for quick drafts. Use `small` or `medium` when accuracy matters and time allows. On Apple Silicon, consider `mlx-whisper` for GPU acceleration.

## Workflow

### Step 1: Check for existing subtitles

Always try official subtitles first — they're more accurate than AI transcription.

**Bilibili**:
```bash
# 1. Get video info (cid)
curl -s "https://api.bilibili.com/x/web-interface/view?bvid=<BVID>" \
  -H "User-Agent: Mozilla/5.0" \
  -H "Referer: https://www.bilibili.com/" | python3 -m json.tool

# 2. Check subtitle list using cid
curl -s "https://api.bilibili.com/x/player/v2?cid=<CID>&bvid=<BVID>" \
  -H "User-Agent: Mozilla/5.0" \
  -H "Referer: https://www.bilibili.com/video/<BVID>/" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(json.dumps(data.get('data', {}).get('subtitle', {}), indent=2, ensure_ascii=False))
"

# 3. If subtitles exist, download the subtitle JSON from the subtitle URL
#    Subtitle URLs are in data.subtitle.subtitles[].subtitle_url
#    Prepend https: if the URL starts with //
```

**YouTube / other platforms via yt-dlp**:
```bash
yt-dlp --list-subs "<URL>"
# If subtitles exist:
yt-dlp --write-sub --write-auto-sub --sub-lang en,zh --skip-download "<URL>"
```

### Step 2: Download audio (if no subtitles)

```bash
# General command (works for most platforms)
yt-dlp --extract-audio --audio-format mp3 --audio-quality 0 \
  -o "/tmp/video_audio.%(ext)s" "<URL>"

# Bilibili-specific: requires cookies to bypass 412 anti-bot error
yt-dlp --cookies-from-browser chrome --extract-audio --audio-format mp3 \
  --audio-quality 0 -o "/tmp/video_audio.%(ext)s" "<BILIBILI_URL>"

# YouTube: usually works without cookies, but cookies help for age-restricted videos
yt-dlp --cookies-from-browser chrome --extract-audio --audio-format mp3 \
  --audio-quality 0 -o "/tmp/video_audio.%(ext)s" "<YOUTUBE_URL>"

# Twitter/X: usually works without cookies
yt-dlp --extract-audio --audio-format mp3 --audio-quality 0 \
  -o "/tmp/video_audio.%(ext)s" "<TWITTER_URL>"
```

**Platform-specific notes**:

| Platform | Cookies needed? | Common issues |
|----------|----------------|---------------|
| Bilibili | Yes (412 error without) | Use `--cookies-from-browser chrome` |
| YouTube | Usually no | Age-restricted/member videos need cookies |
| Twitter/X | Usually no | Some content requires login |
| TikTok | Usually no | Watermarks; use `--no-playlist` |
| Twitch | No | VODs expire; download promptly |

**Troubleshooting yt-dlp**:
- `HTTP 412`: Add `--cookies-from-browser chrome` (or `firefox`/`safari`)
- `HTTP 403`: Try updating yt-dlp first (`pip install -U yt-dlp`)
- `Unable to extract`: Update yt-dlp; site extractors change frequently
- Slow download: Add `--throttled-rate 100K` to retry slow chunks
- Format selection: Use `-F` to list formats, then `-f <format_id>` to pick

### Step 3: Transcribe with Whisper

```bash
# Basic transcription
whisper /tmp/video_audio.mp3 --model base --output_format json \
  --output_dir /tmp/whisper_output --verbose False

# With language hint (faster + more accurate if you know the language)
whisper /tmp/video_audio.mp3 --model base --language en \
  --output_format json --output_dir /tmp/whisper_output --verbose False

# Higher accuracy with small model
whisper /tmp/video_audio.mp3 --model small --output_format json \
  --output_dir /tmp/whisper_output --verbose False

# Word-level timestamps (for finer granularity)
whisper /tmp/video_audio.mp3 --model base --output_format json \
  --word_timestamps True --output_dir /tmp/whisper_output --verbose False
```

**Whisper tips**:
- First run downloads the model (tiny: ~39MB, base: ~74MB, small: ~244MB)
- CPU-only mode uses FP32 (slower but works everywhere)
- For mixed Chinese/English content, don't set `--language`; let Whisper auto-detect
- For English-only content, set `--language en` for better accuracy
- Use `--initial_prompt` to provide context (e.g., proper nouns, domain terms)

### Step 4: Format as Markdown

```python
import json

with open('/tmp/whisper_output/video_audio.json', 'r') as f:
    data = json.load(f)

segments = data.get('segments', [])

def format_time(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

lines = []
lines.append("# <Video Title>")
lines.append("")
lines.append("> **Source**: <URL>")
lines.append("> **Author**: <UP/Channel>")
lines.append("> **Duration**: <duration>")
lines.append("> **Language**: <language>")
lines.append("> **Transcribed by**: OpenAI Whisper (<model> model)")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## Transcript")
lines.append("")

for seg in segments:
    start = seg['start']
    text = seg['text'].strip()
    if text:
        timestamp = format_time(start)
        lines.append(f"**[{timestamp}]** {text}")
        lines.append("")

lines.append("---")
lines.append("")
lines.append(f"*{len(segments)} segments, auto-transcribed by Whisper. Minor recognition errors may exist.*")

output_path = "<output_path>.md"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
```

## Output Format

The final Markdown file should include:
1. **Header**: Video title, source URL, author, duration, language, transcription tool
2. **Transcript body**: Each segment as `**[mm:ss]** text`
3. **Footer**: Segment count and disclaimer about auto-transcription accuracy

## Full Example: Bilibili

```bash
# 1. Get video info
BVID="BV1GWfzBjEV3"
curl -s "https://api.bilibili.com/x/web-interface/view?bvid=$BVID" \
  -H "User-Agent: Mozilla/5.0" \
  -H "Referer: https://www.bilibili.com/" | python3 -m json.tool

# 2. Download audio (with cookies for Bilibili)
/Users/hzd/.local/bin/yt-dlp --cookies-from-browser chrome \
  --extract-audio --audio-format mp3 --audio-quality 0 \
  -o "/tmp/bili_audio.%(ext)s" "https://www.bilibili.com/video/$BVID/"

# 3. Transcribe
/Users/hzd/.workbuddy/binaries/python/versions/3.13.12/bin/whisper \
  /tmp/bili_audio.mp3 --model base --output_format json \
  --output_dir /tmp/whisper_output --verbose False

# 4. Format as Markdown (Python script)
# ... see Step 4 above
```

## Cleanup

After generating the Markdown file, clean up temporary files:
```bash
rm -f /tmp/video_audio.mp3
rm -rf /tmp/whisper_output/
```

## Limitations

- Whisper `base` model may misrecognize proper nouns, technical terms, and code-switching
- Very long videos (>1hr) may need to be split for reliable transcription
- Bilibili cookies may expire; re-export from browser if download fails
- Some platforms rate-limit downloads; add `--sleep-interval 3` if needed
- Auto-generated subtitles (when available) are usually more accurate than Whisper transcription; always check for existing subtitles first
