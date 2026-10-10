"""Final forensic audit - strictly read-only.

Deliberately imports NOTHING from the project's own modules: the candidate XDF is
re-parsed with a fresh reader so that a bug in the generator cannot hide behind
itself. Only the XML/text libraries are used.
"""
import re
import csv
import json
import hashlib
import os
import xml.etree.ElementTree as ET

ORI = '10SW002828_iRom_ori'
MOD = '10SW002828_iRom_stage2'
CAND = 'out/R0C2J772B_CANDIDATE.xdf'
LEGACY = 'out/R0C2J772B_verified.xdf'
AUDIT = 'out/per_table_audit.csv'
SRC_XDF = 'ref/BMW-XDFs-master/B58gen1/00003081501102.xdf'
SRC_REF = 'ref/BMW-XDFs-master/B58gen1/00003081501102_original.bin'
A2L = 'mgflasher-map-packs/A2Ls/B48 B58 Gen 1/Generic/R0C9J8B2B_3081-080_017_002.a2l'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for c in iter(lambda: fh.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def hexint(v):
    return int(str(v), 0)


# ---------------------------------------------------------------- F1
def parse_defs(path):
    """Minimal independent XDF reader: returns the raw facts we need to audit."""
    root = ET.fromstring(open(path, encoding='utf-8').read())
    hdr = root.find('XDFHEADER')
    region = hdr.find('REGION') if hdr is not None else None
    cats = {}
    if hdr is not None:
        for c in hdr.findall('CATEGORY'):
            cats[c.get('index')] = c.get('name')
    defs = []
    for t in root.findall('XDFTABLE'):
        d = dict(title=t.findtext('title'), desc=t.findtext('description'),
                 cat=[cats.get(cm.get('category'), cm.get('category'))
                      for cm in t.findall('CATEGORYMEM')], axes={})
        for a in t.findall('XDFAXIS'):
            e = a.find('EMBEDDEDDATA')
            mm = a.find('MATH')
            d['axes'][a.get('id')] = dict(
                addr=hexint(e.get('mmedaddress')) if (e is not None and e.get('mmedaddress')) else None,
                esize=hexint(e.get('mmedelementsizebits')) if e is not None else 16,
                row=hexint(e.get('mmedrowcount') or 0) if e is not None else 0,
                col=hexint(e.get('mmedcolcount') or 0) if e is not None else 0,
                ic=int(a.findtext('indexcount') or 0),
                eq=(mm.get('equation') if mm is not None else None),
                units=a.findtext('units'), dec=a.findtext('decimalpl'))
        defs.append(d)
    return dict(region_size=region.get('size') if region is not None else None,
                region_start=region.get('startaddress') if region is not None else None,
                desc=hdr.findtext('description') if hdr is not None else None, defs=defs)


def main():
    o = open(ORI, 'rb').read()
    m = open(MOD, 'rb').read()
    doc = parse_defs(CAND)
    defs = doc['defs']
    src = {}
    for t in ET.fromstring(open(SRC_XDF, encoding='utf-8', errors='replace').read()).findall('XDFTABLE'):
        dd = t.findtext('description') or ''
        if dd and dd not in src and 'autogen' not in (t.findtext('title') or ''):
            z = t.find('XDFAXIS[@id="z"]')
            if z is None:
                continue
            e = z.find('EMBEDDEDDATA')
            if e is None or not e.get('mmedaddress'):
                continue
            src[dd] = dict(addr=hexint(e.get('mmedaddress')),
                           esize=hexint(e.get('mmedelementsizebits')),
                           row=hexint(e.get('mmedrowcount') or 0),
                           col=hexint(e.get('mmedcolcount') or 0),
                           ic=int(z.findtext('indexcount') or 0),
                           eq=(z.find('MATH').get('equation') if z.find('MATH') is not None else 'X'))

    conf = {}
    for r in csv.DictReader(open(AUDIT)):
        conf[(r['desc'], r['user_addr'])] = r

    findings, hard = [], []
    seen = set()
    KMAX = {'KL_MD_K_MAX_VL_HS': 0x3F9D0, 'KL_MD_K_MAX_VL': 0x3F9D0,
            'KL_MD_K_MAX_RST_HS': 0x3F9D0, 'KL_MD_K_MAX_RST': 0x3F9D0,
            'KL_MD_K_MAX_BST_HS': 0x3F9D0, 'KL_MD_K_MAX_BST': 0x3F9D0}

    for d in defs:
        desc = d['desc'] or ''
        z = d['axes'].get('z')
        if not z or not z['addr']:
            hard.append((desc, 'no z data axis'))
            continue
        row = z['row'] or z['ic']
        col = z['col'] or z['ic']
        span = row * col * z['esize'] // 8
        if z['addr'] + span > len(o):
            hard.append((desc, 'data out of file bounds'))
        if desc in seen:
            hard.append((desc, 'DUPLICATE definition'))
        seen.add(desc)
        if desc.startswith('KL_MD_K_MAX'):
            continue
        s = src.get(desc)
        if s is None:
            findings.append((desc, 'not present in SP15 source XDF'))
            continue
        delta = z['addr'] - s['addr']
        if z['esize'] != s['esize'] or (s['row'] and row != s['row']) or (s['col'] and col != s['col']):
            hard.append((desc, 'geometry differs from source'))
        if z['eq'] != s['eq']:
            findings.append((desc, 'formula differs from source (intentional?): %s vs %s' % (z['eq'], s['eq'])))
        for role in ('x', 'y'):
            a = d['axes'].get(role)
            sa = None
            for t in ET.fromstring(open(SRC_XDF, encoding='utf-8', errors='replace').read()).findall('XDFTABLE'):
                pass
    print('=== F1  candidate XDF, independently parsed ===')
    print('  REGION start=%s size=%s' % (doc['region_start'], doc['region_size']))
    print('  description: %s' % (doc['desc'] or '')[:150])
    print('  definitions: %d   unique Bosch names: %d' % (len(defs), len(seen)))
    print('  size matches BIN: %s' % (doc['region_size'] == hex(len(o))))
    print()
    print('  HARD DEFECTS (structural): %d' % len(hard))
    for d_, why in hard:
        print('    %-30s %s' % (d_, why))
    print('  FORMULA DIFFERENCES vs source: %d' % len(findings))
    for d_, why in findings:
        print('    %-30s %s' % (d_, why))

    # formula grammar
    print()
    print('=== F1b formula grammar (target-editor compatibility) ===')
    eqs = {}
    for d in defs:
        for role, a in d['axes'].items():
            if a['eq']:
                eqs.setdefault(a['eq'], 0)
                eqs[a['eq']] += 1
    SIMPLE = re.compile(r'^X(\*|/)[0-9.]+$')
    print('  distinct formulas: %d' % len(eqs))
    for e, n in sorted(eqs.items(), key=lambda kv: -kv[1]):
        cls = 'SIMPLE' if SIMPLE.match(e) else ('COMPOUND' if re.fullmatch(r'[X0-9.*/]+', e) else 'OTHER')
        print('    %-5s x%-3d %s' % (cls, n, e))
    bad = [e for e in eqs if not re.fullmatch(r'[X0-9.*/]+', e)]
    print('  formulas outside the parser-safe set [X0-9.*/]: %d %s' % (len(bad), bad))

    # ---------------------------------------------------------------- F2
    diff = set(i for i in range(len(o)) if o[i] != m[i])
    cells, axes = set(), set()
    for d in defs:
        z = d['axes'].get('z')
        if not z or not z['addr']:
            continue
        row = z['row'] or z['ic']
        col = z['col'] or z['ic']
        cells |= set(range(z['addr'], z['addr'] + row * col * z['esize'] // 8))
        for role in ('x', 'y'):
            a = d['axes'].get(role)
            if a and a['addr'] and a['ic']:
                axes |= set(range(a['addr'], a['addr'] + a['ic'] * a['esize'] // 8))
    both = cells & axes
    cov_cell = diff & cells
    cov_axis = diff & axes
    cov = diff & (cells | axes)
    print()
    print('=== F2  coverage, recomputed ===')
    print('  MD5 %s = %s' % (ORI, md5(ORI)))
    print('  MD5 %s = %s' % (MOD, md5(MOD)))
    print('  sizes: %d / %d' % (len(o), len(m)))
    print('  changed bytes (mask from BINs)      : %d' % len(diff))
    print('  candidate cell bytes (distinct)     : %d' % len(cells))
    print('  candidate axis bytes (distinct)     : %d' % len(axes))
    print('  cell AND axis overlap               : %d' % len(both))
    print('  changed bytes covered by DATA CELLS : %d' % len(cov_cell))
    print('  changed bytes covered by AXES       : %d' % len(cov_axis))
    print('  changed bytes covered by AXES ONLY  : %d' % (len(cov_axis) - len(cov_cell & axes)))
    print('  TOTAL covered (union, dedup)        : %d / %d = %.2f %%'
          % (len(cov), len(diff), 100 * len(cov) / len(diff)))
    print('  UNCOVERED                          : %d' % (len(diff) - len(cov)))

    unc = sorted(diff - cov)
    ranges = []
    for i in unc:
        if ranges and i - ranges[-1][1] <= 64:
            ranges[-1][1] = i
        else:
            ranges.append([i, i])
    out = {'total_changed': len(diff), 'covered': len(cov), 'uncovered': len(unc),
           'coverage_pct': round(100 * len(cov) / len(diff), 2),
           'covered_by_cells': len(cov_cell), 'covered_by_axes_only': len(cov_axis) - len(cov_cell & axes),
           'uncovered_ranges': [{'start': hex(a), 'end': hex(b), 'len': b - a + 1,
                                 'changed': sum(1 for k in range(a, b + 1) if k in diff)}
                                for a, b in ranges]}
    json.dump(out, open('out/uncovered_changed_bytes.json', 'w'), indent=1)
    print()
    print('  uncovered ranges written to out/uncovered_changed_bytes.json (%d ranges)' % len(ranges))
    for a, b in ranges[:12]:
        print('    0x%06X-0x%06X  len=%-5d changed=%d' % (a, b, b - a + 1,
              sum(1 for k in range(a, b + 1) if k in diff)))
    if len(ranges) > 12:
        print('    ... %d more' % (len(ranges) - 12))

    # ---------------------------------------------------------------- F4
    print()
    print('=== F4 integrity ===')
    print('  %-34s %s %d' % (ORI, md5(ORI), os.path.getsize(ORI)))
    print('  %-34s %s %d' % (MOD, md5(MOD), os.path.getsize(MOD)))
    lt = ET.fromstring(open(LEGACY, encoding='utf-8', errors='replace').read())
    print('  %-34s md5=%s tables=%d' % (LEGACY, md5(LEGACY), len(lt.findall('XDFTABLE'))))
    flash = [f for f in os.listdir('.') if re.search(r'\.(bin|hex|s19|ori|mod|hex32)$', f, re.I)]
    print('  flash-like files in working dir: %s' % (flash or 'none'))
    print('  BIN mtimes: ori=%d stage2=%d' % (os.path.getmtime(ORI), os.path.getmtime(MOD)))
    print('  candidate mtime=%d  legacy mtime=%d' % (os.path.getmtime(CAND), os.path.getmtime(LEGACY)))


if __name__ == '__main__':
    main()