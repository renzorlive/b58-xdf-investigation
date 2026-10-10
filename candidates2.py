"""Candidate placement with sub-block delta disambiguation.

Stage 1  collect every delta in the band for which a table's own breakpoint axes
         both read as well-formed arrays and its data sits in a meaningful
         declared range.
Stage 2  tables with exactly one surviving delta are CONFIRMED.
Stage 3  delta is piecewise constant across the calibration block, so fit the
         confirmed tables into runs and interpolate a predicted delta for the
         rest (nearest confirmed neighbour in XDF address space).
Stage 4  an ambiguous table is only accepted if its own candidate set contains the
         delta predicted for its position.

Ambiguous tables are reported separately; they are never silently accepted.
"""
import sys
import json
import bisect
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


def range_ok(z, user, d):
    if z.mn is None or z.mx is None:
        return None
    try:
        mn, mx = float(z.mn), float(z.mx)
    except ValueError:
        return None
    if not (mn > -1000 and mx > mn):
        return None
    r, c = z.shape()
    if not r or not c or r * c > 4096:
        return None
    v = read_u16(user, z.address + d, r * c)
    if v is None:
        return None
    return all(mn - 1e-9 <= z.eq(q) <= mx + 1e-9 for q in v)


def axes_of(tb):
    out = {}
    for role, ax, n in (('x', tb.x, None), ('y', tb.y, None)):
        if ax is None or ax.address is None or ax.esize_bits != 16:
            continue
        if ax.major_stride or ax.minor_stride:
            continue
        cnt = (ax.colcount or ax.indexcount) if role == 'x' else (ax.rowcount or ax.indexcount)
        if not cnt or cnt < MIN_PTS or cnt > 64:
            continue
        out[role] = (ax, cnt)
    return out


def analyse(xdf_path, bin_path, mod_path):
    base, tabs = xdfread.parse(xdf_path)
    ori = open(bin_path, 'rb').read()
    mod = open(mod_path, 'rb').read()
    diff = set(i for i in range(len(ori)) if ori[i] != mod[i])

    items = []
    for tb in tabs:
        if 'autogen' in (tb.title or '') or not tb.z or tb.z.address is None:
            continue
        z = tb.z
        r, c = z.shape()
        if z.esize_bits != 16 or not r or not c or r * c > 4096:
            continue
        axn = axes_of(tb)
        if not axn:
            continue
        ds = None
        for role, (ax, n) in axn.items():
            s = {d for d in range(BAND[0], BAND[1] + 1, 2)
                 if axis_ok(read_u16(ori, ax.address + d, n))}
            ds = s if ds is None else (ds & s)
        if not ds:
            continue
        good = set()
        for d in ds:
            ok = range_ok(z, ori, d)
            if ok is not False:
                good.add(d)
        if not good:
            continue
        items.append(dict(tb=tb, z=z, axn=axn, good=sorted(good), addr=z.address))

    confirmed = [it for it in items if len(it['good']) == 1]
    print(f'stage1 candidates {len(items)} | unique-delta CONFIRMED {len(confirmed)}')

    # stage 3: piecewise-constant delta model over XDF address space
    anchors = sorted((it['addr'], it['good'][0]) for it in confirmed)
    xs = [a for a, _ in anchors]
    print(f'confirmed delta runs: {len(set(d for _, d in anchors))} distinct deltas')

    def predict(addr):
        if not anchors:
            return None
        i = bisect.bisect_left(xs, addr)
        best = None
        for j in (i - 1, i, i + 1, i + 2):
            if 0 <= j < len(anchors):
                dist = abs(anchors[j][0] - addr)
                if best is None or dist < best[0]:
                    best = (dist, anchors[j][1])
        return best[1] if best else None

    accepted, ambiguous = [], []
    for it in items:
        d0 = it['good'][0] if len(it['good']) == 1 else None
        if d0 is None:
            p = predict(it['addr'])
            if p is not None and p in it['good']:
                d0 = p
            else:
                ambiguous.append(it)
                continue
        st = it['z'].address + d0
        nd = sum(1 for k in range(st, st + it['z'].byte_span()) if k in diff)
        rec = dict(title=it['tb'].title, desc=it['tb'].desc, delta=hex(d0),
                   user_addr=hex(st), rows=it['z'].rowcount, cols=it['z'].colcount,
                   esize=16, mn=it['z'].mn, mx=it['z'].mx,
                   axes={k: hex(v[0].address + d0) for k, v in it['axn'].items()},
                   axis_pts={k: v[1] for k, v in it['axn'].items()},
                   range_meaningful=range_ok(it['z'], ori, d0) is True,
                   tuned=nd, size=it['z'].byte_span(),
                   n_deltas=len(it['good']), cats=it['tb'].categories)
        (accepted if nd else ambiguous).append(rec)

    acc_tuned = sorted([a for a in accepted if a['tuned']], key=lambda r: -r['tuned'])
    print(f'stage4 accepted {len(accepted)} (with diff evidence {len(acc_tuned)}) | '
          f'left ambiguous {len(ambiguous)}')
    return acc_tuned, accepted, ambiguous


if __name__ == '__main__':
    res, allacc, amb = analyse(*sys.argv[1:4])
    json.dump({'accepted': res, 'ambiguous': [
        {'title': i['tb'].title, 'desc': i['tb'].desc, 'n_deltas': len(i['good'])}
        for i in amb]}, open('out/candidates_disambiguated.json', 'w'), indent=1)
    print()
    print('%-46s %-26s %-10s %-8s %5s %6s' % ('title', 'bosch var', '@user', 'dims', 'tuned', 'ndelta'))
    for r in res:
        print('%-46s %-26s %-10s %2dx%-4d %5d %6d' %
              (r['title'][:46], r['desc'][:26], r['user_addr'], r['rows'], r['cols'],
               r['tuned'], r['n_deltas']))