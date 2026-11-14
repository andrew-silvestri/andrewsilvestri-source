"""Read-only, seekable file object over HTTP range requests.

figshare's ndownloader returns a 302 to a presigned object-store URL that
expires after ~10 s, so every read re-requests the ndownloader URL and lets
requests follow the redirect. Blocks are cached so h5py's many small metadata
reads do not each cost a round trip.
"""
import io
import requests


class HTTPRangeFile(io.RawIOBase):
    def __init__(self, url, block=1 << 20, max_blocks=512):
        self.url = url
        self.block = block
        self.max_blocks = max_blocks
        self.s = requests.Session()
        r = self.s.get(url, headers={"Range": "bytes=0-0"}, timeout=60)
        r.raise_for_status()
        self.size = int(r.headers["Content-Range"].split("/")[-1])
        self.pos = 0
        self.cache = {}
        self.bytes_fetched = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos

    def _fetch(self, b0, b1):
        """Fetch blocks b0..b1 inclusive in one request."""
        lo, hi = b0 * self.block, min((b1 + 1) * self.block, self.size) - 1
        for attempt in range(5):
            try:
                r = self.s.get(self.url, headers={"Range": f"bytes={lo}-{hi}"}, timeout=120)
                r.raise_for_status()
                data = r.content
                if len(data) == hi - lo + 1:
                    break
            except requests.RequestException:
                if attempt == 4:
                    raise
        self.bytes_fetched += len(data)
        if len(self.cache) > self.max_blocks:
            self.cache.clear()
        for b in range(b0, b1 + 1):
            o = (b - b0) * self.block
            self.cache[b] = data[o:o + self.block]

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        n = min(n, self.size - self.pos)
        if n <= 0:
            return b""
        b0, b1 = self.pos // self.block, (self.pos + n - 1) // self.block
        missing = [b for b in range(b0, b1 + 1) if b not in self.cache]
        if missing:
            # Fetch the whole span: _fetch may clear the cache, which would drop blocks of
            # this span that were cached before the call.
            self._fetch(b0, b1)
        buf = b"".join(self.cache[b] for b in range(b0, b1 + 1))
        o = self.pos - b0 * self.block
        out = buf[o:o + n]
        self.pos += len(out)
        return out

    def readinto(self, b):
        d = self.read(len(b))
        b[:len(d)] = d
        return len(d)
