"""Measured pauses for footage cuts: where the voice really stops and starts (editor preset, 2026-10-23).

    python engine/pauses.py levels <source.mp4> <start> <end>          # dB RMS in 50 ms steps, with a bar
    python engine/pauses.py quiet <source.mp4> <t> [<t> ...]           # quiet runs >= 80 ms within +-1.2 s of each t
    python engine/pauses.py gaps <source.mp4> <start> <end>            # real gaps footage.py can cut in, with words
    python engine/pauses.py fix <project> <range> <last_end> <next_start> [<range> <last_end> <next_start> ...]

Local Whisper (no ElevenLabs key) glues words in fast speech and its word times run up to 0.2 s late, so cuts placed
on Whisper edges clip words. footage.py now snaps every cut into a real gap (`find_gaps`: a run of 75 ms or more at
least 22 dB under the speaker's level) and refuses an edge with none; `gaps` lists the candidates with their words.
`quiet` (12% of the loud level) also finds quiet consonants (final م, ف, س, stop closures) inside running speech:
do not cut there. `fix` is kept for old projects only: writing guessed edges into transcript.json makes the ship leak
check verify its own input (reels 7-12, 2026-10-26: «الفهم» heard as «الفيديو» and still "passed"); the ship join
check (engine/joincheck.py) listens to every join instead.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 16000


def pcm(src, t0, dur):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t0):.3f}", "-i", str(src), "-t", f"{dur:.3f}", "-vn",
                          "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def levels(src, t0, t1):
    a, hop = pcm(src, t0, t1 - t0), SR // 20
    for i in range(0, len(a) - hop + 1, hop):
        db = 20 * np.log10(np.sqrt(np.mean(a[i:i + hop] ** 2)) + 1e-9)
        print(f"{t0 + i / SR:9.2f}  {db:6.1f} dB  " + "#" * max(0, int((db + 60) / 2)))


def quiet(src, times):
    """Quiet runs (10 ms frames below 12% of the window's loud level, 80 ms or more) near each time, and the nearest."""
    for t in times:
        t0 = max(0.0, t - 1.2)
        a, hop = pcm(src, t0, 2.4), SR // 100
        rms = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a) - hop, hop)])
        low = rms < 0.12 * np.percentile(rms, 90)
        runs, start = [], None
        for i, q in enumerate(list(low) + [False]):
            if q and start is None:
                start = i
            elif not q and start is not None:
                if i - start >= 8:
                    runs.append((t0 + start / 100, t0 + i / 100))
                start = None
        best = min(runs, key=lambda r: abs((r[0] + r[1]) / 2 - t)) if runs else None
        shown = "  ".join(f"{a:.2f}-{b:.2f}" for a, b in runs) or "none"
        print(f"{t:9.2f}: quiet {shown}" + (f"   -> nearest {best[0]:.2f}-{best[1]:.2f}" if best else ""))


MIN_GAP = 0.075   # s, the shortest run footage.py may cut in (it cuts at least 25 ms after the voice, 50 ms before it)
BELOW = 22.0      # dB under the speaker's level (70th percentile of 10 ms frames around the window)


def find_gaps(src, t0, t1, min_len=MIN_GAP, below=BELOW, ref=3.0):
    """Real gaps between t0 and t1 (source seconds) as [(start, end, min_db)]: runs of 10 ms frames at least `below` dB
    under the speaker's level, `min_len` or longer. The level comes from +-`ref` s around the window so a quiet stretch
    does not lower its own bar. A run touching the window's edge is extended past it, so its true start/end is kept."""
    lo = max(0.0, t0 - ref)
    a, hop = pcm(src, lo, t1 + ref - lo), SR // 100
    n = len(a) // hop
    if not n:
        return []
    db = 20 * np.log10(np.sqrt((a[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    voiced = db[db > -90]
    level = np.percentile(voiced, 70) if len(voiced) else -20.0
    low = list(db < level - below) + [False]
    out, start = [], None
    for i, q in enumerate(low):
        if q and start is None:
            start = i
        elif not q and start is not None:
            s, e = lo + start / 100, lo + i / 100
            if i - start >= round(min_len * 100) and e > t0 and s < t1:
                out.append((round(s, 2), round(e, 2), round(float(db[start:i].min()), 1)))
            start = None
    return out


def gaps(src, t0, t1, words=None):
    for s, e, m in find_gaps(src, t0, t1):
        ctx = ""
        if words:
            before = [w["w"] for w in words if w["end"] <= s + 0.3][-4:]
            after = [w["w"] for w in words if w["start"] >= e - 0.3][:4]
            ctx = f"  ...{' '.join(before)} | {' '.join(after)}..."
        print(f"{s:9.2f}-{e:9.2f}  {round((e - s) * 1000):5d} ms  min {m:6.1f} dB{ctx}")


def fix(proj, triples):
    p = Path(proj) / "transcript.json"
    tr = json.loads(p.read_text(encoding="utf-8"))
    cut = tr["cut_from"]
    cut.setdefault("whisper_ranges", json.loads(json.dumps(cut["ranges"])))
    for i, last, nxt in triples:
        r = cut["ranges"][int(i)]
        r["last_word_end"], r["next_word_start"] = float(last), float(nxt)
        print(f"range {i}: last word end {last}, next word start {nxt} (was {cut['whisper_ranges'][int(i)]['next_word_start']})")
    cut["boundary_fix"] = "last_word_end / next_word_start measured on the source audio (engine/pauses.py)"
    p.write_text(json.dumps(tr, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    lv = sub.add_parser("levels")
    lv.add_argument("source")
    lv.add_argument("start", type=float)
    lv.add_argument("end", type=float)
    gp = sub.add_parser("gaps")
    gp.add_argument("source")
    gp.add_argument("start", type=float)
    gp.add_argument("end", type=float)
    gp.add_argument("--transcript", help="transcript.raw.json, to show the words around each gap")
    qt = sub.add_parser("quiet")
    qt.add_argument("source")
    qt.add_argument("times", type=float, nargs="+")
    fx = sub.add_parser("fix")
    fx.add_argument("project")
    fx.add_argument("values", nargs="+", help="<range> <last_end> <next_start>, repeated")
    a = ap.parse_args()
    if a.cmd == "levels":
        levels(a.source, a.start, a.end)
    elif a.cmd == "gaps":
        words = None
        if a.transcript:
            tr = json.loads(Path(a.transcript).read_text(encoding="utf-8"))
            words = sorted((w for s in tr["segments"] for w in s["words"]), key=lambda w: w["start"])
        gaps(a.source, a.start, a.end, words)
    elif a.cmd == "quiet":
        quiet(a.source, a.times)
    else:
        if len(a.values) % 3:
            sys.exit("fix takes <range> <last_end> <next_start> triples")
        fix(a.project, [a.values[i:i + 3] for i in range(0, len(a.values), 3)])


if __name__ == "__main__":
    from console import utf8
    utf8()
    main()
