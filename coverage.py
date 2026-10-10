"""Exact accounting of the 3,821 changed bytes.

Every changed byte is classified exactly once:
  cell      - inside a proven table's DATA area only
  axis      - inside a proven table's breakpoint axes only
  cell+axis - inside both (reported separately, counted once)
  overlap   - covered by more than one proven table (counted once, flagged)
  unexplained - not covered by any proven table
"""
import json
import sys
import xdfread

ORI = '10SW002828_iRom_ori'

import os as _os
def _mod():
    for c in ('10SW002828_iRom_stage2',_mod()):
        if _os.path.exists(c):
            return c
    raise SystemExit('tuned file not found')
MOD = _mod()


def spans(tb, delta):
    out = {'cell': set(), 'axis': set()}
    z = tb.z
    if z and z.address is not None:
        s = z.address + delta
        out['cell'] |= set(range(s, s + z.byte_span()))
    for ax in (tb.x, tb.y):
        if ax is None or ax.address is None or ax.esize_bits != 16:
            continue
        n = ax.colcount or ax.indexcount if ax.id == 'x' else ax.rowcount or ax.indexcount
        if not n:
            continue
        a = ax.address + delta
        out['axis'] |= set(range(a, a + n * (ax.esize_bits // 8)))
    return out


def account(tables, label, diff):
    cell = set()
    axis = set()
    owner = {}
    dup = set()
    for tb, d in tables:
        sp = spans(tb, d)
        for kind in ('cell', 'axis'):
            for b in sp[kind]:
                if b in cell or b in axis:
                    dup.add(b)
                owner.setdefault(b, kind)
                if kind == 'cell':
                    cell.add(b)
                else:
                    axis.add(b)
    both = cell & axis
    union = cell | axis
    explained = diff & union
    resid = diff - union
    print(f'\n=== {label} ===')
    print(f'  tables considered            : {len(tables)}')
    print(f'  cell-only bytes covered      : {len(cell - axis)}')
    print(f'  axis-only bytes covered      : {len(axis - cell)}')
    print(f'  bytes in BOTH cell and axis  : {len(both)}   (counted once)')
    print(f'  changed bytes in >1 table    : {len(dup & diff)}   (counted once)')
    print(f'  CHANGED EXPLAINED            : {len(explained)} / {len(diff)}  '
          f'({100*len(explained)/len(diff):.1f}%)')
    print(f'  CHANGED UNEXPLAINED          : {len(resid)}')
    return explained, resid, cell, axis


def main():
    ori = open(ORI, 'rb').read()
    mod = open(MOD, 'rb').read()
    diff = set(i for i in range(len(ori)) if ori[i] != mod[i])

    # --- proven set, with the per-table deltas recorded by verify ---
    import verify
    acc, tabs, med = verify.run('ref/BMW-XDFs-master/B58gen1/00003076501103.xdf',
                                'ref/BMW-XDFs-master/B48gen1/00003076501103_original.bin'
                                .replace('B48gen1', 'B58gen1'),
                                ORI, 0x6C0000, 0x740000)
    proven = [(tb, off) for i, tb, off, how, sc in acc]
    ex, resid, cell, axis = account(proven, 'PROVEN set (87 tables, out/R0C2J772B_verified.xdf)', diff)

    # anchored candidates that are NOT already in the proven set
    cand = json.load(open('out/candidates_anchored.json'))
    base, otabs = xdfread.parse(
        'mgflasher-map-packs/XDFs/B48 B58 Gen 1/Generic/MetricUnits/R1C9J772B_3076-070_009_002.MetricUnits.xdf')
    by_desc = {}
    for tb in otabs:
        if tb.desc and tb.desc not in by_desc and 'autogen' not in (tb.title or ''):
            by_desc[tb.desc] = tb
    proven_desc = {tb.desc for tb, _ in proven if tb.desc}
    extra = []
    for c in cand:
        if c['status'] != 'ANCHORED' or not c['tuned']:
            continue
        if c['desc'] in proven_desc:
            continue
        tb = by_desc.get(c['desc'])
        if tb and tb.z and tb.z.address is not None:
            extra.append((tb, int(c['delta'], 16)))
    ex2, resid2, cell2, axis2 = account(extra, f'ADDITIONAL anchored candidates ({len(extra)} tables)', diff)

    # combined, with overlap between the two sets made explicit
    print('\n=== COMBINED ===')
    allt = proven + extra
    ex3, resid3, cell3, axis3 = account(allt, 'proven + additional anchored', diff)
    overlap_sets = cell & cell2
    print(f'\n  cell bytes claimed by both sets: {len(overlap_sets & diff)} changed bytes '
          f'(double counting removed)')

    json.dump({'total_changed': len(diff),
               'explained_proven': sorted(ex & diff),
               'explained_combined': sorted(ex3 & diff),
               'unexplained': sorted(resid3 & diff)},
              open('out/coverage.json', 'w'))

    # unexplained region map
    print('\n=== UNEXPLAINED changed regions ===')
    r = sorted(resid3 & diff)
    groups = []
    for i in r:
        if groups and i - groups[-1][1] <= 64:
            groups[-1][1] = i
        else:
            groups.append([i, i])
    tot = 0
    for a, b in groups:
        c = sum(1 for k in range(a, b + 1) if k in diff)
        tot += c
        print('  0x%06X-0x%06X  span=%-5d changed=%d' % (a, b, b - a + 1, c))
    print('  total unexplained changed bytes: %d' % tot)


if __name__ == '__main__':
    main()