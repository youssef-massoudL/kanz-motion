"""Listen to every cut of a cut-out short: is the word at each edge still the word he said? (ship check, 2026-10-26)

    python engine/joincheck.py <project>                       # every edge of transcript.json cut_from
    python engine/joincheck.py <project> --voice <other.wav>   # the same edges on another voice file
    python engine/joincheck.py listen <source> <t> [<t> ...]   # what is said just before and just after each second

The leak and ending checks read numbers (word edges, measured gaps); they passed reels 7-12 while «الفهم» was heard as
«الفيديو» and «الأمل» as «الامر». This check transcribes the source around each edge (the reference: the uncut words)
and the short's voice.wav around the same cut (what the viewer hears), with local faster-whisper, and compares the
word on each side of the cut: a different word, or the same word heard with low confidence, fails. Both sides go
through the same short-window recognition, so Whisper's own slips mostly cancel out. Results -> out/joins.json.
"""
import argparse
import json
import re
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np

SR = 16000
MODEL = "turbo"
BEFORE, AFTER = 2.5, 2.0   # s of context each side of a cut
SAME = 0.8                 # normalised similarity at or above which two words are the same word
LOW_P = 0.5                # an edge word heard below this probability fails even when it reads the same
DROP_P = 0.2               # ... or heard this much less surely than in the uncut source
STRADDLE = 0.08            # s a source word may reach across the cut (word times) before the cut is inside it
_model = None


def model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(MODEL, device="cpu", compute_type="int8")
    return _model


def pcm(path, t0, dur):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t0):.3f}", "-i", str(path), "-t", f"{dur:.3f}", "-vn",
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def heard(path, t0, t1):
    """[(word, start, end, probability)] recognised in path between t0 and t1 (absolute seconds)."""
    t0 = max(0.0, t0)
    a = pcm(path, t0, t1 - t0)
    if len(a) < SR * 0.3:
        return []
    segs, _ = model().transcribe(a, language="ar", word_timestamps=True, beam_size=5, vad_filter=False,
                                 condition_on_previous_text=False)
    return [(w.word.strip(), round(float(t0 + w.start), 2), round(float(t0 + w.end), 2), round(float(w.probability), 2))
            for s in segs for w in (s.words or []) if w.word.strip()]


def norm(w):
    w = re.sub(r"[ً-ْـ.,،؟?!:؛«»\"']", "", w)
    # Egyptian ق is a glottal stop: Whisper writes «قمار» in one window and «أمار» in the next
    return w.translate(str.maketrans("أإآىةق", "ااايها"))


def same(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def side(words, t, before, n=3):
    """The n words nearest the cut at t, on one side, nearest first (by each word's middle)."""
    ws = [w for w in words if ((w[1] + w[2]) / 2 < t) == before]
    return (ws[::-1] if before else ws)[:n]


def edges(tr):
    """Each cut: (label, source second, short second, side) where side is 'end' (words before it) or 'start'."""
    rs = tr["cut_from"]["ranges"]
    out = []
    for k, r in enumerate(rs):
        o = r["out_start"]
        out.append((f"range {k} start", r["start"], o, "start"))
        out.append((f"range {k} end", r["end"], r.get("out_end", o + r["end"] - r["start"]), "end"))  # tightened: out_end
    return out


def straddling(words, t, src=None):
    """The source word the cut at t falls inside, if any. A cut inside a measured gap (pauses.find_gaps) is never inside
    a word, whatever the word times say (Whisper word ends run up to 0.2 s late)."""
    w = next((w for w in words if w[1] < t - STRADDLE and w[2] > t + STRADDLE), None)
    if w and src is not None:
        import pauses
        # any true silence at the cut counts (30 ms, 18 dB under his voice): footage.py cuts in shorter, shallower
        # dips only with --min-gap/--below after listening, and the words each side are still compared below
        if any(a - 0.01 <= t <= b + 0.01 for a, b, _ in pauses.find_gaps(src, t - 0.3, t + 0.3, min_len=0.03, below=18)):
            return None
    return w


def compare(ref, got, inside=None):
    """(ok, line): the cut is not inside a source word, and the reference's edge word is among the words heard nearest
    the cut (word times in a short window are only good to ~0.2 s), reads the same and is heard with confidence."""
    if inside:
        return False, f"the cut falls inside «{inside[0]}» ({inside[1]:.2f}-{inside[2]:.2f} in the source)"
    if not ref:
        return True, "reference heard nothing here (skipped)"
    if not got:
        return False, f"expected «{ref[0][0]}», heard nothing"
    r = ref[0]
    g = max(got, key=lambda w: (same(r[0], w[0]), w[3]))
    s = same(r[0], g[0])
    ok = s >= SAME and g[3] >= LOW_P and g[3] >= r[3] - DROP_P
    why = "" if ok else (f" (similarity {s:.2f})" if s < SAME else f" (heard with p {g[3]:.2f}, source p {r[3]:.2f})")
    return ok, f"expected «{r[0]}» (p {r[3]:.2f}), heard «{' '.join(f'{w[0]}' for w in got)}» (p {g[3]:.2f}){why}"


def check(proj, voice=None):
    """(problems, warnings, lines) for every cut of the short; writes out/joins.json."""
    proj = Path(proj)
    tr = json.loads((proj / "transcript.json").read_text(encoding="utf-8"))
    cut = tr.get("cut_from") or {}
    if not cut.get("ranges"):
        return [], [], []
    src = Path(cut.get("source") or "")
    if not src.is_absolute():
        src = Path(__file__).resolve().parent.parent / src
    voice = Path(voice) if voice else proj / "audio" / "voice.wav"
    if not src.is_file() or not voice.is_file():
        return [], [f"join check skipped: {'source ' + str(src) if not src.is_file() else str(voice)} not found; "
                    "listen to every cut"], []
    problems, lines, report = [], [], []
    for label, s_src, s_out, kind in edges(tr):
        before = kind == "end"
        # each side is recognised on its own: in a shared window Whisper moves words across the cut. The shared
        # window on the source only answers "is the cut inside a word?"
        if before:
            ref, got = heard(src, s_src - BEFORE, s_src)[-1:], heard(voice, s_out - BEFORE, s_out)[::-1][:3]
        else:
            ref, got = heard(src, s_src, s_src + AFTER)[:1], heard(voice, s_out, s_out + AFTER)[:3]
        ok, line = compare(ref, got, straddling(heard(src, s_src - BEFORE, s_src + AFTER), s_src, src))
        lines.append(f"  {'ok  ' if ok else 'FAIL'} {label} (short {s_out:.2f} s, source {s_src:.2f} s): {line}")
        report.append({"edge": label, "short_s": round(s_out, 2), "source_s": s_src, "ok": ok, "ref": ref, "heard": got})
        if not ok:
            problems.append(f"join: {label} at {s_out:.2f} s: {line} (SHORT-3/13: cut in a real gap, listen)")
    (proj / "out").mkdir(exist_ok=True)
    (proj / "out" / "joins.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return problems, [], lines


def listen(src, times):
    """Each side transcribed on its own (a shared window lets Whisper move a word across the cut)."""
    for t in times:
        b = heard(src, t - BEFORE, t)[-3:]
        a = heard(src, t, t + AFTER)[:3]
        print(f"{t:9.2f}: ...{' '.join(w[0] for w in b)} | {' '.join(w[0] for w in a)}...")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "listen":
        listen(sys.argv[2], [float(t) for t in sys.argv[3:]])
        return
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("project")
    ap.add_argument("--voice")
    a = ap.parse_args()
    problems, warns, lines = check(a.project, a.voice)
    print("\n".join(lines + ["WARNING: " + w for w in warns]))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    from console import utf8
    utf8()
    main()
