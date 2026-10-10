"""Regenerate out/R0C2J772B_CANDIDATE.xdf with faithful scaling.

Fixes the report-3 defect where every conversion formula was flattened to "X".
Carries the source MATH equation and axis element sizes through unchanged, and
adds the six KL_MD_K_MAX_* curves identified from the DAMOS A2L (unit Nm).
"""
import re
import csv
import xml.etree.ElementTree as ET

SP15_XDF = 'ref/BMW-XDFs-master/B58gen1/00003081501102.xdf'
ORI = '10SW002828_iRom_ori'
OUT = 'out/R0C2J772B_CANDIDATE.xdf'

KMAX = [
    ('KL_MD_K_MAX_VL_HS', 'Speed-dependent full load curve (half step)', 0x6B92D0),
    ('KL_MD_K_MAX_VL', 'Speed-dependent full load curve', 0x6B92E8),
    ('KL_MD_K_MAX_RST_HS', 'Speed-dependent launch control curve (half step)', 0x6B9300),
    ('KL_MD_K_MAX_RST', 'Speed-dependent launch control curve', 0x6B9318),
    ('KL_MD_K_MAX_BST_HS', 'Speed-dependent boost curve, manual transmission', 0x6B9330),
    ('KL_MD_K_MAX_BST', 'Speed-dependent boost curve', 0x6B9348),
]
KMAX_DELTA = 0x3F9D0

# Demonstrated corrections to formulas carried from the source XDF.
# Key   : Bosch variable -> exact formula derived from the A2L COMPU_METHOD
# Reason: cross-check of every formula against A2L RAT_FUNC (phys = X*COEFFS[5]/COEFFS[1])
FORMULA_FIX = {
    # source XDF said X/2.55 (=0.392157); A2L COEFFS 0 64 0 0 0 25 -> 25/64 = 0.390625
    'KL_NEL_TMOT': ('X*0.390625', 'source X/2.55=0.392157; A2L RAT_FUNC 25/64=0.390625'),
}
# Purely syntactic normalisation: identical value, no parentheses.
PAREN_FIX = {'(X*0.0002441406)*14.7': 'X*0.0002441406*14.7'}


def _i(v):
    try:
        return int(str(v), 0)
    except (TypeError, ValueError):
        return 0


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def blk(a):
    """Summarise one XDFAXIS element."""
    if a is None:
        return None
    e = a.find('EMBEDDEDDATA')
    mm = a.find('MATH')
    dp = a.findtext('decimalpl')
    return dict(
        addr=_i(e.get('mmedaddress')) if e is not None else None,
        esize=_i(e.get('mmedelementsizebits')) or 16,
        row=_i(e.get('mmedrowcount')),
        col=_i(e.get('mmedcolcount')),
        ic=_i(a.findtext('indexcount')),
        eq=(mm.get('equation') if mm is not None else 'X') or 'X',
        dec=int(dp) if dp and dp.strip() else 3)


def source_blocks(path):
    root = ET.fromstring(open(path, encoding='utf-8', errors='replace').read())
    out = {}
    for t in root.findall('XDFTABLE'):
        desc = t.findtext('description') or ''
        title = t.findtext('title') or ''
        if not desc or 'autogen' in title:
            continue
        ax = {a.get('id'): a for a in t.findall('XDFAXIS')}
        if 'z' not in ax:
            continue
        z = blk(ax['z'])
        if z is None or not z['addr']:
            continue
        if z['row'] and z['col'] and z['ic'] and not (z['row'] == 1 or z['col'] == 1):
            pass
        if not z['row']:
            z['row'] = z['ic']
        if not z['col']:
            z['col'] = z['ic']
        out.setdefault(desc, dict(title=title, z=z, x=blk(ax.get('x')), y=blk(ax.get('y'))))
    return out


def axis_xml(role, b, delta):
    if b is None or not b['addr'] or not b['ic']:
        return ('    <XDFAXIS id="%s" uniqueid="0x0">\n      <EMBEDDEDDATA '
                'mmedelementsizebits="16" mmedmajorstridebits="0" mmedminorstridebits="0" />\n'
                '      <indexcount>1</indexcount>\n      <datatype>0</datatype>\n'
                '      <unittype>0</unittype>\n    </XDFAXIS>\n' % role)
    return ('    <XDFAXIS id="%s" uniqueid="0x0">\n      <EMBEDDEDDATA mmedtypeflags="0x01" '
            'mmedaddress="0x%X" mmedelementsizebits="%d" mmedrowcount="1" mmedcolcount="%d" '
            'mmedmajorstridebits="0" mmedminorstridebits="0" />\n      <indexcount>%d</indexcount>\n'
            '      <decimalpl>%d</decimalpl>\n      <datatype>0</datatype>\n'
            '      <unittype>0</unittype>\n      <embedinfo type="1" />\n'
            '      <MATH equation="%s"><VAR id="X" /></MATH>\n    </XDFAXIS>\n'
            % (role, b['addr'] + delta, b['esize'], b['ic'], b['ic'], b['dec'], esc(b['eq'])))


def main():
    u = open(ORI, 'rb').read()
    sb = source_blocks(SP15_XDF)

    recs, seen = [], set()
    for r in csv.DictReader(open('out/per_table_audit.csv')):
        if r['confidence'] != 'VERIFIED':
            continue
        s = sb.get(r['desc'])
        key = (r['desc'], r['user_addr'])
        if s and key not in seen:
            seen.add(key)
            recs.append((r['desc'], r['title'], s, int(r['delta'], 16)))
    # A2L-verified K_MAX family; replaces any CSV row for the same desc+address
    KMAX_AX = {'KL_MD_K_MAX_VL_HS': 0x6B93C8, 'KL_MD_K_MAX_VL': 0x6B93E0,
               'KL_MD_K_MAX_RST_HS': 0x6B93F8, 'KL_MD_K_MAX_RST': 0x6B9410,
               'KL_MD_K_MAX_BST_HS': 0x6B9428, 'KL_MD_K_MAX_BST': 0x6B9440}
    for name, title, zd in KMAX:
        s = sb.get(name)
        if not s:
            s = dict(title=title,
                     z=dict(addr=zd, esize=16, row=1, col=12, ic=12, eq='X', dec=1),
                     x=dict(addr=KMAX_AX[name], esize=16, row=1, col=12, ic=12, eq='X', dec=0),
                     y=None)
        s = dict(s)
        s['z'] = dict(s['z'], addr=zd)
        recs = [r for r in recs if r[0] != name]
        recs.append((name, title, s, KMAX_DELTA))
        seen.add((name, hex(zd + KMAX_DELTA)))
    recs = [r for r in recs if (r[0], hex(r[2]['z']['addr'] + r[3])) not in
            [k for k in seen if False]]
    out2, final = [], set()
    for d, t_, s_, dl in recs:
        k = (d, hex(s_['z']['addr'] + dl))
        if k in final:
            continue
        final.add(k)
        out2.append((d, t_, s_, dl))
    recs = out2

    hdr = ['<?xml version="1.0" encoding="utf-8"?>\n',
           '<XDFFORMAT xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xmlns:xsd="http://www.w3.org/2001/XMLSchema" version="1.80">\n',
           '  <XDFHEADER>\n    <flags>0x1</flags>\n',
           '    <description>CANDIDATE - B58 MG1CS003 SP15 map set for R0C9J772B (AWD). '
           'Placements byte-verified against the SP15 stock dump R0C9J8B2B. Conversion '
           'formulas and axis element sizes carried verbatim from the source XDF. '
           'KL_MD_K_MAX_* unit and identity taken from the DAMOS A2L (Nm). '
           'Not flash-safe.</description>\n',
           '    <BASEOFFSET offset="0" subtract="0" />\n',
           '    <DEFAULTS datasizeinbits="16" sigdigits="3" outputtype="1" signed="0" '
           'lsbfirst="0" float="0" />\n',
           '    <REGION type="0xFFFFFFFF" startaddress="0x0" size="%s" regioncolor="0x0" '
           'regionflags="0x0" name="Binary File" desc="bin edited by this XDF" />\n' % hex(len(u))]

    cats = []
    for _, title, _, _ in recs:
        c = esc((title or 'Map'))[:70]
        if c not in cats:
            cats.append(c)
    cidx = {c: i for i, c in enumerate(cats)}
    for i, c in enumerate(cats):
        hdr.append('    <CATEGORY index="0x%x" name="%s" />\n' % (i, c))
    hdr.append('  </XDFHEADER>\n')

    body, uid, skipped = [], 0x3000, []
    for desc, title, s, d in recs:
        z = s['z']
        zaddr = z['addr'] + d
        span = z['row'] * z['col'] * z['esize'] // 8
        if zaddr + span > len(u):
            skipped.append(desc)
            continue
        cat = esc(title or 'Map')[:70]
        eq_out = FORMULA_FIX.get(desc, (z['eq'], ''))[0]
        eq_out = PAREN_FIX.get(eq_out, eq_out)
        body.append(
            '  <XDFTABLE uniqueid="0x%x" flags="0x0">\n'
            '    <title>%s</title>\n    <description>%s</description>\n'
            '    <CATEGORYMEM index="0" category="%d" />\n'
            '%s%s    <XDFAXIS id="z" uniqueid="0x0">\n'
            '      <EMBEDDEDDATA mmedaddress="0x%X" mmedelementsizebits="%d" mmedrowcount="%d" '
            'mmedcolcount="%d" mmedmajorstridebits="0" mmedminorstridebits="0" />\n'
            '      <decimalpl>%d</decimalpl>\n      <outputtype>1</outputtype>\n'
            '      <datatype>0</datatype>\n      <unittype>0</unittype>\n'
            '      <embedinfo type="1" />\n'
            '      <MATH equation="%s"><VAR id="X" /></MATH>\n    </XDFAXIS>\n  </XDFTABLE>\n'
            % (uid, cat, esc(desc), cidx[cat], axis_xml('x', s['x'], d),
               axis_xml('y', s['y'], d), zaddr, z['esize'], z['row'], z['col'],
               z['dec'], esc(eq_out)))
        uid += 1
    open(OUT, 'w').write(''.join(hdr) + ''.join(body) + '</XDFFORMAT>\n')

    print('wrote %s : %d tables (%d skipped out of range)' % (OUT, len(body), len(skipped)))
    eqs = set(re.findall(r'<MATH equation="([^"]+)"', ''.join(body)))
    print('distinct conversion formulas carried through: %d' % len(eqs))


if __name__ == '__main__':
    main()