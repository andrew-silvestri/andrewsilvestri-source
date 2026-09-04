"""Set an image as the Windows desktop wallpaper, reversibly.

    python set_wallpaper.py bookshelf-2560x1440.png     set it
    python set_wallpaper.py --undo                      put the old one back

The contract: before changing anything, the path of the current wallpaper is
saved to undo_wallpaper.json next to this script (only if that file does not
already exist, so repeated runs keep the oldest state). --undo restores it
and deletes the file. Nothing else is written, read, or registered anywhere.
"""
import ctypes
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UNDO = os.path.join(HERE, "undo_wallpaper.json")
SPI_SETDESKWALLPAPER = 20
SPIF_PERSIST = 3  # SPIF_UPDATEINIFILE | SPIF_SENDCHANGE


def current():
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                        r"Control Panel\Desktop") as k:
        return winreg.QueryValueEx(k, "WallPaper")[0]


def set_wall(path):
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER, 0, os.path.abspath(path), SPIF_PERSIST)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    if sys.argv[1] == "--undo":
        if not os.path.exists(UNDO):
            print("nothing to undo: no undo_wallpaper.json here")
            return
        prev = json.load(open(UNDO))["previous"]
        set_wall(prev)
        os.remove(UNDO)
        print(f"restored {prev}")
        return
    img = sys.argv[1]
    if not os.path.exists(img):
        print(f"no such file: {img}")
        return
    if not os.path.exists(UNDO):
        try:
            json.dump({"previous": current()}, open(UNDO, "w"))
        except OSError:
            pass
    set_wall(img)
    print(f"wallpaper set to {os.path.abspath(img)}; "
          "python set_wallpaper.py --undo puts the old one back")


if __name__ == "__main__":
    main()
