# Motion language: one brand, not one template

> **Status (2026-10-30): the main engine for graphics** (Youssef; DECISIONS 2026-10-30, rules MOT-1..5 in
> [RULES.md](RULES.md)). `runtime/kanz-motion.js` + `kanz-motion.css`; both templates call `K.motion()`. Projects that
> never call it (everything made before) render exactly as before. Worked demo: `projects/_motion-demo/` (no voice,
> every piece once). **Direction:** Vox-like and flat by default; depth and 3D only where the idea needs it (MOT-5). The
> first pieces lean glossy: moving them toward paper and drawn strokes is the next pass.

## Why this exists

The reels were fast to make and recognisably Kanz, but every insert was built the same way: an approved PNG from
`library/objects/`, a label, a reframe. With about 50 objects in use, the same phone, coins and receipt came back
reel after reel, everything sat flat on the charcoal, and a graphic often appeared because a board needed something
on it. The look was right and the motion was absent.

This layer keeps everything that makes a reel look like Kanz and frees how the ideas move. Pieces are **generated
for the line** (a balance that breaks, a vessel that refills, money that leaves), drawn in brand material, and
animated so the change lands on the word. Repeats are allowed only when they are meant.

## 1. What never changes (the brand)

These make a reel look like Kanz from its first frame. They are not up for variation.

| Constant | Value |
| --- | --- |
| Colour | Tokens from `brand/tokens.json`: black `#08070b`, purple-black `#11081a`, purple `#38104d`, purple surface `#281339`, lavender `#d5adef`, white, body `#eee6f2`. Mixes of two tokens are allowed (`K.BRAND.lavShade`, `lavLight`); new hues are not |
| Pointer | Lavender is the only pointing colour; red `#e0605a` only for a real loss or risk (LOOK-2) |
| Type | Thmanyah Display for headlines and numbers, IBM Plex Sans Arabic for text; Western digits with ٪ (NUM-3) |
| Ground | Charcoal grain, the vignette, the key light; the paper world at chapter turns |
| Layout | His face, the 50/50 split, the full board, the white title sticker, the caption pill: the template stays (his call, 2026-10-30) |
| Material | Generated pieces use the same surfaces (section 4), so a vessel, a gauge and a panel feel like one set |
| Sound | Voice + SFX + room tone, no music (SND-1); one sound at a time (SND-5) |

## 2. What roams (free, within the brand)

| Free | How |
| --- | --- |
| **Which device carries the idea** | Chosen for the line (section 3), not from a shelf. The same idea can be a vessel in one reel and a ring in the next |
| **The reel's motion signature** | `K.motion({ seed: "<slug>" })` seeds `K.vary()`: each reel draws its own entrance family (rise, mask, scale, slide) and key-light side, and keeps them for the whole reel, so one reel is consistent and the next differs. Renders repeat exactly |
| **Composition** | Where pieces sit on the board, how big, what is carried from beat to beat |
| **Pacing inside a beat** | How long the build takes, where the change lands, how the camera frames it |

To fix a choice by hand: `K.motion({ seed: "...", pin: { enter: "mask", words: "rise" } })`. Every choice a render
made is in `window.__motion.choices`.

## 3. Intent: a graphic must earn its place

Retention is the reason a graphic exists. Every piece answers three questions before it is built:

1. **What is he saying at this moment?** One idea: a number changing, a loss, money moving, a risk level, a path, a claim.
2. **What does the viewer see change?** The piece's moment (the break, the fill, the needle crossing red) lands on
   the word that says it. A piece with no moment is decoration.
3. **When does it leave?** On screen while its line lasts, then his face again. Face share stays 50% or more (SHORT-15).

| He is saying | Device | Kit piece |
| --- | --- | --- |
| a value goes up or down | the value itself rolls | `K.mx.roll` |
| part of something is lost (a loss, a fee, a cut) | the thing breaks and the part falls away | `K.mx.shatter` |
| how much is left, how much to get back | a container fills or drains | `K.mx.vessel` |
| a share or a percentage of a whole | a ring closes | `K.mx.ring` |
| money moves from someone to someone | coins travel | `K.mx.flow` |
| a level: risk, leverage, emotion | a needle swings, red past the limit | `K.mx.gauge` |
| a journey, a timeline, start and end | a line draws, the unknown end is dashed | `K.mx.path` |
| the claim, the question, the thesis | the words themselves land | `K.mx.words` |
| "look here" | the light moves to it | `K.mx.light` |

Record the intent in the call (`idea`, `why`) or with `K.mx.intent({at, out, idea, device, why})`; the list is in
`window.__motion.intents` for review. **Repeats are fine when they are meant**: the same vessel across one reel (a
carried hero), or the same piece across a series as its signature. A repeat because nothing else was at hand is
the thing this layer replaces.

## 4. Material: how generated pieces look

- **Surface** (`K.mx.panel`, the vessel body): purple-black glass, a 1 px top highlight, a lavender rim light from
  above, a deep soft shadow. `tone: "charcoal"` for the neutral or "other side" (the broker, not you).
- **Value fill**: a lavender gradient from `lavLight` to `lavShade` with a glass highlight strip on the left.
- **Loss fill**: the same gradient in red, used only once something is lost.
- **Light**: the atmosphere's key light drifts slowly behind the world; `K.mx.light` slides a lavender pool to the focus.
- **Depth**: dust motes at three depths move with the camera (parallax); camera moves get a directional motion blur
  that peaks mid-move. Glows (`#kmx-glow`) only on what is active: a path's head, a crack.
- **Type in pieces**: numbers in Thmanyah Display; labels with `K.text` / `K.tag` so lint reads them.

## 5. How Kanz moves (motion tokens)

| Token | Ease | Used for |
| --- | --- | --- |
| `K.EASE.land` | expo.out | arrivals: fast in, long settle |
| `K.EASE.lift` | power4.out | text and panels revealed |
| `K.EASE.snap` | back.out(1.5) | small emphatic pieces (tags, nodes) |
| `K.EASE.settle` | back.out(2.2) | needles and values that overshoot once, then stop |
| `K.EASE.glide` | sine.inOut | light and slow reframes |
| `K.EASE.fall` | power2.in | what is lost drops away |
| `K.EASE.flow` | power2.inOut | money and paths travelling |

Durations: `K.DUR.quick` 0.28 s, `beat` 0.5, `hold` 0.8, `long` 1.2; word stagger `K.STAGGER` 0.07 s.

Principles: arrivals come out of a soft blur (a camera finding focus, not a pop); what is lost falls with gravity, it
does not fade; a value that changes rolls, it does not swap; the surface of a liquid moves only after it was
disturbed, then settles. **Kept from the rules:** no idle float, bob or wobble on pictures (PACE-9), no snap zooms
(PACE-5), none of the rejected ground plane, coin toss, isometric bars or depth camera (LOOK-6), clean cuts to and
from his face (SHORT-16).

## 6. The kit (runtime/kanz-motion.js)

Load `runtime/kanz-motion.css` after `kanz-look.css` and `runtime/kanz-motion.js` after the other runtime files (the
templates already do). In `scene.js`: `K.look(); K.pace({ defaults: "2026-10-18" }); K.motion({ seed: "<slug>" });`.
Positions are board pixels; every piece takes `at`, most take `out`, `idea`, `why`, `sfx` (false to mute).

| Call | What it draws |
| --- | --- |
| `K.mx.words(b, "خسرت *50٪*؟", {x, y, size, at, style, w})` | words land in reading order; `*starred*` runs (spaces allowed) turn lavender with a drawn underline. One line unless `w` is set |
| `K.mx.roll(b, {x, y, from, value, at, countAt, dur, prefix, suffix, size, max})` | odometer number (integers); `.to(t, v, dur, ease)` for later changes; give `max` if a later value has more digits |
| `K.mx.vessel(b, {x, y, w, h, max, from, value, at, fillAt, dur, loss})` | a container that fills or drains; `.to(t, v)` |
| `K.mx.shatter(b, {x, y, w, h, keep, from, to, prefix, at, breakAt, fallTo})` | a value slab (x, y = its base) cracks at `breakAt`; the lost part turns red and falls, the number rolls down to what is left |
| `K.mx.ring(b, {x, y, r, from, value, at, countAt, prefix, suffix})` | progress ring (0..1), counter-clockwise from the top, number in the middle |
| `K.mx.gauge(b, {x, y, r, value, danger, at, label})` | a dial (0..1); the needle overshoots once; past `danger` the arc is red; `.to(t, v)` |
| `K.mx.flow(b, {from: [x, y], to: [x, y], at, until, rate, travel, symbol, loss})` | coins stream along an arc |
| `K.mx.path(b, {points, ghost, labels, labelBelow, nodes, at, dur})` | a line draws with a lit head, nodes pop as it passes (`nodes`: only these point indices); `ghost: true` makes the last point a dashed unknown |
| `K.mx.coin(b, {x, y, size, symbol, at})` | one brand coin, the flow's coin on its own ("the same dollars") |
| `K.mx.panel(b, {x, y, w, h, at, tone})` | the brand surface to hold other pieces |
| `K.mx.light(b, {x, y, size, at})` | a light pool; `.to(t, x, y, size)`, `.out(t)` |
| `K.mx.enter(el, t, {style})` / `K.mx.exit(el, t)` | the brand entrance and exit for any element |

Rolling numbers sit in a left-to-right box: an Arabic unit goes in `prefix` so it lands on the number's left and reads
«100 سنة» right to left (as `suffix` it reads «سنة 100»). `$` stays a prefix, `٪` a suffix.

Lint knows the pieces (`engine/lint.py` counts `svg.kmx` shapes and panels as objects). The odometer draws its digits
and `$` from CSS, laid out left to right, so the dollar sign always sits on the left of its digits (NUM-5).

## 7. Growing it from references

The kit is meant to grow from what you point at, not from guesses. The loop:

1. **Drop the reference** in `library/references/media/` (local only, never committed) and add an entry to
   `library/references/references.json`: what to take (a motion, a transition, a composition, a type treatment), what
   not to take, and which idea type it serves. Format: [library/references/README.md](../library/references/README.md).
2. **Build it as a variant, not a copy**: a new entrance goes into `K.mx.ENTER` with `ref: "<reference id>"`; a new
   device becomes a `K.mx.<name>` piece. Use the brand material (section 4), the tokens (section 5) and the building
   blocks: `K.mx.track(v0)` (a value over time, deterministic for any seek), `K.onFrame(fn)` (per-frame drawing),
   `K.mx.svg` / `K.mx.el` (SVG in board pixels), `K.vary` (seeded choice).
3. **Show it in `projects/_motion-demo`** on a real line, render, review the frames, then mark the reference `used`.

### Adding a piece: the checklist

- It visualizes one idea type from section 3 and has a visible moment.
- Colours come from `K.BRAND` (or the shared gradients `url(#kmx-lav)`, `#kmx-loss`, `#kmx-surface`, `#kmx-coin`).
- Everything per frame is computed from `q` (never from the previous frame), so stills, lint and renders agree.
- Any GSAP `fromTo` that reveals sets `autoAlpha: 1` in **both** its from and to values. A reveal that only sets it
  in "from" works in stills (which jump to a time) and disappears in the video (which plays in order).
- One sound cue on its moment, through the kit's polite `sfx` (dropped when another cue sits within 0.3 s).
- Labels with `K.text` / `K.tag`, never SVG text, so the size, digit and overlap checks still see them.

## 8. Rules

MOT-1..5 in [RULES.md](RULES.md) ("Motion layer"). The atmosphere moves light and texture behind the pictures, never
the pictures, so PACE-9 still holds; `K.motion({ atmos: false })` turns it off for one reel, `{ atmos: { dust: 0 } }`
keeps only the light.
