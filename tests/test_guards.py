"""Review hardening (2026-10-18): each recurring review note has a check that fails. No browser, no API."""
import json
import shutil
import subprocess

import numpy as np
import pytest

import faces
import footage
import guards
import lint
import make
import shortinfo

W = lambda w, s, e: {"w": w, "start": s, "end": e}  # noqa: E731


# ---------- P0-1 ending guard ----------

def test_ending_guard_adds_tail_and_stops_before_the_next_word():
    words = [W("a", 1.0, 1.4), W("b", 1.5, 2.0), W("c", 2.2, 2.6), W("next", 3.5, 3.9)]
    g, = footage.plan_segments(words, [(1.0, 2.0)])
    assert g["last_word_end"] == 2.0 and g["src_end"] == pytest.approx(2.15)  # clamped 0.05 s before "c"
    assert g["clamped"] and g["next_word_start"] == 2.2
    g, = footage.plan_segments(words, [(1.0, 2.6)])
    assert g["src_end"] == pytest.approx(3.0) and not g["clamped"]           # the full 0.4 s tail
    g, = footage.plan_segments(words, [(1.0, 2.5)])                           # an end inside "c" leaves "c" out
    assert g["last_word_end"] == 2.0
    g, = footage.plan_segments(words, [(1.0, 2.33)], exact=True)
    assert g["src_end"] == 2.33


def test_joined_ranges_open_a_pause_and_shift_words():
    words = [W("a", 1.0, 1.4), W("b", 5.0, 5.4), W("c", 5.5, 5.9), W("d", 9.0, 9.4)]
    s = footage.plan_segments(words, [(1.0, 1.4), (5.0, 5.9)])
    assert s[0]["lead"] == 0
    previous_word = s[0]["out_start"] + s[0]["last_word_end"] - s[0]["src_start"]
    next_word = s[1]["out_start"] + words[1]["start"] - s[1]["src_start"]
    assert next_word - previous_word == pytest.approx(footage.JOIN)  # tail + lead together make the join pause
    assert s[1]["out_start"] == pytest.approx(.4 + footage.JOIN)
    assert footage.short_duration(s) == pytest.approx(.4 + footage.JOIN + 1.3)


def test_voice_fade_sits_inside_the_tail(monkeypatch):
    monkeypatch.setattr(footage, "decode", lambda src, t0, dur: np.ones((int(round(dur * footage.SR)), 2), np.float32))
    g, = footage.plan_segments([W("a", 0.0, 1.0)], [(0.0, 1.0)])
    a = footage.voice_audio("x", [g])
    assert a[int(0.99 * footage.SR), 0] == 1.0          # the word itself is untouched
    assert a[-1, 0] < 0.01                               # silent at the very end
    assert len(a) == int(round(1.4 * footage.SR))


def test_ship_ending_and_leak_checks():
    sr = 8000
    rng = np.random.default_rng(1)
    room = rng.normal(0, 0.001, sr * 3)
    cut = room.copy()
    cut[-int(0.1 * sr):] += rng.normal(0, 0.3, int(0.1 * sr))    # a word still sounding at the end
    assert guards.ending_problems(cut, sr)
    ok = room.copy()
    ok[sr:2 * sr] += rng.normal(0, 0.3, sr)
    assert not guards.ending_problems(ok, sr)
    assert guards.leak_problems({"ranges": [{"start": 0, "end": 3.0, "last_word_end": 2.6, "next_word_start": 2.9}]})
    assert not guards.leak_problems({"ranges": [{"start": 0, "end": 2.85, "last_word_end": 2.6, "next_word_start": 2.9}]})


def test_end_cut_finding():
    assert guards.end_cut_findings(11.5, 11.9, {"ranges": []})
    assert not guards.end_cut_findings(11.9, 11.9, {"ranges": []})
    assert not guards.end_cut_findings(10, 11.9, None)


# ---------- P0-2 face-aware text ----------

def test_fill_boxes_interpolates_and_drops_outliers():
    s = [[100, 100, 300, 300], None, [120, 100, 320, 300], [900, 100, 1000, 140], [140, 100, 340, 300]]
    b = faces.fill_boxes(s, 30, every=6, fps=24)
    assert b[0] == [100, 100, 300, 300] and b[3] == [105, 100, 305, 300]   # a quarter of the way from frame 0 to 12
    assert b[18][0] < 200                                                  # the far-off hit at frame 18 was dropped
    assert faces.fill_boxes([None, None], 12) == [None] * 12


def test_on_face_flags_title_and_captions_not_world_text():
    face = [400, 500, 700, 800]
    frame = {"items": [dict(id=1, kind="title", txt="t", x0=300, x1=800, y0=520, y1=640),
                       dict(id=2, kind="caption", txt="c", x0=300, x1=800, y0=1300, y1=1400),
                       dict(id=3, kind="text", txt="w", x0=400, x1=700, y0=600, y1=700, over_face=False)]}
    hits = guards.on_face_findings(1.0, frame, face)
    assert [h["id"] for h in hits] == [1]
    assert not guards.on_face_findings(1.0, frame, None)


def test_title_text_comes_from_the_pick():
    assert shortinfo.title_text({"options": ["a", "b", "c"], "pick": 2}) == "b"
    assert shortinfo.title_text({"options": ["a", "b"]}) == "a"
    assert shortinfo.title_text({"options": ["a"], "pick": 0, "text": "mine"}) == "mine"
    titles = {"reels": {"x": {"slug": "short-x", "options": ["a"], "pick": 1}}}
    assert shortinfo.title_entry("short-x", titles)[0] == "x"


def test_short_without_title_is_a_finding():
    kinds = [f["kind"] for f in lint.static_scene_findings('K.footage({}); K.finish();')]
    assert "title" in kinds
    assert "title" not in [f["kind"] for f in lint.static_scene_findings('K.footage({}); K.title(); K.finish();')]


def test_ship_title_must_match_the_pick(tmp_path, monkeypatch):
    import shipcheck
    proj = tmp_path / "short-x"
    proj.mkdir()
    monkeypatch.setattr(shortinfo, "TITLES", tmp_path / "_titles.json")
    (tmp_path / "_titles.json").write_text(json.dumps({"reels": {"x": {"slug": "short-x", "options": ["أ", "ب"], "pick": 2}}}),
                                           encoding="utf-8")
    (proj / "scene.js").write_text('K.footage({}); K.title("أ"); K.finish();', encoding="utf-8")
    assert shipcheck.title_problems(proj)
    (proj / "scene.js").write_text('K.footage({}); K.title(); K.finish();', encoding="utf-8")
    assert not shipcheck.title_problems(proj)
    (proj / "scene.js").write_text('K.footage({}); K.finish();', encoding="utf-8")
    assert shipcheck.title_problems(proj)


# ---------- P0-3 freezes ----------

def test_freeze_runs_and_window_overlap():
    diffs = [255] + [5] * 10 + [0.0] * 14 + [5] * 10
    runs = faces.freeze_runs(diffs, 24)
    assert runs == [[round(10 / 24, 3), round(25 / 24, 3)]]
    assert guards.freeze_findings([[0, 3]], [], runs)
    assert not guards.freeze_findings([[2, 3]], [], runs)
    assert guards.freeze_findings([], [[0.9, 2]], runs)            # 0.14 s of it inside a split window shows
    assert faces.freeze_runs([255] + [0.0] * 6, 24) == []          # 0.29 s is not reported


def test_duplicate_run_and_fps():
    assert guards.decimate_runs([False, True, True, False, True], 24) == (3, pytest.approx(3 / 24))
    assert guards.decimate_runs([False] * 5, 24) == (0, 0.0)
    probs, warn = guards.fps_problems(30, 24, 24)
    assert not probs and "judder" in warn
    probs, warn = guards.fps_problems(24, 30, 24)
    assert probs and warn is None


# ---------- P1-4 cut strips ----------

def test_strip_flags_charcoal_flash_half_built_and_one_frame():
    rng = np.random.default_rng(2)
    face = lambda: rng.integers(80, 200, (24, 14)).astype(np.float32)  # noqa: E731
    board = np.full((24, 14), 22.0)
    board[6:18, 3:11] = 190                                              # a built board
    empty = np.full((24, 14), 22.0) + rng.normal(0, 1, (24, 14))
    ok = [face() for _ in range(6)] + [board.copy() for _ in range(6)]
    assert guards.strip_flags(ok, 6) == []
    bad = [face() for _ in range(6)] + [empty] + [board.copy() for _ in range(5)]
    kinds = {f for f, _ in guards.strip_flags(bad, 6)}
    assert {"charcoal", "half-built"} <= kinds
    assert "half-built" not in {f for f, _ in guards.strip_flags(bad, 6, built=False)}
    assert guards.lands_on_board(3.0, [[0, 3.0]], [[9, 12]])          # face -> board: a hard cut onto a board
    assert not guards.lands_on_board(9.0, [[0, 3.0]], [[9, 12]])      # board -> split eases
    assert not guards.lands_on_board(12.0, [[0, 3.0]], [[9, 12]])     # split -> board eases
    assert not guards.lands_on_board(5.0, [[5, 6]], [])                # board -> face
    flash = [board.copy() for _ in range(12)]
    flash[8] = np.full((24, 14), 250.0)
    assert ("flash", 8) in guards.strip_flags(flash, 6)
    other = np.full((24, 14), 22.0)
    other[2:8, 2:6] = 240
    blip = [board.copy() for _ in range(12)]
    blip[9] = other
    assert ("one-frame", 9) in guards.strip_flags(blip, 6)


def test_track_jumps_skip_seams():
    cx = [100.0] * 20 + [140.0] * 20
    assert guards.track_jumps(cx, [[0, 1.6]], 24)
    assert not guards.track_jumps(cx, [[0, 1.6]], 24, seams=[20])
    assert guards.window_edges([[0, 3], [5, 6]], [[3, 4.5]], 6) == [3, 4.5, 5]


# ---------- P1-5 joins + tighten ----------

def test_tighten_keeps_more_after_a_word(tmp_path):
    import tighten_footage
    from PIL import Image
    proj = tmp_path
    for d in ("face", "half"):
        (proj / "assets" / d).mkdir(parents=True)
        for i in range(48):
            Image.new("RGB", (8, 8), (i, i, i)).save(proj / "assets" / d / f"{i + 1:06d}.jpg")
    (proj / "audio").mkdir()
    footage.write_wav(np.zeros((2 * footage.SR, 2), np.float32), proj / "audio" / "voice.wav")
    (proj / "assets" / "track.json").write_text(json.dumps({"cx": list(range(48)), "cy": [0] * 48, "diff": [1.0] * 48, "joins": []}))
    tr = {"segments": [{"start": 0.0, "end": 1.9, "words": [W("a", 0.0, 0.5), W("b", 1.5, 1.9)]}], "duration": 2.0,
          "cut_from": {"ranges": [{"start": 0, "end": 2, "last_word_end": 1.9, "next_word_start": None, "out_start": 0.0, "lead": 0}]}}
    (proj / "transcript.json").write_text(json.dumps(tr))
    t = tighten_footage.tighten(proj, analyse=False)
    w = t["segments"][0]["words"]
    assert w[1]["start"] - w[0]["end"] == pytest.approx(0.3, abs=0.05)       # the pause kept is 0.3 s >= 0.25 (SHORT-13)
    assert t["tightened"]["cuts_at_s"][0] == pytest.approx(0.5 + 0.2, abs=0.05)  # 0.2 s kept after "a", 0.1 before "b"
    j = json.loads((proj / "assets" / "track.json").read_text())
    assert len(j["diff"]) == len(j["cx"]) == len(list((proj / "assets" / "face").glob("*.jpg")))


# ---------- P1-6 language ----------

def test_latin_caption_words_are_found_and_fail_captions(tmp_path):
    assert shortinfo.latin_words([{"w": "Polymarket", "start": 1}, {"w": "سوق", "start": 2}, {"w": "go", "hid": True}]) == [(1, "Polymarket")]
    import captions
    proj = tmp_path
    (proj / "audio").mkdir()
    footage.write_wav(np.zeros((footage.SR, 2), np.float32), proj / "audio" / "voice.wav")
    from provenance import stamp
    tr = {**stamp(proj / "audio" / "voice.wav"), "duration": 1.0, "cut_from": {"ranges": []},
          "segments": [{"words": [W("السوق", 0.1, 0.4), W("Polymarket", 0.5, 0.9)]}]}
    (proj / "transcript.json").write_text(json.dumps(tr), encoding="utf-8")
    (proj / "script.md").write_text("<!-- captions:start -->\nالسوق Polymarket\n<!-- captions:end -->\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="SHORT-14"):
        captions.main(proj)
    assert "window.CUT" in (proj / "build" / "timing.js").read_text(encoding="utf-8")
    (proj / "script.md").write_text("<!-- captions:start -->\nالسوق بوليماركت {{السوق Polymarket}}\n<!-- captions:end -->\n", encoding="utf-8")
    captions.main(proj)


def test_extras_only_for_cut_out_shorts(tmp_path):
    (tmp_path / "transcript.json").write_text(json.dumps({"segments": []}))
    assert shortinfo.extras_js(tmp_path) == ""


# ---------- P1-7 dead frames and spacing ----------

def test_long_empty_stretch_cannot_be_excused():
    ok = [{"kind": "dead", "range": [0, 20], "why": "face"}]
    assert not lint.justified({"kind": "dead", "from": 4.0, "to": 7.0}, ok)
    assert lint.justified({"kind": "dead", "from": 0.5, "to": 4.2}, ok)      # 1.2 s outside the title window
    assert lint.justified({"kind": "fill", "from": 1.0, "to": 3.0}, [{"kind": "fill", "range": [0, 3], "why": "title"}])


def test_tight_gap_in_board_px():
    head = dict(id=1, kind="text", txt="h", head=True, board="1", x0=200, x1=800, y0=200, y1=300, sc=1)
    sub = dict(id=2, kind="text", txt="s", board="1", x0=300, x1=700, y0=310, y1=350)
    assert guards.tight_gap_findings(0, {"items": [head, sub]}, 40)
    assert not guards.tight_gap_findings(0, {"items": [head, {**sub, "y0": 345, "y1": 385}]}, 40)
    small = {**head, "sc": 0.8}
    assert not guards.tight_gap_findings(0, {"items": [small, {**sub, "y0": 333, "y1": 373}]}, 40)  # 33 px = 41 board px


# ---------- P1-8 notes ledger ----------

def test_notes_ledger(tmp_path, capsys):
    make.note(tmp_path, ["39.8", "الدولار مكانه غلط", "v3"])
    make.note(tmp_path, ["fixed", "1"])
    n = json.loads((tmp_path / "notes.json").read_text(encoding="utf-8"))
    assert n == [{"t": 39.8, "note": "الدولار مكانه غلط", "status": "fixed", "version": "v3"}]
    with pytest.raises(SystemExit):
        make.note(tmp_path, [])


# ---------- P1-9 sfx at scene level ----------

def test_sfx_overlap_and_orphan():
    cues = [{"t": 1.0, "cat": "pop"}, {"t": 1.1, "cat": "click"}, {"t": 5.0, "cat": "hit"}]
    out = guards.sfx_findings(cues, [1.0, 1.05])
    assert [h["kind"] for h in out] == ["sfx-overlap", "sfx-orphan"]
    assert not guards.sfx_findings([{"t": 1.0, "cat": "pop"}], [1.2])


# ---------- decisions (a) and (b), P2 money ----------

def test_face_share_for_workshop_shorts():
    assert guards.face_share_findings([[0, 3]], [[5, 6]], 20, live=True)
    assert not guards.face_share_findings([[0, 3]], [[5, 12]], 20, live=True)
    assert not guards.face_share_findings([[0, 3]], [], 20, live=False)


@pytest.mark.parametrize("profile,live,expected", [
    ("", False, False), ("2026-10-17", False, False), ("", True, True),
    ("2026-10-18", False, True), ("2026-10-18", True, True)])
def test_face_share_all_current_shorts(profile, live, expected):
    hits = guards.face_share_findings([[0, 3]], [], 20, live, profile=profile)
    assert any(h["kind"] == "face-share" for h in hits) is expected
    assert not guards.face_share_findings([[0, 3]], [[3, 10]], 20, live, profile=profile)


def test_cut_inside_a_word():
    words = [W("a", 1.0, 1.5), W("b", 1.7, 2.1)]
    assert guards.mid_word_findings([1.2], words)
    assert not guards.mid_word_findings([1.6, 1.02], words)


def test_caption_switch():
    assert not guards.caption_switch_findings([(1, True, 960.0), (2, False, None), (3, True, 954.0)])
    assert guards.caption_switch_findings([(1, True, None), (2, False, 960.0)])


def test_stray_currency():
    item = lambda txt, **kw: dict(id=1, kind="text", txt=txt, x0=0, x1=10, y0=0, y1=10, **kw)  # noqa: E731
    assert guards.currency_findings(0, {"items": [item("الرهان 39.8$")]})
    assert guards.currency_findings(0, {"items": [item("$ 39.8")]})
    assert not guards.currency_findings(0, {"items": [item("الرهان $39.8")]})
    assert guards.currency_findings(0, {"items": [item("الرهان $39.8", currency={"ok": False, "where": "on the right"})]})


# ---------- PACE-6 ending, EXPL-2 still icons (re-do review 2026-10-18) ----------

def box(id, kind="obj", txt="kanz-bank-v01.png", x=300, y=400, w=400, board="1", **kw):
    return dict(id=id, kind=kind, txt=txt, x0=x, x1=x + w, y0=y, y1=y + w, board=board, **kw)


def test_tail_after_the_last_word():
    hit, = guards.tail_findings(66.66, 65.36)                   # the old worked example: tLast + 1.3
    assert hit["kind"] == "long-tail" and hit["rule"] == "PACE-6" and "PACE-6" in hit["why"]
    assert not guards.tail_findings(65.76, 65.36)               # tLast + 0.4
    assert not guards.tail_findings(65.96, 65.36)               # 0.6 s is the limit
    assert not guards.tail_findings(10.0, None)                 # no words: nothing to measure


def test_ship_tail_reads_timing_js(tmp_path, monkeypatch):
    import shipcheck
    (tmp_path / "build").mkdir()
    toks = [{"w": "a", "start": 1.0, "end": 1.5}, {"w": "b", "start": 1.6, "end": 2.0}, {"w": "x", "tr": True, "start": 5, "end": 9}]
    (tmp_path / "build" / "timing.js").write_text("window.TOKENS=" + json.dumps(toks) + ";\nwindow.DURATION=2.2;\n", encoding="utf-8")
    assert shipcheck.last_word_end(tmp_path) == 2.0              # hidden (tr) tokens do not count
    monkeypatch.setattr(shipcheck, "duration", lambda mp4: 3.3)
    assert "PACE-6" in shipcheck.tail(tmp_path, "x.mp4")[0]
    monkeypatch.setattr(shipcheck, "duration", lambda mp4: 2.4)
    assert not shipcheck.tail(tmp_path, "x.mp4")
    assert shipcheck.last_word_end(tmp_path / "none") is None


def test_hook_replay_board_and_hero():
    head = box(9, kind="text", txt="ليه", board=None)
    hook = {"items": [head, box(1, txt="kanz-usd-banknote-v01.png", w=600, board="1")]}
    back = {"items": [box(2, txt="kanz-usd-banknote-v01.png", w=520, board="1"), box(3, kind="text", txt="جزء", board="1")]}
    hit, = guards.replay_findings(hook, back, 66.6)
    assert hit["kind"] == "hook-replay" and hit["rule"] == "PACE-6"
    assert "hook board" in hit["why"] and "hook hero" in hit["why"]
    other = {"items": [box(4, txt="kanz-usd-banknote-v01.png", w=500, board="7")]}   # the hero again, on a new board
    assert "hook hero" in guards.replay_findings(hook, other, 66.6)[0]["why"]
    carried = {"items": [box(5, txt="kanz-usd-banknote-v01.png", w=200, board="7"), box(6, txt="kanz-receipt-v01.png", board="7")]}
    assert not guards.replay_findings(hook, carried, 66.6)                           # a small carried hero is no replay
    faint = {"items": [box(2, txt="kanz-usd-banknote-v01.png", w=600, board="7", opacity=0.3)]}
    assert not guards.replay_findings(hook, faint, 66.6)
    assert not guards.replay_findings(hook, None, 66.6)
    assert guards.main_board({"items": [head]}) is None


def test_still_icon_under_the_voice_is_a_warning():
    words = [W(str(i), i * 0.5, i * 0.5 + 0.4) for i in range(20)]               # 0.4 s of speech every 0.5 s
    icon = lambda t, **kw: (t, {"items": [box(1, **kw), box(9, kind="caption", txt="c")]})  # noqa: E731
    frames = [icon(i * 0.25) for i in range(25)]                                 # 0-6 s: one icon, nothing else
    hit, = guards.still_image_findings(frames, words)
    assert hit["kind"] == "still-image" and hit["level"] == "warn" and hit["rule"] == "EXPL-2"
    assert hit["from"] == 0 and hit["to"] == 6.0
    assert not guards.still_image_findings(frames, words, skip=[(0, 6.5)])        # the hook / a face window
    assert not guards.still_image_findings(frames[:8], words)                     # 1.75 s: 1.4 s of speech
    assert not guards.still_image_findings(frames, [])                            # silence over an icon is not EXPL-2
    grows = [icon(i * 0.25, w=round(200 * 1.08 ** i)) for i in range(25)]        # the icon keeps scaling with the words
    assert not guards.still_image_findings(grows, words)
    drift = [icon(i * 0.25, x=300 + 3 * i) for i in range(25)]                    # camera drift alone keeps it still
    assert guards.still_image_findings(drift, words)
    new = frames[:8] + [(t, {"items": f["items"] + [box(2, kind="text", txt="label")]}) for t, f in frames[8:16]] + frames[16:]
    assert not guards.still_image_findings(new, words)                            # something appears every 2 s
    chart = [(t, {"items": f["items"] + [box(3, txt="path")]}) for t, f in frames]  # a diagram beside it
    assert not guards.still_image_findings(chart, words)
    photo = [icon(i * 0.25, txt="street.jpg") for i in range(25)]                 # a place photo (IMG-4) is not an icon
    assert not guards.still_image_findings(photo, words)


def test_warnings_do_not_fail_strict():
    findings = [{"kind": "still-image", "level": "warn", "justified": False}, {"kind": "long-tail", "justified": False},
                {"kind": "hook-replay", "justified": True}]
    assert lint.unjustified(findings) == 1


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg")
def test_freeze_detected_on_repeated_jpegs(tmp_path):
    from PIL import Image
    d = tmp_path / "assets" / "face"
    d.mkdir(parents=True)
    rng = np.random.default_rng(3)
    frames = [rng.integers(0, 255, (64, 36, 3), dtype=np.uint8) for _ in range(10)]
    seq = frames[:4] + [frames[4]] * 16 + frames[5:]
    for i, f in enumerate(seq):
        Image.fromarray(f).save(d / f"{i + 1:06d}.jpg", quality=90)
    runs = faces.freeze_runs(faces.frame_diffs(d), 24)
    assert len(runs) == 1 and runs[0][1] - runs[0][0] == pytest.approx(16 / 24, abs=0.05)
    subprocess.run  # noqa: B018 (ffmpeg is only needed for the skip condition's sibling tests)


def test_board_alone_three_seconds():
    # face 0-5, board 5-8 (3.0 s: fine), split 8-12, board 12-16 (4 s: too long), face 16-20
    got = guards.board_alone_findings([[0, 5], [16, 20]], [[8, 12]], 20)
    assert [(f["from"], f["to"]) for f in got] == [(12, 16)]
    assert not guards.board_alone_findings([[0, 5], [16, 20]], [[8, 12], [12, 16]], 20)
    # a board running into the end counts too
    assert guards.board_alone_findings([[0, 10]], [], 14)
    assert not guards.excusable({"kind": "board-alone", "from": 12, "to": 16})

