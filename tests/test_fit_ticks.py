"""THE TICK LEVER, AGAINST THE FIGURES IT WAS BUILT FOR.

sitefig.fit_ticks governs one artist class - an axis's tick labels - and this
asks the only two questions worth asking about a lever:

  1. IS IT A NO-OP ON A FIGURE THAT ALREADY PASSES? At NOTES all three of these
     figures ship with 0 layout problems. The lever tries the unchanged figure
     first, so it must return "unchanged" and audit() must still report zero.
     A lever that improves a passing figure has moved something nobody asked it
     to move, and three shipped PNGs would change bytes for no reason.

  2. DOES ITS VERDICT AGREE WITH THE GATE'S? This is the one that failed, and
     it is why `settle` exists. fit_ticks judges with audit()'s own predicate,
     which was the fix for trap 37 - but a correct predicate applied to the
     wrong FRAME is the same failure wearing different clothes. Called before
     continents/fig_continents.py runs sitefig.centre(), fit_ticks measured an
     uncentred figure, found 0.1, 1, 10 and 100 comfortably inside the canvas
     and returned "unchanged". centre() then shifted the grid, and audit() -
     the gate - reported all four off canvas. The lever passed while the gate
     failed, with nothing wrong in it except when it looked.

     `settle` is the repair: whatever the builder still runs after the lever is
     handed to the lever and invoked after every candidate, so the state the
     lever judges is the state that gets saved. --break settle removes it and
     this run must go red.

WHAT THE THREE FIGURES SAY AT 350, MEASURED 2026-09-13:

  beauty_fig3_terms      ticks clear with a 10% margin, no wrapping
  beauty_fig4_strata     ticks clear with a 10% margin, no wrapping (figure retired
                         2026-10-24 with the topic test, D-32; no longer driven)
  continents_fig3_rigidity   RAISES - 4 off canvas at every margin it has,
                             0 overlaps, which is the perpendicular constraint
                             with nothing on the other side of it

None of the three is a conversion. The two beauty figures still have their x
axis label, their panel() label, their fig.text footnote and (on fig4) four
hand-placed value annotations off canvas at 350, and those are three more
artist classes that this lever does not own and must not be stretched to
cover. What this file gates is the lever, not the queue.

WHAT IT DOES NOT ASSERT. It says nothing about the other artist classes, about
the figures' words (the lever may change how a tick label is presented and not
what it says, and the candidate set contains no operation that could), and
nothing about the served width - tests/test_fig_floor.py owns that. It runs
each builder module in its own subprocess inside a throw-away copy of the tree,
so it never writes into site/.

    python tests/test_fit_ticks.py
    python tests/test_fit_ticks.py --break judge     # 0 caught, non-zero blind
    python tests/test_fit_ticks.py --break settle    # 0 caught, non-zero blind
    python tests/test_fit_ticks.py --keep            # leave the work copy
"""
import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# figure key -> (module dir, worker name). One subprocess per module: the two
# builders set rcParams through sitefig.style() and carry module state, and
# test_fig_floor.py already paid for finding out what sharing an interpreter
# does to them.
WORKERS = ("beauty", "continents")

# What each figure is expected to say at 350. Written out rather than derived,
# because a gate that accepts whatever it is told is not a gate.
AT_PHONE = {
    "beauty_fig3_terms": ("applied", "wrap none, margin +10%"),
    "continents_fig3_rigidity": ("raises", None),
}


# --------------------------------------------------------------- the workers

def worker(which):
    """Draw each figure at both widths and report what the lever said and what
    the audit said. Runs inside the work copy with the module's own cwd."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, root)
    import sitefig

    rec = {}
    real = sitefig.fit_ticks
    pending = {}

    def spy(ax, *a, **k):
        labs = [t.get_text() for t in ax.get_yticklabels()
                if t.get_visible() and t.get_text().strip()]
        try:
            v = real(ax, *a, **k)
            pending["lever"] = ["ok", v]
        except ValueError as e:
            pending["lever"] = ["raise", str(e)]
            raise
        finally:
            pending["ticks"] = labs
        return v
    sitefig.fit_ticks = spy

    here = os.path.join(root, which)
    os.chdir(here)
    sys.path.insert(0, here)

    if which == "beauty":
        import fig_beauty as M
        data = json.load(open(M.PAYLOAD, encoding="utf-8"))
        sitefig.style()
        # beauty_fig4_strata retired 2026-10-24 (R5, D-32) with the topic test it drew.
        jobs = [("beauty_fig3_terms", M.fig3)]

        def draw(fn, width):
            out = {}

            def emit(fig, name):
                out["audit"] = list(M.audit(fig))
                plt.close(fig)
                return 0
            keep, M.emit = M.emit, emit
            try:
                fn(data, width=width)
            finally:
                M.emit = keep
            return out.get("audit", ["emit was never reached"])
    else:
        import fig_continents as M
        data = M.load()
        sitefig.style()
        jobs = [("continents_fig3_rigidity", M.fig3_rigidity)]

        def draw(fn, width):
            fig = fn(data, width=width)
            bad = list(M.audit(fig))
            plt.close(fig)
            return bad

    for key, fn in jobs:
        for width in (sitefig.NOTES, sitefig.PHONE):
            pending.clear()
            slot = {"lever": None, "ticks": [], "audit": None, "error": None}
            try:
                slot["audit"] = draw(fn, width)
            except ValueError as e:
                slot["error"] = str(e)
            except Exception as e:                                # noqa: BLE001
                slot["error"] = "%s: %s" % (type(e).__name__, e)
            slot["lever"] = pending.get("lever")
            slot["ticks"] = pending.get("ticks", [])
            rec["%s@%d" % (key, width)] = slot
    return rec


# ------------------------------------------------------------------ the run

def copy_tree():
    sys.path.insert(0, HERE)
    import test_generators as TG
    work = tempfile.mkdtemp(prefix="fitticks-")
    dst = os.path.join(work, "tree")
    shutil.copytree(ROOT, dst, ignore=TG._ignore(ROOT), symlinks=True)
    return work, dst


def blind_judge(tree):
    """fit_ticks' acceptance test forced to 'nothing is wrong'. If the
    predicate is decoration the run stays green (trap 26/34)."""
    p = os.path.join(tree, "sitefig.py")
    t = open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if t.count("\r\n") else "\n"
    head, tail = t.split("def fit_ticks(", 1)
    old = "        return off, hits" + nl
    if tail.count(old) != 1:
        sys.exit("--break judge: fit_ticks' judge() no longer ends in "
                 "'return off, hits' - the break needs rewriting, and until "
                 "it is this file is not testing what it says it tests")
    open(p, "w", encoding="utf-8", newline="").write(
        head + "def fit_ticks(" + tail.replace(old, "        return 0, 0" + nl))


def drop_settle(tree):
    """The ordering repair removed: fit_ticks judges the figure as it is
    before centre() moves it, and the frame it measured is not the frame that
    gets saved."""
    p = os.path.join(tree, "continents", "fig_continents.py")
    t = open(p, encoding="utf-8", newline="").read()
    old = ", settle=lambda: sitefig.centre(fig)"
    if t.count(old) != 1:
        sys.exit("--break settle: the settle argument is not where this "
                 "expects it in continents/fig_continents.py")
    open(p, "w", encoding="utf-8", newline="").write(t.replace(old, ""))


CAND = re.compile(r"\(wrap cols, margin, off-canvas, overlaps\) = (\[.*?\])\.")


def candidates(message):
    m = CAND.search(message or "")
    return ast.literal_eval(m.group(1)) if m else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--break", dest="brk", choices=["judge", "settle"])
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    work, tree = copy_tree()
    if args.brk == "judge":
        blind_judge(tree)
    elif args.brk == "settle":
        drop_settle(tree)

    rec = {}
    try:
        for which in WORKERS:
            res = os.path.join(work, "_ticks_%s.json" % which)
            out = subprocess.run(
                [PY, os.path.join(tree, "tests", "test_fit_ticks.py"),
                 "--worker", which, "--out", res],
                cwd=tree, capture_output=True, text=True,
                encoding="utf-8", errors="replace")
            if not os.path.exists(res):
                print("  %s: the worker produced nothing" % which)
                print("    " + ((out.stderr or out.stdout or "")[-600:]
                                ).replace("\n", "\n    "))
                return 1
            rec.update(json.load(open(res, encoding="utf-8")))
    finally:
        if args.keep:
            print("  work copy kept at %s" % work)
        else:
            shutil.rmtree(work, ignore_errors=True)

    import importlib
    sys.path.insert(0, ROOT)
    sf = importlib.import_module("sitefig")
    bad = []

    print("  lever: sitefig.fit_ticks, judged by audit()'s own predicate")
    print("  widths: %d authored, %d phone; matplotlib through each builder"
          % (sf.NOTES, sf.PHONE))
    for key in sorted(rec):
        name, width = key.rsplit("@", 1)
        s = rec[key]
        lever = s["lever"]
        verdict = ("(never called)" if not lever else
                   "RAISES" if lever[0] == "raise" else lever[1])
        n_audit = "-" if s["audit"] is None else str(len(s["audit"]))
        print("  %-26s @%-4s  lever %-24s audit %s%s"
              % (name, width, verdict, n_audit,
                 "  ERROR" if s["error"] and lever and lever[0] != "raise"
                 else ""))

    for name in AT_PHONE:
        # 1. a no-op on the figure that already passes
        s = rec.get("%s@%d" % (name, sf.NOTES))
        if s is None:
            bad.append("%s: never drawn at %d" % (name, sf.NOTES))
            continue
        if s["lever"] != ["ok", "unchanged"]:
            bad.append("%s at %d: the lever moved a figure that already "
                       "passes - said %r" % (name, sf.NOTES, s["lever"]))
        if s["audit"]:
            bad.append("%s at %d: %d layout problem(s) where the shipped "
                       "figure has none: %s"
                       % (name, sf.NOTES, len(s["audit"]), s["audit"][:3]))

        # 2. what it says at the width the phone serves
        s = rec.get("%s@%d" % (name, sf.PHONE))
        if s is None:
            bad.append("%s: never drawn at %d" % (name, sf.PHONE))
            continue
        want, detail = AT_PHONE[name]
        lever = s["lever"]
        if not lever:
            bad.append("%s at %d: fit_ticks was never called - the builder "
                       "no longer runs the lever" % (name, sf.PHONE))
            continue
        if want == "raises":
            if lever[0] != "raise":
                bad.append("%s at %d: expected the lever to RAISE and it "
                           "returned %r. Either the figure changed or the "
                           "lever stopped seeing what audit() sees."
                           % (name, sf.PHONE, lever[1]))
            else:
                cand = candidates(lever[1])
                if not cand:
                    bad.append("%s at %d: the raise carried no candidate "
                               "table, so it does not say which constraint "
                               "failed" % (name, sf.PHONE))
                elif not all(c[2] > 0 and c[3] == 0 for c in cand):
                    bad.append("%s at %d: this one is supposed to fail "
                               "PERPENDICULAR only - off canvas with no "
                               "crowding - and the candidates say %s"
                               % (name, sf.PHONE, cand[:4]))
        else:
            if lever[0] != "ok":
                bad.append("%s at %d: expected %r, the lever raised"
                           % (name, sf.PHONE, detail))
            elif lever[1] != detail:
                bad.append("%s at %d: expected %r, got %r"
                           % (name, sf.PHONE, detail, lever[1]))
            # 3. the verdict has to agree with the gate about TICK LABELS.
            # audit() truncates the text it names to 30 characters.
            named = {t.strip()[:30] for t in s["ticks"]}
            hit = [b for b in (s["audit"] or [])
                   if any(repr(t) in b for t in named)]
            if hit:
                bad.append("%s at %d: the lever passed it and audit() still "
                           "names a tick label: %s" % (name, sf.PHONE, hit[:3]))

    if bad:
        print("\n  %d problem(s):" % len(bad))
        for b in bad:
            print("   - " + b)
    else:
        print("\n  the lever is a no-op where the figure passes, and where it "
              "does not its verdict is the one audit() reaches")
    if args.brk:
        # A break run reports on the CHECK, not on the tree: 0 when the
        # injected fault was caught, non-zero when the check slept through it.
        print("  --break %s: %s" % (args.brk,
              "caught" if bad else "NOT CAUGHT - this check is decoration"))
        return 0 if bad else 1
    return 1 if bad else 0


if __name__ == "__main__":
    if "--worker" in sys.argv:
        w = sys.argv[sys.argv.index("--worker") + 1]
        dest = sys.argv[sys.argv.index("--out") + 1]
        got = worker(w)
        json.dump(got, open(dest, "w", encoding="utf-8"))
        raise SystemExit(0)
    raise SystemExit(main())
