"""Snapped footage cuts (2026-10-26): every edge sits in a measured gap, the fade never touches a word."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))
import footage  # noqa: E402
import guards  # noqa: E402
import joincheck  # noqa: E402


def W(w, s, e):
    return {"w": w, "start": s, "end": e}


# Whisper glues the words and runs late: "b" really ends at 2.0 (the gap 2.0-2.3), Whisper says 2.15
WORDS = [W("a", 1.0, 1.5), W("b", 1.5, 2.15), W("c", 2.15, 2.8), W("d", 5.0, 5.5), W("e", 5.5, 6.0)]


def test_snapped_edges_sit_in_the_gaps_and_clamp_the_words():
    segs = footage.plan_segments(WORDS, [(1.0, 2.1), (5.0, 6.0)],
                                 snaps=[((0.8, 0.98), (2.0, 2.3)), ((4.85, 4.98), (6.0, 7.0))])
    a, b = segs
    assert a["src_start"] == pytest.approx(0.92)            # 0.06 s of gap before the voice
    assert a["last_word_end"] == 2.0 and a["next_word_start"] == 2.3
    assert a["src_end"] == pytest.approx(2.15)              # 0.15 s join tail, 0.15 s before the next voice
    assert [w["w"] for w in a["words"]] == ["a", "b"] and a["words"][-1]["end"] == 2.0
    assert b["next_word_start"] is None and b["src_end"] == pytest.approx(6.0 + footage.TAIL)
    pause = (a["src_end"] - a["last_word_end"]) + b["lead"] + (b["voice_start"] - b["src_start"])
    assert pause == pytest.approx(footage.JOIN)             # the join stays 0.25 s of quiet
    assert guards.leak_checks({"ranges": [{"start": g["src_start"], "end": g["src_end"], "last_word_end": g["last_word_end"],
                                           "next_word_start": g["next_word_start"]} for g in segs]}) == ([], [])


def test_snapped_fade_starts_where_the_voice_stops(monkeypatch):
    monkeypatch.setattr(footage, "decode", lambda src, t0, dur: np.ones((int(round(dur * footage.SR)), 2), np.float32))
    g, = footage.plan_segments([W("a", 1.0, 1.9)], [(1.0, 2.0)], snaps=[((0.8, 0.98), (2.0, 2.3))], tail=0.15)
    a = footage.voice_audio("x", [g])
    at = lambda t: a[int(round((t - g["src_start"]) * footage.SR)), 0]  # noqa: E731
    assert at(1.99) == 1.0                                  # the word is untouched up to the measured edge
    assert at(2.1) < 1.0 and abs(a[-1, 0]) < 0.01           # faded inside the gap


def test_an_edge_without_a_gap_stops_the_cut(monkeypatch):
    import pauses
    monkeypatch.setattr(pauses, "find_gaps", lambda src, t0, t1, **k: [(t0 + 2.9, t0 + 2.98, -45.0)] if t1 - t0 > 3 else [])
    with pytest.raises(footage.CutError, match="no real gap"):
        footage.snap_ranges("x.mp4", [(1.0, 2.0)])


def test_join_compare_fails_a_changed_or_unsure_word():
    ref = [("الفهم", 1.0, 1.4, 0.9)]
    assert joincheck.compare(ref, [("الفهم", 1.0, 1.4, 0.88), ("عن", 0.8, 1.0, 0.9)])[0]
    assert not joincheck.compare(ref, [("الفيديو", 1.0, 1.4, 0.45)])[0]
    assert not joincheck.compare([("الأمل", 1.0, 1.4, 0.89)], [("الامل", 1.0, 1.4, 0.6)])[0]   # heard far less surely
    assert not joincheck.compare(ref, [], None)[0]
    assert not joincheck.compare(ref, ref, ("تخش", 0.5, 1.2, 0.9))[0]                       # the cut is inside a word
