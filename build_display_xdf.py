#!/usr/bin/env python3
"""Merge manual_inspection + ignition_timing into one display XDF.

Both files load in TunerPro. This combines them into a single XDF with unique
table ids and a unified category tree, so one file is all the user needs.

Three tables are dropped, not copied: UNVERIFIED_REGION_70318B / _7032CB /
_70340B are 133-byte raw windows that lie entirely inside KF_ZW_S_PF1, KF_ZW_PF2
and KF_ZW_PF1 respectively. The ignition tables supersede them, and keeping both
would give the same bytes two different meanings.

Byte-for-byte identical to the source tables: only table ids, category
assignment and ordering change.
"""
import os
import xml.etree.ElementTree as ET
from collections import Counter

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_MANUAL = os.path.join(ROOT, 'out', 'R0C2J772B_manual_inspection.xdf')
SRC_TIMING = os.path.join(ROOT, 'out', 'R0C2J772B_ignition_timing.xdf')
OUT = os.path.join(ROOT, 'out', 'R0C2J772B_display.xdf')

DROP = {
    'UNVERIFIED_REGION_70318B',
    'UNVERIFIED_REGION_7032CB',
    'UNVERIFIED_REGION_70340B',
}


def zspan(t):
    z = t.find('XDFAXIS[@id="z"]/EMBEDDEDDATA')
    if z is None or not z.get('mmedaddress'):
        return None
    a = int(z.get('mmedaddress'), 0)
    b = int(z.get('mmedelementsizebits'))
    rc = int(z.get('mmedrowcount') or 0)
    cc = int(z.get('mmedcolcount') or 0)
    return a, a + rc * cc * b // 8


def main():
    man = ET.parse(SRC_MANUAL).getroot()
    tim = ET.parse(SRC_TIMING).getroot()
    size = int(man.find('XDFHEADER/REGION').get('size'), 0)

    # Disambiguate duplicate titles. R0C2J772B_manual_inspection.xdf contains two
    # distinct tables sharing one German title (different addresses: 0x6D4EAC and
    # 0x6EF114, different A2L symbols). Left alone they are indistinguishable in the
    # TunerPro tree, so the address is appended to make each row identifiable.
    dup = set()
    for title, n in Counter(t.findtext('title') for t in man.findall('XDFTABLE')).items():
        if n > 1:
            dup.add(title)

    # collect manual categories in their original order
    cats = []
    seen = set()
    for c in man.findall('XDFHEADER/CATEGORY'):
        idx = int(c.get('index'), 0)
        if idx not in seen:
            seen.add(idx)
            cats.append((idx, c.get('name') or c.get('type') or 'cat%d' % idx))
    next_cat = max(seen) + 1 if seen else 0

    timing_cat = tim.find('XDFHEADER/CATEGORY')
    timing_cat_index = next_cat
    cats.append((next_cat, timing_cat.get('name') or 'Ignition timing'))

    uid = 1
    out_tabs = []
    retitled = 0

    # ---- manual tables, minus the superseded windows ----
    dropped = []
    for t in man.findall('XDFTABLE'):
        title = t.findtext('title')
        if title.split()[0] in DROP:
            dropped.append(title)
            continue
        t = copy_table(t)
        if title in dup:
            z = t.find('XDFAXIS[@id="z"]/EMBEDDEDDATA')
            t.find('title').text = '%s [0x%06X]' % (title, int(z.get('mmedaddress'), 0))
            retitled += 1
        t.set('uniqueid', str(uid))
        uid += 1
        out_tabs.append(t)

    # ---- timing tables, re-categorised ----
    ntim = 0
    for t in tim.findall('XDFTABLE'):
        t = copy_table(t)
        t.set('uniqueid', str(uid))
        uid += 1
        for cm in t.findall('CATEGORYMEM'):
            cm.set('index', '0')
            cm.set('category', str(timing_cat_index))
        out_tabs.append(t)
        ntim += 1

    root = ET.Element('XDFFORMAT', version='1.80')
    hdr = ET.SubElement(root, 'XDFHEADER')
    ET.SubElement(hdr, 'flags').text = '0x1'
    d = ET.SubElement(hdr, 'description')
    d.text = ('Combined display XDF for BMW B58 / MG1CS003, EPK R0C2J772B, '
              'EPST R0C9J772B, PST S15A-17-11-490, HW 10SW002828.\n\n'
              'Merges %d inspection tables with %d ignition-timing tables into one '
              'file. Load against the matching 8126464-byte BIN. Do not write to the ECU.\n\n'
              'Ignition section: map names, dimensions and the x0.5 deg conversion come '
              'from the Bosch A2L R0C9J8B2B_3081-080_017_002.a2l, which describes '
              'S15A-18. This target is S15A-17, so identity, signedness, scaling, units '
              'and axis semantics are INHERITED, not proven for this image. Addresses and '
              'byte spans were verified against the target binary itself.\n\n'
              'Three raw [UNVERIFIED] windows from the inspection set are omitted '
              '(70318B, 7032CB, 70340B): their bytes are now identified as KF_ZW_S_PF1, '
              'KF_ZW_PF2 and KF_ZW_PF1, and are shown with real axes in the ignition '
              'section instead.\n\n'
              'Exploratory display only. Not a validated tuning definition.'
              % (len(out_tabs) - ntim, ntim))
    # copy DEFAULTS + REGION verbatim from manual
    for tag in ('XDFAPPINFO', 'BASEOFFSET', 'DEFAULTS', 'REGION'):
        src = man.find('XDFHEADER/' + tag)
        if src is not None:
            hdr.append(src)
    for idx, name in cats:
        ET.SubElement(hdr, 'CATEGORY', index=str(idx), type='0', name=name)

    for t in out_tabs:
        root.append(t)

    _write(root)
    return len(out_tabs), ntim, dropped, size, retitled


def copy_table(t):
    import copy
    return copy.deepcopy(t)


def _write(root):
    import re
    ET.register_namespace('', '')
    xml = ET.tostring(root, encoding='unicode')
    # pretty-print with 2-space indent, CRLF (TunerPro-validated form)
    import xml.dom.minidom as md
    pretty = md.parseString(xml.encode('utf-8')).toprettyxml(indent='  ')
    lines = [ln for ln in pretty.split('\n') if ln.strip() != '']
    body = '\r\n'.join(lines[1:]) + '\r\n'
    head = lines[0].replace("<?xml version=\"1.0\" ?>", '<?xml version="1.0" encoding="utf-8"?>')
    with open(OUT, 'w', encoding='utf-8', newline='') as fh:
        fh.write(head + '\r\n')
        fh.write(body)


if __name__ == '__main__':
    n, ntim, dropped, size, retitled = main()
    print('wrote %s' % OUT)
    print('  tables: %d  (%d inspection + %d ignition)' % (n, n - ntim, ntim))
    print('  dropped (superseded by ignition tables): %s' % ', '.join(sorted(dropped)))
    print('  retitled (duplicate titles disambiguated): %d' % retitled)
    print('  REGION size: %d (0x%X)' % (size, size))