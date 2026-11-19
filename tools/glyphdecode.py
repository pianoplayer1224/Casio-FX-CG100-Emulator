#!/usr/bin/env python3
"""Decode photos of calc/cgglyph.py into glyph bitmaps.

    python3 tools/glyphdecode.py        bm_core_videos/9  -> glyphs.json
    python3 tools/glyphdecode.py 10     bm_core_videos/10 -> glyphs10.json

Each page shows magnified glyphs in tiles. The photo is straightened from
the bright panel's corners (status bar included), tiles are found by
colour, and a perspective fit from every tile's left corners (known screen
positions, given the tile pitch) places the sampling grid. Each tile is
snapped by whole blocks to its own grey box's left/top edge, then
finds its own offset (under half a block, absorbing lens distortion), and
each magnified pixel is read as the mean over its central half rather than
one point. Tile pitch = blocks x magnification + 3: small 31x43, medium
45x54, large 37x49. The grey advance boxes are too faint in photos to read;
advances come from cgglyph's printed tables. emu/cgfont_calc.json takes,
per glyph, whichever batch's decode better matches both photos, plus a few
hand fixes ("source" in it lists them). Also saves
straightened tile crops (*_crops.npy) for reviewing glyphs by eye.
"""
import json, sys, numpy as np
from PIL import Image, ImageOps
from scipy import ndimage

PAGES = {  # photo -> (size, first code, last code)
    "20261030_143931": ("small", 32, 79), "20261030_144250": ("small", 80, 126),
    "20261030_144309": ("medium", 32, 55), "20261030_144344": ("medium", 56, 79),
    "20261030_144404": ("medium", 80, 103), "20261030_144440": ("large", 32, 61),
    "20261030_144451": ("large", 62, 91), "20261030_144501": ("large", 122, 126)}
MAG = {"small": 4, "medium": 3, "large": 2}
K, PAD = 8, 16   # coarse image: K px per canvas px, PAD canvas px margin

def persp(src, dst, affine=False):
    if affine:
        A = [[x, y, 1] for x, y in src]
        cu = np.linalg.lstsq(np.array(A, float), np.array([d[0] for d in dst], float), rcond=None)[0]
        cv = np.linalg.lstsq(np.array(A, float), np.array([d[1] for d in dst], float), rcond=None)[0]
        return np.array([cu[0], cu[1], cu[2], cv[0], cv[1], cv[2], 0, 0])
    A, B = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.lstsq(np.array(A, float), np.array(B, float), rcond=None)[0]

def apply(c, x, y):
    d = c[6] * x + c[7] * y + 1
    return (c[0] * x + c[1] * y + c[2]) / d, (c[3] * x + c[4] * y + c[5]) / d

def coarse(path):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    g = np.asarray(im.convert("L"), dtype=np.float32)[::4, ::4]
    mask = g > np.percentile(g, 75) * 0.9
    lab, n = ndimage.label(mask)
    big = ndimage.binary_fill_holes(lab == np.argmax(ndimage.sum(mask, lab, range(1, n + 1))) + 1)
    ys, xs = np.nonzero(big); xs = xs * 4.0; ys = ys * 4.0
    s1, s2 = xs - ys, xs + ys
    tl = (xs[np.argmin(s1)], ys[np.argmin(s1)]); br = (xs[np.argmax(s1)], ys[np.argmax(s1)])
    tr = (xs[np.argmin(s2)], ys[np.argmin(s2)]); bl = (xs[np.argmax(s2)], ys[np.argmax(s2)])
    wpx = np.hypot(tr[0] - tl[0], tr[1] - tl[1]); hpx = np.hypot(bl[0] - tl[0], bl[1] - tl[1])
    H = 216   # the bright area is the whole panel, status bar included
    c = persp([(0, 0), (384, 0), (384, H), (0, H)], [tl, tr, br, bl])
    # output pixel -> canvas (u/K - PAD) -> photo
    W2, H2 = (384 + 2 * PAD) * K, (H + 2 * PAD) * K
    S = np.array([[1 / K, 0, -PAD], [0, 1 / K, -PAD], [0, 0, 1]])
    Hm = np.array([[c[0], c[1], c[2]], [c[3], c[4], c[5]], [c[6], c[7], 1]]) @ S
    Hm /= Hm[2, 2]
    out = im.transform((W2, H2), Image.PERSPECTIVE, tuple(Hm.flatten()[:8]), Image.BICUBIC)
    return np.asarray(out, dtype=float), H

def classify(im):
    v = im.mean(axis=2)
    bg = ndimage.maximum_filter(ndimage.uniform_filter(v, 25), 151)
    r = ndimage.uniform_filter(v / bg, 3)
    br = ndimage.uniform_filter(im[..., 2], 9) / np.maximum(ndimage.uniform_filter(im[..., 0], 9), 1)
    black = r < 0.5
    white = np.median(br[r > 0.95])   # tint of white differs per photo
    grey = (br > white + 0.09) & ~black
    return r, br, black, grey

def boxes(black, grey):
    m = ndimage.binary_opening(grey | black, iterations=3)
    lab, n = ndimage.label(m)
    out = []
    for sl in ndimage.find_objects(lab):
        out.append((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop))  # x0,y0,x1,y1
    return out

GRID = {}

def sharpness(c, r, tw, th, m, n):
    """Mean distance from the black/white threshold at block centres: high
    when the sampling grid sits on the magnified pixels."""
    key = (tw, th, m, n)
    if key not in GRID:
        cols = 384 // tw; Hb = (th - 3) // m; Wb = (tw - 3) // m
        k = np.arange(n)[:, None, None]; j = np.arange(Hb)[None, :, None]; i = np.arange(Wb)[None, None, :]
        X = (k % cols) * tw + (i + 0.5) * m + 0 * j
        Y = 12 + (k // cols) * th + (j + 0.5) * m + 0 * i
        GRID[key] = (X.ravel().astype(float), Y.ravel().astype(float))
    X, Y = GRID[key]
    d = c[6] * X + c[7] * Y + 1
    u = np.rint((c[0] * X + c[1] * Y + c[2]) / d).astype(int)
    v = np.rint((c[3] * X + c[4] * Y + c[5]) / d).astype(int)
    ok = (u >= 0) & (v >= 0) & (u < r.shape[1]) & (v < r.shape[0])
    return float(np.mean(np.abs(r[v[ok], u[ok]] - 0.5))) if ok.any() else 0.0

def edge_offset(c, im, tx, ty, tw, th):
    """Offset (screen px) of a tile's grey box from where the page fit puts
    it: first column / row where the box (grey or ink) covers the tile."""
    gy, gx = np.mgrid[0:(th + 12) * 4, 0:(tw + 12) * 4] / 4.0
    X = tx - 6 + gx; Y = ty - 6 + gy
    d = c[6] * X + c[7] * Y + 1
    xi = np.clip(np.rint((c[0] * X + c[1] * Y + c[2]) / d).astype(int), 0, im.shape[1] - 1)
    yi = np.clip(np.rint((c[3] * X + c[4] * Y + c[5]) / d).astype(int), 0, im.shape[0] - 1)
    v = im[yi, xi].mean(axis=2)
    white = np.percentile(v, 95)
    dark = v < 0.88 * white
    H, W = v.shape
    # rows/columns well inside the tile, away from the neighbouring tiles
    col = dark[int(4 * (6 + th * 0.2)):int(4 * (6 + th * 0.8)), :].mean(axis=0)
    row = dark[:, int(4 * (6 + tw * 0.05)):int(4 * (6 + tw * 0.3))].mean(axis=1)
    c0 = int(4 * 4.5)   # start in the 3 px gap before the tile, past the neighbour
    x = c0 + np.argmax(col[c0:] > 0.6); y = c0 + np.argmax(row[c0:] > 0.6)
    return x / 4.0 - 6, y / 4.0 - 6

def boxmean(II, yi, xi, h):
    """Mean of r over (2h+1)^2 boxes centred on (yi, xi), from the integral image."""
    y0 = np.clip(yi - h, 0, II.shape[0] - 1); y1 = np.clip(yi + h + 1, 0, II.shape[0] - 1)
    x0 = np.clip(xi - h, 0, II.shape[1] - 1); x1 = np.clip(xi + h + 1, 0, II.shape[1] - 1)
    s = II[y1, x1] - II[y0, x1] - II[y1, x0] + II[y0, x0]
    return s / np.maximum((y1 - y0) * (x1 - x0), 1)

TILE = {}
CROPS = {}
SNAP = []
WHITE = [1.0]
FORCE = {}
# tile pitch: width from the reliable horizontal scale, height from the
# published glyph heights (small 10, medium 16, large 22 rows)
CAND = {"small": [(31, 43)], "medium": [(45, 54)], "large": [(37, 49)]}

def decode(path, size, first, last):
    im, Hc = coarse(path)
    r, br, black, grey = classify(im)
    V = ndimage.uniform_filter(im.mean(axis=2), 5)
    WHITE[0] = np.median(br[r > 0.95])
    m = MAG[size]
    B = [b for b in boxes(black, grey) if b[3] - b[1] > 4 * m * K]
    hts = np.array([b[3] - b[1] for b in B]); hmed = np.median(hts)
    B = [b for b in B if abs((b[3] - b[1]) - hmed) < 0.15 * hmed]
    # rows by y
    B.sort(key=lambda b: b[1])
    rows = [[B[0]]]
    for b in B[1:]:
        if b[1] - rows[-1][-1][1] > hmed * 0.5: rows.append([b])
        else: rows[-1].append(b)
    rows = [sorted(rw, key=lambda b: b[0]) for rw in rows]
    n = last - first + 1
    best = None
    for tw, th in CAND[size]:
        Hb = (th - 3) // m
        src, dst = [], []
        for ri, rw in enumerate(rows):
            for b in rw:
                ci = int(round((b[0] / K - PAD) / tw))
                tx, ty = ci * tw, 12 + ri * th
                src += [(tx, ty), (tx, ty + Hb * m)]
                dst += [(b[0], b[1]), (b[0], b[3])]
        aff = len(rows) == 1
        c = persp(src, dst, aff)
        for it in range(3):
            res = [np.hypot(*(np.array(apply(c, *s_)) - d)) for s_, d in zip(src, dst)]
            keep = [i for i, e in enumerate(res) if e < max(2.5 * np.median(res), 4)]
            c = persp([src[i] for i in keep], [dst[i] for i in keep], aff)
        res = np.median([np.hypot(*(np.array(apply(c, *s_)) - d)) for s_, d in zip(src, dst)])
        sharp = sharpness(c, r, tw, th, m, last - first + 1)
        print("    candidate %dx%d residual %.1f sharpness %.3f" % (tw, th, res, sharp))
        if best is None or sharp > best[0]:
            best = (sharp, tw, th, c)
    res, tw, th, c = best if FORCE.get(size) is None else FORCE[size](rows, m)
    # refine: shift and scale the canvas grid by fractions of a pixel so the
    # samples land on the magnified pixels
    def shifted(c, dx, dy, sx, sy):
        # canvas (x, y) -> photo via c at (x*sx + dx, y*sy + dy)
        return np.array([c[0] * sx, c[1] * sy, c[0] * dx + c[1] * dy + c[2],
                         c[3] * sx, c[4] * sy, c[3] * dx + c[4] * dy + c[5],
                         c[6] * sx, c[7] * sy, 0]), (c[6] * dx + c[7] * dy + 1)
    def warp(dx, dy, sx, sy):
        n_, d = shifted(c, dx, dy, sx, sy)
        return np.array(list(n_[:6] / d) + list(n_[6:8] / d))
    bestr = (res, 0.0, 0.0, 1.0, 1.0)
    for sx in (0.99, 0.995, 1.0, 1.005, 1.01):
        for sy in (0.99, 0.995, 1.0, 1.005, 1.01):
            lim = m / 2 - 0.25   # stay within half a block
            for dx in np.arange(-lim, lim + 0.01, 0.25):
                for dy in np.arange(-lim, lim + 0.01, 0.25):
                    sh = sharpness(warp(dx, dy, sx, sy), r, tw, th, m, last - first + 1)
                    if sh > bestr[0]:
                        bestr = (sh, dx, dy, sx, sy)
    print("   refined sharpness %.4f at shift %.2f,%.2f scale %.3f,%.3f" % bestr)
    c = warp(*bestr[1:])
    Hb = (th - 3) // m; Wb = (tw - 3) // m; cols = 384 // tw
    TILE[size] = (tw, th)
    print("%s %s %d-%d: tile %dx%d, %d x %d blocks, %d cols; sharpness %.4f (block %d px)" % (path[-19:], size, first, last, tw, th, Wb, Hb, cols, res, m * K))
    II = np.pad(r, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    samples = []
    for k in range(n):
        tx, ty = (k % cols) * tw, 12 + (k // cols) * th
        # snap the tile to its own grey box: where the box's left and top
        # edges are, in whole blocks, relative to the page fit
        sx, sy = edge_offset(c, im, tx, ty, tw, th)
        tx += int(round(sx / m)) * m; ty += int(round(sy / m)) * m
        SNAP.append((int(round(sx / m)), int(round(sy / m))))
        tint = np.zeros((Hb, Wb))
        # each block: mean over its central half; the tile's own offset
        # (within 0.4 block) is the one whose blocks are most clearly
        # black or white, absorbing lens distortion across the page
        hw = max(2, int(m * K * 0.25))
        jj, ii = np.mgrid[0:Hb, 0:Wb]
        best = None
        for oy in np.arange(-0.4, 0.41, 0.1) * m:
            for ox in np.arange(-0.4, 0.41, 0.1) * m:
                X = tx + (ii + 0.5) * m + ox; Y = ty + (jj + 0.5) * m + oy
                d = c[6] * X + c[7] * Y + 1
                xi = np.rint((c[0] * X + c[1] * Y + c[2]) / d).astype(int)
                yi = np.rint((c[3] * X + c[4] * Y + c[5]) / d).astype(int)
                v = boxmean(II, yi, xi, hw)
                sc = np.abs(v - 0.5).mean()
                if best is None or sc > best[0]:
                    best = (sc, v)
        rv = best[1]
        ink = (rv < 0.5).astype(int)
        # straightened crop of the tile (4 px per screen px) for review
        gy, gx = np.mgrid[0:(th + 12) * 8, 0:(tw + 12) * 8] / 8.0
        X = tx - 6 + gx; Y = ty - 6 + gy
        d = c[6] * X + c[7] * Y + 1
        xi = np.clip(np.rint((c[0] * X + c[1] * Y + c[2]) / d).astype(int), 0, im.shape[1] - 1)
        yi = np.clip(np.rint((c[3] * X + c[4] * Y + c[5]) / d).astype(int), 0, im.shape[0] - 1)
        CROPS[(size, first + k)] = im[yi, xi].astype(np.uint8)
        # local white: the 3 px gaps right of and below the tile
        ref = []
        for jj in range(Hb):
            x, y = apply(c, tx + tw - 1.5, ty + (jj + 0.5) * m); ref.append(V[int(round(y)), int(round(x))])
        for ii in range(Wb):
            x, y = apply(c, tx + (ii + 0.5) * m, ty + th - 1.5); ref.append(V[int(round(y)), int(round(x))])
        wv = np.percentile(ref, 70)
        for jj in range(Hb):
            for ii in range(Wb):
                x, y = apply(c, tx + (ii + 0.5) * m, ty + (jj + 0.5) * m)
                tint[jj, ii] = V[int(round(y)), int(round(x))] / wv
        samples.append((ink, tint, rv))
    # grey vs white per tile column: median brightness (relative to the
    # local white) of its blocks without ink, split into two clusters
    def colv(ink, tint):
        return [np.median(tint[ink[:, i] == 0, i]) if (ink[:, i] == 0).any() else np.nan
                for i in range(tint.shape[1])]
    t = np.array([v for ink, tint, rv in samples for v in colv(ink, tint)])
    t = t[~np.isnan(t)]
    lo, hi = np.percentile(t, 10), np.percentile(t, 90)
    for it in range(20):
        cut = (lo + hi) / 2
        lo, hi = t[t < cut].mean(), t[t >= cut].mean()
    cut = (lo + hi) / 2
    print("   grey %.3f, white %.3f of local white" % (lo, hi))
    out = {}
    for k, (ink, tint, rv) in enumerate(samples):
        cv = colv(ink, tint)
        adv = 0
        while adv < Wb and (np.isnan(cv[adv]) or cv[adv] < cut):
            adv += 1
        out[first + k] = {"adv_cols": adv, "rows": ["".join("#" if v else "." for v in row) for row in ink],
                          "val": [[round(float(v), 2) for v in row] for row in rv],
                          "margin": float(np.min(np.abs(rv - 0.5)))}
    return out

PAGES10 = {
    "20261030_150924": ("small", 32, 79), "20261030_150941": ("small", 80, 126),
    "20261030_151017": ("medium", 32, 55), "20261030_151029": ("medium", 56, 79),
    "20261030_151036": ("medium", 80, 103), "20261030_151042": ("medium", 104, 126),
    "20261030_151114": ("large", 32, 61), "20261030_151123": ("large", 62, 91),
    "20261030_151132": ("large", 92, 121), "20261030_151136": ("large", 122, 126)}

def main(pages=PAGES, folder="9", out="glyphs.json"):
  res = {}
  for name, (size, a, b) in pages.items():
      res.setdefault(size, {}).update(decode("/home/ray/Documents/FX-GC100/bm_core_videos/%s/%s.jpg" % (folder, name), size, a, b))
  json.dump(res, open(out, "w"), indent=0)
  import collections
  print("tile snaps (blocks):", dict(collections.Counter(SNAP)))
  np.save(out.replace(".json", "_crops.npy"), np.array([{"%s/%d" % k: v for k, v in CROPS.items()}], dtype=object))

if __name__ == "__main__":
  if sys.argv[1:] == ["10"]:
    main(PAGES10, "10", "glyphs10.json")
  else:
    main()
