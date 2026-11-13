"""The public text the armchair page reads, fetched into armchair/data/raw/ and recorded in data/fetched.json.

- plutarch_morals_v3.txt: Project Gutenberg eBook #78851, "Plutarch's essays and miscellanies, Vol. 3 (of 5)",
  ed. W. W. Goodwin (the scanned printing is
  dated 1911). It carries "Of Those Sentiments Concerning Nature With Which Philosophers
  Were Delighted", translated by John Dowel: the Placita, a handbook of the philosophers' opinions on nature
  that the ancient tradition attributes to Plutarch and modern scholarship to a compiler named Aetius
  (first or second century AD). Public domain.

split_placita.py cuts the Placita out of this file into data/placita_dowel.txt with its line numbers.

Run:  python fetch_public.py
"""
from netfetch import fetch

FILES = {
    "plutarch_morals_v3.txt": "https://www.gutenberg.org/cache/epub/78851/pg78851.txt",
}

if __name__ == "__main__":
    for name, url in FILES.items():
        p = fetch(url, name)
        if p.stat().st_size < 500_000:
            raise SystemExit(f"{name}: {p.stat().st_size} bytes, not the volume")
