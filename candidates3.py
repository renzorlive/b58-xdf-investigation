"""Candidate placement anchored to the proven set.

The 87 tables in R0C2J772B_verified.xdf were placed by content-anchoring against a
real stock dump of a sibling software version, and survive a declared-range check.
They are treated here as hard ground truth.

For a second, independent XDF that names the same maps:
  1. match tables by Bosch variable name,
  2. compute the delta implied by each verified anchor,
  3. predict a delta for every table from the nearest anchors in address space,
  4. ACCEPT only if the table's own breakpoint axes validate at exactly that delta.

Confidence:
  VERIFIED  - table is itself in the proven 87
  ANCHORED  - axes validate exactly at the interpolated delta from proven anchors
  UNRESOLVED- axes do not validate at the predicted delta, or no anchor nearby
"""
import sys
import json
import bisect
import xdfread
import verify

ORI = '10SW002828_iRom_ori'

import os as _os
def _mod():
    for c in ('10SW002828_iRom_stage2',_mod()):
        if _os.path.exists(c):
            return c
    raise SystemExit('tuned file not found')
MOD = _mod()
BASE_XDF = 'ref/BMW-XDFs-master/B58gen1/00003076501103.xdf'
BASE_REF = 'ref/BMW-XDFs-master/B58gen1/00003076501103_original.bin'
MIN_PTS = 4


def read_u16(d, a, n):
    if a < 0 or a + n * 2 > len(d):
        return None
    return [int.from_bytes(d[a + i * 2:a + i * 2 + 2], 'big') for i in range(n)]


def axis_ok(v):
    if not v or len(v) < MIN_PTS or len(set(v)) < MIN_PTS:
        return False
    if v[0] < 0 or v[-1] > 20000:
        return False
    return all(v[i] < v[i + 1] for i in range(len(v) - 1))


def axes_of(tb):
    out = {}
    for role, ax in (('x', tb.x), ('y', tb.y)):
        if ax is None or ax.address is None or ax.esize_bits != 16:
            continue
        if ax.major_stride or ax.minor_stride:
            continue
        cnt = (ax.colcount or ax.indexcount) if role == 'x' else (ax.rowcount or ax.indexcount)
        if not cnt or cnt < MIN_PTS or cnt > 64:
            continue
        out[role] = (ax, cnt)
    return out


def main(other_xdf):
    ori = open(ORI, 'rb').read()
    mod = open(MOD, 'rb').read()
    diff = set(i for i in range(len(ori)) if ori[i] != mod[i])

    acc, tabs, med = verify.run(BASE_XDF, BASE_REF, ORI, 0x6C0000, 0x740000)
    proven = {}
    for i, tb, off, how, sc in acc:
        if tb.desc and tb.desc not in proven:
            proven[tb.desc] = (tb.z.address + off, tb)
    print(f'proven anchors (unique Bosch names): {len(proven)}')

    base, otabs = xdfread.parse(other_xdf)
    anchors = []
    matched = 0
    for tb in otabs:
        if 'autogen' in (tb.title or '') or not tb.z or tb.z.address is None:
            continue
        if tb.desc in proven:
            d = proven[tb.desc][0] - tb.z.address
            anchors.append((tb.z.address, d, tb))
            matched += 1
    anchors.sort()
    print(f'anchor points recovered from this pack: {matched} tables, '
          f'{len(set(d for _, d, _ in anchors))} distinct deltas')

    xs = [a for a, _, _ in anchors]

    def predict(addr):
        if not xs:
            return None, None
        i = bisect.bisect_left(xs, addr)
        best = None
        for j in (i - 1, i, i + 1):
            if 0 <= j < len(anchors):
                dist = abs(anchors[j][0] - addr)
                if best is None or dist < best[0]:
                    best = (dist, anchors[j][1])
        return (best[1], best[0]) if best else (None, None)

    rows = []
    for tb in otabs:
        if 'autogen' in (tb.title or '') or not tb.z or tb.z.address is None:
            continue
        z = tb.z
        r, c = z.shape()
        if z.esize_bits != 16 or not r or not c or r * c > 4096:
            continue
        axn = axes_of(tb)
        if not axn:
            continue
        d, dist = predict(z.address)
        if d is None:
            continue
        st = z.address + d
        if st < 0 or st + z.byte_span() > len(ori):
            continue
        ok = all(axis_ok(read_u16(ori, ax.address + d, n)) for ax, n in axn.values())
        if not ok:
            continue
        nd = sum(1 for k in range(st, st + z.byte_span()) if k in diff)
        rows.append(dict(title=tb.title, desc=tb.desc, delta=hex(d), user_addr=hex(st),
                         rows=r, cols=c, anchor_dist=dist,
                         axes={k: hex(v[0].address + d) for k, v in axn.items()},
                         axis_pts={k: v[1] for k, v in axn.items()},
                         min=z.mn, max=z.mx, tuned=nd, size=z.byte_span(),
                         cats=tb.categories,
                         status='VERIFIED' if tb.desc in proven else 'ANCHORED'))
    rows.sort(key=lambda r: (-r['tuned'], r['desc']))
    json.dump(rows, open('out/candidates_anchored.json', 'w'), indent=1)
    print(f'anchored placements: {len(rows)} '
          f'({sum(1 for r in rows if r["status"]=="VERIFIED")} VERIFIED / '
          f'{sum(1 for r in rows if r["status"]=="ANCHORED")} ANCHORED), '
          f'{sum(1 for r in rows if r["tuned"])} touch the tuned diff\n')
    print('%-44s %-26s %-10s %-8s %5s %6s %s' %
          ('title', 'bosch var', '@user', 'dims', 'tuned', 'adist', 'status'))
    for r in rows[:45]:
        print('%-44s %-26s %-10s %2dx%-4d %5d %6d %s' %
              (r['title'][:44], r['desc'][:26], r['user_addr'], r['rows'], r['cols'],
               r['tuned'], r['anchor_dist'], r['status']))
    return rows


if __name__ == '__main__':
    main(sys.argv[1])