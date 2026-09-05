# Bookshelf wallpaper

`bookshelf-app.html` is the whole application. Open it in any browser —
double-clicking the file works, no server, no internet. Drop in your
Goodreads export (Goodreads → My Books → Import/Export → Export), set your
screen size, and press Download.

Nothing leaves the page unless you ask it to: the CSV is parsed in the
browser, the shelf is drawn in the browser, and the PNG is written by the
browser. You can pull the network cable first if you want to check. Nothing
is stored between visits.

The CSV is parsed in the browser and never leaves it. The optional cover
mode sends the ISBN of each book that has one to Open Library — nothing else
from your export — and follows its redirect to Internet Archive. One request
per book, with no title, no rating, no cookie, no referrer. An ISBN is a book, and several hundred sent together are a list of
your books, so the box is off until you tick it, switches itself off again
whenever you load a file, and the panel reports what came back: how many
covers, how many books had no ISBN to look up, how many Open Library has no
cover for, how many could not be fetched.

To use the result as your wallpaper, right-click the PNG → Set as desktop
background, or on Windows:

    python set_wallpaper.py bookshelf-2560x1440.png
    python set_wallpaper.py --undo

`--undo` restores whatever wallpaper you had before. The script writes one
file (`undo_wallpaper.json`, next to itself) and nothing else. Removal is
deleting the folder.

Two modes. Drawn spines (the default, fully offline): width from page
count, dress from era, deterministic per title. A book with no page count in
the export is drawn at your library's median width and a book with no year
is dressed plain; the caption counts both. Real covers: tick the box and the
shelf becomes a wall of your books' actual covers, fetched from Open Library
by ISBN as described above, all brought to one matte finish so mixed scans
sit together; a book without a cover is left off rather than faked. There is
no database of photographed book *spines* anywhere, at any scale, which is
why those are the two modes.
