"""Derive a calibration-block delta band for an XDF that has no paired stock dump.

Method: every table with a real breakpoint axis should, at the correct delta, read
back as a well-formed breakpoint array (finite, ascending, non-negative). Deltas that
satisfy that across many independent tables are the physical placement. Deltas are
never assumed - they are counted.
"""
import sys
from collections import Counter
import xdfread

BAND_LO = 0x3E000
BAND_HI = 0x44000
MIN_PTS = 4


def axis_ok(vals):
    if not vals or len(vals) < MIN_PTS:
        return False
    if any(v is None for v in vals):
        return False
    if vals[0] < 0 or vals[-1] > 20000:
        return False
    if any(vals[i] >= vals[i + 1] for i in range(len(vals) - 1)):
        return False
    return len(set(vals)) >= MIN_PTS


def read_u16(data, addr, n):
    if addr < 0 or addr + n * 2 > len(data):
        return None
    return [int.from_bytes(data[addr + i * 2:addr + i * 2 + 2], 'big') for i in range(n)]


def scan(xdf_path, bin_path, lo=BAND_LO, hi=BAND_HI, step=2):
    base, tabs = xdfread.parse(xdf_path)
    user = open(bin_path, 'rb').read()
    hits = Counter()
    used = 0
    for tb in tabs:
        if 'autogen' in (tb.title or ''):
            continue
        ax = tb.x
        if ax is None or ax.address is None or ax.esize_bits != 16:
            continue
        n = ax.colcount or ax.indexcount
        if not n or n < MIN_PTS or n > 64:
            continue
        if ax.major_stride or ax.minor_stride:
            continue
        used += 1
        for d in range(lo, hi + 1, step):
            if axis_ok(read_u16(user, ax.address + d, n)):
                hits[d] += 1
    return hits, used


if __name__ == '__main__':
    xdf, binf = sys.argv[1], sys.argv[2]
    hits, used = scan(xdf, binf)
    print(f'tables with a usable x-axis: {used}')
    tot = sum(hits.values())
    print(f'deltas passing axis validity: {len(hits)} distinct, {tot} votes')
    best = hits.most_common(25)
    for d, c in best:
        print('  delta +0x%05X  votes=%d' % (d, c))