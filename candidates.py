"""Generate and grade candidate table placements for a user binary.

Read-only. Produces candidates with evidence; never edits the verified XDF or BIN.

For each table we test every delta inside the empirically derived band and keep a
placement only when the table's own breakpoint axes read as well-formed arrays.
Each surviving placement is then graded by how the stock->tuned diff interacts
with it, which is independent evidence rather than a plausibility guess.
"""
import sys
import json
import re
from collections import Counter, defaultdict
import xdfread

BAND = (0x3EC00, 0x41800)
MIN_PTS = 4


def read_u16(data, addr, n):
    if addr < 0 or addr + n * 2 > len(data):
        return None
    return [int.from_bytes(data[addr + i * 2:addr + i * 2 + 2], 'big') for i in range(n)]


def axis_ok(v):
    if not v or len(v) < MIN_PTS or len(set(v)) < MIN_PTS:
        return False
    if v[0] < 0 or v[-1] > 20000:
        return False
    return all(v[i] < v[i + 1] for i in range(len(v) - 1))


def cells_ok(z, user, delta):
    """All data cells inside the declared range (when the range is meaningful)."""
    if z.mn is None or z.mx is None:
        return None
    try:
        mn, mx = float(z.mn), float(z.mx)
    except ValueError:
        return None
    if not (mn > -1000 and mx > mn):
        return None           # uninformative declared range (-32768..32767)
    r, c = z.shape()
    if not r or not c or r * c > 4096:
        return None
    v = read_u16(user, z.address + delta, r * c) if z.esize_bits == 16 else None
    if v is None:
        return None
    return all(mn - 1e-9 <= z.eq(q) <= mx + 1e-9 for q in v)


def analyse(xdf_path, bin_path, mod_path):
    base, tabs = xdfread.parse(xdf_path)
    ori = open(bin_path, 'rb').read()
    mod = open(mod_path, 'rb').read()
    diff = set(i for i in range(len(ori)) if ori[i] != mod[i])

    out = []
    for tb in tabs:
        if 'autogen' in (tb.title or '') or not tb.z or tb.z.address is None:
            continue
        z = tb.z
        r, c = z.shape()
        if not r or not c or r * c > 4096 or z.esize_bits != 16:
            continue
        axn = {}
        for role, ax in (('x', tb.x), ('y', tb.y)):
            if ax is None or ax.address is None or ax.esize_bits != 16:
                continue
            n = ax.colcount or ax.indexcount if role == 'x' else ax.rowcount or ax.indexcount
            if not n or n < MIN_PTS or n > 64 or ax.major_stride or ax.minor_stride:
                continue
            axn[role] = (ax, n)
        if not axn:
            continue

        cand = set()
        detail = {}
        for role, (ax, n) in axn.items():
            ds = set()
            for d in range(BAND[0], BAND[1] + 1, 2):
                if axis_ok(read_u16(ori, ax.address + d, n)):
                    ds.add(d)
            detail[role] = ds
            cand |= ds
        if not cand:
            continue
        both = detail.get('x', set()) & detail.get('y', set()) if len(detail) == 2 else None
        if both:
            cand = both

        scored = []
        for d in sorted(cand):
            st = z.address + d
            if st < 0 or st + z.byte_span() > len(ori):
                continue
            nbytes = z.byte_span()
            nd = sum(1 for k in range(st, st + nbytes) if k in diff)
            scored.append((nd, d))
        if not scored:
            continue
        scored.sort(reverse=True)
        nd, d = scored[0]
        if nd == 0:
            continue                    # tuner never touched it -> no diff evidence
        ok = cells_ok(z, ori, d)
        if ok is False:
            continue
        out.append(dict(title=tb.title, desc=tb.desc, delta=hex(d),
                        user_addr=hex(z.address + d), rows=r, cols=c,
                        esize=16, mn=z.mn, mx=z.mx,
                        axes={k: hex(v[0].address + d) for k, v in axn.items()},
                        axis_pts={k: v[1] for k, v in axn.items()},
                        eq_defined=ok is True, tuned=nd, size=z.byte_span(),
                        cats=tb.categories))
    return out, tabs


if __name__ == '__main__':
    xdf, binf, modf = sys.argv[1], sys.argv[2], sys.argv[3]
    res, tabs = analyse(xdf, binf, modf)
    res.sort(key=lambda r: -r['tuned'])
    print(f'{len(res)} candidate placements with diff evidence (of {len(tabs)} tables)\n')
    json.dump(res, open('out/candidates_R1C9J772B.json', 'w'), indent=1)
    print('%-46s %-24s %-10s %4s %5s %s' % ('title', 'bosch var', '@user', 'rows', 'tuned', 'size'))
    for r in res:
        print('%-46s %-24s %-10s %2dx%-3d %5d %5d %s' %
              (r['title'][:46], r['desc'][:24], r['user_addr'], r['rows'], r['cols'],
               r['tuned'], r['size'], '' if r['eq_defined'] is not False else 'RANGE-FAIL'))