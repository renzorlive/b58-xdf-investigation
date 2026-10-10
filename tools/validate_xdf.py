#!/usr/bin/env python3
"""Cross-platform validator for the generated XDFs.

Usage (Windows / Linux / macOS, Python 3.8+):
    python tools/validate_xdf.py                 # structural checks only
    python tools/validate_xdf.py --bin <path>    # also decode values from a BIN

Checks: XML parse, XDF structure, REGION size, table/axis geometry, formula safety,
address bounds, duplicate uniqueids, and (with --bin) raw decode against the binary.
Pure standard library - no dependencies.
"""
import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_XDFS = [
    'out/R0C2J772B_display.xdf',
    'out/R0C2J772B_ignition_timing.xdf',
    'out/R0C2J772B_manual_inspection.xdf',
]
SAFE_EQ = re.compile(r'^[X0-9.*/]+$')


def hi(v):
    return int(str(v), 0)


def validate(path, bindata=None):
    errs, warns, info = [], [], {}
    try:
        root = ET.parse(path).getroot()
    except Exception as exc:
        return ['XML parse failed: %s' % exc], warns, info

    if root.tag != 'XDFFORMAT':
        errs.append('root tag is %s, expected XDFFORMAT' % root.tag)
    hdr = root.find('XDFHEADER')
    if hdr is None:
        errs.append('XDFHEADER missing')
        return errs, warns, info
    for req in ('BASEOFFSET', 'DEFAULTS', 'REGION'):
        if hdr.find(req) is None:
            errs.append('XDFHEADER/%s missing' % req)
    reg = hdr.find('REGION')
    rsize = hi(reg.get('size')) if reg is not None and reg.get('size') else 0
    info['region_size'] = rsize

    cats = {hi(c.get('index')) for c in hdr.findall('CATEGORY') if c.get('index') is not None}
    tabs = root.findall('XDFTABLE')
    info['tables'] = len(tabs)
    info['categories'] = len(cats)
    uid_seen, eqs, noaddr = set(), set(), 0
    cells = 0

    for t in tabs:
        d = t.findtext('description') or t.findtext('title') or '?'
        cm = t.find('CATEGORYMEM')
        if cm is None or hi(cm.get('category')) not in cats:
            errs.append('%s: CATEGORYMEM does not resolve' % d[:40])
        u = t.get('uniqueid')
        if u in uid_seen:
            errs.append('%s: duplicate uniqueid %s' % (d[:40], u))
        uid_seen.add(u)
        if not (t.findtext('title') or '').strip():
            errs.append('%s: empty title' % d[:40])
        A = {}
        for a in t.findall('XDFAXIS'):
            e = a.find('EMBEDDEDDATA')
            mm = a.find('MATH')
            if mm is not None and mm.get('equation'):
                eq = mm.get('equation')
                eqs.add(eq)
                if not SAFE_EQ.match(eq):
                    errs.append('%s: unsafe formula %r' % (d[:40], eq))
            addr = hi(e.get('mmedaddress')) if (e is not None and e.get('mmedaddress')) else None
            ic = int(a.findtext('indexcount') or 0)
            A[a.get('id')] = dict(addr=addr, esz=hi(e.get('mmedelementsizebits')) if e is not None else 16,
                                 row=hi(e.get('mmedrowcount') or 0), col=hi(e.get('mmedcolcount') or 0),
                                 ic=ic)
            if addr is None:
                noaddr += 1
                if ic != 1:
                    errs.append('%s: %s axis has no address but indexcount=%d' % (d[:40], a.get('id'), ic))
        z = A.get('z')
        if not z or z['addr'] is None:
            errs.append('%s: no z data axis' % d[:40])
            continue
        row = z['row'] or z['ic']
        col = z['col'] or z['ic']
        if not row or not col:
            errs.append('%s: zero dimensions' % d[:40])
            continue
        span = row * col * z['esz'] // 8
        if rsize and z['addr'] + span > rsize:
            errs.append('%s: span exceeds REGION (0x%X+%d)' % (d[:40], z['addr'], span))
        cells += span
        for role, key in (('x', 'col'), ('y', 'row')):
            a = A.get(role)
            if not a:
                errs.append('%s: missing %s axis' % (d[:40], role))
                continue
            if a['addr'] is not None and a['ic'] > 1:
                n = {'col': col, 'row': row}[key]
                if a['ic'] != n:
                    errs.append('%s: %s axis has %d points, table has %d'
                                % (d[:40], role, a['ic'], n))
        if bindata:
            vals = []
            for i in range(row * col):
                off = z['addr'] + i * (z['esz'] // 8)
                vals.append(int.from_bytes(bindata[off:off + z['esz'] // 8], 'big'))
            info.setdefault('decoded', []).append((d, min(vals), max(vals)))
    info['distinct_formulas'] = len(eqs)
    info['address_less_axes'] = noaddr
    info['mapped_bytes'] = cells
    return errs, warns, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bin', help='path to a BIN to decode values from')
    ap.add_argument('xdfs', nargs='*', help='XDF files (default: the two deliverables)')
    a = ap.parse_args()
    bindata = open(a.bin, 'rb').read() if a.bin else None
    files = a.xdfs or [os.path.join(ROOT, p) for p in DEFAULT_XDFS]
    rc = 0
    for f in files:
        errs, warns, info = validate(f, bindata)
        print('=' * 70)
        print(os.path.basename(f))
        if not os.path.exists(f):
            print('  MISSING - expected at %s' % f)
            rc = 1
            continue
        print('  region size      : %s' % info.get('region_size'))
        print('  tables           : %s' % info.get('tables'))
        print('  categories       : %s' % info.get('categories'))
        print('  distinct formulas: %s' % info.get('distinct_formulas'))
        print('  address-less axes: %s' % info.get('address_less_axes'))
        print('  mapped bytes     : %s' % info.get('mapped_bytes'))
        if bindata is not None:
            print('  bin size         : %d  (decode performed)' % len(bindata))
            for d, lo, hi in (info.get('decoded') or [])[:6]:
                print('     %-42s raw %d..%d' % (d[:42], lo, hi))
        if errs:
            print('  ERRORS (%d):' % len(errs))
            for e in errs:
                print('    - %s' % e)
            rc = 1
        else:
            print('  RESULT           : PASS - no errors')
    print('=' * 70)
    return rc


if __name__ == '__main__':
    sys.exit(main())
