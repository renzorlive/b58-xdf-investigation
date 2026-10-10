"""Tuner delta forensic report - strictly read-only.

Reconciles the original/Stage-2 difference mask against out/changed_bytes_inventory.csv
and characterises every changed region. Writes out/tuner_delta_regions.csv.
Nothing is modified.
"""
import csv
import hashlib
import xml.etree.ElementTree as ET

ORI = '10SW002828_iRom_ori'
MOD = '10SW002828_iRom_stage2'
CAND = 'out/R0C2J772B_CANDIDATE_axesclean.xdf'
INV = 'out/changed_bytes_inventory.csv'
OUT = 'out/tuner_delta_regions.csv'
GAP = 64
CAL_LO, CAL_HI = 0x6C0000, 0x740000


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as hi_:
        for c in iter(lambda: hi_.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for c in iter(lambda: fh.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def hi(v):
    return int(str(v), 0)


def main():
    o = open(ORI, 'rb').read()
    m = open(MOD, 'rb').read()
    print('=== 1  file identity ===')
    for p in (ORI, MOD):
        print('  %-28s size=%d md5=%s' % (p, len(open(p, 'rb').read()), md5(p)))
        print('  %-28s sha256=%s' % ('', sha256(p)))
    assert len(o) == len(m) == 8126464

    diff = set(i for i in range(len(o)) if o[i] != m[i])
    print()
    print('=== 2  difference mask ===')
    print('  changed bytes recomputed : %d' % len(diff))

    inv = list(csv.DictReader(open(INV)))
    inv_sum = sum(int(r['changed_bytes']) for r in inv)
    print('  inventory CSV rows       : %d' % len(inv))
    print('  inventory changed_bytes  : %d' % inv_sum)
    # cross-check every byte
    inv_bytes = set()
    for r in inv:
        a, b = int(r['start'], 16), int(r['end'], 16)
        inv_bytes |= set(range(a, b + 1))
    only_in_mask = sorted(diff - inv_bytes)
    # per-region: count changed bytes of the mask inside each inventory span
    per_region_ok = True
    for r in inv:
        a, b = int(r['start'], 16), int(r['end'], 16)
        actual = sum(1 for k in range(a, b + 1) if k in diff)
        if actual != int(r['changed_bytes']):
            per_region_ok = False
            print('    MISMATCH region %s %s-%s csv=%d actual=%d'
                  % (r['region'], r['start'], r['end'], r['changed_bytes'], actual))
    print('  changed bytes inside inventory spans  : %d / %d' % (len(diff) - len(only_in_mask), len(diff)))
    print('  changed bytes outside inventory spans : %d' % len(only_in_mask))
    print('  per-region counts agree                : %s' % per_region_ok)
    print('  inventory total == recomputed mask     : %s' % (inv_sum == len(diff)))
    print('  RECONCILED                             : %s'
          % (not only_in_mask and per_region_ok and inv_sum == len(diff)))

    # ---- candidate definitions (axes-clean) ----
    root = ET.parse(CAND).getroot()
    cells, owner = set(), {}
    axes, aowner = set(), {}
    for t in root.findall('XDFTABLE'):
        d = t.findtext('description') or ''
        z = t.find('XDFAXIS[@id="z"]')
        e = z.find('EMBEDDEDDATA')
        ic = int(z.findtext('indexcount') or 0)
        row = hi(e.get('mmedrowcount') or 0) or ic
        col = hi(e.get('mmedcolcount') or 0) or ic
        st = hi(e.get('mmedaddress'))
        for k in range(st, st + row * col * hi(e.get('mmedelementsizebits')) // 8):
            cells.add(k)
            owner.setdefault(k, d)
        for role in ('x', 'y'):
            a = t.find('XDFAXIS[@id="%s"]' % role)
            if a is None:
                continue
            ae = a.find('EMBEDDEDDATA')
            if ae is None or not ae.get('mmedaddress'):
                continue
            n = int(a.findtext('indexcount') or 0)
            if not n:
                continue
            ast = hi(ae.get('mmedaddress'))
            for k in range(ast, ast + n * hi(ae.get('mmedelementsizebits')) // 8):
                axes.add(k)
                aowner.setdefault(k, '%s/%s' % (d, role))

    import collections
    prob = set()
    for r in csv.DictReader(open('out/per_table_audit.csv')):
        if r['confidence'] in ('PROBABLE', 'PARTIAL'):
            a = int(r['user_addr'], 16)
            prob |= set(range(a, a + int(r['size'])))

    # ---- 3/4 per-region table ----
    ordered = sorted(diff)
    regions = []
    for i in ordered:
        if regions and i - regions[-1][1] <= GAP:
            regions[-1][1] = i
        else:
            regions.append([i, i])

    rows = []
    for n, (a, b) in enumerate(regions, 1):
        ch = [k for k in range(a, b + 1) if k in diff]
        in_cell = [k for k in ch if k in cells]
        in_axis = [k for k in ch if k in axes]
        in_prob = [k for k in ch if k in prob]
        if in_cell and not in_axis:
            kind = 'VERIFIED_DATA_CELL'
        elif in_axis and not in_cell:
            kind = 'VERIFIED_AXIS'
        elif in_cell and in_axis:
            kind = 'CELL_AND_AXIS'
        elif in_prob:
            kind = 'PROBABLE_TABLE'
        elif b < CAL_LO:
            kind = 'OUTSIDE_CAL_BLOCK_LOW'
        elif a >= CAL_HI:
            kind = 'OUTSIDE_CAL_BLOCK_HIGH'
        else:
            kind = 'UNIDENTIFIED_IN_CAL_BLOCK'
        defs = sorted({owner[k] for k in in_cell} | {aowner[k] for k in in_axis}
                      | {r['desc'] for r in csv.DictReader(open('out/per_table_audit.csv'))
                         if r['confidence'] in ('PROBABLE', 'PARTIAL')
                         and int(r['user_addr'], 16) <= a < int(r['user_addr'], 16) + int(r['size'])})
        rows.append(dict(
            region=n, start='0x%08X' % a, end='0x%08X' % b,
            span=b - a + 1, changed_bytes=len(ch),
            kind=kind,
            changed_offsets=' '.join('0x%06X' % k for k in ch),
            ori_bytes=o[a:b + 1].hex(),
            stage2_bytes=m[a:b + 1].hex(),
            changed_ori_bytes=''.join('%02x' % o[k] for k in ch),
            changed_stage2_bytes=''.join('%02x' % m[k] for k in ch),
            overlapping_definitions=';'.join(defs) if defs else '',
            n_in_cells=len(in_cell), n_in_axes=len(in_axis), n_in_probable=len(in_prob),
            evidence_limit=('placement byte-proven in target BIN; map NAME inherited from '
                            'S15A-18 reference, not proven for S15A-17 target'
                            if in_cell or in_axis else
                            'no definition reaches these bytes; no interpretation possible')))

    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # ---- 5 category analysis ----
    print()
    print('=== 5  change categories ===')
    cats = collections.Counter()
    for r in rows:
        cats[r['kind']] += r['changed_bytes']
    for k, v in sorted(cats.items(), key=lambda kv: -kv[1]):
        print('  %-26s %5d bytes in %d regions'
              % (k, v, sum(1 for r in rows if r['kind'] == k)))
    print()
    print('  TOTAL %d bytes in %d regions' % (sum(cats.values()), len(rows)))
    print()
    lo = sum(1 for k in diff if k < CAL_LO)
    n_high = sum(1 for k in diff if k >= CAL_HI)
    print('  changed bytes below cal block 0x6C0000 : %d' % lo)
    print('  changed bytes above cal block 0x740000 : %d' % n_high)
    out_h = sorted(k for k in diff if k >= CAL_HI)
    if out_h:
        print('  addresses: %s' % ' '.join('0x%06X' % k for k in out_h))
        a, b = out_h[0], out_h[-1]
        print('  context around the high region (ori):')
        for x in range(max(0, a - 48), min(len(o), b + 16), 16):
            seg = o[x:x + 16]
            if not any(o[y] != m[y] for y in range(x, min(x + 16, len(o)))):
                continue
            print('    0x%06X %s  %s' % (x, seg.hex(),
                                         ''.join(chr(c) if 32 <= c < 127 else '.' for c in seg)))
    print()
    print('wrote %s (%d rows)' % (OUT, len(rows)))


if __name__ == '__main__':
    main()