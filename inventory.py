"""Reproducible change inventory - strictly read-only.

Produces out/changed_bytes_inventory.csv. Every one of the 3,821 changed bytes is
classified exactly once:

  VERIFIED_CELL    inside the data cells of a VERIFIED definition in the axes-clean candidate
  VERIFIED_AXIS    inside a TRUSTED (addressed, sanity-passing) axis of that candidate
  PROBABLE         inside a table the audit classified PROBABLE or PARTIAL, which is
                   deliberately NOT in the candidate
  UNEXPLAINED      no definition of any kind reaches it

Byte-level evidence and semantic identification are kept in separate columns.
"""
import csv
import hashlib
import xml.etree.ElementTree as ET

ORI = '10SW002828_iRom_ori'
MOD = '10SW002828_iRom_stage2'
CAND = 'out/R0C2J772B_CANDIDATE_axesclean.xdf'
LEGACY = 'out/R0C2J772B_verified.xdf'
AUDIT = 'out/per_table_audit.csv'
OUTCSV = 'out/changed_bytes_inventory.csv'
GAP = 64


def hi(v):
    return int(str(v), 0)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for c in iter(lambda: fh.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def main():
    o = open(ORI, 'rb').read()
    m = open(MOD, 'rb').read()
    assert len(o) == len(m)
    diff = set(i for i in range(len(o)) if o[i] != m[i])

    # ---- candidate definitions (axes-clean) ----
    root = ET.parse(CAND).getroot()
    cells = set()
    owner_cell = {}
    axes = set()
    owner_axis = {}
    for t in root.findall('XDFTABLE'):
        d = t.findtext('description') or ''
        z = t.find('XDFAXIS[@id="z"]')
        e = z.find('EMBEDDEDDATA')
        ic = int(z.findtext('indexcount') or 0)
        row = hi(e.get('mmedrowcount') or 0) or ic
        col = hi(e.get('mmedcolcount') or 0) or ic
        st = hi(e.get('mmedaddress'))
        sp = row * col * hi(e.get('mmedelementsizebits')) // 8
        for k in range(st, st + sp):
            cells.add(k)
            owner_cell[k] = d
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
                owner_axis[k] = '%s/%s' % (d, role)

    # ---- PROBABLE / PARTIAL tables, deliberately not emitted ----
    prob_cells = set()
    owner_prob = {}
    for r in csv.DictReader(open(AUDIT)):
        if r['confidence'] not in ('PROBABLE', 'PARTIAL'):
            continue
        a = int(r['user_addr'], 16)
        for k in range(a, a + int(r['size'])):
            prob_cells.add(k)
            owner_prob[k] = r['desc']

    def classify(b):
        if b in cells:
            return 'VERIFIED_CELL', owner_cell[b], 'SP15 byte-identity + axes corroborate'
        if b in axes:
            return 'VERIFIED_AXIS', owner_axis[b], 'axis bytes identical to SP15 reference'
        if b in prob_cells:
            return 'PROBABLE', owner_prob[b], 'byte-verified but axis failed corroboration; not emitted'
        return 'UNEXPLAINED', '', 'no definition in any local file reaches this address'

    # ---- group into regions ----
    ordered = sorted(diff)
    regions = []
    for i in ordered:
        if regions and i - regions[-1][1] <= GAP:
            regions[-1][1] = i
        else:
            regions.append([i, i])

    rows = []
    total = 0
    for n, (a, b) in enumerate(regions, 1):
        cnt = 0
        per = {}
        for k in range(a, b + 1):
            if k not in diff:
                continue
            cls, ref, why = classify(k)
            per.setdefault((cls, ref, why), 0)
            per[(cls, ref, why)] += 1
            cnt += 1
        total += cnt
        dominant = max(per.items(), key=lambda kv: kv[1])
        rows.append(dict(
            region=n,
            start='0x%08X' % a, end='0x%08X' % b,
            span=b - a + 1, changed_bytes=cnt,
            classification=dominant[0][0],
            reference=dominant[0][1],
            byte_level_evidence=dominant[0][2],
            semantic_identification='not established' if dominant[0][0] == 'UNEXPLAINED'
                                    else 'definition carries a Bosch name from the source pack',
            breakdown='; '.join('%s=%d' % (k[0], v) for k, v in sorted(per.items())),
        ))

    with open(OUTCSV, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # ---- verify totals, no double counting ----
    allclass = {}
    for k in diff:
        c = classify(k)[0]
        allclass[c] = allclass.get(c, 0) + 1
    s = sum(allclass.values())
    print('regions written                : %d' % len(rows))
    print('sum of region changed_bytes    : %d' % total)
    print('independently counted diff     : %d' % len(diff))
    print('classification total           : %d' % s)
    print('NO DOUBLE COUNTING             : %s' % (s == len(diff) == total))
    print()
    for k in sorted(allclass):
        print('  %-16s %5d  (%5.2f %%)' % (k, allclass[k], 100 * allclass[k] / len(diff)))
    print()
    print('hashes:')
    for p in (ORI, MOD, LEGACY, 'out/R0C2J772B_CANDIDATE.xdf', CAND):
        print('  %-40s %s' % (p, md5(p)))
    print('\nwrote %s' % OUTCSV)


if __name__ == '__main__':
    main()