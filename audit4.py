"""Report #4: validate and regenerate the candidate XDF.

Adds the six KL_MD_K_MAX_* curves, whose identity, addresses and Nm unit are now
established from the DAMOS A2L (authoritative) rather than from XDF metadata.
Every emitted definition is re-audited against the per-table CSV.
"""
import csv
import json
import re
import xdfread

A2L = 'mgflasher-map-packs/A2Ls/B48 B58 Gen 1/Generic/R0C9J8B2B_3081-080_017_002.a2l'
SP15_XDF = 'ref/BMW-XDFs-master/B58gen1/00003081501102.xdf'
SP15_REF = 'ref/BMW-XDFs-master/B58gen1/00003081501102_original.bin'
ORI = '10SW002828_iRom_ori'
MOD = '10SW002828_iRom_stage2'

A2L_BASE = 0x300000          # verified: A2L addr = XDF addr + 0x300000
KMAX_DELTA = 0x3F9D0

# Bosch variable, XDF data addr, XDF axis addr - all from the A2L
KMAX = [
    ('KL_MD_K_MAX_VL_HS', 'Speed-dependent full load curve (half step)', 0x6B92D0, 0x6B93C8),
    ('KL_MD_K_MAX_VL', 'Speed-dependent full load curve', 0x6B92E8, 0x6B93E0),
    ('KL_MD_K_MAX_RST_HS', 'Speed-dependent launch control curve (half step)', 0x6B9300, 0x6B93F8),
    ('KL_MD_K_MAX_RST', 'Speed-dependent launch control curve', 0x6B9318, 0x6B9410),
    ('KL_MD_K_MAX_BST_HS', 'Speed-dependent boost curve, manual transmission', 0x6B9330, 0x6B9428),
    ('KL_MD_K_MAX_BST', 'Speed-dependent boost curve', 0x6B9348, 0x6B9440),
]


def audit_existing(path, csv_path):
    base, tabs = xdfread.parse(path)
    ref = open(SP15_REF, 'rb').read()
    u = open(ORI, 'rb').read()
    m = open(MOD, 'rb').read()
    rows = list(csv.DictReader(open(csv_path)))
    bykey = {(r['desc'], r['user_addr']): r for r in rows}

    problems = []
    cells = {}
    for t in tabs:
        z = t.z
        rec = bykey.get((t.desc, hex(z.address)))
        if rec is None:
            problems.append(('%s @0x%X' % (t.desc, z.address), 'not present in audit CSV'))
            continue
        # geometry
        if str(z.rowcount) != rec['rows'] or str(z.colcount) != rec['cols']:
            problems.append((t.desc, 'dimension mismatch vs CSV'))
        if str(z.esize_bits) != rec['esize']:
            problems.append((t.desc, 'element size mismatch vs CSV'))
        # endianness / datatype
        if z.dtype != 0:
            problems.append((t.desc, 'not unsigned'))
        # conversion formula
        sc = rec['scaling']
        want = 1.0 if sc.startswith('identity') else float(sc.lstrip('x').split()[0])
        if abs(z.eq(1.0) - want) > 1e-9:
            problems.append((t.desc, 'scaling mismatch vs CSV'))
        # in-range
        if z.address + z.byte_span() > len(u):
            problems.append((t.desc, 'out of file bounds'))
        # byte identity against the SP15 reference
        d = int(rec['delta'], 16)
        ra = int(rec['ref_addr'], 16)
        if ref[ra:ra + z.byte_span()] != u[z.address:z.address + z.byte_span()]:
            problems.append((t.desc, 'bytes NOT identical to SP15 reference'))
        # axes
        for role, ax, cnt in (('x', t.x, rec['x_axis']), ('y', t.y, rec['y_axis'])):
            if not cnt or cnt == '':
                continue
            a = int(cnt, 16)
            if not ax or ax.address != a:
                problems.append((t.desc, '%s-axis address mismatch' % role))
                continue
            n = ax.colcount or ax.indexcount if role == 'x' else ax.rowcount or ax.indexcount
            if n:
                rax = ax.address - d
                if ref[rax:rax + n * 2] != u[a:a + n * 2]:
                    problems.append((t.desc, '%s-axis bytes differ from reference' % role))
        # duplicates / overlap
        a0 = z.address
        for p0, p1 in cells.items():
            if a0 < p1 and p0 < a0 + z.byte_span():
                problems.append((t.desc, 'OVERLAPS %s' % t.desc))
        cells[a0] = a0 + z.byte_span()
    return tabs, problems, len(set(t.desc for t in tabs))


def main():
    u = open(ORI, 'rb').read()
    ref = open(SP15_REF, 'rb').read()
    m = open(MOD, 'rb').read()
    diff = set(i for i in range(len(u)) if u[i] != m[i])

    print('=== AUDIT of existing out/R0C2J772B_CANDIDATE.xdf ===')
    tabs, problems, uniq = audit_existing('out/R0C2J772B_CANDIDATE.xdf',
                                          'out/per_table_audit.csv')
    print('  tables=%d  unique Bosch names=%d  problems=%d' % (len(tabs), uniq, len(problems)))
    for p, why in problems:
        print('    PROBLEM %-32s %s' % (p, why))
    if not problems:
        print('    no problems found')

    # ---- K_MAX family, verified against A2L ----
    print('\n=== KL_MD_K_MAX_* family (A2L-verified, unit Nm) ===')
    base, tabs15 = xdfread.parse(SP15_XDF)
    krows = []
    for name, title, zd, zx in KMAX:
        zud, xud = zd + KMAX_DELTA, zx + KMAX_DELTA
        dat_ok = ref[zd:zd + 24] == u[zud:zud + 24]
        ax_ok = ref[zx:zx + 24] == u[xud:xud + 24]
        zo = [int.from_bytes(u[zud + i * 2:zud + i * 2 + 2], 'big') for i in range(12)]
        zm = [int.from_bytes(m[zud + i * 2:zud + i * 2 + 2], 'big') for i in range(12)]
        ch = sum(1 for a, b in zip(zo, zm) if a != b)
        print('  %-20s data 0x%06X axis 0x%06X  dataID=%-5s axisID=%-5s  %3d Nm -> %3d Nm (%d/12)'
              % (name, zud, xud, dat_ok, ax_ok, zo[0], zm[0], ch))
        krows.append(dict(desc=name, title=title, addr=zud, axis=xud,
                          data_identical=dat_ok, axis_identical=ax_ok,
                          ori=zo[0], mod=zm[0], changed=ch))

    json.dump(krows, open('out/kmax_family.json', 'w'), indent=1)

    # ---- coverage reconciliation ----
    rows = list(csv.DictReader(open('out/per_table_audit.csv')))
    sp15 = [r for r in rows if r['confidence'] == 'VERIFIED']
    c_sp15 = set()
    for r in sp15:
        a = int(r['user_addr'], 16)
        c_sp15 |= set(range(a, a + int(r['size'])))
    c_kmax = set()
    for name, title, zd, zx in KMAX:
        a = zd + KMAX_DELTA
        c_kmax |= set(range(a, a + 24))

    import verify
    LEG_X = 'ref/BMW-XDFs-master/B58gen1/00003076501103.xdf'
    LEG_R = 'ref/BMW-XDFs-master/B58gen1/00003076501103_original.bin'
    acc, _, _ = verify.run(LEG_X, LEG_R, ORI, 0x6C0000, 0x740000)
    ref = open(LEG_R, 'rb').read()
    c_leg = set()
    for i, tb, off, how, sc in acc:
        z = tb.z
        n = z.byte_span()
        if ref[z.address:z.address + n] == u[z.address + off:z.address + off + n]:
            c_leg |= set(range(z.address + off, z.address + off + n))

    cov = {}
    for label, s in (('SP15 verified (73)', c_sp15),
                     ('legacy byte-identical (43)', c_leg),
                     ('K_MAX family (6)', c_kmax)):
        cov[label] = len(diff & s)
    allc = c_sp15 | c_leg | c_kmax
    cov['combined deduplicated'] = len(diff & allc)
    cov['total changed'] = len(diff)
    cov['combined pct'] = round(100 * len(diff & allc) / len(diff), 1)
    cov['overlap sp15&legacy'] = len(c_sp15 & c_leg)
    cov['overlap sp15&kmax'] = len(c_sp15 & c_kmax)
    print('\n=== COVERAGE (deduplicated changed bytes) ===')
    for k, v in cov.items():
        print('  %-28s %s' % (k, v))
    json.dump(cov, open('out/coverage_report4.json', 'w'), indent=1)


if __name__ == '__main__':
    main()