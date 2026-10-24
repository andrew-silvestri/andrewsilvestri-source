"""Render a house-style Manim scene into everything the clip component needs.

    python clips/render_clip.py <scene.py> <SceneClass> --name <slug> [--out site/assets/clips]

Writes, into --out:
    <slug>.webm   VP9, no audio
    <slug>.mp4    H.264 (yuv420p, faststart), no audio
    <slug>.png    the poster: the frame at the scene's POSTER_T
    <slug>.vtt    captions from the scene's CAPTIONS
    <slug>.json   what insight.clip() reads: title, measured duration, size,
                  bytes and SHA-1 of each file, the scene it came from

and refuses (exit 1, nothing written) when either video is 4 MB or more, when
a caption overlaps another or runs past the measured duration, or when the
scene has no TITLE, or when the scene or house.py calls Pango text (Text,
MarkupText, Paragraph): clip text is LaTeX. _INSIGHT rule 2 sets the 4 MB
ceiling.

Manim runs under MANIM_WORKSPACE/.venv (the pinned manim==0.18.1), or under
the interpreter named by MANIM_PYTHON. Only the interpreter is borrowed from
the workspace: clips/house.py imports nothing from its shared/ library, which
is the internship's (house.py's header says why).
"""
import argparse
import hashlib
import json
import re
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.dirname(HERE)
MANIM_PY = os.environ.get("MANIM_PYTHON") or os.path.join(
    os.path.dirname(PUB), "MANIM_WORKSPACE", ".venv", "Scripts", "python.exe")
LIMIT = 4 * 1024 * 1024
W, H, FPS = 1280, 720, 30


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if r.returncode != 0:
        sys.exit("render_clip: %s exited %d\n%s" % (os.path.basename(cmd[0]), r.returncode, (r.stderr or r.stdout)[-3000:]))
    return r.stdout


def scene_meta(scene_py, cls):
    code = ("import importlib.util,json,sys;"
            "s=importlib.util.spec_from_file_location('m',sys.argv[1]);m=importlib.util.module_from_spec(s);"
            "s.loader.exec_module(m);c=getattr(m,sys.argv[2]);"
            "print(json.dumps({'title':c.TITLE,'captions':c.CAPTIONS,'poster_t':c.POSTER_T}))")
    return json.loads(run([MANIM_PY, "-c", code, scene_py, cls]).strip().splitlines()[-1])


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", path])
    return float(json.loads(out)["format"]["duration"])


def vtt_time(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return "%02d:%02d:%06.3f" % (h, m, s)


def sha1(path):
    return hashlib.sha1(open(path, "rb").read()).hexdigest()


# Every clip sets its text in LaTeX (house.py: label, number, equation). Manim's
# Pango-backed classes drew loose, uneven text in the first clip, and Andrew
# asked on 2026-10-23 that LaTeX be used for every clip, past and future. The
# rule is enforced here, on the path every clip is rendered by, not in house.py
# (HANDOFF trap 19: a constraint sits on the last code that can violate it).
PANGO = re.compile(r"\b(Text|MarkupText|Paragraph)\s*\(")


def pango_calls(*paths):
    hits = []
    for p in paths:
        for i, line in enumerate(open(p, encoding="utf-8"), 1):
            code = line.split("#", 1)[0]
            if PANGO.search(code):
                hits.append("%s:%d: %s" % (os.path.basename(p), i, line.strip()))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene")
    ap.add_argument("cls")
    ap.add_argument("--name", required=True)
    ap.add_argument("--out", default=os.path.join(PUB, "site", "assets", "clips"))
    a = ap.parse_args()
    scene = os.path.abspath(a.scene)
    hits = pango_calls(scene, os.path.join(HERE, "house.py"))
    if hits:
        sys.exit("render_clip: clip text must be LaTeX (house.label/number/equation), not Pango text:\n  "
                 + "\n  ".join(hits))
    meta = scene_meta(scene, a.cls)
    if not meta["title"]:
        sys.exit("render_clip: %s has no TITLE" % a.cls)

    with tempfile.TemporaryDirectory() as tmp:
        run([MANIM_PY, "-m", "manim", "render", "--format", "mp4", "-r", "%d,%d" % (W, H),
             "--fps", str(FPS), "--media_dir", tmp, "--disable_caching", "-v", "WARNING", scene, a.cls],
            cwd=os.path.dirname(scene))
        raw = [os.path.join(dp, f) for dp, _, fs in os.walk(tmp) for f in fs
               if f == a.cls + ".mp4" and "partial_movie_files" not in dp]
        if len(raw) != 1:
            sys.exit("render_clip: expected one %s.mp4 from manim, found %d" % (a.cls, len(raw)))
        raw = raw[0]
        dur = duration(raw)

        caps = meta["captions"]
        prev_end = 0.0
        for t0, t1, text in caps:
            if not (0 <= t0 < t1 <= dur + 0.05):
                sys.exit("render_clip: caption %r runs outside 0..%.2fs" % (text, dur))
            if t0 < prev_end - 1e-9:
                sys.exit("render_clip: caption %r overlaps the one before" % text)
            prev_end = t1

        stage = os.path.join(tmp, "out")
        os.makedirs(stage)
        base = os.path.join(stage, a.name)
        run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-crf", "23", "-preset", "slow", "-movflags", "+faststart", base + ".mp4"])
        run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-an", "-c:v", "libvpx-vp9", "-b:v", "0",
             "-crf", "36", "-row-mt", "1", "-deadline", "good", base + ".webm"])
        pt = meta["poster_t"] if meta["poster_t"] is not None else max(0.0, dur - 1.0 / FPS)
        run(["ffmpeg", "-y", "-v", "error", "-ss", "%.3f" % pt, "-i", raw, "-frames:v", "1", base + ".png"])
        with open(base + ".vtt", "w", encoding="utf-8", newline="\n") as fh:
            fh.write("WEBVTT\n\n")
            for i, (t0, t1, text) in enumerate(caps, 1):
                fh.write("%d\n%s --> %s\n%s\n\n" % (i, vtt_time(t0), vtt_time(t1), text))

        files = {}
        for ext in ("webm", "mp4", "png", "vtt"):
            p = base + "." + ext
            files[ext] = {"bytes": os.path.getsize(p), "sha1": sha1(p)}
        for ext in ("webm", "mp4"):
            if files[ext]["bytes"] >= LIMIT:
                sys.exit("render_clip: %s.%s is %d bytes, the ceiling is %d (4 MB)" % (a.name, ext, files[ext]["bytes"], LIMIT))
        for ext in ("webm", "mp4"):
            d = duration(base + "." + ext)
            if abs(d - dur) > 0.15:
                sys.exit("render_clip: %s.%s lasts %.2fs, manim rendered %.2fs" % (a.name, ext, d, dur))

        out = {"name": a.name, "title": meta["title"], "duration_s": round(dur, 3),
               "width": W, "height": H, "fps": FPS, "poster_t": pt,
               "scene": os.path.relpath(scene, PUB).replace(os.sep, "/"), "class": a.cls,
               "files": files}
        with open(base + ".json", "w", encoding="utf-8", newline="\n") as fh:
            json.dump(out, fh, indent=1)
            fh.write("\n")
        os.makedirs(a.out, exist_ok=True)
        for ext in ("webm", "mp4", "png", "vtt", "json"):
            shutil.copyfile(base + "." + ext, os.path.join(a.out, a.name + "." + ext))
    print("%s: %.2fs, webm %d B, mp4 %d B, poster %d B -> %s" % (
        a.name, dur, files["webm"]["bytes"], files["mp4"]["bytes"], files["png"]["bytes"], a.out))


if __name__ == "__main__":
    main()
