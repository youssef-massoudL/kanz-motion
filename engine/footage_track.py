"""Cut a short from a long 16:9 Kanz live with the camera TRACKING the speaker: a drop-in next to engine/footage.py.

    python engine/footage_track.py <project_dir> <source.mp4> <transcript.raw.json> <start> <end> [--also S E ...]
        [--video-from S] [--zoom Z] [--half-h PX] [--face-y F] [--fps 24] [--no-half] [--no-tighten] [--tail 0.4]

Same arguments and the same outputs as footage.py (voice.wav, transcript.json, assets/face/000001.jpg...), plus the
half-frame set the split layout needs:

  assets/face/   1080x1920  tracked 9:16 crop, for K.footage (full-screen face windows)
  assets/half/   1080x960   tracked crop that fits one half of the split (runtime/kanz-split.js, K.split)
  assets/track.json         the smoothed camera path (per frame centre x/y in source pixels) for review
  assets/track-check.jpg    8 source frames with both crop rectangles drawn: look at it before using the frames

How it tracks (Ahmed 2026-10-17: the camera follows him, he moves around the 16:9 frame): the face is detected at 4 fps
(OpenCV Haar, frontal + profile; outliers dropped, gaps interpolated), then the path goes through a dead-zone follower
(the crop only moves once he leaves the middle of it, like a camera operator) and a wide Gaussian (sigma 0.7 s), and
every frame is resampled with sub-pixel warpAffine, so the crop glides and never steps or jitters. Both outputs use the
one path, so the full-screen face and the split half stay in sync.

  --zoom     9:16 crop zoom (1 = full source height; 1.2 = tighter). Default 1.
  --half-h   source pixels of height in the split half (the half is 9:8, so width is 1.125x). Default 560 (face ~400 px
             wide on screen). Smaller = tighter on the face.
  --face-y   where the face sits in the half, 0 = top, 1 = bottom (default 0.42)
  --video-from  as footage.py: the first clean source second; the first clean frame is held until then.
  --also, --tail, --join, --exact-end   as footage.py: the ending guard (last word + 0.4 s, stopped before the next
             source word, never into the last word) and joined ranges with about 0.25 s of silence in all at each join
             (SHORT-13); the camera path restarts at a join.
  --no-tighten  workshop shorts run engine/tighten_footage.py by default (dead air: gaps over 0.42 s are trimmed to
             0.30 s, frame-rounded); this keeps every pause.
Then engine/faces.py writes assets/faces.json (eyes-and-mouth boxes) and assets/freezes.json. track.json also keeps
"diff", the per-frame change of the source picture inside the crop, so a stalled stream is found although the crop glides.
(No --tv-until: the TV-set opening is a fixed wide shot, use footage.py for that.)
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

from footage import (CutError, add_range_args, plan_from_args, report, short_duration, voice_audio,
                     write_transcript, write_wav)

SW, SH = 1280, 720  # live-source frame size; read from the file below, these are only the fallback


def probe(src):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", src], capture_output=True, text=True, check=True).stdout.strip().split(",")
    return int(r[0]), int(r[1])


def frames(src, t0, dur, fps, w, h):
    """Yield BGR frames t0..t0+dur at fps via a rawvideo pipe (never a folder of temp JPEGs)."""
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", src, "-vf", f"fps={fps}",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    size = w * h * 3
    try:
        while True:
            b = p.stdout.read(size)
            if len(b) < size:
                break
            yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
    finally:  # also when the caller stops early: no "broken pipe" noise from ffmpeg
        p.kill()
        p.stdout.close()
        p.wait()


_CASC = {}


def detect(img):
    """Largest face centre (x, y, size) in the image, or None. Frontal first, then profile (head turned)."""
    if not _CASC:
        base = cv2.data.haarcascades
        _CASC["f"] = [cv2.CascadeClassifier(base + n) for n in ("haarcascade_frontalface_default.xml", "haarcascade_frontalface_alt2.xml")]
        _CASC["p"] = cv2.CascadeClassifier(base + "haarcascade_profileface.xml")
    g = cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    hits = []
    for c in _CASC["f"]:
        hits = c.detectMultiScale(g, 1.1, 5, minSize=(70, 70))
        if len(hits):
            break
    if not len(hits):
        hits = _CASC["p"].detectMultiScale(g, 1.1, 5, minSize=(70, 70))
        if not len(hits):
            hits = [(img.shape[1] - x - w, y, w, h) for x, y, w, h in _CASC["p"].detectMultiScale(g[:, ::-1], 1.1, 5, minSize=(70, 70))]
    if not len(hits):
        return None
    x, y, w, h = max(hits, key=lambda r: r[2] * r[3])
    return x + w / 2, y + h / 2, float(w)


def gauss(v, sigma_samples):
    if sigma_samples < 0.5:
        return v
    r = int(sigma_samples * 3)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_samples) ** 2)
    k /= k.sum()
    return np.convolve(np.pad(v, r, mode="edge"), k, mode="valid")


def deadzone(v, db):
    """Follower that holds still while the target stays within +-db of it, and only trails the target past that."""
    out = np.empty_like(v)
    c = v[0]
    for i, x in enumerate(v):
        if x - c > db:
            c = x - db
        elif c - x > db:
            c = x + db
        out[i] = c
    return out


def clean(series, thresh):
    """Drop outliers against a running median, then fill gaps linearly; returns None when nothing was detected."""
    a = np.array([np.nan if s is None else s for s in series], float)
    ok = ~np.isnan(a)
    if ok.sum() < 3:
        return None
    med = np.array([np.nanmedian(a[max(0, i - 4):i + 5]) for i in range(len(a))])
    raw = a.copy()
    a[np.abs(a - med) > thresh] = np.nan
    ok = ~np.isnan(a)
    if not ok.any():  # a short range with a few far-apart detections: every one looked like an outlier, keep them
        a, ok = raw, ~np.isnan(raw)
    return np.interp(np.arange(len(a)), np.flatnonzero(ok), a[ok])


def track(src, t0, dur, w, h, tfps=4):
    """Smoothed per-sample (cx, cy, face size) at the track rate, as lists; falls back to the frame centre."""
    pts = [detect(f) for f in frames(src, t0, dur, tfps, w, h)]
    n = len(pts)
    found = sum(p is not None for p in pts)
    print(f"tracking: face found in {found}/{n} samples ({found / max(n, 1):.0%})")
    cols = [clean([None if p is None else p[i] for p in pts], t) for i, t in ((0, 90), (1, 60), (2, 60))]
    if cols[0] is None:
        print("WARNING: no face detected, the crop stays centred", file=sys.stderr)
        return np.full(n, w / 2), np.full(n, h / 2), np.full(n, 230.0), n and found / n
    return cols[0], cols[1], cols[2], found / max(n, 1)


def warp(img, cx, cy, cw, ch, ow, oh):
    """Crop a cw x ch window centred on (cx, cy) (sub-pixel, may be fractional) into an ow x oh image."""
    s = ow / cw
    m = np.float32([[s, 0, -(cx - cw / 2) * s], [0, s, -(cy - ch / 2) * s]])
    return cv2.warpAffine(img, m, (ow, oh), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)


def main():
    ap = argparse.ArgumentParser()
    add_range_args(ap)
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--half-h", type=float, default=560)
    ap.add_argument("--face-y", type=float, default=0.42)
    ap.add_argument("--no-half", action="store_true")
    ap.add_argument("--no-tighten", action="store_true")
    ap.add_argument("--no-analyse", action="store_true")
    a = ap.parse_args()
    proj = Path(a.project)
    face, half = proj / "assets" / "face", proj / "assets" / "half"
    for d in (face,) + (() if a.no_half else (half,)):
        d.mkdir(parents=True, exist_ok=True)
        for f in d.glob("*.jpg"):
            f.unlink()
    for old in ("face_full", "half_full"):  # a fresh cut: tighten_footage must start from these new frames
        shutil.rmtree(proj / "assets" / old, ignore_errors=True)
    (proj / "audio").mkdir(exist_ok=True)
    tr = json.loads(Path(a.transcript).read_text(encoding="utf-8"))
    try:
        segs = plan_from_args(a, tr)
    except CutError as err:
        raise SystemExit(str(err))
    report(segs)
    w, h = probe(a.source)
    ch9 = h / a.zoom
    cw9 = ch9 * 9 / 16
    hh = a.half_h
    hw = hh * 1080 / 960
    tfps = 4
    n, hold_total, rates, joins = 0, 0, [], []
    X9a, Y9a, diffs, check = [], [], [], []
    total = int(round(short_duration(segs) * a.fps))
    marks = {int(i) for i in np.linspace(0, total - 1, 8)}
    for k, g in enumerate(segs):
        s, e = g["src_start"] - g["lead"], g["src_end"]   # a join pause shows the next range's own lead-in frames
        v0 = max(s, a.video_from or s) if k == 0 else s
        hold = int(round((v0 - s) * a.fps))
        if k == 0:
            hold_total = hold
        else:
            joins.append(n)
        nf = max(1, int(round((g["out_start"] + e - g["src_start"]) * a.fps)) - n - hold)

        # ---- camera path (it restarts at a join: the picture cuts there) --------------------------------------------
        cx_s, cy_s, fs_s, rate = track(a.source, v0, e - v0, w, h, tfps)
        rates.append(rate)
        tt = np.arange(nf) / a.fps
        ts = np.arange(len(cx_s)) / tfps
        cx = np.interp(tt, ts, cx_s)
        cy = np.interp(tt, ts, cy_s)
        cx = gauss(deadzone(cx, 35), 0.7 * a.fps)          # glide: wait until he leaves the middle, then trail him smoothly
        cy = gauss(deadzone(cy, 50), 1.2 * a.fps)          # vertical moves are rare and slower
        x9 = np.clip(cx, cw9 / 2, w - cw9 / 2)
        y9 = np.clip(cy if a.zoom > 1 else np.full(nf, h / 2), ch9 / 2, h - ch9 / 2)
        xh = np.clip(cx, hw / 2, w - hw / 2)
        yh = np.clip(cy + (0.5 - a.face_y) * hh, hh / 2, h - hh / 2)
        pad = lambda v: np.concatenate([np.full(hold, v[0]), v])  # the first clean frame repeats while the clip opens
        X9, Y9, XH, YH = pad(x9), pad(y9), pad(xh), pad(yh)

        # ---- frames ------------------------------------------------------------------------------------------------
        gen = frames(a.source, v0, e - v0 + 0.5, a.fps, w, h)
        first = next(gen) if hold else None
        last = prev = None
        for i in range(hold + nf):
            img = first if i < hold else next(gen, None)
            if img is None:  # source ended a frame early: hold the last
                img = last
            last = img
            cv2.imwrite(str(face / f"{n + 1:06d}.jpg"), warp(img, X9[i], Y9[i], cw9, ch9, 1080, 1920), [cv2.IMWRITE_JPEG_QUALITY, 92])
            if not a.no_half:
                cv2.imwrite(str(half / f"{n + 1:06d}.jpg"), warp(img, XH[i], YH[i], hw, hh, 1080, 960), [cv2.IMWRITE_JPEG_QUALITY, 92])
            # change of the source picture inside this frame's 9:16 crop, both frames cut the same way, so a repeated
            # source frame reads 0 even while the crop glides (engine/faces.py turns runs of these into freezes)
            x0, x1 = int(max(0, X9[i] - cw9 / 2)), int(min(w, X9[i] + cw9 / 2))
            y0, y1 = int(max(0, Y9[i] - ch9 / 2)), int(min(h, Y9[i] + ch9 / 2))
            small = lambda im: cv2.resize(cv2.cvtColor(im[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY), (135, 240),
                                          interpolation=cv2.INTER_AREA).astype(np.float32)
            diffs.append(255.0 if prev is None else round(float(np.abs(small(img) - small(prev)).mean()), 3))
            prev = img
            if n in marks:
                im = img.copy()
                cv2.rectangle(im, (int(X9[i] - cw9 / 2), int(Y9[i] - ch9 / 2)), (int(X9[i] + cw9 / 2), int(Y9[i] + ch9 / 2)), (60, 200, 255), 3)
                cv2.rectangle(im, (int(XH[i] - hw / 2), int(YH[i] - hh / 2)), (int(XH[i] + hw / 2), int(YH[i] + hh / 2)), (255, 120, 220), 3)
                check.append(cv2.resize(im, (480, 270)))
            n += 1
        gen.close()
        X9a += [float(v) for v in X9]
        Y9a += [float(v) for v in Y9]
    rows = [np.hstack(check[j:j + 4]) for j in range(0, len(check) - len(check) % 4, 4)]
    if rows:
        cv2.imwrite(str(proj / "assets" / "track-check.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    steps = [abs(b - c) for j, (c, b) in enumerate(zip(X9a, X9a[1:])) if j + 1 not in joins] or [0.0]
    rate = float(np.mean(rates)) if rates else 0
    (proj / "assets" / "track.json").write_text(json.dumps({
        "source": a.source, "fps": a.fps, "hold_frames": hold_total, "detected_share": round(rate, 3), "zoom": a.zoom,
        "half_h": hh, "crop9_w": round(cw9, 1), "joins": joins, "cx": [round(v, 2) for v in X9a],
        "cy": [round(v, 2) for v in Y9a], "diff": diffs}), encoding="utf-8")
    print(f"camera: max step {max(steps):.2f} px/frame (crop {cw9:.0f} px wide; < 3 px steps glide, a visible jitter is > 6)")

    # ---- audio and words: shared with footage.py ------------------------------------------------------------------
    write_wav(voice_audio(a.source, segs, a.exact_end), proj / "audio" / "voice.wav")
    write_transcript(proj, tr, a.source, segs, max(a.start, a.video_from or a.start))
    print(f"{n} frames ({n / a.fps:.2f} s), voice {short_duration(segs):.2f} s, {sum(len(g['words']) for g in segs)} words -> {proj}"
          + ("" if a.no_half else f" (assets/face {n}, assets/half {n})"))
    if not a.no_tighten:  # workshop shorts: dead air out by default (Ahmed 2026-10-17; default since 2026-10-18)
        import tighten_footage
        tighten_footage.tighten(proj, analyse=not a.no_analyse, fps=a.fps)
    elif not a.no_analyse:
        import faces
        faces.analyse(proj, fps=a.fps, kind="live", source=a.source)


if __name__ == "__main__":
    from console import utf8
    utf8()
    main()
