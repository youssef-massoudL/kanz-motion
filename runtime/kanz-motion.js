/* Kanz motion layer (2026-10-30): opt-in, loaded after the other runtime files. K.motion() turns it on; projects that
 * never call it render exactly as before. Guide: docs/MOTION-LANGUAGE.md.
 *
 * Why it exists: the shared kit built every insert from the same PNG shelf (one icon, one label, a reframe), so reels
 * read as one template, flat and repeating. This layer gives the scene author generated, on-brand pieces that
 * visualize the line itself (a balance that breaks, a vessel that drains, money that flows), plus the depth and light
 * the flat boards lacked. Brand stays fixed (tokens below); motion and composition roam within it, seeded per reel.
 *
 *   K.motion({seed, look, atmos, blur, pin})  turn the layer on, after K.look() and K.pace(); seed = the reel's slug;
 *                                        look "flat" (default, Vox cut paper, MOT-5) or "gloss" (gradients, glows)
 *   K.BRAND, K.EASE, K.DUR               brand colours (brand/tokens.json + derived mixes) and motion tokens
 *   K.vary(key, options, {fresh})        seeded choice: one signature per reel per key, or a fresh pick per call
 *   K.onFrame(fn(q, t))                  per-frame hook for custom generated pieces (deterministic in q)
 *   K.mx.enter(el, t, {style, dur})      brand entrance from the variant table K.mx.ENTER (rise, mask, scale, slide)
 *   K.mx.intent({at, out, idea, device, why})  record what a graphic is for (window.__motion.intents)
 *   K.mx.atmos(o)                        moving key light + depth dust under the world (on by default)
 *   K.mx.panel(b, o)                     the brand surface: purple-black glass, lavender rim light
 *   K.mx.words(b, "text *kw*", o)        kinetic headline: words land in reading order, keyword lavender + underline
 *   K.mx.roll(b, o) -> {to}              odometer number, digits roll (integers), prefix/suffix
 *   K.mx.vessel(b, o) -> {to}            a container that fills or drains to a value; the surface settles after
 *   K.mx.shatter(b, o)                   a value slab that cracks and loses its top part (a loss, a cut, a fee)
 *   K.mx.path(b, o)                      a journey line that draws with a lit head; nodes pop; optional ghost end
 *   K.mx.flow(b, o)                      coins stream from one point to another (money moving)
 *   K.mx.gauge(b, o) -> {to}             a dial with a needle that overshoots and settles; red past `danger`
 *   K.mx.ring(b, o) -> {to}              a progress ring with its number in the middle
 *   K.mx.coin(b, o)                      one brand coin ($ or another symbol), the flow's coin on its own
 *   (K.mx.light was removed 2026-10-30, MOT-6: no light that follows the graphic; a no-op that warns)
 *   K.mx.track(v0) / K.mx.svg(...)       building blocks for new pieces (see "Adding a piece" in the guide)
 *
 * Every piece takes `at` (seconds) and registers one sound cue per visual event. Positions are board pixels.
 */
(function () {
  const K = window.K, tl = K.tl, ns = "http://www.w3.org/2000/svg";
  const stage = document.getElementById("stage"), world = document.getElementById("world");
  K.mx = {};

  // ---------- brand: tokens only, plus mixes of two tokens (never a new hue) ----------
  const hx = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const mix = (a, b, f) => "#" + hx(a).map((v, i) => Math.round(v + (hx(b)[i] - v) * f).toString(16).padStart(2, "0")).join("");
  const rgba = (h, a) => `rgba(${hx(h).join(",")},${a})`;
  const C = (K.BRAND = {
    black: "#08070b", purpleBlack: "#11081a", purple: "#38104d", surface: "#281339", lavender: "#d5adef",
    white: "#ffffff", text: "#eee6f2", paper: "#ece8ee", ink: "#141217", muted: "#9a95a0",
    red: "#e0605a", // LOOK-2: genuine losses or risk only
  });
  C.lavShade = mix(C.lavender, C.purple, 0.4);
  C.lavLight = mix(C.lavender, C.white, 0.45);
  C.redShade = mix(C.red, C.purpleBlack, 0.35);
  C.redLight = mix(C.red, C.white, 0.3);
  K.mx.mix = mix; K.mx.rgba = rgba;

  // ---------- motion tokens: the brand's way of moving ----------
  K.EASE = {
    land: "expo.out",        // things arrive fast and settle long (entrances)
    lift: "power4.out",      // text and panels
    snap: "back.out(1.5)",   // small emphatic pieces (tags, nodes)
    settle: "back.out(2.2)", // needles and values that overshoot once
    glide: "sine.inOut",     // light and slow reframes
    fall: "power2.in",       // what is lost drops away
    flow: "power2.inOut",    // money and paths travelling
  };
  K.DUR = { quick: 0.28, beat: 0.5, hold: 0.8, long: 1.2 };
  K.STAGGER = 0.07;

  // ---------- seeded variation: same brand, not the same reel ----------
  function hash(s) { let h = 1779033703 ^ s.length; for (let i = 0; i < s.length; i++) { h = Math.imul(h ^ s.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); } return h >>> 0; }
  function rng(seed) {
    let a = hash(String(seed));
    return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  const slug = (location.pathname.match(/projects\/([^/]+)\//) || [])[1] || "kanz";
  K.MX = { on: false, seed: slug, pin: {}, blur: true, look: "flat" };
  window.__motion = { seed: slug, choices: {}, intents: [] };
  let rand = rng(slug), sig = {};
  K.mx.rand = () => rand();
  // K.vary("enter", ["rise", "mask"]): the reel's signature for that key (same answer every call), so one reel is
  // consistent and the next reel differs. {fresh: true} draws a new pick each call (still seeded, so renders repeat).
  // K.motion({pin: {enter: "mask"}}) fixes a key by hand.
  K.vary = function (key, options, o = {}) {
    let v;
    if (K.MX.pin[key] != null) v = K.MX.pin[key];
    else if (!o.fresh && sig[key] != null) v = sig[key];
    else v = options[Math.floor(rand() * options.length)];
    if (!o.fresh) sig[key] = v;
    (window.__motion.choices[key] = window.__motion.choices[key] || []).push(v);
    return v;
  };

  // ---------- per-frame hook ----------
  const frameFns = [];
  K.onFrame = (fn) => { frameFns.push(fn); return fn; };
  const seek0 = K.seek;
  K.seek = function (t) {
    seek0(t);
    const q = Math.floor(t * K.fps + 1e-6) / K.fps;
    for (const f of frameFns) f(q, t);
  };

  // a value over time from scheduled changes, evaluated per frame (deterministic for any seek order)
  K.mx.track = function (v0) {
    const segs = [];
    return {
      segs,
      to(t, v, dur = 0.9, ease = "power3.out") { segs.push({ t, dur: Math.max(1e-3, dur), v, e: gsap.parseEase(ease) }); segs.sort((a, b) => a.t - b.t); return this; },
      at(q) { let cur = v0; for (const s of segs) { if (q < s.t) break; const p = Math.min(1, (q - s.t) / s.dur); cur = cur + (s.v - cur) * s.e(p); } return cur; },
      // how much it is moving: 1 right after a change, decaying (for surfaces that settle)
      stir(q, k = 2.2) { let a = 0; for (const s of segs) if (q >= s.t) a += Math.exp(-(q - s.t) * k) * Math.min(1, (q - s.t) / 0.12); return Math.min(1.4, a); },
    };
  };

  // ---------- small helpers ----------
  const hide = (e) => tl.set(e, { autoAlpha: 0 }, 0);
  const place = (e, x, y) => gsap.set(e, { left: x, top: y, xPercent: -50, yPercent: -50 });
  const svgEl = (tag, attrs = {}, parent) => {
    const e = document.createElementNS(ns, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  };
  // an <svg> whose local (0,0) is board point (x, y); w/h only size the box (overflow is visible)
  K.mx.svg = function (parent, x, y, w, h) {
    const s = svgEl("svg", { class: "kmx", width: w, height: h, viewBox: `0 0 ${w} ${h}` });
    parent.appendChild(s);
    gsap.set(s, { left: x, top: y });
    return s;
  };
  K.mx.el = svgEl;
  let uid = 0;
  const id = (p) => `kmx-${p}-${++uid}`;
  // polite cues: a kit sound is dropped when another cue already sits within 0.3 s (SND-5: one sound at a time; the
  // camera's whoosh usually owns a board change). An explicit sfx name always plays.
  // the two looks (MOT-5): "flat" (default) is Vox-like cut paper: flat brand colour, a hard drop shadow, edges that boil
  // like the engine's hand-drawn marks; "gloss" keeps the gradients, rim lights and glows for a beat that needs depth
  const flat = () => K.MX.look !== "gloss";
  const paper = (el) => { if (flat()) el.setAttribute("filter", "url(#kmx-paper)"); return el; }; // boil + hard shadow
  const ink = (el) => { if (flat()) el.setAttribute("filter", "url(#kmx-ink)"); return el; };     // boil only
  K.mx.paper = paper; K.mx.ink = ink; K.mx.flat = flat;
  const sfx = (t, cat, gain, o) => {
    const c = K.cue(o && o.sfx, cat);
    if (!c) return;
    if (!(o && o.sfx) && K.cues.some((q) => Math.abs(q.t - t) < 0.3)) return;
    K.sfx(t, c, gain);
  };

  // ---------- shared SVG material (one set of names for both looks) ----------
  function defs() {
    if (document.getElementById("kmx-defs")) return;
    const s = svgEl("svg", { id: "kmx-defs", width: 0, height: 0, style: "position:absolute" });
    document.body.appendChild(s);
    const d = svgEl("defs", {}, s);
    const lin = (name, stops, x2 = 0, y2 = 1) => {
      const g = svgEl("linearGradient", { id: name, x1: 0, y1: 0, x2, y2 }, d);
      stops.forEach(([o, c, a = 1]) => svgEl("stop", { offset: o, "stop-color": c, "stop-opacity": a }, g));
    };
    const F = flat(), one = (c) => [[0, c], [1, c]]; // flat: a gradient name that holds one brand colour
    lin("kmx-lav", F ? one(C.lavender) : [[0, C.lavLight], [0.35, C.lavender], [1, C.lavShade]]);
    lin("kmx-loss", F ? one(C.red) : [[0, C.redLight], [0.4, C.red], [1, C.redShade]]);
    lin("kmx-surface", F ? one(C.surface) : [[0, mix(C.surface, C.lavender, 0.08)], [1, C.purpleBlack]]);
    lin("kmx-liquid", F ? one(C.lavender) : [[0, C.lavender, 0.95], [1, C.lavShade, 0.95]]);
    lin("kmx-liquid-loss", F ? one(C.red) : [[0, C.red, 0.95], [1, C.redShade, 0.95]]);
    const rg = svgEl("radialGradient", { id: "kmx-coin", cx: 0.38, cy: 0.32, r: 0.75 }, d);
    (F ? one(C.lavender) : [[0, C.lavLight], [0.55, C.lavender], [1, C.lavShade]]).forEach(([o, c]) => svgEl("stop", { offset: o, "stop-color": c }, rg));
    // boil: the hand-drawn wobble, re-seeded 8 times a second in K.motion (the engine's own marks step the same way).
    // User-space regions so thin and straight shapes (a level line, a tick) never get a zero-size filter box.
    const boil = (name, shadow) => {
      const f = svgEl("filter", { id: name, filterUnits: "userSpaceOnUse", x: -3000, y: -3000, width: 8000, height: 8000 }, d);
      svgEl("feTurbulence", { class: "kmx-boil", type: "fractalNoise", baseFrequency: 0.03, numOctaves: 2, seed: 1, result: "n" }, f);
      svgEl("feDisplacementMap", { in: "SourceGraphic", in2: "n", scale: 4.5, xChannelSelector: "R", yChannelSelector: "G", result: "b" }, f);
      if (shadow) svgEl("feDropShadow", { in: "b", dx: 0, dy: 9, stdDeviation: 0, "flood-color": C.black, "flood-opacity": 0.5 }, f);
    };
    boil("kmx-ink", false);
    boil("kmx-paper", true);
    if (F) boil("kmx-glow", false); // flat: what glowed (a path's head, a crack) is drawn ink instead
    else {
      const glow = svgEl("filter", { id: "kmx-glow", x: "-50%", y: "-50%", width: "200%", height: "200%" }, d);
      svgEl("feGaussianBlur", { stdDeviation: 9, result: "b" }, glow);
      const m = svgEl("feMerge", {}, glow); svgEl("feMergeNode", { in: "b" }, m); svgEl("feMergeNode", { in: "SourceGraphic" }, m);
    }
    const soft = svgEl("filter", { id: "kmx-soft", x: "-50%", y: "-50%", width: "200%", height: "200%" }, d);
    svgEl("feGaussianBlur", { stdDeviation: 14 }, soft);
    const mb = svgEl("filter", { id: "kmx-mblur", x: "-5%", y: "-5%", width: "110%", height: "110%" }, d);
    svgEl("feGaussianBlur", { id: "kmx-mblur-g", stdDeviation: "0 0" }, mb);
  }

  // ---------- entrances: the variant table (extension point for references) ----------
  // Each entry: fn(el, t, dur) adds the tweens; `ref` names the reference in library/references/references.json it
  // was built from (null = house style). Add a variant by adding an entry; scenes pick by name or by K.vary.
  // flat: no blur, a small overshoot (cut paper landing); gloss: out of a soft blur, long settle
  const bl = (px) => (flat() ? {} : { filter: `blur(${px}px)` }), bl0 = () => (flat() ? {} : { filter: "blur(0px)" });
  const landEase = () => (flat() ? "back.out(1.4)" : K.EASE.land);
  const ENTER = (K.mx.ENTER = {
    rise: { ref: null, note: "lifts 46 px (flat: with a small overshoot; gloss: out of a soft blur)", fn: (el, t, d) => tl.fromTo(el, { y: 46, autoAlpha: 0, ...bl(10) }, { y: 0, autoAlpha: 1, ...bl0(), duration: d || 0.55, ease: landEase(), immediateRender: false }, t) },
    mask: { ref: null, note: "revealed from its baseline up, a short rise", fn: (el, t, d) => tl.fromTo(el, { y: 26, autoAlpha: 1, clipPath: "inset(100% -20% -20% -20%)" }, { y: 0, autoAlpha: 1, clipPath: "inset(-20% -20% -20% -20%)", duration: d || 0.5, ease: K.EASE.lift, immediateRender: false }, t) },
    scale: { ref: null, note: "lands from 1.3x (flat: pops in from 0.6x)", fn: (el, t, d) => tl.fromTo(el, { scale: flat() ? 0.6 : 1.3, autoAlpha: 0, ...bl(14) }, { scale: 1, autoAlpha: 1, ...bl0(), duration: d || 0.5, ease: landEase(), immediateRender: false }, t) },
    slide: { ref: null, note: "slides in along the reading direction (from the right)", fn: (el, t, d) => tl.fromTo(el, { x: 70, autoAlpha: 0, ...bl(8) }, { x: 0, autoAlpha: 1, ...bl0(), duration: d || 0.5, ease: landEase(), immediateRender: false }, t) },
  });
  K.mx.enter = function (el, t, o = {}) {
    const style = o.style || K.vary(o.key || "enter", Object.keys(ENTER));
    hide(el);
    (ENTER[style] || ENTER.rise).fn(el, t, o.dur);
    return style;
  };
  K.mx.exit = (el, t, dur = 0.3) => tl.to(el, { autoAlpha: 0, y: -18, ...bl(6), duration: dur, ease: "power2.in" }, t);

  // ---------- intent: every graphic says what it is for ----------
  K.mx.intent = function (o) { window.__motion.intents.push(o); return o; };
  const noteIntent = (o, device) => { if (o.idea) K.mx.intent({ at: o.at, out: o.out, idea: o.idea, device, why: o.why }); };

  // ---------- atmosphere: moving key light + dust with depth ----------
  K.mx.atmos = function (o = {}) {
    if (document.getElementById("kmx-atmos")) return;
    const cv = document.createElement("canvas");
    cv.id = "kmx-atmos"; cv.width = K.W; cv.height = K.H;
    stage.insertBefore(cv, document.getElementById("camwrap") || world);
    const g = cv.getContext("2d");
    const r = rng(K.MX.seed + ":atmos");
    const ph = [r() * 6.28, r() * 6.28, r() * 6.28];
    const side = K.vary("light-side", [-1, 1]); // which side the key light leans to, per reel
    const n = o.dust == null ? (flat() ? 0 : 34) : o.dust, strength = o.light == null ? 1 : o.light;
    const motes = Array.from({ length: n }, () => ({ x: r() * K.W, y: r() * K.H, z: 0.25 + r() * 0.75, r: 1 + r() * 2.6, a: 0.05 + r() * 0.17, v: 8 + r() * 16, p: r() * 6.28 }));
    K.onFrame((q) => {
      g.clearRect(0, 0, K.W, K.H);
      if (strength > 0) {
        const lx = 540 + side * 170 + 150 * Math.sin((q / 23) * 6.28 + ph[0]), ly = 640 + 130 * Math.sin((q / 31) * 6.28 + ph[1]);
        let gr = g.createRadialGradient(lx, ly, 0, lx, ly, 820);
        gr.addColorStop(0, rgba(C.lavender, 0.11 * strength)); gr.addColorStop(0.45, rgba(C.lavShade, 0.05 * strength)); gr.addColorStop(1, rgba(C.purple, 0));
        g.fillStyle = gr; g.fillRect(0, 0, K.W, K.H);
        const px = 540 - side * 260 + 120 * Math.sin((q / 37) * 6.28 + ph[2]), py = 1300;
        gr = g.createRadialGradient(px, py, 0, px, py, 900);
        gr.addColorStop(0, rgba(C.purple, 0.32 * strength)); gr.addColorStop(1, rgba(C.purple, 0));
        g.fillStyle = gr; g.fillRect(0, 0, K.W, K.H);
      }
      const cx = gsap.getProperty(world, "x") || 0;
      for (const m of motes) {
        const x = (((m.x + cx * 0.05 * m.z + 14 * Math.sin(q * 0.35 + m.p)) % K.W) + K.W) % K.W;
        const y = (((m.y - m.v * m.z * q) % (K.H + 40)) + K.H + 40) % (K.H + 40) - 20;
        const rr = m.r * (0.6 + m.z);
        g.fillStyle = rgba(C.lavLight, m.a * m.z);
        g.beginPath(); g.arc(x, y, rr, 0, 6.283); g.fill();
      }
    });
  };

  // ---------- camera motion blur (only during real moves, along their direction) ----------
  const blurMoves = [];
  function installBlur() {
    const cam1 = K.cam;
    K.cam = function (t, id, o = {}) {
      const from = K._cam;
      cam1(t, id, o);
      const to = K._cam, dur = t <= 0 ? 0 : o.dur || 0.5;
      if (!K.MX.blur || !from || !to || dur < 0.2) return;
      const dx = (to.x - from.x) / dur, dy = (to.y - from.y) / dur; // screen px per second
      if (Math.hypot(dx, dy) < 600) return;
      blurMoves.push({ t, dur, sx: Math.min(16, Math.abs(dx) / 240), sy: Math.min(16, Math.abs(dy) / 240) });
    };
    const fe = document.getElementById("kmx-mblur-g");
    K.onFrame((q, t) => {
      let e = 0, m = null;
      for (const b of blurMoves) if (t >= b.t && t <= b.t + b.dur) { m = b; e = Math.pow(Math.sin(Math.PI * (t - b.t) / b.dur), 2); }
      if (!m || e < 0.03) { world.style.filter = ""; return; }
      fe.setAttribute("stdDeviation", `${(m.sx * e).toFixed(2)} ${(m.sy * e).toFixed(2)}`);
      world.style.filter = "url(#kmx-mblur)";
    });
  }

  // ---------- K.motion: turn it on ----------
  K.motion = function (o = {}) {
    if (K.MX.on) return;
    K.MX.on = true;
    if (o.seed) K.MX.seed = String(o.seed);
    K.MX.pin = o.pin || {};
    K.MX.blur = o.blur !== false;
    K.MX.look = o.look === "gloss" ? "gloss" : "flat";
    window.__motion.seed = K.MX.seed;
    rand = rng(K.MX.seed); sig = {};
    stage.classList.add("kmx-on");
    stage.classList.toggle("kmx-flat", flat());
    defs();
    const boils = document.querySelectorAll("#kmx-defs feTurbulence.kmx-boil");
    K.onFrame((q) => { const sd = String((Math.floor(q * 8 + 1e-6) % 40) + 1); boils.forEach((f) => f.setAttribute("seed", sd)); });
    installBlur();
    if (o.atmos !== false) K.mx.atmos(o.atmos || {});
  };

  // ---------- surface ----------
  K.mx.panel = function (parent, o) {
    const e = K.el("div", "kmx-panel" + (o.tone === "charcoal" ? " charcoal" : ""), parent);
    gsap.set(e, { width: o.w, height: o.h, borderRadius: o.radius == null ? 30 : o.radius });
    place(e, o.x, o.y);
    if (o.at != null) { K.mx.enter(e, o.at, { style: o.style, key: "panel" }); sfx(o.at, "paper", 0.3, o); }
    if (o.out != null) K.mx.exit(e, o.out);
    return e;
  };

  // ---------- kinetic words ----------
  // "خسرت *50٪*؟": words land one by one in reading order; *keyword* turns lavender and gets a drawn underline.
  K.mx.words = function (parent, text, o) {
    const size = o.size || 96;
    const box = K.el("div", "t head kmx-words", parent);
    if (o.headline !== false) box.dataset.role = "headline";
    gsap.set(box, { fontSize: size, color: o.color || C.white, lineHeight: 1.2 });
    if (o.w) gsap.set(box, { width: o.w }); else gsap.set(box, { flexWrap: "nowrap", whiteSpace: "nowrap" });
    const words = [];
    // a *starred* run is one keyword unit even across spaces ("*رأس مالك*"); punctuation after it stays attached
    (text.match(/\*[^*]+\*\S*|\S+/g) || []).forEach((raw) => {
      const kw = raw.startsWith("*");
      const html = raw.replace(/\*/g, "");
      const w = K.el("span", "kmx-w" + (kw ? " kw" : ""), box, html);
      if (kw) w.style.color = C.lavender;
      words.push({ w, kw });
    });
    place(box, o.x, o.y);
    if (o.at != null) {
      const style = o.style || K.vary("words", Object.keys(ENTER));
      hide(box); tl.set(box, { autoAlpha: 1 }, o.at);
      words.forEach(({ w, kw }, i) => {
        const t = o.at + i * (o.stagger || K.STAGGER);
        ENTER[style].fn(w, t, o.dur);
        hide(w);
        if (kw) {
          const ul = K.el("div", "kmx-ul", w);
          tl.fromTo(ul, { scaleX: 0 }, { scaleX: 1, duration: 0.45, ease: K.EASE.lift, immediateRender: false }, t + 0.22);
          hide(ul); tl.set(ul, { autoAlpha: 1 }, t + 0.22);
        }
      });
      sfx(o.at, "whoosh", 0.22, o);
    }
    if (o.out != null) K.mx.exit(box, o.out);
    noteIntent(o, "words");
    return box;
  };

  // ---------- rolling number ----------
  const AR = "٠١٢٣٤٥٦٧٨٩";
  K.mx.roll = function (parent, o) {
    const from = o.from == null ? 0 : o.from, top = Math.max(Math.abs(from), Math.abs(o.value == null ? from : o.value), o.max || 0);
    const nd = Math.max(1, String(Math.floor(top)).length);
    const box = K.el("div", "t head kmx-roll", parent);
    box.dir = "ltr";
    gsap.set(box, { fontSize: o.size || 140, color: o.color || C.white });
    // prefix and suffix are plain text drawn from CSS like the digits; the box is dir=ltr, so a "$" always sits on
    // the left of its digits and on their line (NUM-5 holds by construction)
    const affix = (txt, small) => { if (!txt) return; const a = K.el("span", "kmx-affix" + (small ? " small" : ""), box); a.dataset.d = K.D.digits ? K.fmtNum(String(txt)) : String(txt); return a; };
    affix(o.prefix, o.smallAffix);
    const slots = [];
    for (let k = nd - 1; k >= 0; k--) {
      const s = K.el("span", "kmx-slot", box), col = K.el("span", "kmx-col", s);
      // digits come from CSS (data-d), not text nodes: the column holds 11 stacked digits, and as text lint would read the
      // hidden ones as a $ set apart from its number (stray-currency)
      for (let i = 0; i <= 10; i++) K.el("span", "", col).dataset.d = K.DIGITS === "ar" && K.D.digits ? AR[i % 10] : String(i % 10);
      slots.push({ k, s, col });
    }
    affix(o.suffix != null ? o.suffix : "", o.smallAffix !== false && o.suffix && o.suffix.length > 1);
    place(box, o.x, o.y);
    const tr = K.mx.track(from);
    if (o.value != null && o.value !== from) tr.to(o.countAt != null ? o.countAt : (o.at || 0) + 0.15, o.value, o.dur || 0.9, o.ease || "power3.out");
    const em = 1.1;
    const render = (q) => {
      const v = Math.max(0, tr.at(q));
      for (const { k, s, col } of slots) {
        const d = Math.pow(10, k), whole = Math.floor(v / d + 1e-9) % 10;
        let p = k === 0 ? v % 10 : whole;
        if (k > 0) { const low = (v % d) / d; if (low > 0.9) p += (low - 0.9) * 10; }
        const f = p - Math.floor(p); if (f < 0.06) p = Math.floor(p); else if (f > 0.94) p = Math.ceil(p); // no half-digit tails
        col.style.transform = `translateY(${(-p * em).toFixed(4)}em)`;
        const vis = k === 0 ? 1 : Math.max(0, Math.min(1, (v / d - 0.9) * 10));
        s.style.width = (0.6 * vis).toFixed(3) + "em"; s.style.opacity = vis.toFixed(3);
      }
    };
    K.onFrame(render); render(0);
    if (o.at != null) { K.mx.enter(box, o.at, { style: o.style, key: "number" }); }
    if (o.out != null) K.mx.exit(box, o.out);
    noteIntent(o, "roll");
    const api = { el: box, track: tr, to(t, v, dur = 0.9, ease = "power3.out") { tr.to(t, v, dur, ease); return api; } };
    if (o.value != null && o.value !== from) sfx((o.countAt != null ? o.countAt : (o.at || 0) + 0.15) + (o.dur || 0.9) * 0.7, "coin", 0.3, o);
    return api;
  };

  // ---------- vessel: fills or drains ----------
  K.mx.vessel = function (parent, o) {
    const w = o.w || 300, h = o.h || 480, max = o.max || 100, pad = 24;
    const from = o.from == null ? 0 : o.from;
    const s = K.mx.svg(parent, o.x - w / 2 - pad, o.y - h / 2 - pad, w + pad * 2, h + pad * 2);
    const g = paper(svgEl("g", { transform: `translate(${pad},${pad})` }, s));
    const cid = id("clip");
    const cp = svgEl("clipPath", { id: cid }, svgEl("defs", {}, s));
    svgEl("rect", { x: 0, y: 0, width: w, height: h, rx: 38 }, cp);
    svgEl("rect", { x: 0, y: 0, width: w, height: h, rx: 38, fill: "url(#kmx-surface)" }, g);
    const inner = svgEl("g", { "clip-path": `url(#${cid})` }, g);
    const liquid = svgEl("path", { fill: o.loss ? "url(#kmx-liquid-loss)" : "url(#kmx-liquid)" }, inner);
    const crest = svgEl("path", { fill: "none", stroke: o.loss ? C.redLight : C.lavLight, "stroke-width": 4, "stroke-linecap": "round", opacity: 0.9 }, inner);
    if (!flat()) svgEl("rect", { x: 26, y: 30, width: 22, height: h - 60, rx: 11, fill: C.white, opacity: 0.07 }, inner); // glass highlight
    [0.25, 0.5, 0.75].forEach((f) => svgEl("line", { x1: w - 34, x2: w - 14, y1: h - h * f, y2: h - h * f, stroke: C.white, "stroke-opacity": 0.22, "stroke-width": 3, "stroke-linecap": "round" }, g));
    svgEl("rect", { x: 0, y: 0, width: w, height: h, rx: 38, fill: "none", stroke: rgba(C.lavender, flat() ? 0.6 : 0.38), "stroke-width": flat() ? 5 : 3 }, g);
    const tr = K.mx.track(from);
    const fillAt = o.fillAt != null ? o.fillAt : (o.at || 0) + 0.3;
    if (o.value != null && o.value !== from) tr.to(fillAt, o.value, o.dur || 1.1, o.ease || "power2.inOut");
    const render = (q) => {
      const v = Math.max(0, Math.min(max, tr.at(q))), lvl = h - (v / max) * h, a = 12 * tr.stir(q, 1.8);
      let d = `M0,${h + 4} L0,${lvl.toFixed(1)}`, c = "";
      for (let i = 0; i <= 24; i++) {
        const x = (w * i) / 24, y = lvl + a * Math.sin((x / w) * 6.28 * 1.4 + q * 7.5) + a * 0.45 * Math.sin((x / w) * 6.28 * 3.1 - q * 5.2);
        d += ` L${x.toFixed(1)},${y.toFixed(1)}`; c += (i ? " L" : "M") + `${x.toFixed(1)},${y.toFixed(1)}`;
      }
      liquid.setAttribute("d", d + ` L${w},${h + 4} Z`);
      crest.setAttribute("d", c);
      crest.setAttribute("opacity", v > 0.5 ? 0.9 : 0);
    };
    K.onFrame(render); render(0);
    if (o.at != null) { hide(s); tl.fromTo(s, { autoAlpha: 0, y: 60, ...bl(10) }, { autoAlpha: 1, y: 0, ...bl0(), duration: 0.6, ease: landEase(), immediateRender: false }, o.at); sfx(o.at, "pop", 0.3, o); }
    if (o.value != null && o.value !== from) sfx(fillAt, o.value > from ? "riser" : "whoosh", 0.25, o);
    if (o.out != null) K.mx.exit(s, o.out);
    noteIntent(o, "vessel");
    const api = { el: s, track: tr, to(t, v, dur = 1.1, ease = "power2.inOut") { tr.to(t, v, dur, ease); sfx(t, v > tr.at(t - 1e-3) ? "riser" : "whoosh", 0.25, o); return api; } };
    return api;
  };

  // ---------- shatter: a value slab loses part of itself ----------
  // x, y = centre of the slab's base. keep = the share that stays (0.5 for "lose half"). The roll above follows.
  K.mx.shatter = function (parent, o) {
    const w = o.w || 240, h = o.h || 460, keep = o.keep == null ? 0.5 : o.keep, at = o.at || 0, br = o.breakAt != null ? o.breakAt : at + 1;
    const r = rng(K.MX.seed + ":shatter:" + uid);
    const s = K.mx.svg(parent, o.x - w / 2, o.y - h, w, h);
    const cy = h * (1 - keep), n = 7;
    const crack = Array.from({ length: n + 1 }, (_, i) => [(w * i) / n, cy + (i === 0 || i === n ? 0 : (r() - 0.5) * 34)]);
    const pts = (a) => a.map((p) => p.map((v) => v.toFixed(1)).join(",")).join(" ");
    // each part carries its own edge and rim light, so nothing of the lost part stays behind after the break
    const edge = flat() ? {} : { stroke: rgba(C.white, 0.2), "stroke-width": 2, "stroke-linejoin": "round" };
    const keepG = paper(svgEl("g", {}, s));
    const keepPoly = svgEl("polygon", { points: pts([...crack, [w, h], [0, h]]), fill: "url(#kmx-lav)", ...edge }, keepG);
    if (!flat()) svgEl("rect", { x: 10, y: cy + 22, width: 14, height: Math.max(0, h - cy - 32), rx: 7, fill: C.white, opacity: 0.14 }, keepG);
    const lostG = paper(svgEl("g", {}, s));
    const lostPoly = svgEl("polygon", { points: pts([[0, 0], [w, 0], ...crack.slice().reverse()]), fill: "url(#kmx-lav)", ...edge }, lostG);
    if (!flat()) svgEl("rect", { x: 10, y: 10, width: 14, height: Math.max(0, cy - 32), rx: 7, fill: C.white, opacity: 0.14 }, lostG);
    const crackLine = svgEl("polyline", { points: pts(crack), fill: "none", stroke: C.white, "stroke-width": 5, "stroke-linejoin": "round", filter: "url(#kmx-glow)" }, s);
    const shards = Array.from({ length: 5 }, (_, i) => {
      const x = w * (0.15 + 0.7 * r()), sz = 10 + r() * 16;
      return { el: svgEl("polygon", { points: `${x},${cy} ${x + sz},${cy - sz * 0.4} ${x + sz * 0.3},${cy + sz * 0.6}`, fill: C.red }, s), dx: (r() - 0.5) * 360, dy: -60 - r() * 160, rot: (r() - 0.5) * 540 };
    });
    // build: the slab rises from its base
    hide(s);
    tl.fromTo(s, { autoAlpha: 1, scaleY: 0, transformOrigin: "50% 100%" }, { autoAlpha: 1, scaleY: 1, duration: 0.7, ease: K.EASE.land, immediateRender: false }, at);
    sfx(at, "pop", 0.3, o);
    // break: crack flashes, the lost part turns red, kicks, then falls away
    const L = crack.reduce((a, p, i) => (i ? a + Math.hypot(p[0] - crack[i - 1][0], p[1] - crack[i - 1][1]) : 0), 0);
    gsap.set(crackLine, { strokeDasharray: L, strokeDashoffset: L, opacity: 0 });
    tl.set(crackLine, { opacity: 1 }, br - 0.18);
    tl.fromTo(crackLine, { strokeDashoffset: L }, { strokeDashoffset: 0, duration: 0.16, ease: "none", immediateRender: false }, br - 0.18);
    tl.to(crackLine, { opacity: 0, duration: 0.3 }, br + 0.1);
    tl.set(lostPoly, { attr: { fill: "url(#kmx-loss)" } }, br);
    const sideDir = o.fallTo === "right" ? 1 : -1;
    tl.to(lostG, { x: 12 * -sideDir, y: -16, rotation: 4 * -sideDir, duration: 0.12, ease: "power2.out", svgOrigin: `${w / 2} ${cy}` }, br);
    tl.to(lostG, { x: 170 * sideDir, y: 900, rotation: 34 * sideDir, opacity: 0, duration: 0.95, ease: K.EASE.fall, svgOrigin: `${w / 2} ${cy}` }, br + 0.12);
    shards.forEach((sh) => {
      gsap.set(sh.el, { opacity: 0 });
      tl.set(sh.el, { opacity: 1 }, br);
      tl.to(sh.el, { x: sh.dx, y: sh.dy + 500, rotation: sh.rot, opacity: 0, duration: 0.9, ease: "power1.in", svgOrigin: `${w / 2} ${cy}` }, br);
    });
    sfx(br, "hit", 0.45, o);
    // the value above it
    let roll = null;
    if (o.from != null) {
      roll = K.mx.roll(parent, { x: o.x, y: o.y - h - 80, from: o.from, value: o.to, countAt: br + 0.1, dur: 0.7, at: at + 0.25, size: o.size || 110, prefix: o.prefix, suffix: o.suffix, max: o.from, style: "rise", sfx: false });
      tl.to(roll.el, { top: o.y - h * keep - 80, duration: 0.7, ease: K.EASE.land }, br + 0.3); // after the lost part has dropped clear
      if (o.lossColor !== false) tl.to(roll.el, { color: C.red, duration: 0.25 }, br + 0.1);
    }
    if (o.out != null) { K.mx.exit(s, o.out); if (roll) K.mx.exit(roll.el, o.out); }
    noteIntent(o, "shatter");
    return { el: s, keep: keepPoly, roll };
  };

  // ---------- path: a journey that draws with a lit head ----------
  function smooth(p) {
    let d = `M${p[0][0]},${p[0][1]}`;
    for (let i = 0; i < p.length - 1; i++) {
      const a = p[i - 1] || p[i], b = p[i], c = p[i + 1], e = p[i + 2] || c;
      d += ` C${b[0] + (c[0] - a[0]) / 6},${b[1] + (c[1] - a[1]) / 6} ${c[0] - (e[0] - b[0]) / 6},${c[1] - (e[1] - b[1]) / 6} ${c[0]},${c[1]}`;
    }
    return d;
  }
  const invert = (ease, f) => { let lo = 0, hi = 1; for (let i = 0; i < 30; i++) { const m = (lo + hi) / 2; if (ease(m) < f) lo = m; else hi = m; } return (lo + hi) / 2; };
  K.mx.path = function (parent, o) {
    const pts = o.points, at = o.at || 0, dur = o.dur || 1.6, ghost = o.ghost ? o.points.length - 1 : -1;
    const solid = ghost > 0 ? pts.slice(0, ghost) : pts;
    const s = K.mx.svg(parent, 0, 0, 1000, 860);
    const d = smooth(solid);
    const under = svgEl("path", { d, fill: "none", stroke: rgba(C.white, 0.08), "stroke-width": 10, "stroke-linecap": "round" }, s);
    const glow = svgEl("path", { d, fill: "none", stroke: C.lavender, "stroke-width": 14, "stroke-linecap": "round", opacity: flat() ? 0 : 0.45, filter: "url(#kmx-soft)" }, s);
    const line = ink(svgEl("path", { d, fill: "none", stroke: C.lavender, "stroke-width": flat() ? 9 : 8, "stroke-linecap": "round" }, s));
    const head = flat() ? paper(svgEl("circle", { r: 14, fill: C.lavender, stroke: C.purpleBlack, "stroke-width": 5 }, s))
      : svgEl("circle", { r: 13, fill: C.lavLight, filter: "url(#kmx-glow)" }, s);
    const L = line.getTotalLength();
    [glow, line].forEach((p) => p.setAttribute("stroke-dasharray", `${L} ${L + 10}`));
    const ease = gsap.parseEase(o.ease || K.EASE.flow);
    const prog = (q) => (q <= at ? 0 : q >= at + dur ? 1 : ease((q - at) / dur));
    K.onFrame((q) => {
      const p = prog(q), off = (L * (1 - p)).toFixed(1);
      line.setAttribute("stroke-dashoffset", off); glow.setAttribute("stroke-dashoffset", off);
      const pt = line.getPointAtLength(L * p);
      head.setAttribute("cx", pt.x.toFixed(1)); head.setAttribute("cy", pt.y.toFixed(1));
      head.setAttribute("opacity", p > 0 && p < 1 ? 1 : 0);
    });
    hide(s); tl.set(s, { autoAlpha: 1 }, at);
    tl.fromTo(under, { opacity: 0 }, { opacity: 1, duration: 0.3, immediateRender: false }, at);
    // where each point sits along the line, then the time the head reaches it
    const samples = 240, along = [];
    for (let i = 0; i <= samples; i++) { const pt = line.getPointAtLength((L * i) / samples); along.push([pt.x, pt.y, i / samples]); }
    const fracOf = (p) => along.reduce((b, a) => (Math.hypot(a[0] - p[0], a[1] - p[1]) < Math.hypot(b[0] - p[0], b[1] - p[1]) ? a : b))[2];
    const labels = o.labels || [];
    const shown = o.nodes || solid.map((_, i) => i); // o.nodes: indices that get a node (a price path: the turns only)
    const nodes = solid.map((p, i) => {
      if (!shown.includes(i)) return null;
      const t = at + dur * invert(ease, Math.max(0.001, fracOf(p)));
      const tNode = i === 0 ? at : t;
      const c = paper(svgEl("circle", { cx: p[0], cy: p[1], r: 16, fill: C.purpleBlack, stroke: C.lavender, "stroke-width": 6 }, s));
      gsap.set(c, { transformOrigin: "50% 50%" }); hide(c);
      tl.fromTo(c, { autoAlpha: 0, scale: 0.2 }, { autoAlpha: 1, scale: 1, duration: 0.35, ease: K.EASE.settle, immediateRender: false }, tNode);
      if (labels[i]) K.tag(parent, labels[i], { x: p[0], y: p[1] + (o.labelBelow ? 62 : -62), at: tNode + 0.05, lav: i === solid.length - 1 && !o.ghost, sfx: o.sfx === false || !i || K.cues.some((c) => Math.abs(c.t - tNode - 0.05) < 0.3) ? false : undefined });
      return { c, t: tNode };
    });
    if (ghost > 0) {
      const gp = pts[ghost], last = solid[solid.length - 1];
      const gd = svgEl("path", { d: `M${last[0]},${last[1]} L${gp[0]},${gp[1]}`, fill: "none", stroke: rgba(C.lavender, 0.45), "stroke-width": 6, "stroke-dasharray": "4 18", "stroke-linecap": "round" }, s);
      const gc = svgEl("circle", { cx: gp[0], cy: gp[1], r: 24, fill: "none", stroke: rgba(C.lavender, 0.55), "stroke-width": 4, "stroke-dasharray": "6 8" }, s);
      const tg = at + dur + 0.25;
      hide(gd); hide(gc);
      tl.fromTo(gd, { autoAlpha: 0, clipPath: "inset(0 0 0 100%)" }, { autoAlpha: 1, clipPath: "inset(0 0 0 0%)", duration: 0.5, ease: K.EASE.lift, immediateRender: false }, tg);
      tl.fromTo(gc, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.4, immediateRender: false }, tg + 0.35);
      if (labels[ghost]) K.tag(parent, labels[ghost], { x: gp[0], y: gp[1] + (o.labelBelow ? 66 : -66), at: tg + 0.4, lav: true });
    }
    sfx(at, "marker", 0.3, o);
    if (o.out != null) K.mx.exit(s, o.out);
    noteIntent(o, "path");
    return { el: s, nodes };
  };

  // ---------- flow: coins travel from one point to another ----------
  function coin(parent, size, symbol, loss) {
    const g = paper(svgEl("g", {}, parent));
    svgEl("circle", { r: size / 2, fill: loss ? "url(#kmx-loss)" : "url(#kmx-coin)", stroke: flat() ? C.purpleBlack : loss ? C.redLight : C.lavLight, "stroke-opacity": flat() ? 1 : 0.7, "stroke-width": flat() ? 3 : 2 }, g);
    svgEl("circle", { r: size * 0.35, fill: "none", stroke: loss ? C.redShade : C.lavShade, "stroke-width": 2.5 }, g);
    const tx = svgEl("text", { "text-anchor": "middle", "dominant-baseline": "central", "font-size": size * 0.42, fill: C.purple }, g);
    tx.textContent = symbol;
    return g;
  }
  // one coin on its own (the flow's coin): a badge for "money", "the same dollars"
  K.mx.coin = function (parent, o) {
    const size = o.size || 90;
    const s = K.mx.svg(parent, o.x, o.y, 1, 1);
    coin(s, size, o.symbol || "$", o.loss);
    if (o.at != null) { K.mx.enter(s, o.at, { style: o.style || "scale", key: "coin" }); sfx(o.at, "coin", 0.3, o); }
    if (o.out != null) K.mx.exit(s, o.out);
    return s;
  };
  K.mx.flow = function (parent, o) {
    const at = o.at || 0, until = o.until || at + 2, rate = o.rate || 6, travel = o.travel || 0.95, size = o.size || 62;
    const [x0, y0] = o.from, [x1, y1] = o.to;
    const mx = (x0 + x1) / 2, my = (y0 + y1) / 2, len = Math.hypot(x1 - x0, y1 - y0) || 1;
    const arc = o.arc == null ? -0.35 * len : o.arc; // negative = bows upward
    const cx = mx + (-(y1 - y0) / len) * arc * Math.sign(x0 - x1 || 1), cy = my + ((x1 - x0) / len) * arc * Math.sign(x0 - x1 || 1);
    const bez = (u) => [(1 - u) * (1 - u) * x0 + 2 * (1 - u) * u * cx + u * u * x1, (1 - u) * (1 - u) * y0 + 2 * (1 - u) * u * cy + u * u * y1];
    const s = K.mx.svg(parent, 0, 0, 1000, 860);
    const route = svgEl("path", { d: `M${x0},${y0} Q${cx},${cy} ${x1},${y1}`, fill: "none", stroke: rgba(C.lavender, 0.22), "stroke-width": 4, "stroke-dasharray": "3 14", "stroke-linecap": "round" }, s);
    const n = Math.max(1, Math.ceil((until - at) * rate));
    const r = rng(K.MX.seed + ":flow:" + uid);
    const coins = Array.from({ length: n }, (_, i) => ({ g: coin(s, size * (0.82 + r() * 0.3), o.symbol || "$", o.loss), t0: at + i / rate + (r() - 0.5) * 0.06, jit: (r() - 0.5) * 26, rot: (r() - 0.5) * 40 }));
    const ease = gsap.parseEase(K.EASE.flow);
    K.onFrame((q) => {
      for (const c of coins) {
        const u = (q - c.t0) / travel;
        if (u < 0 || u > 1) { c.g.setAttribute("opacity", 0); continue; }
        const e = ease(u), [px, py] = bez(e);
        const sc = u < 0.15 ? 0.55 + 0.45 * (u / 0.15) : u > 0.85 ? 1 - ((u - 0.85) / 0.15) * 0.6 : 1;
        const op = u < 0.08 ? u / 0.08 : u > 0.9 ? 1 - (u - 0.9) / 0.1 : 1;
        c.g.setAttribute("opacity", op.toFixed(3));
        c.g.setAttribute("transform", `translate(${px.toFixed(1)},${(py + c.jit * Math.sin(e * Math.PI)).toFixed(1)}) rotate(${(c.rot * (1 - e)).toFixed(1)}) scale(${sc.toFixed(3)})`);
      }
    });
    hide(s); tl.set(s, { autoAlpha: 1 }, at - 0.2);
    tl.fromTo(route, { opacity: 0 }, { opacity: 1, duration: 0.3, immediateRender: false }, at - 0.2);
    if (o.out != null) K.mx.exit(s, o.out); else tl.to(route, { opacity: 0, duration: 0.4 }, until + travel);
    sfx(at, "coin", 0.3, o);
    noteIntent(o, "flow");
    return { el: s };
  };

  // ---------- gauge ----------
  K.mx.gauge = function (parent, o) {
    const r = o.r || 250, pad = 60, at = o.at || 0, danger = o.danger == null ? 0.7 : o.danger;
    const s = K.mx.svg(parent, o.x - r - pad, o.y - r - pad, 2 * (r + pad), r + pad + 40);
    const cx = r + pad, cy = r + pad;
    const P = (v, rr = r) => [cx - rr * Math.cos(Math.PI * v), cy - rr * Math.sin(Math.PI * v)];
    const arc = (a, b, rr = r) => { const p = P(a, rr), q = P(b, rr); return `M${p[0].toFixed(1)},${p[1].toFixed(1)} A${rr},${rr} 0 0 1 ${q[0].toFixed(1)},${q[1].toFixed(1)}`; };
    svgEl("path", { d: arc(0, 1), fill: "none", stroke: rgba(C.white, 0.08), "stroke-width": 34, "stroke-linecap": "round" }, s);
    svgEl("path", { d: arc(danger, 1), fill: "none", stroke: rgba(C.red, 0.16), "stroke-width": 34 }, s);
    for (let i = 0; i <= 10; i++) { const a = P(i / 10, r + 30), b = P(i / 10, r + (i % 5 ? 42 : 52)); svgEl("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: i / 10 > danger ? C.red : C.muted, "stroke-width": i % 5 ? 3 : 5, "stroke-linecap": "round", opacity: 0.8 }, s); }
    const safeArc = paper(svgEl("path", { fill: "none", stroke: "url(#kmx-lav)", "stroke-width": 34, "stroke-linecap": "round" }, s));
    const riskArc = paper(svgEl("path", { fill: "none", stroke: "url(#kmx-loss)", "stroke-width": 34 }, s));
    const needle = paper(svgEl("g", {}, s));
    svgEl("polygon", { points: `${cx - 11},${cy} ${cx},${cy - r + 46} ${cx + 11},${cy}`, fill: C.white }, needle);
    svgEl("circle", { cx, cy, r: 24, fill: C.purpleBlack, stroke: C.lavender, "stroke-width": 6 }, s);
    const tr = K.mx.track(o.from || 0);
    tr.to(at + 0.35, o.value, o.dur || 1.1, K.EASE.settle);
    const render = (q) => {
      const v = Math.max(0, Math.min(1.02, tr.at(q)));
      const a = Math.min(v, danger);
      safeArc.setAttribute("d", a > 0.004 ? arc(0, a) : ""); safeArc.setAttribute("opacity", a > 0.004 ? 1 : 0);
      riskArc.setAttribute("d", v > danger + 0.004 ? arc(danger, Math.min(1, v)) : ""); riskArc.setAttribute("opacity", v > danger + 0.004 ? 1 : 0);
      needle.setAttribute("transform", `rotate(${((v - 0.5) * 180).toFixed(2)} ${cx} ${cy})`);
    };
    K.onFrame(render); render(0);
    K.mx.enter(s, at, { style: o.style, key: "gauge" });
    sfx(at + 0.35, "click", 0.35, o);
    if (o.label) K.text(parent, o.label, { x: o.x, y: o.y + 90, size: 40, color: C.text, at: at + 0.3 });
    if (o.out != null) K.mx.exit(s, o.out);
    noteIntent(o, "gauge");
    const api = { el: s, track: tr, to(t, v, dur = 1.0) { tr.to(t, v, dur, K.EASE.settle); sfx(t, "click", 0.3, o); return api; } };
    return api;
  };

  // ---------- ring ----------
  K.mx.ring = function (parent, o) {
    const r = o.r || 170, at = o.at || 0, sw = o.stroke || 26, box = 2 * r + sw * 2;
    const s = K.mx.svg(parent, o.x - box / 2, o.y - box / 2, box, box);
    const c = box / 2;
    const circ = `M${c},${c - r} A${r},${r} 0 1 0 ${c},${c + r} A${r},${r} 0 1 0 ${c},${c - r}`; // counter-clockwise from the top (RTL)
    svgEl("path", { d: circ, fill: "none", stroke: rgba(C.white, 0.08), "stroke-width": sw }, s);
    const arc = paper(svgEl("path", { d: circ, fill: "none", stroke: o.loss ? "url(#kmx-loss)" : "url(#kmx-lav)", "stroke-width": sw, "stroke-linecap": "round", pathLength: 1, "stroke-dasharray": "1 1" }, s));
    const tr = K.mx.track(o.from || 0);
    const t0 = o.countAt != null ? o.countAt : at + 0.2;
    tr.to(t0, o.value, o.dur || 1.0, "power3.out");
    const render = (q) => { const v = Math.max(0, Math.min(1, tr.at(q))); arc.setAttribute("stroke-dashoffset", (1 - v).toFixed(4)); arc.setAttribute("opacity", v > 0.003 ? 1 : 0); };
    K.onFrame(render); render(0);
    K.mx.enter(s, at, { style: o.style, key: "ring" });
    const num = o.number === false ? null : K.mx.roll(parent, { x: o.x, y: o.y, from: Math.round((o.from || 0) * 100), value: Math.round(o.value * 100), countAt: t0, dur: o.dur || 1.0, at, size: o.size || 96, prefix: o.prefix, suffix: o.suffix == null ? "٪" : o.suffix, smallAffix: false, style: "scale", sfx: false, ...(o.numberOpts || {}) });
    sfx(t0 + (o.dur || 1) * 0.7, "coin", 0.3, o);
    if (o.out != null) { K.mx.exit(s, o.out); if (num) K.mx.exit(num.el, o.out); }
    noteIntent(o, "ring");
    return { el: s, num, track: tr };
  };

  // ---------- K.mx.light: removed (MOT-6) ----------
  // A light pool that slid after the graphic. Youssef, 2026-10-30: "the light following the graphic: never add it". Kept
  // as a no-op so older scenes still load; it draws nothing and warns. Pieces carry their own lighting (section 4).
  K.mx.light = function () {
    const w = "K.mx.light is removed (MOT-6): never a light that follows the graphic; it draws nothing";
    if (!K.warnings.includes(w)) { K.warnings.push(w); console.warn(w); }
    const stub = { el: null, to() { return stub; }, out() { return stub; } };
    return stub;
  };
})();
