/* Scene template. Boards are areas of one continuous world; the camera moves between them.
 * Anchor every entrance to a word in the voice: N("word") in script order, or T("word", afterSeconds).
 * Defaults for new videos (Ahmed, 2026-10-11; docs/LOOK-V2.md section 9): complete first frame, fill the frame,
 * charts with weight, bars to scale, paper world for chapter turns. Ending (2026-10-18, PACE-6): a moving last beat that
 * stops 0.4 s after the last word, never a replay of the hook.
 * Pace (Ahmed 2026-10-13, docs/PACE.md): boards arrive built (K.go + at: g.lead), camera drift, one hero carried
 * between boards, 24 fps motion, room-tone bed; script-route voices are retimed (make.py retime) before the scene.
 * Variety (Ahmed 2026-10-13, docs/PACE.md): one K.punch({riser: true}) on the key sentence, K.stack/K.pile for amounts,
 * K.swap for state changes, map/globe + K.pin for places, real series via engine/data.py with `source`. No ground plane.
 * Worked example: examples/us-dollar-decisions-pace/ (also projects/_paper-demo/, projects/_chart-demo/). */
const { N, T, num } = K;
const tl = K.tl;
const OBJ = "../../library/objects/";
K.look(); // look v2 (docs/LOOK-V2.md): safe zones, light, contact shadows. Call before the first K.cam()
// pace (docs/PACE.md): smooth camera, 24 fps motion, mix 2, room tone, drift between moves (K.finish).
// defaults (docs/PACE.md "Visual defaults"): caption band kept clear, boards arrive built, punch hides the caption,
// capped fly-ins, marks sized to their element, one digit system (K.DIGITS), 28/34 px floors, paper contrast, no snap
// zooms. Switch one off with e.g. { defaults: "2026-10-18", fly: false }. 2026-10-18 adds the shorts defaults
// (title and subtitles off his face, eased split moves, K.under breathing room; docs/RULES.md SHORT-4, -16, TXT-5)
K.pace({ defaults: "2026-10-18" });
// motion layer (docs/MOTION-LANGUAGE.md, MOT-1..4): generated on-brand pieces (K.mx.*), a motion signature seeded by
// this folder's name, moving key light + depth dust, camera motion blur. Pick each line's piece from the guide's table.
K.motion();
// snake layout: neighbours 1,100 px apart in a row, rows 1,800 apart (closer rows show under the captions)
const hook = K.board("hook", 0, 0), b2 = K.board("two", -1100, 0);
K.cam(0, "hook");

// ---------- opening: on screen from frame 1 (no `at` on the illustration or the headline parts) ----------
// HOOK-1..4 (Ahmed 2026-10-21): open on an ILLUSTRATION, a drawn scene in the Live C v10 style, never a still photo or a
// static icon. Use the video's own scene from its image pass (assets/codex/kanz/scene-*.png); the approved references
// are in library/scenes/. It arrives (K.settle), then something on it moves with the opening words (a path drawing on,
// a carried piece, a live diagram for a number) while the camera drifts. Nothing else competes until the first line ends.
const SCENES = "../../library/scenes/";
const g2 = K.go(T("الكلمة"), "two", { scale: 1.3, dx: 220, dy: -60 }); // first word of the next chapter; start close
K.headline([{ html: "عنوان" }, { html: "السؤال؟", kw: true }], { out: g2.start });
K.captionsFrom = g2.start; // the headline already says the question (HOOK-3); a first line that is not on screen: K.captionsFrom = 0
const hero = K.img(hook, SCENES + "scene-crossroads.png", { x: 500, y: 560, w: 620, shadow: false });
K.settle(hero, 0, { fromScale: 1.1, fromY: 40, dur: 1.2 });
K.strike(hook, 860, 900, 560, 760, { at: Math.max(0.3, T("السؤال") - 0.2), dur: 1.0, color: "#D5ADEF", width: 10 }); // the path draws on with the words

// ---------- next chapter: arrives built, starts close, pulls out as the next idea arrives ----------
// K.carry(hero, "two", g2.start, { x: 500, y: 760, w: 260, opacity: 0.3 }); // carry the hero when it returns later
K.img(b2, OBJ + "kanz-house-v01.png", { x: 760, y: 330, w: 420, at: g2.lead, enter: "fly" });
// K.frame(N("التالية") - 0.25, "two");                 // pull out to the whole board on the second idea
// const word = K.text(b2, "الكلمة", { x: 500, y: 120, size: 80, head: true, at: g2.lead });
// K.oval(b2, word, { at: N("الكلمة") });                // marks take the element they point at (box + 16 px)
// K.arrow(b2, word, house2, { at: N("البيت") });        // an arrow names its target
// K.world(g2.start, "paper");  // paper world for chapter turns; K.world(t, "charcoal") to return
// K.area(b2, { x: 500, y: 470, w: 760, h: 420, data: [100, 104, 103, 110, 120], min: 96, max: 121, at: g2.lead, dur: 1.2 });
// const S = K.scale(1200000, 390); // one scale per comparison; bars share the zero baseline y
// const a = K.bar(b2, { x: 560, y: 720, w: 190, value: 1100000, scale: S, at: g2.lead });

// ---------- visual types (docs/routes/images.md; shots.json -> engine/codex_assets.py) ----------
// PLACE -> full-screen photo on a board of its own that holds text, tags and any explanatory overlay such as a live line,
// never decorative icons. Never the opening shot (HOOK-4): it comes after the illustrated opening.
// const gPlace = K.go(T("الكازينو"), "place");
// K.screen("assets/codex/free/casino-exterior.png", gPlace.start, T("التالية"));
// K.text(K.boards.place.el, "عنوان", { x: 500, y: 130, size: 80, head: true, at: gPlace.lead });
// REAL PERSON or MOMENT -> real openly licensed or public-moment press photo (IMG-8); credit in CREDITS.md, not the frame.
// Keep it in the board's upper two thirds so it clears the captions; tags on it sit on top:
// K.snap35(b2, "assets/photos/person.jpg", { x: 500, y: 560, w: 520, h: 640, rot: -4, at: g2.lead, slim: true, flash: false });
// PRICE, PERCENTAGE or AMOUNT -> a moving diagram built in the engine (K.area, K.bar/K.delta, K.count, K.stack, arrows).
// CAUSES, ACTORS and STORIES -> a drawn scene in the Live C v10 style (library/scenes/), one per beat, still once drawn in.
// Kanz icons only support either (EXPL-1, EXPL-2: no still picture explaining for over 2 s).

// ---------- ending (PACE-6, 2026-10-18): the last line gets its own moving visual, building into the last word ----------
// Never cut back to the hook or replay its hero (lint `hook-replay`); the video stops 0.4 s after the last word
// (lint `long-tail`, ship `tail`). Worked example: the bill column draining into pounds in examples/us-dollar-decisions-pace.
const tLast = (window.TOKENS || []).slice(-1)[0]?.end || 4;
// const gEnd = K.go(N("أول-كلمة-في-الجملة-الأخيرة"), "end");
// K.frame(gEnd.arrive, "end", { scale: 1.1, dur: tLast + 0.4 - gEnd.arrive }); // keep the camera moving to the end
// K.stack(K.boards.end.el, OBJ + "...", { x: 500, y: 640, n: 6, at: gEnd.lead, stagger: (tLast - 0.3 - gEnd.lead) / 5 }); // the last lands on the last word
K.duration = tLast + 0.4;
K.finish(); // last line: adds the camera drift between moves
