# Rules in force

One line per rule, with an id that lint findings, reviews and fix requests can cite ("HOOK-1 at 2 s"). Only current
rules are here; where each came from, Ahmed's words and what it replaced are in [DECISIONS.md](DECISIONS.md). The
**Check** column names the `engine/lint.py` finding kind (or tool) that enforces a rule; "eye" means the review sheet.
Component how-tos stay in [LOOK-V2.md](LOOK-V2.md) and [PACE.md](PACE.md). New videos only: finished Reels render as
they were.

## Repo and delivery

| Id | Rule | Check |
| --- | --- | --- |
| REPO-1 | kanz-motion is public. Engine, runtime, docs, template, demos and `examples/` only; never keys, voice recordings, renders, unreleased scripts, record ids, Drive ids, emails or server paths. Commits use the GitHub no-reply address | `.gitignore`, pre-push hook |
| REPO-2 | Editors' copies: projects, voices and MP4s stay on the editor's machine; never `git add`, commit or push there, never ask them to | |
| REPO-3 | Updates come one way through `docs/UPDATE.md`; never `reset --hard`, `clean`, `checkout -- .` or drop a stash in an editor's copy | |
| REPO-4 | `projects/` is local (git-ignored) except `_template` and the `_*-demo` engine demos; worked examples live in `examples/` | `.gitignore` |
| REPO-5 | New reusable components go in `runtime/` (not inside a project) and are documented in README | eye |
| REPO-6 | One local Chromium job (lint, render, stills, cover, contrast) at a time per machine, across all checkouts; renders are local by default, the VPS only for a job Ahmed requests with explicit `--host` | `engine/slot.py` waits on a lock in the user's local app data |
| DEL-1 | Rendered ≠ approved ≠ posted. Deliver to Drive + Airtable (`In Review`) only when Ahmed asks | |
| DEL-2 | Delivery runs from the private Kanz repo: `reports/kanz-motion-deliveries/README.md` (Ahmed's copy only) | |
| DEL-3 | Receipts and the usage log are written in the Kanz repo, never in kanz-motion | `.gitignore` (`delivery.json`) |

## Voice and captions

| Id | Rule | Check |
| --- | --- | --- |
| VOICE-1 | Voice notes: cut retakes by keeping the last clean take; every cut in `audio/edl.json` with its reason (`_why`) | eye |
| VOICE-2 | Voice notes play at 1.25x | `edl.json` |
| VOICE-3 | Re-transcribe the edited voice and read it through: no word lost or doubled | eye |
| VOICE-4 | Script videos: Ahmed's copy uses the instant clone "Ahmed Shaaban Shorts"; never the professional clone. Editors use the voice Ahmed names for their own key | `.env` |
| VOICE-5 | Once the voice is final: `make.py retime <slug>` (script) or `make.py retime <slug> 1.0` (voice note), then write the scene | |
| VOICE-6 | Scripts are pasted verbatim into `script.md`; never rewrite them; flag doubts | eye |
| VOICE-7 | TTS failures: fix in `say.json` (voice-only spelling), add new ones to `library/voice/lexicon.json`; tell Ahmed the EAR times | `voicecheck.py` |
| VOICE-8 | Mute real breaths and sighs (`breaths.py`, `"mute"` in `edl.json`); say which you left in | `breaths.py` |
| VOICE-9 | Once Ahmed picks a pronunciation take, splice that exact audio from its cache/take file; never regenerate the same spelling and assume it matches | ear, cache/take file |
| VOICE-10 | A re-do with "the same voice track" keeps the approved take and retimes it to today's pace (`make.py retime <slug>`: 1.08 tempo, pauses to 0.3 s; voice notes keep their 1.25x and use retime 1.0) (US Dollar v6) | `make.py retime` |
| CAP-1 | Captions come from the corrected `script.md`, never raw ASR; flag uncertain words for Ahmed | `captions.py` |
| CAP-2 | Read the "check these captions" words `make.py` prints (usually digits) | eye |

## Hook and pace

| Id | Rule | Check |
| --- | --- | --- |
| HOOK-1 | Voice-note and script Reels open on an illustration: a drawn scene in the Live C v10 style (`library/scenes/`, Codex mode `kanz`) under the headline, visible on frame 1 and moving with the opening words (it finishes drawing in, or something on it changes). Shorts open on his face instead (SHORT-4) | eye, `hook` |
| HOOK-2 | Opening layout: the headline (the question, or the story's first line) in at most three lines, keyword last in lavender, over the one illustration; nothing else competes until the first line ends; no idle float. When the opening is about a price, percentage or loss, a live diagram moves on or beside the illustration from frame 1 (EXPL-1) | eye (lint `dead` is expected here) |
| HOOK-3 | Captions in the opening: when the headline already shows the question being voiced, `K.captionsFrom` = end of the question; otherwise captions run from frame 1 (`K.captionsFrom = 0`) | `hook`, eye |
| HOOK-4 | No static opening: never a still photo, a still picture or a static icon as the first shot, and no static hero icon in the opening. Full-screen place photos belong on later boards (IMG-4). Replaces the photo openings of quiz 2026-10-20 Q4 and the 2026-10-11 hero icon (Ahmed 2026-10-21) | eye, lint `still-image` |
| PACE-1 | New scenes: `K.look()`, then `K.pace({ defaults: "2026-10-18" })`, and `K.finish()` as the last line | `structure`, `make.py check` |
| PACE-2 | The 2026-10-17 defaults stay on: caption band kept clear, boards arrive built, punch hides the caption, capped fly-ins, marks sized to their element | `caption-band`, `half-built-arrival`, `markup-crossing-text` |
| PACE-3 | Boards arrive built (`K.go` + `at: g.lead`), open close and pull out (`K.frame`); never land on an empty board | `half-built-arrival`, `dead` |
| PACE-4 | Carry one hero between boards (`K.carry`, `K.dim`); never clear a board before building the next | eye |
| PACE-5 | No snap zooms (`K.snap`) or face jump zooms by default; the camera drifts and pulls out | `K.snap` warns |
| PACE-6 | Paper world (`K.world`) at chapter turns. Board ending (shorts choose face or board by SHORT-7): never cut back to the hook or replay an earlier picture. The last line gets its own moving visual that keeps building into the last word, and the video ends about 0.4 s after that word (`K.duration = tLast + 0.4`): no silent tail, no static end card | lint `long-tail`, `hook-replay`; ship `tail`; eye |
| PACE-7 | Variety where the script gives a reason: one `K.punch` on the thesis, `K.stack`/`K.pile` for amounts, `K.swap` for state changes, map/globe + `K.pin` for places | eye |
| PACE-8 | 3D: `K.flip` for myth -> fact, `K.browser` for genuine website screenshots, `K.fold` for a reveal | eye |
| PACE-9 | Nothing idles: no float, bob, shake or wobble on pictures, hook hero included; pictures arrive and sit still, the camera drifts and explanatory pieces move with the words (Live C v10) | lint `idle-motion` warns on float with the 2026-10-18 defaults |

## Pictures

| Id | Rule | Check |
| --- | --- | --- |
| IMG-1 | Every video gets an image pass before the scene is written: `shots.json` from the whole script, then Codex | `codex_assets.py` |
| IMG-2 | Generate with Codex without asking first (`codex_assets.py --jobs 4`); compare icons with the references, regenerate mismatches | eye |
| IMG-3 | Icons follow the approved Kanz icon style whatever the topic; no topic-specific aesthetic | eye |
| IMG-4 | Place or setting -> full-screen photo; real person or moment -> disposable print (`K.snap35`); price, percentage or amount -> moving engine diagram; causes, actors and stories -> a drawn scene in the Live C v10 style (`library/scenes/`), with Kanz icons only as supporting props (EXPL-1) | eye |
| EXPL-1 | Diagram for numbers, drawing for ideas: anything with a price, percentage or amount uses a moving engine diagram (`K.area`, `K.bar`/`K.delta`, `K.count`, `K.stack`, arrows and flows); causes, actors and stories use a drawn scene in the Live C v10 style (`library/scenes/`), one scene per beat, still once drawn in. Never a still chart picture standing in for a number explanation | eye |
| EXPL-2 | Icons support, they don't explain: an icon can be the hero only for a plain thing (a house, a bank, a wallet). No board holds one unchanging picture while the voice explains for more than about 2 s; something on it moves with the words | eye, lint `still-image` (a warning), `dead` |
| IMG-5 | Voice-note and script Reels use the same visual types; a place photo gets a board of its own with text, tags and any explanatory overlay; a photo is never the opening shot (HOOK-4) | eye |
| IMG-6 | No date stamp or credit line on screen; credits for the post caption go in `projects/<slug>/CREDITS.md` | eye |
| IMG-7 | Text over a photo reaches 4.5:1 against its brightest background pixels | `contrast.py` |
| IMG-8 | Real people are never generated or repainted: use real openly licensed photos or press photos of real public moments, with source, licence or credit in `CREDITS.md`. A generated photo-real picture of a real PLACE or setting for a past event is allowed when no real photo of that moment exists; record it as generated in `CREDITS.md` (Gambler's Fallacy v7, Monte Carlo 1913) | eye |
| IMG-9 | Gambling content: never a hijab-wearing character, generated person or photo | eye |
| IMG-10 | Websites on screen are genuine screenshots (URL + capture date in `CREDITS.md`), the main visual of their slide | eye |
| IMG-11 | Disposable prints (`K.snap35`) use the slim frame, `slim: true`: a thin border all round and only a modest strip underneath, not the wide Polaroid margins; the photo stays untouched | eye |
| IMG-12 | Never show a woman from behind (a back view of a girl or woman, alone or in a group) | `kanz-npc-crowd-back-v01` retired in the manifest, so ship stops on it (OBJ-2); eye for generated images |
| OBJ-1 | Objects: approved `library/objects/` or new Codex objects in the fixed icon style; never invent a style for a topic | eye |
| OBJ-2 | Only objects marked `approved` in `library/objects/manifest.json` ship; a candidate needs Ahmed's approval first | `objects.py`; `make.py ship` stops on a library object that is not approved |
| OBJ-3 | New objects move into `library/objects/` only after Ahmed approves them, with their status in the manifest | |

## Look, numbers and text

| Id | Rule | Check |
| --- | --- | --- |
| LOOK-1 | Charcoal grain background, Thmanyah Display headlines, IBM Plex Sans Arabic text | eye |
| LOOK-2 | Lavender `#D5ADEF` is the only pointing colour; red only for genuine losses or risk | eye |
| LOOK-3 | On the paper world, objects and figures keep their contrast (the default darkens them and adds a thin edge) | eye |
| LOOK-4 | No logo by default; if a video adds it, it contrasts with what is behind it (it turns dark on the paper world by itself; check photos, cards and screenshots) | `structure` |
| LOOK-5 | Chart colours stay varied as they are (one neutral chart style was rejected) | |
| LOOK-6 | Rejected, do not rebuild: ground plane, coin toss, isometric 3D bars, depth camera | eye |
| LOOK-7 | No slide counters | `structure` |
| LOOK-8 | Text and label sequences run right -> left; market charts keep time left -> right | eye |
| LOOK-9 | Text stays inside the safe zones (x 120-960 × y 270-1440; 65-1015 above y 1000) | `safe`, `edge` |
| NUM-1 | Show only numbers the voice says; real market figures carry a source on screen and in `CREDITS.md` | eye, `data.py` |
| NUM-2 | No "مثال افتراضي" tag when the voice frames the figures as an example ("خلينا نقول", "لو") | eye |
| NUM-3 | One digit system: Western digits with the Arabic percent sign (`35`, `65٪`), on screen and in captions | `digits` |
| NUM-4 | Bars that compare numbers share one scale and zero baseline (`K.scale`); small true gaps get a bracket | `bars` |
| NUM-5 | A dollar amount is written `$39.8`, the $ on the left of its digits and on their line: `K.money(39.8)` on screen; captions do it by themselves with the 2026-10-18 defaults | `stray-currency` |
| TXT-1 | Size floors in board px: source lines 28 px, labels 34 px | `small-text` |
| TXT-2 | At most four labelled elements on a board at once; split a busier board into two beats | `crowded-board` |
| TXT-3 | No label that repeats the caption word for word; a label adds what the caption doesn't say | `caption-repeat` |
| TXT-4 | No text under objects, captions or other text | `covered`, `text-on-text`, `covered-shape` |
| TXT-5 | Breathing room: a subheadline sits at least `K.GAP` (40 board px) under its headline; `K.under(head, html)` places it | `tight-gap` |
| TXT-6 | Nothing crosses a headline: panel and card edges, grid and chart lines, objects and diagrams start at least `K.GAP` below its last line (move or shrink the panel, not the headline) ; board headlines are marked `data-role="headline"` (`.head` alone is only the display font) | `headline-cross` |
| TXT-7 | A label stays fully visible for at least 0.8 s, except word-timed punch labels | `brief` |

## Motion layer

In force since 2026-10-30 (Youssef). Guide: [MOTION-LANGUAGE.md](MOTION-LANGUAGE.md).

| Id | Rule | Check |
| --- | --- | --- |
| MOT-1 | A graphic carries the idea being said, has one visible moment on that word, and leaves when the line ends; his face otherwise (SHORT-15 still holds) | eye, `window.__motion.intents` |
| MOT-2 | New graphics are generated in brand material (`K.mx.*`, `K.BRAND` tokens and mixes of two tokens, the shared gradients); no new hues, no stock graphics; library objects only for a plain thing | eye |
| MOT-3 | Each reel has its own seeded motion signature (`K.motion()`, seeded by the project folder); a repeated piece or object is intentional (a carried hero, a series signature), never filler | eye, `window.__motion.choices` |
| MOT-4 | `K.motion()` turns on the moving key light, depth dust and camera motion blur; they move light and texture behind the pictures, never the pictures (PACE-9 holds); `K.motion({ atmos: false })` turns the atmosphere off for one reel | eye |
| MOT-5 | Look: Vox-like and flat by default (`K.motion()`: flat brand colour, hard paper shadow, boiling drawn edges); `K.motion({ look: "gloss" })`, depth and 3D only where the idea needs it | eye |
| MOT-6 | Never a light that follows the graphic (a moving light pool or spotlight on the focus); pieces carry their own lighting. `K.mx.light` is removed (a no-op) | lint `follow-light` (warn) |
| MOT-7 | A graphic shares the screen with him (the 50/50 split) or cuts in alone for at most 3 s and cuts back to him (face or split); never a board on its own over 3 s, never a board handing on to another board. Lay boards out for both views (in the split the board shows at 0.8 above the seam, where the subtitles sit). Not waivable: recut | lint `board-alone` (motion-layer shorts) |

## Sound

| Id | Rule | Check |
| --- | --- | --- |
| SND-1 | No music: voice + SFX + room tone only; no generated music | eye |
| SND-2 | SFX only CC0 or explicitly licensed, each in `engine/sfx_library.py` with its source; Sonniss/Mixkit files local only, never committed; generated ones (`sfx_gen.py`) always in a new category, so finished videos keep their sounds | `manifest.json` |
| SND-3 | Room tone under every pause (`K.bed = "room"`), 40% quieter since 2026-10-18 (amplitude x0.6, after any `K.bedUnder`); set `K.bedUnder` per video when it is still too loud | ear, `render.py` `BED_TRIM` |
| SND-4 | Loudness -16 LUFS (± 1) | `make.py check/ship` |
| SND-5 | Mix and master: one sound effect at a time (cues under 0.3 s apart keep the louder; the next effect chokes the last; none longer than 1.4 s), the voice high-passed and gently compressed, effects ducked under speech and kept 6 dB under it, two-pass loudness to -16 LUFS with a -1.5 dBTP ceiling. An approved render gets new sound with `make.py remix <name> <from> <to>` (picture copied bit for bit) whenever a delivered reel is touched again (a revision or a re-upload); no bulk re-run. Scenes write one cue per visual event: none within 0.3 s of another, none on nothing | `render.py` mix 2, `sfx-overlap`, `sfx-orphan` |

## Shorts cut from a long video

| Id | Rule | Check |
| --- | --- | --- |
| SHORT-1 | Source media, photos, face frames and full transcripts stay local (git-ignored) | `.gitignore` |
| SHORT-2 | Leave out passages that attack people by religion or repeat unproven allegations; say why | eye |
| SHORT-3 | Start on a word, drop lines that point back to the long video, end before the next sentence. The ending guard aims for 0.4 s after the last word with a 0.05 s next-word margin and the fade inside the tail; the scene runs to the voice end. Listen to the untrimmed source: the whole audible last word always wins over that margin; add quiet after a verified cut instead of cutting into the word, never leak the next sentence. The guard reports a conflict for a human ear | `footage.py`, `end-cut`, ship ending + leak, ear |
| SHORT-4 | The first 3 s always show his face with a title over it: `K.title()`, a white sticker, no purple; text from `shorts/_titles.json` (3 options per reel, Ahmed picks, option 1 until he does); no subtitles while it shows (`K.title` sets `K.captionsFrom`); long-video (YouTube) shorts: middle of the frame just above the subtitle band (default `y` 1150); workshop/live titles start at y 330, then move wherever the face boxes leave his eyes and mouth clear through all 3 s (Live E used y 190), never a fixed coordinate; Ahmed edits the text and approves on the review page. With the 2026-10-18 defaults `K.title()` takes the text from `_titles.json` and its height from the face boxes (`assets/faces.json`) | `title`, `on-face`, ship title |
| SHORT-5 | Keep a styled TV-set opening (`--tv-until`) and the source's burned-in labels | eye |
| SHORT-6 | Every face <-> motion change is a clean cut in a pause, onto a board built ~0.3 s before; no flash, no white frames | `mid-word-cut`, ship cut strips |
| SHORT-7 | Pick the ending by the last line: his face for his own opinion or punchline, held to ~0.2 s after the last word (Casino E v10); a board when it still explains something or says a number, with its own moving last beat (Casino G v8); never a hook replay or a static held board | eye |
| SHORT-8 | Pay off what the hook promises ("three words" -> three titled beats) | eye |
| SHORT-9 | Every picture belongs to the line; no decorative props | eye |
| SHORT-10 | Before delivery, check 12-frame strips around every cut in the final MP4: `make.py ship` writes `out/cuts-<version>.jpg` and fails on charcoal, flash, half-built and one-frame flags and face-track jumps | ship cut strips |
| SHORT-11 | Workshop/live footage: motion inserts alternate between a 50/50 split screen (tracked face + board) and a full-screen board, clean cuts in the pauses; reuse the shared split/tracking helpers | eye |
| SHORT-12 | In the 50/50 split the subtitles sit in the middle, centred on the seam (on its board side when his face is right under it); on face-only and board-only moments they return to their usual place, never over his eyes or mouth; when his face reaches the band they move down (below his chin, at most to y 1500), never up over his head (`kanz-footage.js` capTopFor) (`kanz-split.js`, `kanz-footage.js`) | `caption-switch`, `on-face` |
| SHORT-13 | Where the voice is joined (two passages or a removed pause), total silence is about 0.25 s (Casino H v12 used a 0.2 s gap); the picture cuts clean. Never place a join or pause from transcript word edges alone: confirm it on the source waveform and by listening. When a syllable sounds clipped, check the source for its own jump cut and show short source/context listening options before choosing. Workshop footage has its dead air tightened by default (`footage_track.py` runs `tighten_footage.py`: pauses over 0.42 s cut to 0.30 s at word boundaries; `--no-tighten` keeps them) | `footage.py` (edges snap into measured pauses), `tighten_footage.py`, ship `joins` (`joincheck.py`), ear |
| SHORT-14 | Shorts cut from long videos and lives: subtitles are always Egyptian Arabic, even where he speaks English (translate the meaning; keep his voice as is; keep the verbatim transcript in a comment in `script.md`). Only for cut-out shorts, not voice-note or script Reels | `captions.py` (Latin words fail) |
| SHORT-15 | Every cut-out short (YouTube and workshop): his face, full screen or in the split, is on screen at least 50% of the runtime; boards only where the line explains a mechanism, says a number or names something, and those inserts move | `face-share` (2026-10-18 defaults; legacy workshop check unchanged) |
| SHORT-16 | Every change to or from his full face is a clean cut (face <-> board and face <-> split), in a pause, never inside a word; no dissolve, crossfade or see-through frame anywhere. Split <-> full-screen board moves ease over 0.35 s (2026-10-18 defaults) | `mid-word-cut` |
| SHORT-17 | No frozen source picture in a face or split window (a stalled stream reads as lag): `assets/freezes.json` from the footage tools lists stalls of 0.5 s or more; choose other source seconds or cover the stall with a full-screen board | `freeze`, ship duplicate frames |
| SHORT-18 | In cut-out shorts, remove accidental stutters, false starts and repeated phrases where a natural cut preserves the meaning; no rewriting speech or deleting deliberate emphasis. Listen from source to final, record each cut and say which could not be removed | cut record, ear |
| SHORT-19 | Q&A shorts (Package 04, `shorts/package-04/work/qakit.js`): the question bubble from `QA.ask` is the title (it calls `K.title`, SHORT-4 holds); graphics only in the 50/50 split with him, never alone; a reel that ends on the `QA.reply` board may run up to 3 s after the last word (the board is read there), the exception to PACE-6's 0.4 s; no attendee name on screen, captions included (write the line as `shown {{spoken}}`) | lint `title`, `long-tail`; ship `tail`; eye |

## Review

| Id | Rule | Check |
| --- | --- | --- |
| REV-1 | Lint every scene; fix each finding or justify it in `lint-ok.json`. Dead stretches (nothing new, camera still) are detected from 2.5 s and thin/empty frames from 1.5 s. An empty stretch (dead or fill) over 1.5 s outside the 0-3 s title window cannot be justified | `lint.py --strict` |
| REV-2 | Review through one contact sheet (`make.py review`), not image by image | |
| REV-3 | A first delivery passes `make.py ship <slug> <version>` and its check sheet is looked at. A revision changing only a few seconds may use render + `make.py check <slug> <version> --partial` (loudness, ending, frames) + the notes sheet for the changed seconds; its receipt says "partial checks passed", never "full ship passed" | `make.py ship/check`; commands in README |
| REV-4 | Renders run locally by default, even with `KANZ_RENDER_HOST` set; use explicit `--host` on render/ship/remix only when Ahmed asks for that VPS job (`--local` remains a no-op). Run in the background, never poll | `make.py render/ship/remix` |
| REV-5 | Fix requests come as timestamps: find the exact moment in the audio/frames first and say where it really was | |
| REV-6 | Check fonts, Arabic joining, overlaps and timing on frames pulled from the MP4 itself | `make.py check` |
| REV-7 | Every review note goes in `projects/<slug>/notes.json` (`make.py note`): time, his words, status and evidence with version/interval. Proof matches the complaint: layout -> still from the final MP4 (`out/notes-<version>.jpg`); audio -> listened interval of the final MP4, with the source when edited; motion/cuts -> played interval or frame strip from the final MP4. An accepted defect is marked `accepted`, never `fixed` | ship notes, ear/playback |
