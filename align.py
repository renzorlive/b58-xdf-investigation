"""Re-anchor an XDF onto a user binary by locating breakpoint axes by content (tolerant)."""
import xdfread
import os
from collections import defaultdict


def axis_values(ax, ref):
    """Values of an axis read from a reference binary, in stored order."""
    if ax is None or ax.address is None or ax.esize_bits != 16:
        return None
    r, c = ax.shape()
    n = max(r * c, ax.indexcount or 0)
    if n < 2 or n > 512:
        return None
    if ax.major_stride or ax.minor_stride:
        ms = ax.major_stride // 8 or 2
        ns = ax.minor_stride // 8 or 2
        out = []
        for cc in range(c):
            for rr in range(r):
                o = ax.address + cc * ms + rr * ns
                if o + 2 > len(ref):
                    return None
                out.append(int.from_bytes(ref[o:o + 2], 'big'))
        return out
    o = ax.address
    if o + n * 2 > len(ref):
        return None
    return [int.from_bytes(ref[o + i * 2:o + i * 2 + 2], 'big') for i in range(n)]


def find_seq(vals, user, lo, hi, minrun=8):
    """Find a uint16 sequence in user[lo:hi]. Returns list of start offsets (absolute).
    Requires at least one run of minrun consecutive equal values, then verifies the rest."""
    n = len(vals)
    need = min(minrun, n)
    # pick the most distinctive window: the longest run of values that repeats elsewhere
    best = None
    for start in range(0, n - need + 1):
        win = vals[start:start + need]
        pat = b''.join(v.to_bytes(2, 'big') for v in win)
        c = user.count(pat, lo, hi)
        if c == 0:
            continue
        if best is None or c < best[0]:
            best = (c, start, pat)
        if c == 1:
            break
    if best is None:
        return []
    _, start, pat = best
    hits = []
    p = lo
    while True:
        i = user.find(pat, p, hi)
        if i < 0:
            break
        base = i - start * 2
        if base >= lo and base + n * 2 <= hi:
            ok = all(int.from_bytes(user[base + k * 2:base + k * 2 + 2], 'big') == vals[k]
                     for k in range(n))
            if ok:
                hits.append(base)
        p = i + 2
        if len(hits) > 64:
            break
    return hits


def main(xdf_path, ref_path, bin_path, lo, hi, minrun=8, require_both=True):
    ref = open(ref_path, 'rb').read()
    user = open(bin_path, 'rb').read()
    base, tabs = xdfread.parse(xdf_path)
    cache = {}

    def find_ax(ax):
        if ax is None or ax.address is None:
            return []
        k = (ax.address, ax.rowcount, ax.colcount, ax.major_stride, ax.minor_stride, ax.indexcount)
        if k not in cache:
            v = axis_values(ax, ref)
            cache[k] = find_seq(v, user, lo, hi, minrun) if v else []
        return cache[k]

    out = []
    n_ok = n_both = n_partial = 0
    for tb in tabs:
        hx = find_ax(tb.x)
        hy = find_ax(tb.y)
        ox = {h - tb.x.address for h in hx} if (hx and tb.x) else set()
        oy = {h - tb.y.address for h in hy} if (hy and tb.y) else set()
        both = ox & oy
        if both:
            off = sorted(both)[0]
            n_both += 1
            out.append((tb, off, 'both'))
        elif not require_both and (ox or oy):
            off = sorted(ox or oy)[0]
            n_partial += 1
            out.append((tb, off, 'partial'))
        else:
            out.append((tb, None, 'none'))
        n_ok += 1
    print(f'{os.path.basename(xdf_path)}: both-axes {n_both}, partial {n_partial}, none {n_ok-n_both-n_partial} / {n_ok}')
    return out, base


if __name__ == '__main__':
    import sys
    main(sys.argv[1], sys.argv[2], sys.argv[3],
         int(sys.argv[4], 0), int(sys.argv[5], 0))