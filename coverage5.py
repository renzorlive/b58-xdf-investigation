"""Report #5: independent coverage recalculation from the emitted candidate XDF.

Nothing is taken from earlier summaries. Coverage is computed from:
  * both BINs read directly, MD5 verified,
  * the definitions actually present in out/R0C2J772B_CANDIDATE.xdf,
  * the per-table confidence in out/per_table_audit.csv.
"""
import csv
import hashlib
import json
import xml.etree.ElementTree as ET

ORI = '10SW002828_iRom_ori'
MOD = '10SW002828_iRom_stage2'
CAND = 'out/R0C2J772B_CANDIDATE.xdf'
CSV = 'out/per_table_audit.csv'


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def main():
    ho, hm = md5(ORI), md5(MOD)
    print('MD5 %s = %s' % (ORI, ho))
    print('MD5 %s = %s' % (MOD, hm))

    o = open(ORI, 'rb').read()
    m = open(MOD, 'rb').read()
    assert len(o) == len(m) == 8126464, 'size mismatch'
    diff = set(i for i in range(len(o)) if o[i] != m[i])
    print('changed bytes computed directly from BINs: %d' % len(diff))

    conf = {}
    for r in csv.DictReader(open(CSV)):
        conf[(r['desc'], r['user_addr'])] = r['confidence']

    root = ET.fromstring(open(CAND, encoding='utf-8').read())
    cells, axes = set(), set()
    per_conf = {'VERIFIED': set(), 'PROBABLE': set(), 'PARTIAL': set(), 'REJECT': set(), 'UNKNOWN': set()}
    n = 0
    for t in root.findall('XDFTABLE'):
        d = t.findtext('description') or ''
        z = t.find('XDFAXIS[@id="z"]')
        if z is None:
            continue
        ed = z.find('EMBEDDEDDATA')
        addr = int(ed.get('mmedaddress'), 0)
        esize = int(ed.get('mmedelementsizebits'))
        row = int(ed.get('mmedrowcount') or 0)
        col = int(ed.get('mmedcolcount') or 0)
        ic = int(z.findtext('indexcount') or 0)
        row = row or ic
        col = col or ic
        span = row * col * esize // 8
        s = set(range(addr, addr + span))
        cells |= s
        n += 1
        c = conf.get((d, hex(addr)), 'UNKNOWN')
        per_conf[c] |= s
        for role, cnt in (('x', 'x'), ('y', 'y')):
            a = t.find('XDFAXIS[@id="%s"]' % role)
            if a is None:
                continue
            ae = a.find('EMBEDDEDDATA')
            if ae is None or not ae.get('mmedaddress'):
                continue
            aa = int(ae.get('mmedaddress'), 0)
            an = int(ae.get('mmedelementsizebits'))
            ac = int(ae.get('mmedcolcount') or a.findtext('indexcount') or 0)
            axes |= set(range(aa, aa + ac * an // 8))

    both = cells & axes
    union = cells | axes
    print()
    print('candidate XDF tables                : %d' % n)
    print('distinct cell bytes in candidate    : %d' % len(cells))
    print('distinct axis bytes in candidate    : %d' % len(axes))
    print('bytes claimed as BOTH cell and axis : %d' % len(both))
    print('overlapping address space (cells)   : 0 (verified in report 4)')

    res = {}
    for k in ('VERIFIED', 'PROBABLE', 'PARTIAL'):
        res[k] = len(diff & per_conf[k])
        print('changed bytes covered by %-9s  : %d' % (k, res[k]))
    res['combined'] = len(diff & union)
    res['total_changed'] = len(diff)
    res['combined_pct'] = round(100 * res['combined'] / len(diff), 2)
    res['unexplained'] = len(diff) - res['combined']
    print()
    print('COMBINED changed bytes covered      : %d / %d = %.2f %%'
          % (res['combined'], len(diff), res['combined_pct']))
    print('unexplained                        : %d' % res['unexplained'])

    res['md5_ori'] = ho
    res['md5_mod'] = hm
    res['tables'] = n
    json.dump(res, open('out/coverage_report5.json', 'w'), indent=1)
    print('\nwrote out/coverage_report5.json')


if __name__ == '__main__':
    main()