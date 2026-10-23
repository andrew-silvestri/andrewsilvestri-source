"""No CRLF in what ships (D-35, trap 32).

.gitattributes says `* text=auto eol=lf`, but a generator that writes text
mode on Windows without newline="\\n" (json.dump into open(p, "w"), a csv
writer's default "\\r\\n") puts CRLF in the working tree, `git status` hides
it because git normalises on compare, and rezip_downloads.py ships working-
tree bytes. On 2026-10-22 106 tracked files had drifted and the live
longevity archive carried 7 CRLF files. This reads bytes, never text (a
text-mode read normalises exactly the thing that broke).

Checks every member of every archive in site/downloads/ and every text file
under site/ (pages, scripts, styles, sitemap). Binary members (a NUL byte in
the first 8 KB, or a known binary extension) are skipped.

    python tests/test_lf.py           exit 1 on any CRLF
    python tests/test_lf.py --break   a zip holding one CRLF csv, in a temp dir; must exit 1
"""
import io
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.environ.get("LF_SITE") or os.path.join(os.path.dirname(HERE), "site")
BINARY = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".pdf", ".zip", ".xlsx", ".xls",
          ".woff", ".woff2", ".ttf", ".otf", ".npz", ".npy", ".parquet", ".gz", ".dll", ".so",
          ".pyc", ".mp4", ".webm")


def is_text(name, b):
    return not name.lower().endswith(BINARY) and b"\x00" not in b[:8192]


def scan(root):
    bad, n = [], 0
    for d, ds, fs in os.walk(root):
        ds[:] = [x for x in ds if x != "_preview"]
        for f in fs:
            p = os.path.join(d, f)
            rel = os.path.relpath(p, root)
            b = open(p, "rb").read()
            if f.lower().endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(b)) as z:
                    for m in z.namelist():
                        mb = z.read(m)
                        if m.endswith("/") or not is_text(m, mb):
                            continue
                        n += 1
                        if b"\r\n" in mb:
                            bad.append(f"{rel}!{m} ({mb.count(b'\r\n')} CRLF)")
            elif is_text(f, b):
                n += 1
                if b"\r\n" in b:
                    bad.append(f"{rel} ({b.count(b'\r\n')} CRLF)")
    return n, bad


def main():
    if "--break" in sys.argv:
        tmp = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(tmp, "downloads"))
            with zipfile.ZipFile(os.path.join(tmp, "downloads", "x-code.zip"), "w") as z:
                z.writestr("outputs/summary.csv", b"metric,value\r\nbe,1.53\r\n")
            n, bad = scan(tmp)
        finally:
            shutil.rmtree(tmp)
        print("  --break: one archive member written with a csv writer's default \\r\\n")
    else:
        n, bad = scan(SITE)
    for b in bad:
        print("  CRLF  " + b)
    print(f"  {n} text files and archive members read as bytes: {len(bad)} with CRLF")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
