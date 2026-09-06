"""
Break the model on purpose and check the test notices.

A test that has never failed is a claim, not a check. This mutates
build_beauty.py in memory, one realistic fault at a time, runs
test_beauty.model_maths() against the mutated copy, and reports whether it
caught each one. Nothing on disk is touched: each mutant is written to a
temporary directory and imported from there.

The faults are the ones a drift check cannot see, because a drift check
compares the payload against the same function that wrote it:

  swapped columns      the design matrix's columns and names come apart, so
                       one term wears another's coefficient
  wrong reference      the category dummies drop the wrong level, so every
                       category is measured against the wrong baseline
  leaky g-computation  the adjusted means forget to clear a species' own
                       category before predicting it under another
  flipped drop-one     the fall in R-squared is reported with its sign
                       reversed, which would rank the terms backwards

Run:  python3 break_model.py
"""

import importlib.util
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_beauty  # noqa: E402

SOURCE = os.path.join(HERE, "build_beauty.py")

MUTANTS = [
    # Not a swap of the num lookup: design() takes a column and its name from
    # the same entry, so swapping that dict swaps both together and changes
    # nothing. Misaligning them takes a change to the assembled matrix.
    ("misaligned columns",
     "    return np.column_stack(cols), names",
     "    return np.column_stack(cols[::-1]), names"),
    ("wrong reference category",
     '        elif t == "category":\n            for c in CATS[1:]:',
     '        elif t == "category":\n            for c in CATS[:-1]:'),
    ("leaky g-computation",
     '    for c in CATS[1:]:\n        base[:, idx["cat_" + c]] = 0',
     '    for c in CATS[1:]:\n        pass'),
    ("flipped drop-one",
     '        drop[t] = r2 - r2t',
     '        drop[t] = r2t - r2'),
    # The manifest's digest is only useful if the sentence describing how it
    # was made produces it. Both of these keep category_digest() internally
    # consistent and break its agreement with that sentence, which is the
    # only thing a reader has. Anchors here avoid backslashes on purpose:
    # writing these as a shell heredoc collapsed the escaped newline and the
    # mutation silently failed to apply, reporting as "source moved".
    ("digest gains a header",
     '    blob = "".join(',
     '    blob = "species,category" + "".join('),
    ("digest stops sorting",
     "    pairs = sorted(zip(",
     "    pairs = list(zip("),
]


def load(src, name):
    d = tempfile.mkdtemp()
    p = os.path.join(d, name + ".py")
    open(p, "w", encoding="utf-8").write(src)
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    src = open(SOURCE, encoding="utf-8").read()
    print("  unmutated:", end=" ")
    clean = test_beauty.model_maths(load(src, "bb_clean"))
    print("caught nothing" if not clean else f"FAILS CLEAN: {clean}")
    missed = [] if not clean else ["the unmutated model already fails"]

    for i, (label, old, new) in enumerate(MUTANTS):
        if old not in src:
            missed.append(f"{label}: the code it mutates has moved; update break_model.py")
            print(f"  {label:22s} NOT APPLIED (source moved)")
            continue
        try:
            found = test_beauty.model_maths(load(src.replace(old, new, 1), f"bb_mut{i}"))
        except Exception as e:                                   # noqa: BLE001
            # A fault that stops the build is a fault the build cannot ship.
            print(f"  {label:22s} caught, by raising {type(e).__name__}: {e}")
            continue
        if found:
            print(f"  {label:22s} caught: {found[0]}")
        else:
            missed.append(f"{label}: the mutant passed the test")
            print(f"  {label:22s} MISSED")
    print(f"  {len(MUTANTS) - len([m for m in missed if 'passed' in m or 'moved' in m])}"
          f"/{len(MUTANTS)} faults caught")
    for m in missed:
        print("  PROBLEM: " + m)
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())
