"""The ship checks on the rendered MP4 (review hardening, 2026-10-18). make.py ship and make.py check call run().

Every project:
  ending     the voice has stopped before the final 0.15 s of the MP4 (the last word is not cut off)
  tail       the MP4 ends within 0.6 s of the last word in build/timing.js: no silent tail (PACE-6, 2026-10-18)
  notes      projects/<slug>/notes.json (Ahmed's review notes): a still at every noted time -> out/notes-<version>.jpg,
             each listed as fixed or OPEN; a note is reported fixed only with its still from this version
Cut-out shorts (transcript.json cut_from) also:
  cuts       a 12-frame strip around every cut (face/split windows from out/lint.json, plus ffmpeg scene changes)
             -> out/cuts-<version>.jpg; charcoal, flash, half-built and one-frame flags fail (SHORT-10)
  leak       every source range stops NEXT_WORD_GAP before the next source word; a tighter whole-word ending
             (last word end + up to 10 ms) warns for human listening instead (SHORT-3)
  joins      every cut is heard (engine/joincheck.py, local faster-whisper): the word each side of the cut must be
             the word in the uncut source, heard as surely, and no cut may fall inside a word (out/joins.json).
             The leak check only reads numbers; this one passed nothing it could not hear (reels 7-12, 2026-10-26)
  title      a K.title, with the text from shorts/_titles.json (SHORT-4)
  freeze     duplicate frames (mpdecimate) in face and split windows: a run of 0.5 s or more fails
  fps        footage frames at the render's frame rate; the source's own rate is reported
  track      face-track jumps over 6 px a frame inside face/split windows

A cut flag can be excused in lint-ok.json as {"kind": "cut-strip", "t": <cut time>, "why": "..."}.
Explicit partial checks for small revisions run ending/tail and notes only here; make.py still checks frames and
loudness (REV-3, quiz 2026-10-20, Q9). Full check and ship keep all shorts checks.
"""
import json
import re
import subprocess
from pathlib import Path

import numpy as np

import guards
import shortinfo
import footage

SR = 48000
STRIP = 12
THUMB = (180, 320)


def audio_mono(path, t0=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", f"{t0:.3f}"] if t0 is not None else []) + ["-i", str(path), "-vn", "-ac", "1",
                                                                                          "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def duration(mp4):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                                capture_output=True, text=True, check=True).stdout)


def ending(proj, mp4):
    """Voice energy in the last 0.15 s of the MP4. An effect still ringing there (voice.wav quiet) is only a warning."""
    probs = guards.ending_problems(audio_mono(mp4), SR)
    if not probs:
        return [], []
    voice = proj / "audio" / "voice.wav"
    if voice.exists():
        d = duration(mp4)
        v = audio_mono(voice)
        v = v[: int(d * SR)] if len(v) >= int(d * SR) else np.concatenate([v, np.zeros(int(d * SR) - len(v), np.float32)])
        if not guards.ending_problems(v, SR):
            return [], ["the last 0.15 s are loud but the voice is silent there: an effect is still ringing at the end"]
    return probs, []


def last_word_end(proj):
    """End of the last spoken word in build/timing.js (output time), or None."""
    f = proj / "build" / "timing.js"
    m = re.search(r"window\.TOKENS=(\[.*?\]);", f.read_text(encoding="utf-8"), re.S) if f.exists() else None
    ends = [t["end"] for t in (json.loads(m.group(1)) if m else []) if not t.get("tr") and t.get("end") is not None]
    return max(ends, default=None)


def tail(proj, mp4):
    """PACE-6: no silent tail after the last word on the rendered MP4."""
    src = (proj / "scene.js").read_text(encoding="utf-8") if (proj / "scene.js").exists() else ""
    return ["tail: " + f["why"] for f in guards.tail_findings(duration(mp4), last_word_end(proj), guards.tail_limit(src))]


def frames_rgb(mp4, t, n, size=THUMB):
    w, h = size
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-ss", f"{max(t, 0):.4f}", "-frames:v", str(n),
                          "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    k = len(raw) // (w * h * 3)
    return np.frombuffer(raw[: k * w * h * 3], np.uint8).reshape(k, h, w, 3)


def scene_cuts(mp4, thr=0.25):
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mp4), "-vf", f"select='gt(scene,{thr})',showinfo", "-f", "null", "-"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", log)]


def cut_times(short, mp4, fps):
    edges = guards.window_edges(short.get("faces"), short.get("splits"), short.get("duration") or duration(mp4))
    for t in scene_cuts(mp4):
        if all(abs(t - e) > 0.2 for e in edges):
            edges.append(round(t, 3))
    return sorted(edges)


def cut_strips(proj, mp4, version, short, fps, allow):
    """SHORT-10: 12 frames around every cut, one row each, flagged frames outlined. Returns (problems, sheet path)."""
    from PIL import Image, ImageDraw
    from contact import label_font
    cuts = cut_times(short, mp4, fps)
    if not cuts:
        return [], None
    w, h = THUMB
    sheet = Image.new("RGB", (STRIP * w, len(cuts) * (h + 34)), "white")
    d, font = ImageDraw.Draw(sheet), label_font(22)
    problems = []
    for row, c in enumerate(cuts):
        first = int(np.ceil(c * fps - 1e-6)) - STRIP // 2
        fr = frames_rgb(mp4, first / fps, STRIP)
        if not len(fr):
            continue
        grey = [f.mean(axis=2)[::4, ::4] for f in fr]
        flags = guards.strip_flags(grey, min(STRIP // 2, len(grey) - 1), fps,
                                   built=guards.lands_on_board(c, short.get("faces"), short.get("splits")))
        bad = [f for f in flags if not any(a.get("kind") == "cut-strip" and abs(a.get("t", -9) - c) < 0.05 and str(a.get("why", "")).strip()
                                           for a in allow)]
        y = row * (h + 34)
        for i, f in enumerate(fr):
            sheet.paste(Image.fromarray(f), (i * w, y))
        for flag, i in bad:
            d.rectangle([i * w + 2, y + 2, i * w + w - 3, y + h - 3], outline=(230, 40, 40), width=6)
        d.line([(STRIP // 2) * w, y, (STRIP // 2) * w, y + h], fill=(213, 173, 239), width=4)
        d.text((6, y + h + 4), f"cut {c:.2f}s  " + (", ".join(f"{f} @{(first + i) / fps:.2f}s" for f, i in bad) or "ok"),
               fill=(200, 0, 0) if bad else (0, 0, 0), font=font)
        problems += [f"cut {c:.2f}s: {f} frame at {(first + i) / fps:.2f}s" for f, i in bad]
    out = proj / "out" / f"cuts-{version}.jpg"
    sheet.save(out, quality=86)
    return problems, out


def decimate_flags(mp4, a, b):
    log = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "debug", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(mp4),
                          "-vf", "mpdecimate", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    return [m == "drop" for m in re.findall(r"Parsed_mpdecimate_\d+ @ [^\]]+\] (keep|drop)", log)]


def freezes_in_mp4(mp4, short, fps, limit=0.5):
    problems, total = [], 0
    for kind, wins in (("face", short.get("faces")), ("split", short.get("splits"))):
        for a, b in wins or []:
            if b - a < 0.3:
                continue
            drops, longest = guards.decimate_runs(decimate_flags(mp4, a, b), fps)
            total += drops
            if longest >= limit - 1e-6:
                problems.append(f"{kind} window {a:.2f}-{b:.2f}: the picture stands still for {longest:.2f} s (mpdecimate)")
    return problems, total


def source_fps(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=avg_frame_rate", "-of",
                            "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout.strip()
        n, dd = r.split("/")
        return float(n) / float(dd)
    except (OSError, ValueError, ZeroDivisionError, subprocess.CalledProcessError):
        return None


def title_problems(proj):
    """SHORT-4: a footage short has K.title, and its text is the pick in shorts/_titles.json (never copied by hand)."""
    import lint
    src = (proj / "scene.js").read_text(encoding="utf-8")
    code = lint.static_scene_findings(src)
    if any(f["kind"] == "title" for f in code):
        return ["no K.title: every short opens with its title (SHORT-4)"]
    _, entry = shortinfo.title_entry(proj.name)
    want = shortinfo.title_text(entry)
    m = re.search(r"\bK\s*\.\s*title\s*\(\s*([\"'`])((?:\\.|(?!\1).)*)\1", src)
    if want and m and m.group(2).replace("*", "").strip() != want.replace("*", "").strip():
        return [f"K.title text differs from shorts/_titles.json ('{want}'): call K.title() with no text"]
    if not entry and not m:
        return ["K.title() has no text and shorts/_titles.json has no entry for this project"]
    return []


def notes(proj, mp4, version):
    """Stills at every noted time -> out/notes-<version>.jpg; returns lines to print."""
    f = proj / "notes.json"
    if not f.exists():
        return []
    from contact import sheet
    items = json.loads(f.read_text(encoding="utf-8"))
    if not items:
        return []
    d = proj / "out" / f"notes-{version}"
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.jpg"):
        old.unlink()
    lines = []
    for i, n in enumerate(items, 1):
        t = float(n["t"])
        status = "fixed" if n.get("status") == "fixed" else "OPEN"
        name = d / f"n{i:02d}-{t:05.1f}s-{status}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-ss", f"{t:.3f}", "-frames:v", "1", str(name)], check=True)
        if status == "fixed":
            n["checked_in"] = version
        lines.append(f"  note {i} at {t:.1f}s [{status}] {n.get('note', '')}  (still: {name.relative_to(proj).as_posix()})")
    f.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    lines.append("  notes sheet -> " + str(sheet(d, proj / "out" / f"notes-{version}.jpg")))
    return lines


def review_problems(proj, report):
    """New shorts require metadata and a matching lint report; legacy projects explicitly keep the old path."""
    profile = max(shortinfo.defaults_profile(proj), report.get("profile") or "")
    if not shortinfo.cut_from(proj) or profile < "2026-10-18":
        return []
    out = [h["why"] for h in shortinfo.metadata_findings(proj, profile)]
    short = report.get("short") if isinstance(report.get("short"), dict) else {}
    if (report.get("review") != shortinfo.review_stamp(proj) or not short.get("cut") or
            not all(k in short for k in ("faces", "splits", "duration", "fps"))):
        out.append("missing or stale out/lint.json for this new short: run lint --strict before ship (SHORT-4/17)")
    return out


def run(proj, mp4, version, allow=(), picture=True, partial=False):
    """All checks (picture=False, for make.py remix: the sound checks only). Returns (problems, warnings, info lines)."""
    proj = Path(proj)
    lint_report = shortinfo.load(proj / "out" / "lint.json") or {}
    if not isinstance(lint_report, dict):
        lint_report = {}
    short = lint_report.get("short") if isinstance(lint_report.get("short"), dict) else {}
    fps = short.get("fps") or 24
    problems, warns, info = [], [], []
    ending_errors, w = ending(proj, mp4)
    problems += ending_errors + tail(proj, mp4)
    warns += w
    if not picture:  # a remix cannot move the ending (the picture is copied): report it, do not fail
        return [], warns + [p + " (a remix keeps the cut; fix it in a new version)" for p in problems], info
    if partial:  # REV-3: no fresh full-scene lint required for the changed-seconds review
        info += notes(proj, mp4, version)
        if not info:
            problems.append("partial check needs notes.json entries for the changed seconds (REV-3/7)")
        return problems, warns, info
    cut = shortinfo.cut_from(proj)
    if cut:
        review = review_problems(proj, lint_report)
        if review:
            return problems + review, warns, info
        gap = getattr(footage, "NEXT_WORD_GAP", 0.05)
        p, w = guards.leak_checks(cut, gap=gap)
        problems += p
        warns += w
        try:
            import joincheck
            p, w, lines = joincheck.check(proj)
            problems += p
            warns += w
            info += ["joins heard (out/joins.json):"] + lines if lines else []
        except ImportError:
            warns.append("join check skipped: faster-whisper is not installed; listen to every cut before shipping")
        if ending_errors and guards.leak_checks({"ranges": cut.get("ranges", [])[-1:]}, gap=gap)[1]:
            last = last_word_end(proj)
            if last is not None and duration(mp4) >= last - 1e-6:
                problems = [p for p in problems if p not in ending_errors]
                info.append("ending energy reaches the tail; the whole last word is retained (SHORT-3, listen)")
        problems += title_problems(proj)
        p, total = freezes_in_mp4(mp4, short, fps)
        problems += p
        info.append(f"duplicate frames in face/split windows: {total}")
        faces = shortinfo.load(proj / "assets" / "faces.json") or {}
        track = shortinfo.load(proj / "assets" / "track.json") or {}
        frames_fps = faces.get("fps") or track.get("fps")
        src = Path(cut.get("source") or "")
        src = src if src.is_absolute() else shortinfo.ROOT / src
        p, w = guards.fps_problems(source_fps(src) if src.is_file() else None, frames_fps, fps)
        problems += p
        warns += [w] if w else []
        if track.get("cx"):
            tr = shortinfo.load(proj / "transcript.json") or {}
            seams = list(track.get("joins") or []) + [round(t * fps) for t in (tr.get("tightened") or {}).get("cuts_at_s", [])]
            problems += guards.track_jumps(track["cx"], (short.get("faces") or []) + (short.get("splits") or []), fps, seams=seams)
        p, sheet = cut_strips(proj, mp4, version, short, fps, allow)  # SHORT-10 is a shorts rule
        problems += p
        if sheet:
            info.append(f"cut strips -> {sheet}")
    info += notes(proj, mp4, version)
    return problems, warns, info
