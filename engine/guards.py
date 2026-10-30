"""Checks that turn Ahmed's recurring review notes into failures (review hardening, 2026-10-18).

Pure functions over data the lint page or the MP4 already gave: lint.py and make.py call them; tests call them with
made-up data. Each docstring names the note it stops coming back.
"""
import re

TITLE_END = 3.0        # s: the opening title window (SHORT-4)
EMPTY_LIMIT = 1.5      # s: an empty stretch longer than this outside the title window cannot be excused (P1-7)
SFX_GAP = 0.3          # s: cues closer than this stack (SND-5)
SFX_REACH = 0.25       # s: a cue this far from any visual event lands on nothing
FREEZE_SHOWN = 0.12    # s (3 frames) of a freeze inside a face/split window is visible
FACE_SHARE = 0.5       # workshop shorts: his face on screen at least this share of the runtime (SHORT-15)
BOARD_ALONE = 3.0      # motion-layer shorts: longest a graphic may hold the screen without him (MOT-7)
WORD_EDGE = 0.03       # s: a cut this far inside a word is a cut in the word (SHORT-16)


def overlap(a, b):
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def box_hit(r, box):
    """Area of rectangle r (dict x0..y1) inside box [x0, y0, x1, y1]."""
    return max(0, min(r["x1"], box[2]) - max(r["x0"], box[0])) * max(0, min(r["y1"], box[3]) - max(r["y0"], box[1]))


# ---------- lint: frames from the page ----------

# Subtitles on face-only moments (SHORT-12, Ahmed 2026-10-18 on live H: "this was super we can stick to it"): their
# usual top (look2 #captions, y 1268) or lower, down to CAP_LOWEST in runtime/kanz-footage.js, never up over his head.
CAP_BAND_TOP, CAP_LOWEST = 1268, 1500

def on_face_findings(t, frame, box):
    """Text drawn over his eyes or mouth (`on-face`): the title over his eyes (casino A, C, E, G, H)."""
    if not box:
        return []
    out = []
    for it in frame["items"]:
        if it["kind"] not in ("text", "caption", "title") or it.get("opacity", 1) < .5 or not it.get("over_face", it["kind"] != "text"):
            continue
        area = (it["x1"] - it["x0"]) * (it["y1"] - it["y0"])
        if area and box_hit(it, box) > 0.02 * area:
            out.append(dict(kind="on-face", t=t, id=it["id"], what=it["txt"][:40], by=it["kind"]))
    return out


def freeze_findings(face_windows, split_windows, runs, min_shown=FREEZE_SHOWN):
    """Face or split windows showing a source freeze (`freeze`): live C's "lag"."""
    out = []
    for kind, wins in (("face", face_windows), ("split", split_windows)):
        for w in wins or []:
            for r in runs or []:
                ov = overlap((w[0], w[1]), r)
                if ov >= min_shown:
                    out.append({"kind": "freeze", "from": round(max(w[0], r[0]), 3), "to": round(min(w[1], r[1]), 3),
                                "why": f"{kind} window {w[0]:.2f}-{w[1]:.2f} shows a frozen source picture {r[0]:.2f}-{r[1]:.2f} s"})
    return out


def outside_title(start, end, title_end=TITLE_END):
    return max(0.0, end - max(start, title_end))


def excusable(finding, title_end=TITLE_END, limit=EMPTY_LIMIT):
    """lint-ok.json may not excuse an empty stretch (dead / fill) over `limit` s outside the title window (P1-7:
    "empty seconds on screen" kept coming back as justified findings)."""
    if finding.get("kind") == "board-alone":  # MOT-7: fixed by recutting, never waived
        return False
    if finding.get("kind") not in ("dead", "fill"):
        return True
    return outside_title(finding.get("from", 0), finding.get("to", 0), title_end) <= limit


def tight_gap_findings(t, frame, gap):
    """A subheadline closer than `gap` px under its headline on the same board (`tight-gap`): "breathing room" on
    casino C and F."""
    items = [i for i in frame["items"] if i["kind"] == "text" and i.get("opacity", 1) >= .5 and i["txt"]]
    heads = [i for i in items if i.get("head")]
    out = []
    for h in heads:
        for s in items:
            if s is h or s.get("head") or s.get("board") != h.get("board"):
                continue
            if min(h["x1"], s["x1"]) - max(h["x0"], s["x0"]) <= 0.3 * min(h["x1"] - h["x0"], s["x1"] - s["x0"]):
                continue
            d = (s["y0"] - h["y1"]) / (h.get("sc") or 1)  # in board px: the split shows the board at 0.8x
            if -0.25 * (s["y1"] - s["y0"]) / (h.get("sc") or 1) < d < gap - 0.5:
                out.append(dict(kind="tight-gap", t=t, id=s["id"], what=s["txt"][:30], by=h["txt"][:30],
                                why=f"{max(d, 0):.0f} px under the headline < {gap:.0f} px"))
    return out


def headline_cross_findings(t, frame, gap):
    """Anything that crosses a K.headline, or a board headline marked data-role="headline", or starts less than `gap`
    board px under its last line (TXT-6): panel and card edges, chart and grid lines, objects, images, blocks. The
    headline box is the union of its visible words; identified full-bleed backgrounds, captions, the headline's own glow
    and faint elements are ignored. `.head` alone is the display font (counters, buttons, big labels), not a headline:
    flagging it turned an approved Reel's moving price counters into 35 findings (Rising Stock v5, 2026-10-20)."""
    words = [i for i in frame["items"] if i["kind"] == "text" and i.get("hl") and i.get("opacity", 1) >= .5 and i["txt"]]
    heads = [i for i in frame["items"] if i["kind"] == "text" and i.get("bh") and not i.get("hl")
             and i.get("board") and i.get("opacity", 1) >= .5 and i["txt"]]
    if words:
        heads.append(dict(x0=min(w["x0"] for w in words), x1=max(w["x1"] for w in words),
                          y0=min(w["y0"] for w in words), y1=max(w["y1"] for w in words),
                          txt=" ".join(w["txt"] for w in words), hl=True, sc=words[0].get("sc", 1)))
    out = []
    for h in heads:
        sc = h.get("sc") or 1
        for i in frame["items"]:
            if i is h or i["kind"] in ("caption", "title") or i.get("hl") or i.get("background") or i.get("opacity", 1) < .5:
                continue
            if not h.get("hl") and i.get("board") != h.get("board"):
                continue
            if i["kind"] == "text" and not i.get("card"):
                continue  # plain labels: text-on-text and tight-gap cover them
            if min(h["x1"], i["x1"]) <= max(h["x0"], i["x0"]):
                continue
            if i["y1"] <= h["y0"] or i["y0"] >= h["y1"] + (gap - .5) * sc:
                continue
            d = (i["y0"] - h["y1"]) / sc
            why = "crosses the headline" if d < 0 else f"less than {gap:.0f} px under the headline"
            out.append(dict(kind="headline-cross", t=t, id=i["id"], what=i["txt"][:30], by=h["txt"][:30], why=why))
    return out


CURRENCY_OK = re.compile(r"\$[⁦‎]?[\d٠-٩]")


def currency_findings(t, frame):
    """A $ not attached on the left of its digits (`stray-currency`): casino E 39.8 s, reported fixed, still wrong.
    `pos` (from the page) says where the $ glyph really landed relative to its number."""
    out = []
    for it in frame["items"]:
        if it["kind"] not in ("text", "caption", "title") or "$" not in it["txt"] or it.get("opacity", 1) < .5:
            continue
        txt = it["txt"]
        bad = [m.start() for m in re.finditer(r"\$", txt) if not CURRENCY_OK.match(txt, m.start())]
        why = "a $ not followed by its digits (use K.money)" if bad else None
        pos = it.get("currency")
        if not why and pos and not pos.get("ok", True):
            why = f"the $ renders {pos.get('where', 'away from its digits')} (use K.money)"
        if why:
            out.append(dict(kind="stray-currency", t=t, id=it["id"], what=txt[:40], why=why))
    return out


def sfx_findings(cues, events, gap=SFX_GAP, reach=SFX_REACH):
    """Cues within `gap` s of each other (`sfx-overlap`; the mixer drops one, so it should not be written) and cues
    more than `reach` s from any visual event (`sfx-orphan`). Effects stacking: Ahmed 2026-10-18."""
    out = []
    cs = sorted(cues, key=lambda c: c["t"])
    for a, b in zip(cs, cs[1:]):
        if b["t"] - a["t"] < gap - 1e-6:
            out.append(dict(kind="sfx-overlap", t=round(b["t"], 3), what=f"{a['cat']} {a['t']:.2f}s + {b['cat']} {b['t']:.2f}s",
                            why=f"{b['t'] - a['t']:.2f} s apart < {gap} s"))
    ev = sorted(events)
    for c in cs:
        near = min((abs(e - c["t"]) for e in ev), default=1e9)
        if near > reach:
            out.append(dict(kind="sfx-orphan", t=round(c["t"], 3), what=c["cat"],
                            why=f"no visual event within {reach} s (nearest {near:.2f} s)" if near < 1e8 else "no visual event"))
    return out


def window_union(windows, duration):
    """Clip windows to the actual runtime and merge their union (SHORT-15)."""
    merged = []
    for a, b in sorted((max(0, a), min(b, duration)) for a, b, *_ in windows or []):
        if b <= a:
            continue
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(b, merged[-1][1])
        else:
            merged.append([a, b])
    return merged


def face_share(face_windows, split_windows, duration):
    windows = window_union(list(face_windows or []) + list(split_windows or []), duration)
    return sum(b - a for a, b in windows) / duration if duration > 0 else 0.0


def face_share_findings(face_windows, split_windows, duration, live, share=FACE_SHARE, profile=""):
    """His face (full or split) at least half the runtime: all current cut-out shorts (SHORT-15, quiz 2026-10-20, Q3).
    Legacy scenes keep the workshop-only check."""
    out = []
    for a in window_union(face_windows, duration):
        for b in window_union(split_windows, duration):
            if overlap(a, b) > 1e-6:
                out.append(dict(kind="face-overlap", **{"from": max(a[0], b[0]), "to": min(a[1], b[1])},
                                why="face and split windows overlap (SHORT-15)"))
    got = face_share(face_windows, split_windows, duration)
    if (live or profile >= "2026-10-18") and got + 1e-6 < share:
        out.append(dict(kind="face-share", t=0, why=f"his face shows {got:.0%} of {duration:.1f} s < {share:.0%} (SHORT-15)"))
    return out


def board_alone_findings(face_windows, split_windows, duration, limit=BOARD_ALONE):
    """Graphics alone on screen (neither his full face nor the split) longer than `limit` s (`board-alone`, MOT-7):
    graphics share the screen with him in the split, or cut in alone for a short beat and cut back to him. Stretches
    merge, so a board can never hand on to another board. Never excusable in lint-ok.json: fix it by recutting."""
    shown, out, t = window_union(list(face_windows or []) + list(split_windows or []), duration), [], 0.0
    for a, b in shown + [[duration, duration]]:
        if a - t > limit + 0.05:
            out.append(dict(kind="board-alone", rule="MOT-7", **{"from": round(t, 2), "to": round(a, 2)},
                            why=f"graphics alone for {a - t:.1f} s > {limit:.0f} s: split with him, or cut back to him (MOT-7)"))
        t = max(t, b)
    return out


def lands_on_board(c, face_windows, split_windows):
    """True when the picture after the change at c is a full-screen board reached by a hard cut (the half-built check
    applies); False at every split edge (the split <-> board move eases) and where his face follows."""
    near = lambda x: abs(x - c) < 0.02  # noqa: E731
    if any(near(a) or near(b) for a, b, *_ in split_windows or []):
        return False
    return not any(near(a) for a, b, *_ in face_windows or [])


def window_edges(face_windows, split_windows, duration):
    """Every time the picture changes between face, split and board."""
    edges = set()
    for a, b, *_ in list(face_windows or []) + list(split_windows or []):
        for x in (a, b):
            if 0.05 < x < duration - 0.05:
                edges.add(round(x, 3))
    return sorted(edges)


def mid_word_findings(edges, words, edge=WORD_EDGE):
    """A cut or split move inside a spoken word (`mid-word-cut`, SHORT-16)."""
    out = []
    for x in edges:
        for w in words:
            if w["start"] + edge < x < w["end"] - edge:
                out.append(dict(kind="mid-word-cut", t=x, what=w["w"], why=f"cut at {x:.2f} s inside a word {w['start']:.2f}-{w['end']:.2f}"))
                break
    return out


def end_cut_findings(duration, voice_end, cut):
    """The scene ends before the voice does (`end-cut`): the last word cut off (casino A v4, F v3, H v2, E v4)."""
    if cut and duration < voice_end - 0.05:
        return [dict(kind="end-cut", t=round(duration, 3), why=f"K.duration {duration:.2f} s < voice {voice_end:.2f} s")]
    return []


TAIL_LIMIT = 0.6       # s after the last word: the video ends ~0.4 s after it (PACE-6)
QA_TAIL_LIMIT = 3.0    # a Q&A short's reply board (QA.reply, Package 04) is read after the last word: QA.TAIL 2.4 s + the cut
QA_REPLY = re.compile(r"\bQA\s*\.\s*reply\s*\(")
HERO_SHARE = 0.6       # the hook hero back at this share of its hook width or more is a replay (PACE-6)
STILL_LIMIT = 2.0      # s of speech over one unchanging picture (EXPL-2)
ICON = re.compile(r"\.png$", re.I)


def tail_findings(duration, last_word_end, limit=TAIL_LIMIT):
    """Silence after the last word (`long-tail`, PACE-6): "remove the dead silence" (re-do review 2026-10-18, the
    1.3 s tail every Reel copied from the worked example)."""
    if last_word_end is None or duration - last_word_end <= limit + 1e-6:
        return []
    return [dict(kind="long-tail", t=round(last_word_end, 3), rule="PACE-6",
                 why=f"the video runs {duration - last_word_end:.2f} s after the last word > {limit} s "
                     f"(PACE-6: K.duration = tLast + 0.4)")]


def tail_limit(scene_src):
    """PACE-6's tail, or the Q&A exception (Youssef 2026-10-30): a scene ending on QA.reply may run QA_TAIL_LIMIT."""
    return QA_TAIL_LIMIT if QA_REPLY.search(scene_src or "") else TAIL_LIMIT


def visible(frame, kinds=None):
    return [i for i in frame["items"] if i["kind"] != "caption" and i.get("opacity", 1) >= .5
            and (kinds is None or i["kind"] in kinds)]


def main_board(frame):
    """The board covering most of the frame (visible items' area), or None (headline only, footage)."""
    area = {}
    for i in visible(frame):
        if i.get("board"):
            area[i["board"]] = area.get(i["board"], 0) + (i["x1"] - i["x0"]) * (i["y1"] - i["y0"])
    return max(area, key=lambda b: area[b]) if area else None


def hero_of(frame):
    """The largest visible picture (img.obj) of a frame, or None."""
    pics = [i for i in visible(frame, ("obj",)) if re.search(r"\.(png|jpe?g|webp|svg)$", i["txt"], re.I)]
    return max(pics, key=lambda i: (i["x1"] - i["x0"]) * (i["y1"] - i["y0"])) if pics else None


def replay_findings(hook_frame, end_frame, t_end, share=HERO_SHARE):
    """The last frame back on the hook board or showing the hook's hero again (`hook-replay`, PACE-6): "we end the
    video with the same pic as the hook sucks", "we don't need a replica" (re-do review 2026-10-18)."""
    if not hook_frame or not end_frame:
        return []
    why = []
    board = main_board(hook_frame)
    if board and main_board(end_frame) == board:
        why.append("the last frame is on the hook board")
    hero = hero_of(hook_frame)
    if hero:
        w = hero["x1"] - hero["x0"]
        if any(i["txt"] == hero["txt"] and i["x1"] - i["x0"] >= share * w for i in visible(end_frame, ("obj",))):
            why.append(f"the hook hero {hero['txt']} is back on the last frame")
    if not why:
        return []
    return [dict(kind="hook-replay", t=round(t_end, 3), rule="PACE-6",
                 why="; ".join(why) + " (PACE-6: the last line gets its own moving visual, never a replay of the hook)")]


def still_image_findings(frames, words, skip=(), limit=STILL_LIMIT, moved_px=25.0, grown=0.04):
    """A stretch where the only picture on screen is one unchanging icon while the voice keeps explaining
    (`still-image`, EXPL-2, a warning): "not explanatory at all", "this needs to be dynamic ... rather than just an
    image" (re-do review 2026-10-18). frames: [(t, frame)] in time order; skip: [(a, b)] windows not checked (the hook,
    face/split windows). A run ends when anything appears or leaves, or the icon moves or grows (camera drift and the
    idle float stay under moved_px / grown between samples)."""
    def key(frame):
        items = visible(frame)
        objs = [i for i in items if i["kind"] == "obj"]
        if len(objs) != 1 or not ICON.search(objs[0]["txt"]):
            return None
        return (objs[0]["id"], frozenset(i["id"] for i in items)), objs[0]

    def moved(a, b):
        ca, cb = ((a["x0"] + a["x1"]) / 2, (a["y0"] + a["y1"]) / 2), ((b["x0"] + b["x1"]) / 2, (b["y0"] + b["y1"]) / 2)
        wa, wb = a["x1"] - a["x0"], b["x1"] - b["x0"]
        return abs(ca[0] - cb[0]) > moved_px or abs(ca[1] - cb[1]) > moved_px or abs(wa - wb) > grown * max(wa, 1)

    def speech(a, b):
        return sum(overlap((a, b), (w["start"], w["end"])) for w in words)

    out, run = [], None   # run: [start, key, last icon box]

    def close(end):
        if run and speech(run[0], end) > limit + 1e-6:
            out.append({"kind": "still-image", "level": "warn", "rule": "EXPL-2", "from": round(run[0], 3), "to": round(end, 3),
                        "what": run[2]["txt"], "why": f"{speech(run[0], end):.1f} s of speech over one still icon > {limit} s "
                                                      f"(EXPL-2: explain it with a moving diagram; icons only support)"})

    for t, frame in frames:
        k = None if any(a <= t < b for a, b in skip) else key(frame)
        if run and k and k[0] == run[1] and not moved(run[2], k[1]):
            run[2] = k[1]
            continue
        close(t)
        run = [t, k[0], k[1]] if k else None
    if run:
        close(frames[-1][0])
    return out


def caption_switch_findings(samples):
    """Subtitles on the seam exactly when the split shows (`caption-switch`, SHORT-12). samples: [(t, split_shown,
    caption_top_px or None)]."""
    out = []
    for t, shown, top in samples:
        on_seam = top is not None and 940 <= top <= 980
        if shown != on_seam:
            out.append(dict(kind="caption-switch", t=t, why=f"split {'on' if shown else 'off'} but subtitles at {top}"))
    return out


# ---------- ship: the MP4 and the source ----------

def env_db(x, win):
    import numpy as np
    x = np.asarray(x, dtype=np.float64)
    if len(x) < win:
        return np.array([-120.0])
    c = np.cumsum(np.concatenate([[0.0], x * x]))
    p = (c[win:] - c[:-win]) / win
    return 10 * np.log10(np.maximum(p, 1e-12))


def ending_problems(mono, sr, last=0.15, margin=6.0):
    """Voice still sounding in the final `last` s of the MP4 (the last word cut off): the loudest 20 ms there must stay
    within `margin` dB of the room-tone floor (the 10th percentile of 20 ms levels over the file)."""
    import numpy as np
    win = int(0.02 * sr)
    lv = env_db(mono, win)
    floor = float(np.percentile(lv, 10))
    tail = env_db(mono[-int(last * sr) - win:], win)
    peak = float(tail.max())
    if peak > floor + margin:
        return [f"voice still sounding in the last {last} s ({peak:.0f} dB, room tone {floor:.0f} dB): the last word is cut off"]
    return []


def leak_checks(cut, gap=None):
    """SHORT-3: keep next-word clearance, or the whole last word with an explicit listening warning."""
    if gap is None:
        import footage
        gap = getattr(footage, "NEXT_WORD_GAP", 0.05)
    out, warns = [], []
    for r in (cut or {}).get("ranges", []):
        nxt, last, end = r.get("next_word_start"), r["last_word_end"], r["end"]
        if end < last - 1e-6:
            out.append(f"range {r['start']:.2f}-{r['end']:.2f} ends before its last word ({r['last_word_end']:.2f} s)")
        elif nxt is not None and end > nxt - gap + 1e-6:
            if nxt - last < gap and end <= last + .010 + 1e-6:
                warns.append(f"ending: kept the whole last word; next word {(nxt - last) * 1000:.0f} ms later, listen")
            else:
                out.append(f"range {r['start']:.2f}-{end:.2f} leaves {nxt - end:.3f} s before the next source word "
                           f"({nxt:.2f} s), needs {gap:.2f} s (SHORT-3)")
    return out, warns


def leak_problems(cut, gap=None):
    """Failures only; ship uses leak_checks so a tight whole-word ending also reaches the human ear."""
    return leak_checks(cut, gap)[0]


def decimate_runs(flags, fps):
    """From mpdecimate's keep/drop sequence (True = drop, a repeat of the frame before): (drops, longest run in s)."""
    longest = cur = 0
    for f in flags:
        cur = cur + 1 if f else 0
        longest = max(longest, cur)
    return sum(flags), (longest + 1) / fps if longest else 0.0


def fps_problems(source_fps, frames_fps, render_fps):
    out = []
    if frames_fps and abs(frames_fps - render_fps) > 0.01:
        out.append(f"footage frames are {frames_fps:g} fps but the render runs at {render_fps:g} fps (frames skip or repeat)")
    warn = None
    if source_fps and render_fps and abs(source_fps / render_fps - round(source_fps / render_fps)) > 0.02:
        warn = (f"source is {source_fps:.3g} fps, the render {render_fps:g} fps: ffmpeg drops frames unevenly (a slight "
                f"judder on fast moves)")
    return out, warn


CHARCOAL = 22   # grey level of the charcoal board


def frame_stats(g):
    """(mean, spread, content) of a small grey frame; content = share of pixels well away from the charcoal board."""
    import numpy as np
    g = np.asarray(g, dtype=np.float32)
    return float(g.mean()), float(g.std()), float((np.abs(g - CHARCOAL) > 30).mean())


def strip_flags(frames, cut_index, fps=24, charcoal=(52, 7.0), flash=55, big=28.0, small=10.0, built=True):
    """Frames around one cut (small grey arrays, the cut between cut_index - 1 and cut_index). Flags (SHORT-10):
      charcoal   near-empty charcoal (mean < 52, spread < 7): the cut landed before the board was built
      flash      a frame `flash` levels brighter than both neighbours
      half-built the first frame after the cut has under half the content the board has 0.25 s later (only where a
                 hard cut lands on a full-screen board, built=True: an eased split move changes its content on purpose)
      one-frame  a single frame unlike both neighbours while they match each other (a wrong board for one frame)
    Returns [(flag, index), ...]."""
    import numpy as np
    st = [frame_stats(f) for f in frames]
    flags = []
    for i, (m, s, c) in enumerate(st):
        if m < charcoal[0] and s < charcoal[1]:
            flags.append(("charcoal", i))
        if 0 < i < len(st) - 1 and m - st[i - 1][0] > flash and m - st[i + 1][0] > flash:
            flags.append(("flash", i))
    later = min(len(st) - 1, cut_index + int(0.25 * fps))
    if built and cut_index < len(st) and st[later][2] > 0.08 and st[cut_index][2] < 0.5 * st[later][2]:
        flags.append(("half-built", cut_index))
    d = lambda i, j: float(np.abs(np.asarray(frames[i], np.float32) - np.asarray(frames[j], np.float32)).mean())
    for k in range(1, len(frames) - 1):
        if d(k - 1, k) > big and d(k, k + 1) > big and d(k - 1, k + 1) < small:
            flags.append(("one-frame", k))
    return flags


def track_jumps(cx, windows, fps, limit=6.0, seams=()):
    """Face-track jumps inside face/split windows: a camera step over `limit` source px per frame (SHORT-10). `seams`
    are frame indices where the picture cuts on purpose (voice joins, tighten_footage cuts)."""
    out, skip = [], {int(x) for x in seams}
    for a, b, *_ in windows or []:
        i0, i1 = int(a * fps), min(len(cx) - 1, int(b * fps))
        steps = [0.0 if i + 1 in skip else abs(cx[i + 1] - cx[i]) for i in range(i0, i1)]
        if steps and max(steps) > limit:
            k = i0 + steps.index(max(steps))
            out.append(f"face track jumps {max(steps):.1f} px at {k / fps:.2f} s")
    return out
