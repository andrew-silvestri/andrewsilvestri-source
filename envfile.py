"""Read a named setting from the environment, or from the user's .env file.

Keys live in C:\\Users\\dasil\\.env, outside every repository (D-42). This
returns the value of ONE named variable and never prints, logs or returns
anything else from the file. ENV_FILE overrides the path. A value already in
the environment wins over the file.
"""
import os

DEFAULT = os.path.join(os.path.expanduser("~"), ".env")


def get(name, default=""):
    v = os.environ.get(name, "").strip()
    if v:
        return v
    path = os.environ.get("ENV_FILE", DEFAULT)
    try:
        with open(path, encoding="utf-8-sig") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("export "):
                    line = line[7:].lstrip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == name:
                    v = v.strip()
                    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                        v = v[1:-1]
                    return v.strip()
    except OSError:
        pass
    return default
