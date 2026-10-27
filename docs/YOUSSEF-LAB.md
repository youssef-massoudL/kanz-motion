# Youssef Lab

**Owner: Youssef** (created 2026-10-16). A workspace for drafts and experiments: new icons/objects, styles,
3D elements and animations that the current engine (`library/objects/`, `docs/LOOK-V2.md`, `runtime/kanz-3d.js`,
`docs/PACE.md`) does not have yet.

**Everything in this lane is an unapproved draft.** It stays in `library/youssef/` and is not used in final Kanz
output or copied into the main library (`library/objects/`) until Ahmed approves it. The normal approval process in
`AGENTS.md` applies to it unchanged.

## How it works

1. Youssef asks for an asset, style, 3D element or animation the engine lacks.
2. The agent designs and builds it as a draft, aiming beyond what already exists.
3. The draft goes in the matching place:

| Kind | Where | Notes |
| --- | --- | --- |
| Icons / objects | `library/youssef/objects/` | transparent PNG or SVG, `youssef-<subject>-v01.png` |
| Styles / looks | `library/youssef/styles/` (+ CSS via `K.lab.style`) | fonts, colours, grain, light |
| 3D elements | `library/youssef/3d/` (+ components in `runtime/`) | CSS-3D, three.js or pre-rendered |
| Animations | `library/youssef/animations/` (+ `K.lab.add`) | seekable GSAP timelines only, so renders stay deterministic |

4. Each draft gets an entry in `library/youssef/manifest.json` with `"status": "unapproved"` (id, kind, file, date,
   Youssef's request, tool, source or licence) and a line in the changelog below.
5. Reusable components register through `K.lab` (`runtime/kanz-youssef.js`), loaded after `kanz-look.js`,
   `kanz-pace.js` and `kanz-3d.js`.
6. The agent tells Youssef what was built and where.

## Promotion

A draft moves out of this folder only after Ahmed approves it. Then the manifest entry changes to
`"status": "approved"` with the date and Ahmed's note, and the file is copied into the main library or runtime.
Until then, final Reels, covers and deliveries use approved assets only.

## Unchanged rules

SFX are CC0, licensed or generated and logged; websites on screen are genuine screenshots with source and date;
real market figures carry a source; shown numbers are numbers the voice says; `lint.py`, the review sheet and the
render check still run; rendered is not posted.

## Changelog

- 2026-10-16: lane created (`library/youssef/`, `runtime/kanz-youssef.js`, this file).
- 2026-10-16: psychological-biases Reel draft (`projects/psych-biases`: storyboard.html, scene.js on estimated timing): 9 vector props in `library/youssef/objects/` and `K.lab.irisDive`, all unapproved.
- 2026-10-19: psych-biases v4 (`projects/psych-biases/scene.js`, `storyboard-v4.html`): chart hook with drawn technical analysis, blindfold paper, trim-path cockpit, Telegram-style chat, BUY press, news post, plan checklist, polaroid, price stickers. UI pieces are unapproved drafts. Timing is still estimated (no voice, no ElevenLabs key); the previous eye/stage scene is kept as `scene.v2-lab-eye.js`.
