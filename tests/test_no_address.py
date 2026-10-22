"""No personal email address anywhere the site ships (D-30, D-43).

Reads every file under site/ as bytes - pages, scripts, the CV PDF with its
streams inflated, and every member of every archive in site/downloads/ - and
fails on a gmail.com or utexas.edu address in plain, URL-encoded (%40, %2E)
or HTML-entity (&#64;) form. Matched by domain so this file names no address;
third-party addresses (NIST's, in meter's AGA8 sources) are other domains.

Why it exists: beauty-code.zip shipped the Gmail address five times inside
recorded OpenAlex request URLs and the utexas address in four fetch scripts,
About carried a mailto link, and the CV PDF carried a mailto annotation. None
of the checks then read file content for this. rezip_downloads.py refuses to
write such an archive; this covers the rest of site/ and an archive built
some other way.

    python tests/test_no_address.py           exit 1 on any hit
    python tests/test_no_address.py --break   plant the historical case (a
                                              recorded URL with mailto=...%40gmail.com,
                                              inside a zip) in a copy; must exit 1
"""
import io
import os
import re
import shutil
import sys
import tempfile
import zipfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(os.path.dirname(HERE), "site")
# Same pattern as rezip_downloads.PERSONAL; kept apart so a change to one is
# not silently a change to both.
PERSONAL = re.compile(rb"[A-Za-z0-9._%+-]+(?:@|%40|&#0*64;|&#x0*40;)(?:gmail|utexas)(?:\.|%2e)(?:com|edu)\b",
                      re.I)
SKIP_DIRS = {"_preview"}   # gitignored option renderings; publish.sh deletes them from the mirror


def inflate_pdf(b):
    parts = [b]
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", b, re.S):
        try:
            parts.append(zlib.decompress(m.group(1)))
        except zlib.error:
            pass
    return b"\n".join(parts)


def scan(name, b, hits):
    if b[:4] == b"PK\x03\x04":
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            for n in z.namelist():
                scan(name + "!" + n, z.read(n), hits)
        return
    if b[:5] == b"%PDF-":
        b = inflate_pdf(b)
    c = len(PERSONAL.findall(b))
    if c:
        hits.append((name, c))


def run(root):
    hits, n = [], 0
    for d, ds, fs in os.walk(root):
        ds[:] = [x for x in ds if x not in SKIP_DIRS]
        for f in fs:
            p = os.path.join(d, f)
            n += 1
            with open(p, "rb") as fh:
                scan(os.path.relpath(p, root), fh.read(), hits)
    return n, hits


def main():
    if "--break" in sys.argv:
        tmp = tempfile.mkdtemp()
        try:
            root = os.path.join(tmp, "site")
            os.makedirs(os.path.join(root, "downloads"))
            row = (b"group,url\nBirds,https://api.openalex.org/works?filter=x&per-page=1"
                   b"&mailto=someone%40gmail.com\n")
            with zipfile.ZipFile(os.path.join(root, "downloads", "x-code.zip"), "w",
                                 zipfile.ZIP_DEFLATED) as z:
                z.writestr("data/group_counts.csv", row)
            n, hits = run(root)
        finally:
            shutil.rmtree(tmp)
        print(f"  --break: planted a recorded URL with an encoded address inside a zip; {len(hits)} hit(s)")
    else:
        n, hits = run(SITE)
    for name, c in hits:
        print(f"  HIT x{c}  {name}")
    print(f"  {n} files under site/ read (archives opened, PDFs inflated): "
          f"{sum(c for _, c in hits)} personal address(es)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
