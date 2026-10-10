"""Validation of out/R0C2J772B_manual_inspection.xdf - read-only."""
import re
import csv
import json
import hashlib
import xml.etree.ElementTree as ET

XDF = 'out/R0C2J772B_manual_inspection.xdf'
ORI = '10SW002828_iRom_ori'
MOD = '10SW002828_iRom_stage2'
SIZE = 8126464
SAFE_EQ = re.compile(r'^[X0-9.*/]+$')


def hi(v):
    return int(str(v), 0)


def main():
    o = open(ORI, 'rb').read()
    m = open(MOD, 'rb').read()
    raw = open(XDF, encoding='utf-8').read()

    print('=== 1 XML ===')
    root = ET.fromstring(raw)
    print('  parses: OK   root=%s  version=%s'
          % (root.tag, root.get('version')))
    reg = root.find('XDFHEADER/REGION')
    print('  REGION start=%s size=%s -> decimal %d  BIN=%d  MATCH=%s'
          % (reg.get('startaddress'), reg.get('size'), hi(reg.get('size')), SIZE,
             hi(reg.get('size')) == SIZE))
    cats = {hi(c.get('index')) for c in root.findall('XDFHEADER/CATEGORY')}

    tabs = root.findall('XDFTABLE')
    print()
    print('=== 2 per-table validation ===')
    errs = []
    cells = axes = naddr = 0
    rows = []
    for t in tabs:
        d = t.findtext('description') or ''
        cat = t.find('CATEGORYMEM')
        if cat is None or hi(cat.get('category')) not in cats:
            errs.append((d, 'category index not declared'))
        A = {}
        for a in t.findall('XDFAXIS'):
            e = a.find('EMBEDDEDDATA')
            n = int(a.findtext('indexcount') or 0)
            A[a.get('id')] = dict(
                addr=hi(e.get('mmedaddress')) if e is not None and e.get('mmedaddress') else None,
                esize=hi(e.get('mmedelementsizebits')) if e is not None else 16,
                row=hi(e.get('mmedrowcount') or 0) if e is not None else 0,
                col=hi(e.get('mmedcolcount') or 0) if e is not None else 0,
                ic=n, eq=a.find('MATH').get('equation') if a.find('MATH') is not None else None)
        z = A.get('z')
        if not z or z['addr'] is None:
            errs.append((d, 'no z data address'))
            continue
        row = z['row'] or z['ic']
        col = z['col'] or z['ic']
        if not row or not col or row < 1 or col < 1:
            errs.append((d, 'impossible dimensions'))
        span = row * col * z['esize'] // 8
        if z['addr'] + span > SIZE:
            errs.append((d, 'data span exceeds BIN (%d bytes)' % (z['addr'] + span)))
        cells += span
        for role in ('x', 'y'):
            a = A.get(role)
            if not a:
                errs.append((d, 'missing %s axis' % role))
                continue
            if a['eq'] is not None and not SAFE_EQ.match(a['eq']):
                errs.append((d, 'unsafe formula in %s axis: %s' % (role, a['eq'])))
            if a['addr'] is None:
                naddr += 1
                if a['ic'] != 1:
                    errs.append((d, '%s axis has no address but indexcount != 1' % role))
                continue
            nb = a['ic'] * a['esize'] // 8
            if a['addr'] + nb > SIZE:
                errs.append((d, '%s axis exceeds BIN' % role))
            if role == 'x' and col > 1 and a['ic'] != col:
                errs.append((d, 'x axis points %d != %d columns' % (a['ic'], col)))
            if role == 'y' and row > 1 and a['ic'] != row:
                errs.append((d, 'y axis points %d != %d rows' % (a['ic'], row)))
            axes += nb
        # decode stock values
        vals = []
        for i in range(row * col):
            off = z['addr'] + i * (z['esize'] // 8)
            vals.append(int.from_bytes(o[off:off + z['esize'] // 8], 'big'))
        vmod = []
        for i in range(row * col):
            off = z['addr'] + i * (z['esize'] // 8)
            vmod.append(int.from_bytes(m[off:off + z['esize'] // 8], 'big'))
        rows.append(dict(desc=d, addr='0x%X' % z['addr'], dims='%dx%d' % (row, col),
                         bits=z['esize'], points=row * col, eq=z['eq'],
                         eq_safe=bool(z['eq'] and SAFE_EQ.match(z['eq'])),
                         axes_addr=sum(1 for r in ('x', 'y') if A.get(r) and A[r]['addr']),
                         axes_none=naddr if False else sum(1 for r in ('x', 'y')
                                                           if A.get(r) and A[r]['addr'] is None),
                         vmin=min(vals), vmax=max(vals),
                         stock_vs_stage2=sum(1 for a, b in zip(vals, vmod) if a != b)))

    print('  tables=%d  errors=%d' % (len(tabs), len(errs)))
    for d, why in errs:
        print('    ERROR %-30s %s' % (d[:30], why))
    if not errs:
        print('  no structural errors')

    eqs = set()
    for t in tabs:
        for a in t.findall('XDFAXIS'):
            mm = a.find('MATH')
            if mm is not None and mm.get('equation'):
                eqs.add(mm.get('equation'))
    unsafe = [e for e in eqs if not SAFE_EQ.match(e)]
    print()
    print('=== 3 formulas ===')
    print('  distinct equations=%d  outside safe set=%d %s' % (len(eqs), len(unsafe), unsafe))

    print()
    print('=== 4 coverage ===')
    cell_set, axis_set = set(), set()
    for t in tabs:
        A = {}
        for a in t.findall('XDFAXIS'):
            e = a.find('EMBEDDEDDATA')
            A[a.get('id')] = (hi(e.get('mmedaddress')) if e is not None and e.get('mmedaddress') else None,
                              hi(e.get('mmedelementsizebits')) if e is not None else 16,
                              hi(e.get('mmedrowcount') or 0), hi(e.get('mmedcolcount') or 0),
                              int(a.findtext('indexcount') or 0))
        z = A['z']
        row = z[2] or z[4]
        col = z[3] or z[4]
        cell_set |= set(range(z[0], z[0] + row * col * z[1] // 8))
        for r in ('x', 'y'):
            a = A[r]
            if a[0] is not None and a[4]:
                axis_set |= set(range(a[0], a[0] + a[4] * a[1] // 8))
    diff = set(i for i in range(SIZE) if o[i] != m[i])
    print('  distinct data-cell bytes : %d' % len(cell_set))
    print('  distinct axis bytes     : %d' % len(axis_set))
    print('  cell AND axis overlap   : %d' % len(cell_set & axis_set))
    print('  changed bytes covered   : %d / %d = %.2f%%'
          % (len(diff & (cell_set | axis_set)), len(diff),
             100 * len(diff & (cell_set | axis_set)) / len(diff)))
    print('  tables whose values differ stock vs stage2: %d'
          % sum(1 for r in rows if r['stock_vs_stage2']))

    print()
    print('=== 5 TunerPro format comparison ===')
    ok = {
        'xml decl + XDFFORMAT 1.80': raw.startswith('<?xml') and 'version="1.80"' in raw,
        'XDFHEADER present': root.find('XDFHEADER') is not None,
        'BASEOFFSET present': root.find('XDFHEADER/BASEOFFSET') is not None,
        'DEFAULTS present': root.find('XDFHEADER/DEFAULTS') is not None,
        'REGION present': reg is not None,
        'every CATEGORYMEM resolves': not any('category' in e for _, e in errs),
        'every table has title+description': all(
            (t.findtext('title') or '') and (t.findtext('description') or '') for t in tabs),
        'z axes carry MATH/VAR': all(
            t.find('XDFAXIS[@id="z"]/MATH/VAR') is not None for t in tabs),
        'z axes are unsigned (datatype 0)': all(
            (t.find('XDFAXIS[@id="z"]/datatype') is not None
             and t.find('XDFAXIS[@id="z"]/datatype').text == '0') for t in tabs),
        'no table has duplicate uniqueid': len({t.get('uniqueid') for t in tabs}) == len(tabs),
    }
    for k, v in ok.items():
        print('  %-42s %s' % (k, 'PASS' if v else 'FAIL'))

    with open('out/manual_xdf_validation.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    json.dump({'tables': len(tabs), 'errors': len(errs), 'eqs': len(eqs),
               'unsafe_eqs': unsafe, 'coverage': len(diff & (cell_set | axis_set)),
               'total_changed': len(diff),
               'address_less_axes': sum(r['axes_none'] for r in rows),
               'format_checks': ok}, open('out/manual_xdf_validation.json', 'w'), indent=1)
    print()
    print('wrote out/manual_xdf_validation.csv and .json')


if __name__ == '__main__':
    main()