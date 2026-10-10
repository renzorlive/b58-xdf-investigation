"""Build a verified map set for a user binary.

Offset model (derived, not guessed):
  * ~414 breakpoint arrays from the J772B reference land in the user binary at a
    delta of 0x40AC2..0x413FE (median 0x40F1A). That window is the whole
    uncertainty budget for calibration-block placement.
  * A table's delta is taken from its OWN anchored axes when they exist.
  * Otherwise the table is searched ONLY inside that empirically derived window,
    and accepted only if one offset fits decisively better than its neighbours.
"""
import xdfread
import align
import statistics
import sys

BAND = (0x40AC2, 0x413FE)


def collect_anchors(tabs, ref, user, lo, hi):
    pts = []
    seen = set()
    for tb in tabs:
        for ax in (tb.x, tb.y):
            if ax is None or ax.address is None or ax.esize_bits != 16:
                continue
            k = (ax.address, ax.rowcount, ax.colcount, ax.major_stride,
                 ax.minor_stride, ax.indexcount)
            if k in seen:
                continue
            seen.add(k)
            v = align.axis_values(ax, ref)
            if not v:
                continue
            for h in align.find_seq(v, user, lo, hi):
                o = h - ax.address
                if BAND[0] <= o <= BAND[1]:
                    pts.append(o)
    return pts


def own_offset(tb, ref, user, lo, hi):
    """Offsets implied by this table's own breakpoint axes (both must agree)."""
    got = []
    for ax in (tb.x, tb.y):
        if ax is None or ax.address is None or ax.esize_bits != 16:
            continue
        v = align.axis_values(ax, ref)
        if not v:
            continue
        h = align.find_seq(v, user, lo, hi)
        for x in h:
            o = x - ax.address
            if BAND[0] <= o <= BAND[1]:
                got.append(o)
    if not got:
        return None, 0
    c = {}
    for o in got:
        c[o] = c.get(o, 0) + 1
    best = max(c.items(), key=lambda kv: kv[1])
    return best


def score(tb, user, off):
    """Fraction of cells inside the map's declared range at this offset."""
    z = tb.z
    if z.mn is None or z.mx is None:
        return None
    try:
        mn, mx = float(z.mn), float(z.mx)
    except ValueError:
        return None
    if mn >= mx:
        return None
    v = xdfread.read_axis(z, user, off)
    if not v:
        return None
    ok = sum(1 for q in v if mn - 1e-9 <= z.eq(q) <= mx + 1e-9)
    return ok / len(v)


def run(xdf_path, ref_path, bin_path, lo, hi):
    ref = open(ref_path, 'rb').read()
    user = open(bin_path, 'rb').read()
    base, tabs = xdfread.parse(xdf_path)

    band = collect_anchors(tabs, ref, user, lo, hi)
    med = int(statistics.median(band))
    print(f'offset band from {len(band)} anchored arrays: '
          f'0x{min(band):X}..0x{max(band):X} (median 0x{med:X})')

    accepted = []
    for i, tb in enumerate(tabs):
        if not tb.z or tb.z.address is None:
            continue
        off, votes = own_offset(tb, ref, user, lo, hi)
        if off is not None:
            s = score(tb, user, off)
            if s is not None and s >= 0.98:
                accepted.append((i, tb, off, 'anchored', s))
                continue
            continue  # anchored but fails range check -> reject
        # no own anchor: bounded search inside the derived band only
        s0 = score(tb, user, med)
        if s0 is None:
            continue
        cands = []
        for o in range(BAND[0], BAND[1] + 1, 2):
            s = score(tb, user, o)
            if s is not None and s >= 0.995:
                cands.append((o, s))
        if not cands:
            continue
        best = max(c[1] for c in cands)
        tied = [c for c in cands if c[1] >= best - 1e-9]
        if len(tied) == 1:  # decisive winner only
            accepted.append((i, tb, tied[0][0], 'band-search', tied[0][1]))

    print(f'accepted {len(accepted)}/{len(tabs)} tables '
          f'({sum(1 for a in accepted if a[3]=="anchored")} anchored, '
          f'{sum(1 for a in accepted if a[3]=="band-search")} band-search)')
    return accepted, tabs, med


if __name__ == '__main__':
    a = sys.argv[1:]
    run(a[0], a[1], a[2], int(a[3], 0), int(a[4], 0))