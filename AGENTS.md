# Instructions for agents working on Kanz Motion

This repo turns a voice note, a written script or a long Kanz video into Kanz Reels. It is its own Git repository
(`github.com/yasserr98/kanz-motion`), **public**: anyone can clone it. In Ahmed's copy it sits inside the Kanz working
folder (`D:\Claude Projects\Kanz\kanz-motion`); the private Kanz repo around it holds brand authority, delivery and logs.

**Owner since 2026-10-30: Youssef.** The main engine is his fork, `github.com/youssef-massoudL/kanz-motion` (remote
`fork`, branch `main`): build on it and push there, never to `origin` (`yasserr98`, the original). Earlier decisions in
DECISIONS.md stay in force until he changes them; engine decisions from 2026-10-30 on are his.

**Rules in force: [docs/RULES.md](docs/RULES.md)** (one line each, with the ids lint and reviews cite). Ahmed's dated
decisions and what each replaced: [docs/DECISIONS.md](docs/DECISIONS.md). If a doc, an old project or an example
disagrees with RULES.md, RULES.md wins.

## Read before a video (only these)

1. `docs/RULES.md`, then the route: [voice note](docs/routes/voice-note.md), [script](docs/routes/script.md) or
   [shorts](docs/routes/shorts.md), and [the image pass](docs/routes/images.md).
2. The worked example's `scene.js`: `examples/us-dollar-decisions-pace` (voice note or script) or
   `examples/short-house-always-wins` (shorts). Never copy an older project: most predate pace.
3. **[docs/MOTION-LANGUAGE.md](docs/MOTION-LANGUAGE.md)** before writing a scene: the motion layer is the main engine
   for graphics (MOT rules): pick the generated piece (`K.mx.*`) that carries each line; library objects only for a
   plain thing. Then look up components in `docs/LOOK-V2.md` / `docs/PACE.md` when you use them, not up front.
   `docs/VOX-RESEARCH-FINDINGS.md` is historical background, not required.

## Which copy you are in

- **Ahmed's copy** (`D:\Claude Projects\Kanz\kanz-motion`): pushes engine, runtime, docs, template, demos and `examples/`.
  Projects are git-ignored: never commit a video's project, script or render here (REPO-1, REPO-4).
- **Any other clone is an editor's copy:** projects, voices and MP4s stay on that machine; never `git add`, commit or push,
  never ask the editor to (REPO-2). They hand the MP4 over directly. Updates: [docs/UPDATE.md](docs/UPDATE.md) (REPO-3).

## Make a video ("create a video", "make a Reel")

Work in this folder, even if the chat opened in the Kanz repo or a Kanz worktree (use the absolute path).

1. **Setup.** `python engine/make.py doctor` once per machine/session; fix every FAIL. Opus (medium) writes
   the storyboard and reviews; Sonnet 5.5 (medium) builds, renders and fixes notes ([EFFICIENCY](docs/EFFICIENCY.md)).
2. **Inputs.** Voice note (file path), written script, or a long video for shorts. Ask only for what is missing.
3. **Voice and script.** Follow the route file to the end of its retime step (VOICE, CAP rules).
4. **Image pass.** `shots.json` from the whole script, a visual type per shot, Codex generates, before the scene is
   written ([images](docs/routes/images.md); IMG, OBJ rules).
5. **Scene.** Copy the worked example's `scene.js` and adapt it; new projects start from `projects/_template`.
   `K.look()`, `K.pace({ defaults: "2026-10-18" })`, `K.motion()`, `K.finish()` last (PACE-1, PACE-2, MOT-1..4). Open on a moving
   illustration (a drawn scene), never a still photo or static icon (HOOK-1..4); no idle motion (PACE-9). Boards arrive built, one carried hero, no snap zooms
   (PACE-3..5), paper world at chapter turns, a moving last board that ends ~0.4 s after the last word, never a hook
   replay (PACE-6); shorts choose face or board by SHORT-7. Numbers as animated diagrams; ideas as drawn scenes
   (`library/scenes/`), icons only support (EXPL-1, EXPL-2). Western digits with ٪ (NUM-3), sizes 28/34 px (TXT-1),
   at most four labels a board (TXT-2), labels never
   repeat the caption (TXT-3), nothing crosses a headline (TXT-6, `headline-cross`), only numbers the voice says (NUM-1). Objects: approved in the manifest only (OBJ-2).
6. **Review.** `python engine/lint.py projects/<slug>`; fix or justify every finding in `lint-ok.json` (REV-1). Then
   `make.py review <slug> <times>` -> look at `out/review.jpg`, fix, repeat (REV-2).
7. **Ship.** `make.py ship <slug> v1`: lint --strict, render locally (explicit `--host` only when Ahmed asks for a VPS job;
   `--local` remains a no-op), 12 frames from the MP4, loudness, the ending, and for shorts the cut strips, title,
   freezes and frame rate. It stops at the first failure (REV-3, REV-4). Look at `out/check-v1.jpg`, `out/cuts-v1.jpg`
   and `out/notes-v1.jpg`, then open the MP4 for Ahmed (`ii <path>`). Run it in the background; do not poll. Review
   notes go in `notes.json` (`make.py note`); small revisions may use render + `check --partial` + notes sheet
   (README, REV-3); proof matches the complaint: final-MP4 still, listened audio or motion interval (REV-7).
8. **Cover** (style A): `projects/<slug>/cover.json` -> `python engine/cover.py projects/<slug>`; check the crop lines in
   `out/cover-review.jpg`.
9. **Record (Ahmed's copy only).** Add a row to the usage log and update the backlog in the Kanz repo
   (`reports/kanz-motion-deliveries/USAGE-LOG.md`, `docs/09-backlog.md`). Deliver to Drive + Airtable only when Ahmed asks,
   from the Kanz repo (`reports/kanz-motion-deliveries/README.md`); the receipt goes there (DEL-1..3). Editors skip this.

Fix requests come as timestamps ("47s there is a sigh"): find the exact moment in the audio/frames before changing
anything, and say where it really was if it differs (REV-5).

## Usage discipline (Claude Pro limits)

- One fresh session per video; Opus (medium) storyboards and reviews; Sonnet 5.5 (medium) builds, renders and fixes
  notes ([docs/EFFICIENCY.md](docs/EFFICIENCY.md)).
- Review through one contact sheet, not image by image. One local Chromium job at a time per machine, across all checkouts:
  `engine/slot.py` queues them using a lock in local app data (REPO-6); "waiting for the local render slot" means queued.

## Brand authority (Kanz repo, when it is alongside)

`docs/21-kanz-visual-identity.md`, `brand/explainer-icons/README.md`, `brand/image-treatment/CREATE-A-BRANDED-IMAGE.md`,
`brand/KANZ-CONTENT-DELIVERY.md`. The brand fonts, Thmanyah Display included, ship in `brand/fonts/` (Ahmed 2026-10-21).

## Repo hygiene

- Never commit `node_modules/`, `library/sfx/raw/`, `out/`, voice audio, `.env`, `delivery.json`, record ids, Drive ids,
  emails or server paths. Only Ahmed's sessions push, and
  only engine, runtime, docs, template, demos and examples. Commits use the GitHub no-reply address set in this repo's
  Git config, never a personal email.
- The public history was cleaned on 2026-10-21 (DECISIONS). A branch started before that is on the old history: rebase
  its own commits onto the current `main` before merging; the pre-push hook refuses pushes that carry the old history.
- Reusable components go in `runtime/` and get documented in README and `docs/` (REPO-5). A new rule from Ahmed goes in
  `docs/RULES.md` (one line, an id) and `docs/DECISIONS.md` (dated, his words) in the same change.
