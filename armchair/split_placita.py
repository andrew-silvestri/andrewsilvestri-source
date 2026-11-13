"""Cut the Placita (Books I-V) out of the Gutenberg volume into data/placita_dowel.txt.

Each output line is "<source line number>\t<text>", so every opinion in data/opinions.csv can be traced to
the line of the public-domain text it paraphrases. The cut starts at the treatise's title and ends before
the next treatise ("A BREVIATE OF A DISCOURSE"); the script refuses a volume where either marker is not
found exactly once in the body, or where the five BOOK headings are not found in order.

Run:  python split_placita.py
"""
import re

from netfetch import HERE, verified

START = "OF THOSE SENTIMENTS CONCERNING NATURE WITH WHICH PHILOSOPHERS WERE"
END = "A BREVIATE OF A DISCOURSE, SHOWING THAT THE STOICS SPEAK GREATER"


def cut():
    path, _ = verified("plutarch_morals_v3.txt")
    lines = path.read_text(encoding="utf-8").splitlines()
    starts = [i for i, s in enumerate(lines) if s.strip() == START]
    ends = [i for i, s in enumerate(lines) if s.strip() == END]
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        raise SystemExit(f"markers: start {starts}, end {ends}")
    body = list(range(starts[0], ends[0]))
    books = [i for i in body if re.fullmatch(r"BOOK [IVX]+\.", lines[i].strip())]
    if [lines[i].strip() for i in books] != ["BOOK I.", "BOOK II.", "BOOK III.", "BOOK IV.", "BOOK V."]:
        raise SystemExit(f"book headings: {[lines[i] for i in books]}")
    return lines, body, books


if __name__ == "__main__":
    lines, body, books = cut()
    out = HERE / "data" / "placita_dowel.txt"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Placita (pseudo-Plutarch / Aetius), tr. John Dowel, in Plutarch's Morals vol. 3, ed. W. W. Goodwin,\n"
                "# Boston, printing of 1911; public domain. Cut from Project Gutenberg eBook #78851 by split_placita.py.\n"
                "# Column 1 is the line number in that eBook's plain-text file.\n")
        for i in body:
            f.write(f"{i + 1}\t{lines[i]}\n")
    print(f"{out.name}: lines {body[0] + 1}-{body[-1] + 1}; books at {[b + 1 for b in books]}")
