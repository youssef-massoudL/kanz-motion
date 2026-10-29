/* Motion layer demo (2026-10-30): every K.mx piece once, on fixed seconds, no voice. Not an audience-facing video.
 * Each beat is a real line from the packages, so the piece is judged on the idea it carries (docs/MOTION-LANGUAGE.md).
 * Render: python engine/render.py projects/_motion-demo --stills 1,3,6.5,11,15.5,21  (or the whole MP4) */
K.look();
K.pace({ defaults: "2026-10-18" });
K.motion({ seed: "motion-demo" });

const A = K.board("loss", 0, 0), B = K.board("back", -1100, 0), C = K.board("fee", -2200, 0),
  D = K.board("risk", -3300, 0), E = K.board("path", -4400, 0);
K.cam(0, "loss");

// 1. «خسرت 50٪؟»: the balance itself breaks, the lost half falls away, the number follows it down
K.mx.light(A, { x: 500, y: 560, size: 760, at: 0 });
K.mx.words(A, "خسرت *50٪*؟", { x: 500, y: 110, size: 112, at: 0.1 });
K.mx.shatter(A, { x: 500, y: 820, w: 250, h: 460, keep: 0.5, from: 100, to: 50, prefix: "$", at: 0.35, breakAt: 1.9,
  idea: "a 50% loss is half your money gone", why: "the loss happens on screen at the word, not as a label" });
K.frame(2.6, "loss", { scale: 1.08, dy: 40 });

// 2. «محتاج 100٪ عشان ترجع»: the half that is left has to double to fill the same vessel
K.cam(4.6, "back", { dur: 0.55 });
K.mx.words(B, "محتاج *100٪* عشان ترجع", { x: 500, y: 110, size: 80, at: 4.75 });
const v = K.mx.vessel(B, { x: 300, y: 540, w: 250, h: 420, max: 100, from: 50, value: 100, at: 4.8, fillAt: 6.0, dur: 1.3,
  idea: "from 50 back to 100 is +100%", why: "the same container makes 'double' visible" });
K.mx.roll(B, { x: 300, y: 255, from: 50, value: 100, prefix: "$", at: 4.9, countAt: 6.0, dur: 1.3, size: 84, sfx: false });
K.mx.ring(B, { x: 720, y: 540, r: 150, from: 0, value: 1, at: 5.4, countAt: 6.0, dur: 1.3, prefix: "+", size: 80 });
K.frame(7.4, "back", { scale: 1.12 });

// 3. «كل صفقة بتدفع عمولة»: money leaves your wallet for the broker while the balance ticks down
K.cam(9.2, "fee", { dur: 0.55 });
K.mx.words(C, "العمولة بتاكل *رأس مالك*", { x: 500, y: 110, size: 80, at: 9.35 });
K.mx.panel(C, { x: 790, y: 500, w: 290, h: 290, at: 9.45 });
K.mx.panel(C, { x: 210, y: 500, w: 290, h: 290, at: 9.6, tone: "charcoal" });
K.text(C, "محفظتك", { x: 790, y: 700, size: 40, color: "#eee6f2", at: 9.6 });
K.text(C, "الوسيط", { x: 210, y: 700, size: 40, color: "#9a95a0", at: 9.75 });
const bal = K.mx.roll(C, { x: 790, y: 500, from: 10000, value: 10000, prefix: "$", at: 9.5, size: 66, max: 10000 });
bal.to(10.3, 7400, 2.4, "power1.inOut");
K.mx.flow(C, { from: [700, 470], to: [300, 470], at: 10.1, until: 12.3, rate: 5,
  idea: "fees move money out of your account", why: "a flow reads as a leak, a number alone does not" });

// 4. «حجم المخاطرة»: one trade with the whole account pushes the needle into red
K.cam(13.6, "risk", { dur: 0.55 });
K.mx.words(D, "حجم *المخاطرة*", { x: 500, y: 110, size: 104, at: 13.75 });
const L = K.mx.light(D, { x: 500, y: 520, size: 700, at: 13.7 });
K.mx.gauge(D, { x: 500, y: 640, r: 270, value: 0.88, at: 13.9, danger: 0.7, label: "صفقة بالحساب كله",
  idea: "all-in sizing is extreme risk", why: "the needle crossing into red is the moment of the line" });
L.to(15.0, 760, 470, 560);

// 5. «بدأت منين؟ ورايح فين؟»: the path draws from the start; the end is still a dashed question
K.cam(17.8, "path", { dur: 0.55 });
K.mx.words(E, "من فين *لفين*؟", { x: 500, y: 110, size: 108, at: 17.95 });
K.mx.path(E, { points: [[860, 650], [650, 500], [440, 600], [190, 420]], ghost: true, at: 18.4, dur: 2.0,
  labels: ["البداية", null, null, "النهاية؟"], labelBelow: true,
  idea: "you know where you started, not where you are going", why: "the unfinished dashed end is the question" });
K.frame(20.8, "path", { scale: 1.1, dx: -60 });

K.finish();
