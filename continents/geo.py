"""Equal Earth, forward and inverse, plus the furniture a world map needs.

Equal Earth (Savric, Patterson and Jenny 2019, International Journal of
Geographical Information Science 33(3), 454-465,
doi:10.1080/13658816.2018.1504949) is used here because every number this
page draws on a map is an area claim: land as a share of the globe, land
within 30 degrees of the equator, the share of the region above 60 N that is
land, the share of the surface two scenarios disagree about. On a projection
that is not equal-area those captions would be false about their own picture.
Do not change the projection without checking every one of them.

The second reason is the pole line. Amasia is a circumpolar northern
landmass - 91 per cent of the region above 60 N is land - and it is the most
distinctive of the four scenarios. Equal Earth's pole line is 59 per cent of
the equator's width, Eckert IV's is 50, and Mollweide's is zero: Mollweide
would smear exactly the thing that distinguishes Amasia from Aurica into a
point, and that pair is the page's "same planet, opposite consequences".

Equal Earth's forward is closed form. Eckert IV and Mollweide both need
Newton iteration in the forward direction, so this is less code, not more.

Extent: x in [-2.7066, 2.7066], y in [-1.3180, 1.3180], aspect 2.0535.
"""
import math

import numpy as np

A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
_SQRT3 = math.sqrt(3.0)

X_MAX = 2.7066299836960743      # forward(180, 0)[0]
Y_MAX = 1.3180373923371969      # forward(0, 90)[1]
ASPECT = X_MAX / Y_MAX


def _y_of_theta(th):
    return A1 * th + A2 * th ** 3 + A3 * th ** 9 + A4 * th ** 11


def _dy_dtheta(th):
    return A1 + 3 * A2 * th ** 2 + 9 * A3 * th ** 8 + 11 * A4 * th ** 10


def forward(lon_deg, lat_deg):
    """Longitude and latitude in degrees to Equal Earth x, y. Vectorised."""
    lo = np.radians(np.asarray(lon_deg, dtype=float))
    la = np.radians(np.asarray(lat_deg, dtype=float))
    th = np.arcsin(np.clip(_SQRT3 / 2.0 * np.sin(la), -1.0, 1.0))
    denom = 3.0 * (9 * A4 * th ** 8 + 7 * A3 * th ** 6 + 3 * A2 * th ** 2 + A1)
    x = 2.0 * _SQRT3 * lo * np.cos(th) / denom
    return x, _y_of_theta(th)


def inverse(x, y, iterations=8):
    """Equal Earth x, y back to longitude and latitude in degrees.

    Returns (lon, lat, inside). y is monotone in theta, so Newton converges
    to better than 1e-12 in about five steps; eight is belt and braces and
    still cheap because the whole panel is done in one vectorised pass.
    Points outside the map body come back with inside False, and their
    lon/lat are meaningless rather than clamped.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    th = np.clip(y / A1, -math.pi / 3.0, math.pi / 3.0)
    for _ in range(iterations):
        th = th - (_y_of_theta(th) - y) / _dy_dtheta(th)
    sin_lat = 2.0 / _SQRT3 * np.sin(th)
    inside = np.abs(sin_lat) <= 1.0
    lat = np.degrees(np.arcsin(np.clip(sin_lat, -1.0, 1.0)))
    denom = 3.0 * (9 * A4 * th ** 8 + 7 * A3 * th ** 6 + 3 * A2 * th ** 2 + A1)
    lon = np.degrees(denom * x / (2.0 * _SQRT3 * np.cos(th)))
    return lon, lat, inside & (np.abs(lon) <= 180.0 + 1e-9)


def limb(n=361):
    """The closed outline of the map body, as x, y arrays."""
    lat = np.linspace(-90.0, 90.0, n)
    xr, yr = forward(np.full(n, 180.0), lat)
    xl, yl = forward(np.full(n, -180.0), lat)
    x = np.concatenate([xr, xl[::-1], xr[:1]])
    y = np.concatenate([yr, yl[::-1], yr[:1]])
    return x, y


def graticule(step=30, n=181):
    """Parallels and meridians every `step` degrees, as a list of x, y pairs."""
    out = []
    for lat in range(-90 + step, 90, step):
        lo = np.linspace(-180.0, 180.0, n)
        out.append(forward(lo, np.full(n, float(lat))))
    for lon in range(-180, 181, step):
        la = np.linspace(-90.0, 90.0, n)
        out.append(forward(np.full(n, float(lon)), la))
    return out


def split_at_seam(lon, lat):
    """Break a lon/lat polyline wherever it crosses the antimeridian.

    Nothing in matplotlib knows what a dateline is: a single segment from
    179 E to 179 W is drawn as a horizontal streak across the whole map,
    which reads as a rendering glitch rather than a data error. Splitting is
    done in lon/lat, before projecting, and yields a list of pieces.
    """
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    if lon.size < 2:
        return [(lon, lat)]
    cut = np.nonzero(np.abs(np.diff(lon)) > 180.0)[0] + 1
    pieces, start = [], 0
    for c in list(cut) + [lon.size]:
        if c - start >= 2:
            pieces.append((lon[start:c], lat[start:c]))
        start = c
    return pieces


def _self_test():
    """Round-trip and the two published extents."""
    assert abs(forward(180.0, 0.0)[0] - X_MAX) < 1e-12
    assert abs(forward(0.0, 90.0)[1] - Y_MAX) < 1e-12
    rng = np.random.default_rng(1)
    lo = rng.uniform(-180, 180, 20000)
    la = rng.uniform(-90, 90, 20000)
    x, y = forward(lo, la)
    lo2, la2, inside = inverse(x, y)
    assert inside.all()
    assert np.abs(lo2 - lo).max() < 1e-9, np.abs(lo2 - lo).max()
    assert np.abs(la2 - la).max() < 1e-9, np.abs(la2 - la).max()
    a, b = split_at_seam([170.0, 175.0, -175.0, -170.0], [0.0, 1.0, 2.0, 3.0])
    assert len(a[0]) == 2 and len(b[0]) == 2
    print(f"geo.py ok  x_max {X_MAX:.10f}  y_max {Y_MAX:.10f}  "
          f"aspect {ASPECT:.4f}  round-trip < 1e-9 on 20,000 points")


if __name__ == "__main__":
    _self_test()
