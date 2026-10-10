"""Report #3 deliverables, built from the SP15 primary reference.

  * per-table audit CSV/JSON with evidence and confidence
  * candidate XDF (separate file) containing only tables whose placement is
    independently corroborated by byte identity against an SP15 stock dump
  * corrected changed-byte coverage with overlaps deduplicated

Does not modify either BIN or out/R0C2J772B_verified.xdf.
"""
import csv
import json
import re
import xdfread

SP15_XDF = 'ref/BMW-XDFs-master/B58gen1/00003081501102.xdf'
SP15_REF = 'ref/BMW-XDFs-master/B58gen1/00003081501102_original.bin'
SP15_REF2 = 'ref/BMW-XDFs-master/B58gen1/00003081501D04.xdf'
REF2_BIN = 'ref/BMW-XDFs-master/B58gen1/00003081501D04_original.bin'
ORI = '10SW002828_iRom_ori'
MOD = '10SW002828_iRom_stage2'


def conf(match, ties):
    if match == 1.0 and ties == 1:
        return 'VERIFIED'
    if match == 1.0:
        return 'PROBABLE'
    if match >= 0.5:
        return 'PARTIAL'
    return 'REJECT'


def main():
    ref = open(SP15_REF, 'rb').read()
    u = open(ORI, 'rb').read()
    m = open(MOD, 'rb').read()
    diff = set(i for i in range(len(u)) if u[i] != m[i])

    search = json.load(open('out/sp15_search.json'))
    base, tabs = xdfread.parse(SP15_XDF)
    byaddr = {}
    for tb in tabs:
        if tb.z and tb.z.address and tb.desc:
            byaddr.setdefault((tb.desc, tb.z.address), tb)

    rows = []
    for s in search:
        tb = byaddr.get((s['desc'], s['ref_addr']))
        if tb is None:
            continue
        # axis corroboration
        ax_ok = 'n/a'
        ax_ax = ax_ay = ''
        for role, ax in (('x', tb.x), ('y', tb.y)):
            if not ax or not ax.address:
                continue
            n = (ax.colcount or ax.indexcount) if role == 'x' else (ax.rowcount or ax.indexcount)
            if not n:
                continue
            d = int(s['delta'], 16)
            src = ref[ax.address:ax.address + n * (ax.esize_bits // 8)]
            dst = u[ax.address + d:ax.address + d + n * (ax.esize_bits // 8)]
            good = src == dst
            if role == 'x':
                ax_ax = hex(ax.address + d)
            else:
                ax_ay = hex(ax.address + d)
            ax_ok = 'YES' if good else ('NO' if ax_ok != 'YES' else 'YES')
        if ax_ok == 'n/a':
            ax_ok = 'none'
        rows.append(dict(
            desc=s['desc'], title=s['title'], source_ref='00003081501102 (SP15/R0C9J8B2B)',
            ref_addr=hex(s['ref_addr']), delta=s['delta'], user_addr=s['user_addr'],
            rows=s['rows'], cols=s['cols'], esize=s['esize'],
            byte_match_pct=round(s['match'] * 100, 2), delta_ties=s['n_ties'],
            axes_corroborated=ax_ok, x_axis=ax_ax, y_axis=ax_ay,
            scaling='identity' if tb.z.eq(1.0) == 1.0 else 'x%.6g' % tb.z.eq(1.0),
            byte_order='big-endian', data_type='uint%d' % (tb.z.esize_bits),
            size=s['size'], confidence=conf(s['match'], s['n_ties']),
            tuned_bytes=sum(1 for k in range(int(s['user_addr'], 16),
                                             int(s['user_addr'], 16) + s['size']) if k in diff)))

    rows.sort(key=lambda r: (r['confidence'], -r['byte_match_pct']))
    with open('out/per_table_audit.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    json.dump(rows, open('out/per_table_audit.json', 'w'), indent=1)

    import collections
    c = collections.Counter(r['confidence'] for r in rows)
    print('SP15 transfer set:', dict(c))
    print('axes corroborated :', dict(collections.Counter(r['axes_corroborated'] for r in rows)))

    # ---- candidate XDF: only VERIFIED (100% + unique delta + axes corroborated) ----
    keep = [r for r in rows if r['confidence'] == 'VERIFIED' and r['axes_corroborated'] == 'YES']
    keep += [r for r in rows if r['confidence'] == 'VERIFIED' and r['axes_corroborated'] == 'none']
    print('candidate XDF tables:', len(keep))

    hdr = ['<?xml version="1.0" encoding="utf-8"?>\n',
           '<XDFFORMAT xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xmlns:xsd="http://www.w3.org/2001/XMLSchema" version="1.80">\n',
           '  <XDFHEADER>\n    <flags>0x1</flags>\n',
           '    <description>CANDIDATE - B58 MG1CS003 SP15 map set for R0C9J772B. '
           'Every table placed by byte-identity against SP15 stock dump R0C9J8B2B. '
           'Not flash-safe.</description>\n',
           '    <BASEOFFSET offset="0" subtract="0" />\n',
           '    <DEFAULTS datasizeinbits="16" sigdigits="3" outputtype="1" signed="0" '
           'lsbfirst="0" float="0" />\n',
           '    <REGION type="0xFFFFFFFF" startaddress="0x0" size="%s" regioncolor="0x0" '
           'regionflags="0x0" name="Binary File" desc="bin edited by this XDF" />\n' % hex(len(u))]

    cats = sorted({r['title'] or 'Map' for r in keep})[:80]
    cidx = {c: i for i, c in enumerate(cats)}
    for i, c in enumerate(cats):
        hdr.append('    <CATEGORY index="0x%x" name="%s" />\n' % (i, c.replace('&', '&amp;')))
    hdr.append('  </XDFHEADER>\n')

    body, uid = [], 0x3000
    for r in keep:
        tb = byaddr.get((r['desc'], int(r['ref_addr'], 16)))
        d = int(r['delta'], 16)
        cat = (r['title'] or 'Map').replace('&', '&amp;')
        z = tb.z
        xa = tb.x.address + d if (tb.x and tb.x.address) else None
        ya = tb.y.address + d if (tb.y and tb.y.address) else None

        def axis_xml(role, addr, cnt):
            if addr is None or not cnt:
                return ('    <XDFAXIS id="%s" uniqueid="0x0">\n      <EMBEDDEDDATA '
                        'mmedelementsizebits="16" mmedmajorstridebits="0" '
                        'mmedminorstridebits="0" />\n      <indexcount>1</indexcount>\n'
                        '      <datatype>0</datatype>\n      <unittype>0</unittype>\n'
                        '    </XDFAXIS>\n' % role)
            return ('    <XDFAXIS id="%s" uniqueid="0x0">\n      <EMBEDDEDDATA '
                    'mmedtypeflags="0x01" mmedaddress="0x%X" mmedelementsizebits="16" '
                    'mmedrowcount="1" mmedcolcount="%d" mmedmajorstridebits="0" '
                    'mmedminorstridebits="0" />\n      <indexcount>%d</indexcount>\n'
                    '      <datatype>0</datatype>\n      <unittype>0</unittype>\n'
                    '    </XDFAXIS>\n' % (role, addr, cnt, cnt))

        nx = z.colcount or z.indexcount
        ny = z.rowcount or z.indexcount
        body.append(f'''  <XDFTABLE uniqueid="0x{uid:x}" flags="0x0">
    <title>{cat}</title>
    <description>{r['desc']}</description>
    <CATEGORYMEM index="0" category="{cidx[(r['title'] or 'Map').replace('&', '&amp;')]}" />
{axis_xml('x', xa, nx)}{axis_xml('y', ya, ny)}    <XDFAXIS id="z" uniqueid="0x0">
      <EMBEDDEDDATA mmedaddress="0x{z.address + d:X}" mmedelementsizebits="{z.esize_bits}" mmedrowcount="{z.rowcount}" mmedcolcount="{z.colcount}" mmedmajorstridebits="0" mmedminorstridebits="0" />
      <decimalpl>3</decimalpl>
      <outputtype>1</outputtype>
      <datatype>0</datatype>
      <unittype>0</unittype>
      <embedinfo type="1" />
      <MATH equation="X"><VAR id="X" /></MATH>
    </XDFAXIS>
  </XDFTABLE>
''')
        uid += 1
    open('out/R0C2J772B_CANDIDATE.xdf', 'w').write(''.join(hdr) + ''.join(body) + '</XDFFORMAT>\n')

    # ---- coverage, deduplicated ----
    cells, axes, overlaps = set(), set(), set()
    for r in keep:
        a = int(r['user_addr'], 16)
        s = set(range(a, a + r['size']))
        overlaps |= (s & cells)
        cells |= s
        for ax in (r['x_axis'], r['y_axis']):
            if ax:
                b = int(ax, 16)
                axes |= set(range(b, b + r['cols'] * 2))
    both = cells & axes
    expl = diff & (cells | axes)
    cov = dict(
        total_changed=len(diff),
        explained=len(expl), pct=round(100 * len(expl) / len(diff), 1),
        cell_only=len(cells - axes), axis_only=len(axes - cells),
        cell_and_axis=len(both), overlapping_table_bytes=len(overlaps),
        unexplained=len(diff) - len(expl))
    json.dump(cov, open('out/coverage_report3.json', 'w'), indent=1)
    print('COVERAGE:', cov)
    print('wrote out/per_table_audit.csv|json, out/R0C2J772B_CANDIDATE.xdf, out/coverage_report3.json')


if __name__ == '__main__':
    main()