/* Workshop-short template, editor preset (2026-10-23; opt-in, docs/routes/workshop-editor-preset.md). Copy this folder
 * to projects/short-<slug>/ after engine/footage_track.py has written assets/face, assets/half and transcript.json, set
 * N to the frame count, replace the anchor words with the clip's own, then `python engine/captions.py projects/short-<slug>`.
 * Shape (SHORT-4, -11, -15): his face with the title for the first 3 s, split windows for the mechanism, a full board only
 * where it fills the frame (candle and line charts are SVG and do not count toward the lint fill check: keep them in the
 * split), his face again for his own point at the end (SHORT-7).
 * The preset on top of the repo defaults: dissolves instead of hard face cuts, boards fade out before an unrelated board
 * shows (K.boardSwap), price moves as candles, sounds only on what is on screen (K.onScreenSounds), men-only characters
 * (never kanz-npc-crowd-back-v01.png, now retired: it shows a woman from behind, IMG-12; no kanz-npc-f01-*).
 * Anchors: K.T() skips the shown words of a translated line (`Arabic {{English}}`), so anchor on the spoken words in {{ }}.
 */
const { T } = K;
const tl = K.tl;
const OBJ = "../../library/objects/";
const PRE = 0.3;
const C = K.cutBefore;
const N = 720;                         // frames in assets/face (= assets/half), printed by footage_track.py

K.look();
K.pace({ defaults: "2026-10-18" });

const s1 = C("الكلمة", 3);            // split after the 3 s title: the first mechanism
const f1 = C("التالية");               // back to his face
const s2 = C("التالتة");               // a second split
const b2 = C("الرابعة");               // same split, a new unrelated board (K.boardSwap below)
const f2 = C("الأخيرة");               // his face to the end
const END = window.DURATION;

K.footage({ dir: "assets/face", n: N, xstyle: "dissolve", xfade: 0.35, windows: [[0, s1], [f1, s2], [f2, END + 1]] });
K.split({ dir: "assets/half", n: N, windows: [[s1, f1], [s2, f2]] });
K.title();

const B = { one: K.board("one", 0, 0), two: K.board("two", -1100, 0), three: K.board("three", -2200, 0) };

// ---------- 1. first split: built ~0.3 s before the cut (under his face), so the dissolve shows a finished board ----------
K.cam(0, "one", { scale: 1.0 });
K.text(B.one, "عنوان", { x: 500, y: 200, size: 72, head: true, at: s1 - PRE });
K.candles(B.one, { x: 500, y: 480, w: 760, h: 380, at: s1 - PRE, dur: 2.0,
  data: K.candleSeries([104, 109, 107, 115, 121, 118, 126, 131], 100) });

// ---------- 2. second split: the camera moves while his face covers it ----------
K.cam(s2 - PRE, "two", { dur: 0.04, sfx: false, scale: 1.0 });
K.img(B.two, OBJ + "kanz-npc-m01-neutral-v01.png", { x: 500, y: 520, w: 380, shadow: false, at: s2 - PRE, enter: "fly" });

// ---------- 3. an unrelated board inside the same split: fade the old one out first ----------
K.boardSwap(B.two, B.three, "three", b2);
K.tag(B.three, "وسم", { x: 500, y: 300, size: 50, lav: true, at: b2 + 0.1 });

K.onScreenSounds();
K.finish();
