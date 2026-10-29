# Kanz Motion

**Handover workflow: Claude with the Codex plugin.** Start with [HANDOVER-SETUP.md](docs/HANDOVER-SETUP.md) for assistant setup and installation. Static carousels use the separate [Codex-only carousel repository](https://github.com/yasserr98/kanz-carousels).

Turns a voice note into a Kanz-branded, Vox-style explainer Reel (1080×1920), using Kanz's
approved fonts, colours and editorial objects, with timed Arabic captions and sound effects.

The visual system started from the 2026-10-05 research on how Vox builds its explainers
([docs/VOX-RESEARCH-FINDINGS.md](docs/VOX-RESEARCH-FINDINGS.md), historical: where it differs, `docs/RULES.md` wins,
then `docs/LOOK-V2.md` and `docs/PACE.md` for how components work).

## What it does

```
voice note ─► transcribe (word timings) ─► cut retakes, tighten pauses, speed 1.25x
           ─► corrected captions ─► retime 1.0 ─► image pass ─► scene (boards, camera, marks, charts)
           ─► render frames in Chromium ─► mix voice + SFX ─► MP4
```

- **One continuous world**: each beat lives on a "board"; the camera travels between boards
  (right → left, like reading Arabic) instead of cutting between slides.
- **Everything is timed to the voice**: `T("word")` returns when that word is spoken.
- **Vox devices, Kanz look**: hand-drawn ovals, underlines and arrows that "boil", lavender
  highlights, paper cards with tape, charts that draw on, big numbers, a hook headline,
  captions with one keyword in lavender, 24 fps motion with the grain and "boil" kept stepped, and fine grain
  (`docs/PACE.md`).
- **Sound**: every element registers a cue (paper, tape, marker, click, pop, whoosh, coin, hit, fire);
  the renderer mixes them under the voice from `library/sfx/` (CC0 sounds plus licensed generated effects, see Licences).
- **Effects**: `K.fire(board, cx, baseY, w, {at, out, h})` draws brand-coloured fire (lavender core to deep plum,
  flickering tongues, rising embers, pulsing glow) with a CC0 crackle (BigSoundBank s0987); first used for the
  volcano in the Risk Management Reel (a project local to Ahmed's copy).

- **Shorts from a long video** (2026-10-16): `engine/footage.py` cuts the speaker's face, voice and word timings
  from a long Kanz video into a project; `runtime/kanz-footage.js` (`K.footage`) alternates that face with the motion
  boards, captions running across both, with a clean cut onto an already-built board at every change (`xstyle`); `--tv-until` keeps a styled
  source opening (the speaker in a TV set) and zooms into the face. Route: [docs/routes/shorts.md](docs/routes/shorts.md).
- **Photos and Codex images** (2026-10-16): `K.screen()` (`runtime/kanz-snap.js`) fills the frame with a photo of a
  place and darkens the headline and caption bands as much as that photo needs; `K.snap35()` shows a real, licensed
  photo of a person or moment as a disposable-camera print (no date). `engine/codex_assets.py` generates a video's
  photos and icons with Codex from `shots.json`; `engine/contrast.py` checks every headline on the rendered frame (4.5:1).
  The template loads it, so voice-note and script Reels use the same image-pass workflow as the shorts.
- **Motion layer** (2026-10-30, the main engine for graphics; both templates call it): `K.motion()` (`runtime/kanz-motion.js`) adds generated,
  on-brand pieces that visualize the line itself instead of a library PNG: kinetic headlines (`K.mx.words`), rolling
  numbers, a value slab that breaks (`K.mx.shatter`), a vessel that fills or drains, rings, a risk gauge, money flows
  and journey paths, plus a soft background key light and camera motion blur. Flat Vox cut-paper look by default
  (`look: "gloss"` for depth); never a light that follows the graphic (MOT-6). Brand stays fixed, motion is seeded
  per reel. Guide: [docs/MOTION-LANGUAGE.md](docs/MOTION-LANGUAGE.md); references it grows from:
  `library/references/`; demo: `projects/_motion-demo`.
- **Rendering** (quiz 2026-10-20, Q8): local by default, one Chromium job at a time across all checkouts.
  `KANZ_RENDER_HOST` alone never routes a job remotely. Only when Ahmed asks, add `--host` to
  `make.py render`, `ship` or `remix`; `--local` remains an accepted no-op.

## Setup (once, on a new computer)

Needs Python 3.11+, Node.js 18+, `ffmpeg` on PATH and (for voice notes) [`uv`](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/yasserr98/kanz-motion.git
cd kanz-motion
npm ci
python -m pip install -r requirements.txt
python -m playwright install chromium
python engine/make.py doctor                    # checks tools, fonts, keys, render host, Codex, references
python engine/make.py review us-dollar-decisions-pace 3,20,45   # smoke test: examples/us-dollar-decisions-pace/out/review.jpg
```

For ElevenLabs copy `.env.example` to `.env`: set `ELEVENLABS_API_KEY` to your key and `ELEVENLABS_VOICE_ID` to the
voice Ahmed names for that key (VOICE-4; never commit `.env`). With a key,
the engine also uses ElevenLabs for transcription (Scribe v2, which tags coughs/sighs), for timing
captions to the exact script (forced alignment, cached), for the optional voice isolator and for
generated sound effects. Without one it falls back to local faster-whisper. A Freesound key is optional.

## What to connect, and what each one unlocks

The engine runs on your computer. These accounts and tools make more of it work; none of their keys or ids ever go
into this repo.

**For making videos (anyone with a copy):**

| Connect | Needed? | What it unlocks |
| --- | --- | --- |
| **Claude** (Claude Code / the Claude desktop app) | Yes | The operator. It reads `AGENTS.md`, plans the storyboard, writes the scene, runs every step and reviews the contact sheets. Opus plans and reviews, Sonnet builds ([EFFICIENCY](docs/EFFICIENCY.md)). |
| **Codex CLI**, signed in | Strongly recommended | The image pass: from the shot list it draws icons and explanatory scenes in the approved Kanz style and makes full-screen place photos (`engine/codex_assets.py`). Without it, use the approved `library/objects/` and `library/scenes/`. |
| **ElevenLabs** API key | Recommended | Accurate transcription with word timings that also marks coughs and sighs, captions locked to the exact script, a voice cleaner for noisy notes, and new sound effects. Without it, transcription runs locally (slower, less exact) and there is no written-script route. |
| **Ahmed's voice on ElevenLabs** | For written scripts | A written script becomes a voiceover in his voice (the "Ahmed Shaaban Shorts" clone), with known mispronunciations fixed automatically (`library/voice/lexicon.json`). The clone lives in Ahmed's ElevenLabs account: Ahmed's copy uses it directly; anyone else uses the voice Ahmed names for their own key. |
| **yt-dlp + OpenCV** (`requirements-shorts.txt`) | For shorts | Downloads a long YouTube video or X Live and follows his face around the frame, so shorts can be cut from it. |
| **Freesound** key | Optional | Searching for more free (CC0) sound effects. |
| A render server (`KANZ_RENDER_HOST`) | Optional | Renders on a server instead of this computer, only when Ahmed asks for that job (REV-4). |

**For the Kanz team's publishing side (Ahmed's private Kanz repo, not this one):**

| Connect | What it unlocks |
| --- | --- |
| **Airtable** (Kanz Content) | Every piece's record: the approved script, its status (In Review, Ready to be posted, Posted), the Drive link, the caption and the posting dates. Connected, Claude takes the approved script from the record and updates status, caption and links after delivery. |
| **Google Drive** (Kanz Content folder) | One folder per Reel holding the final `01.mp4`. Airtable links to it and Metricool takes the video from it. |
| **Metricool** | Scheduling and auto-publishing Reels to TikTok, Instagram, Facebook, X and YouTube at the agreed times, after Ahmed's go-ahead for each batch, and confirming when each one is live. |
| **Apify** | Web data on request: checking what is actually live on each platform so the accounts stay in sync, pulling Ahmed's articles, and finding reference videos for research. Paid per run. |

GitHub is not needed to get or update this repo (it is public); only Ahmed's copy pushes.

## Make a video from a voice note

```bash
python engine/make.py new my-video "path/to/voice-note.m4a"
python engine/make.py clean my-video            # optional, noisy notes: isolated voice to compare
# 1. read projects/my-video/transcript.raw.json, write projects/my-video/audio/edl.json (keep last good takes)
python engine/make.py audio my-video            # also writes script.md, prefilled from the transcript
python engine/make.py breaths my-video          # sighs/breaths to mute: audio/edl.json "mute"
# 2. correct projects/my-video/script.md (fix recognition slips, mark *keywords*)
python engine/captions.py projects/my-video     # corrected captions, never raw ASR
python engine/make.py retime my-video 1.0       # tighten pauses; audio is already 1.25x
# 3. image pass: shots.json from the whole script, then assets (docs/routes/images.md)
# 4. write scene.js using examples/us-dollar-decisions-pace
python engine/lint.py projects/my-video         # safe zones, dead stretches, thin frames: out/lint.jpg
python engine/make.py review my-video 2,10,30   # one contact sheet: out/review.jpg
python engine/make.py ship my-video v1          # lint --strict, render, MP4 frames, loudness; stops at the first failure
```

## Make a video from a written script (ElevenLabs)

```bash
python engine/make.py script my-video           # then paste the copy into script.md, mark *keywords*
python engine/tts.py --list-voices              # use the voice Ahmed names for your key: ELEVENLABS_VOICE_ID
python engine/make.py sample my-video 1.0       # compare with sample my-video 1.15; Ahmed picks the speed
python engine/make.py tts my-video <speed>      # use Ahmed's chosen speed; full voice + timings + captions
python engine/make.py retime my-video           # pace: pauses to 0.3 s, 1.08x, captions re-timed (docs/PACE.md)
# image pass: shots.json from the whole script, then assets (docs/routes/images.md)
# write scene.js using examples/us-dollar-decisions-pace, then review / ship as above
```

The worked scenes are current teaching copies; the delivered Reels used an older look. Renderability without local media:

| Example | What to copy | Fresh clone |
| --- | --- | --- |
| `examples/us-dollar-decisions-pace` | Script scene; also the scene for a voice note | Stills work with tracked timings/assets; full MP4 needs private voice audio |
| `examples/short-house-always-wins` | Shorts scene | Needs local face frames, voice and title-registry setup; cannot render the complete example as supplied (see its README) |
| `examples/what-is-inflation` | Voice-note audio edit list and corrected captions only | No scene or voice media; cannot render |

Your own videos live in `projects/`, which Git ignores. **Before making videos in volume read [docs/EFFICIENCY.md](docs/EFFICIENCY.md)**:
which model to use, how to keep each video cheap, and the usage log.

Opus (medium) writes the storyboard and reviews; Sonnet 5.5 (medium) builds, renders and fixes notes, with one
fresh session per video. A re-do with the same voice keeps the approved take and runs `make.py retime <slug>`
(1.08 tempo, pauses to 0.3 s); voice notes retain 1.25x and use `make.py retime <slug> 1.0` (VOICE-10).

Voice-note/script Reels open on an illustration: a drawn scene in the Live C v10 style under the headline, visible on
frame 1 and moving with the opening words; never a still photo or a static icon as the first shot (HOOK-1..4, Ahmed
2026-10-21). Captions wait for the end of the question only when the headline already shows it (HOOK-3).
Pictures arrive and sit still, including the hook hero; legacy `float` still works but current-profile lint warns
`idle-motion` (PACE-9). Prices, percentages and amounts use moving engine diagrams; causes, actors and stories
use drawn scenes in the approved [Live C v10 style](library/scenes/README.md) (EXPL-1, IMG-4).
A past event's real place/setting may be photo-real generated when no real photo of that moment exists; label
it generated in `CREDITS.md`. Real people are never generated or repainted (IMG-8).

Every cut-out short, YouTube or workshop, shows his face full screen or in the split for at least 50% of its
runtime (SHORT-15; enforced on the current defaults, legacy workshop checks unchanged). Pick the ending by
the last line: his opinion/punchline ends on his face, ~0.2 s after the last word; an explanation/number gets
its own moving last board, never a hook replay or static held board (SHORT-7).

## Small revisions

A first delivery must pass `make.py ship <slug> v1`. For a revision changing only a few seconds (REV-3), record
each changed interval in `notes.json`, render, then check the final MP4:

```bash
python engine/make.py note <slug> 12.5 "12.0-14.0 s: his words and the requested fix" v1
# apply the fix; record version/interval and evidence matching the complaint in notes.json (REV-7)
python engine/make.py note <slug> fixed 1
python engine/make.py render <slug> v2
# once the background render completes:
python engine/make.py check <slug> v2 --partial
```

Run the render in the background, without polling. `check --partial` fails on problems and checks loudness, ending and
MP4 frames; it also writes `out/check-v2.jpg` and `out/notes-v2.jpg` from the required notes entries. Ordinary `check` and `ship` retain all shorts checks
(including a fresh lint stamp); `--partial` skips those full-short checks and is accepted only by `check`.
Look at the check and notes sheets for the changed seconds; listen to audio changes and play motion changes,
recording the version and interval as evidence. Use the actual note number instead of `1` above.
The receipt in the private Kanz repo must say **"partial checks passed"**, never **"full ship passed"**.
Changes beyond a few seconds use `ship` again.

## Live/workshop shorts: tracking and split

For shorts cut from Ahmed's 16:9 X Live workshops (Ahmed 2026-10-17: the camera tracks him; inserts alternate between a
50/50 split and a full-screen board). Built for the Volume short (a project local to Ahmed's copy); reuse it, do not
rebuild it.

1. **Frames (use instead of `footage.py`, same arguments):**
   `python engine/footage_track.py projects/short-<slug> shorts/<live>/source/video.mp4 shorts/<live>/transcript.raw.json <start> <end> [--video-from S]`
   Writes `assets/face/` (1080x1920 tracked 9:16), `assets/half/` (1080x960 tracked crop for one split half), `audio/voice.wav`,
   `transcript.json`, `assets/track.json`, and `assets/track-check.jpg` (8 source frames, yellow = 9:16 crop, pink = half
   crop): open it and confirm his face stays inside both. It prints the share of samples where a face was found and the
   largest camera step; a step under ~3 px/frame glides. Slow: about 5 s of work per second of video, run it in the
   background. Options: `--zoom` (tighter 9:16), `--half-h` (source px high in the half, default 560; smaller = tighter on
   the face), `--face-y` (face height in the half, default 0.42), `--no-half`. No `--tv-until` (use `footage.py` for a TV opening).
2. **Scene:** load `runtime/kanz-footage.js` and `runtime/kanz-split.js` in `index.html` (after kanz-3d.js), then, after
   `K.look(); K.pace({ defaults: "2026-10-18" });` (bare `K.pace()` is legacy compatibility):
   ```js
   K.footage({ dir: "assets/face", n: N, end: END, windows: [[0, 3.2], ...] });   // full-screen face (first 3 s always)
   K.split({ dir: "assets/half", n: N, windows: [[a, b], ...] });                // split: face half + board half
   // anywhere outside both = full-screen board
   ```
   Face windows and split windows must not overlap; alternate split and full-screen boards, cutting in the pauses, and
   build each board ~0.3 s before its cut (`PRE = 0.3`). `K.split` options: `face: "bottom"` (default: board on top,
   his face below, the captions cover his chest; `"top"` puts the face under the platform bar), `boardScale` (0.8),
   `boardY` (board centre: 590 / 1205), `sfx: true` for whooshes. The board half is the normal world scaled and clipped,
   so the same K.* objects work in both layouts; keep board objects between y 250 and 930 of the 1000x860 board's
   centre and a headline short.
3. **Check:** `python engine/make.py review <slug> <times>` and pull a split moment, a full-board moment and a face moment.
   Source overlays (the Kanz logo, the "WARSHA1015" promo box, the name tag) can fall inside the crop when he leans right;
   they are the source's own, check them in the stills. Tracked guard demo: `projects/_guards-demo`;
   a real split-footage demo needs local media.

## Review guards (2026-10-18)

The notes Ahmed kept repeating on the shorts are engine defaults and failing checks now (docs/RULES.md lists each rule
with its check; `projects/_guards-demo` shows every one, clean and broken):

- **Footage tools** (`footage.py`, `footage_track.py`): every edge snapped into a measured pause (`pauses.py gaps`;
  no pause, no cut), `--also S E` voice joins with a 0.25 s pause, dead air tightened by default for workshops, then
  `engine/faces.py`: `assets/faces.json` (eyes-and-mouth box per frame) and `assets/freezes.json`.
- **Runtime** with `K.pace({ defaults: "2026-10-18" })`: `K.title()` takes its text from `shorts/_titles.json` and its
  height off his face; subtitles move off his face; `K.split` eases to and from a full board (cuts to and from his
  face stay clean); `K.money(39.8)` keeps `$39.8` together in Arabic text; `K.under(head, html)` leaves `K.GAP` px of
  breathing room. Each can be switched on alone in an older scene (`ease: true`, `faces: true`, `gap: true`).
- **Lint** (`engine/guards.py`): on-face, freeze, title, end-cut, face-share, mid-word-cut, caption-switch, sfx-overlap,
  sfx-orphan, stray-currency, tight-gap, headline-cross (TXT-6); `lint-ok.json` cannot excuse an empty stretch over 1.5 s after the title.
- **Ship** (`engine/shipcheck.py`): the ending, the next-sentence leak, the title pick, duplicate frames in face windows,
  frame rate, face-track jumps, `out/cuts-<version>.jpg` (12 frames around every cut, flagged frames outlined) and
  `out/notes-<version>.jpg` (a still for every note in `notes.json`; `make.py note`). `make.py remix` runs the sound
  checks only.

## Layout

| Path | What |
| --- | --- |
| `engine/` | `make.py` (step runner), `transcribe` (Scribe / Whisper), `tts`, `align` (forced alignment), `captions`, `edit_audio`, `breaths` (sighs to mute), `retime` (pace: pauses + tempo), `voicecheck` (TTS failures, `library/voice/lexicon.json`), `render`, `contact` (review sheets), `lint` (pre-render checks), `doctor` (setup check), `objects` (object approval status), `contrast` (headline contrast over photos), `cover` (Reel cover, style A), `data` (real series for charts, with sources), `codex_assets` (images and icons through Codex, from `shots.json`), `footage` (shorts cut from a long video), `footage_track` (workshop shorts with a tracked camera), `pauses` (measured cut points when Whisper glues words), `tighten_footage` (dead air out of footage shorts), `faces` (face boxes and freezes), `shortinfo` (what the engine knows about a short), `guards` (lint checks from Ahmed's recurring notes), `shipcheck` (checks on the rendered MP4), `slot` (one Chromium job per machine), `sfx_library`, `sfx_gen` (generated SFX), `eleven` (API client), `provenance` (hashes for voice-derived timings), `console` (UTF-8 output), `vps_render.sh` (render on a server, only with explicit `--host`) |
| `runtime/` | `kanz.js` (timeline + components) and `kanz.css` (brand tokens, layout); `kanz-look.js/.css` look v2 (safe zones, light, depth, documents, photos, maps, counting numbers, piles), see [docs/LOOK-V2.md](docs/LOOK-V2.md); `kanz-pace.js` pacing layer (arrive built, drift, carry, room tone, frame guard), see [docs/PACE.md](docs/PACE.md); `kanz-3d.js` (`K.flip`, `K.browser`, `K.fold`, worked example `projects/_3d-demo`); `kanz-snap.js` (`K.screen` full-screen photos, `K.snap35` disposable prints); `kanz-footage.js` (`K.footage`, face windows for shorts); `kanz-split.js` (`K.split`, the 50/50 workshop split); `kanz-workshop.js` (opt-in workshop editor preset: `K.cutBefore`, `K.boardSwap`, `K.candleSeries`, `K.onScreenSounds`, see [docs/routes/workshop-editor-preset.md](docs/routes/workshop-editor-preset.md)) |
| `brand/` | Kanz fonts (Thmanyah Display, IBM Plex Sans Arabic with its OFL licence), logo and colour tokens (from the Kanz repo's `assets/kanz-brand-current`) |
| `library/objects/` | grayscale editorial objects (from the Kanz motion library), `manifest.json` (approved / candidate status of each) and their `PROVENANCE-*.md` generation records |
| `library/scenes/` | the four approved drawn-scene references (Live C v10 style) and their prompts, for causes, actors and stories (EXPL-1) |
| `library/backgrounds/` | the approved charcoal grain background |
| `library/sfx/` | 124 CC0 one-shots + generated effects (register, riser, shutter) (`generated.json`, prompt per file) + `manifest.json` (source page and licence for each file) |
| `library/voice/` | `lexicon.json`: words the cloned voice gets wrong (`replace` respellings, `watch` flags) |
| `projects/_template/` | what `make.py new` / `make.py script` copy into a new project; `projects/_*-demo/` engine demos (no voice, not for posting) |
| `projects/<name>/` | one video: audio edit list, transcripts, `script.md`, `scene.js`, `shots.json`, `CREDITS.md` (sources, licences, post-caption credits). Local only: Git ignores your projects |
| `examples/<name>/` | current teaching copies of worked examples, with local-media requirements above; without record ids or receipts |
| `shorts/<video>/` | candidate moments and picker pages for shorts cut from a long video; source media, photos and full transcripts stay local |
| `tests/` | `python -m pytest tests` (engine), `runtime_checks.py` and `golden_stills.py` (runtime), `RUNTIME-REVIEW.md` |
| `docs/` | `RULES.md` (rules in force, with ids), `DECISIONS.md` (Ahmed's dated decisions), `routes/` (voice note, script, shorts, image pass), `LOOK-V2.md`, `PACE.md` (look and pace components), `HANDOVER-SETUP.md` and `UPDATE.md` (editors), `EFFICIENCY.md` (model choice, lean sessions), `CODEX-ASSET-REQUESTS.md` (object batches), `VOX-RESEARCH-FINDINGS.md` (2026-10-05 research, historical) |
| `voice-clone/` | local only (git-ignored) |

## Rules

Read [AGENTS.md](AGENTS.md) (the checklist) and [docs/RULES.md](docs/RULES.md) (the rules in force) before changing
anything. In short: keep the approved Kanz visual identity, make new objects only through Codex following the Kanz MD
rules, and never put real market numbers on screen without a source.

## Licences

- SFX: CC0 (Kenney.nl and BigSoundBank), plus seven effects generated with ElevenLabs on a paid plan, each in its own category and listed with its prompt in `library/sfx/generated.json`. ElevenLabs: paid plans include a commercial licence, without attribution ([help centre](https://elevenlabs.io/docs/help-center/legal/can-i-publish-the-content-i-generate-on-the-platform), checked 2026-10-21). See `library/sfx/manifest.json`.
- GSAP: free under the GreenSock standard licence (npm).
- Fonts: IBM Plex Sans Arabic is SIL OFL 1.1 (IBM Corp., reserved name "Plex"); the licence is in
  `brand/fonts/OFL-IBM-Plex.txt`. Thmanyah Display (Thmanyah) ships in `brand/fonts/` by Ahmed's decision
  (2026-10-21); its own licence terms are in the font file.
- Objects, logo and brand assets belong to Kanz.

## Sharing this repo

The repo is public: send the link. No GitHub account is needed to clone or update it, only Git installed
(`git clone https://github.com/yasserr98/kanz-motion.git`). A "Download ZIP" copy works too: `docs/UPDATE.md`
updates either kind of folder, with or without Git. Editors only pull; their projects and videos stay on their
machine and never go back to GitHub (AGENTS.md, "Which copy you are in"). They get the engine and shared assets:
engine, brand fonts, objects, drawn scenes, sounds and the worked examples. They do **not** get `.env` (keys),
voice-note audio or rendered videos; each person uses their own ElevenLabs key. Treat Kanz objects and logo as Kanz-only, not for
other brands.
