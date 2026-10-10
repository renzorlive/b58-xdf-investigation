"""Smallest corrective patch: drop 10 untrustworthy axis references.

Those axes read sentinel values (>=60000) or are non-monotonic in the user BIN,
so they are not breakpoint arrays. Their addresses come from the community
source XDF and are wrong for this ECU. The DATA definitions are byte-verified
and are NOT touched.

Read-only with respect to the BINs and to out/R0C2J772B_CANDIDATE.xdf: this
writes a separate file.
"""
import re
import xml.etree.ElementTree as ET

SRC = 'out/R0C2J772B_CANDIDATE.xdf'
DST = 'out/R0C2J772B_CANDIDATE_axesclean.xdf'
ORI = '10SW002828_iRom_ori'
SENTINEL = 60000

o = open(ORI, 'rb').read()
text = open(SRC, encoding='utf-8').read()

MINIMAL = ('<XDFAXIS id="%s" uniqueid="0x0">\n'
           '      <EMBEDDEDDATA mmedelementsizebits="16" mmedmajorstridebits="0" '
           'mmedminorstridebits="0" />\n'
           '      <indexcount>1</indexcount>\n'
           '      <datatype>0</datatype>\n'
           '      <unittype>0</unittype>\n'
           '    </XDFAXIS>\n')

dropped = []
out = []
pos = 0
for m in re.finditer(r'<XDFTABLE\b.*?</XDFTABLE>', text, re.S):
    blk = m.group(0)
    d = re.search(r'<description>(.*?)</description>', blk, re.S)
    desc = d.group(1) if d else '?'
    changed = False
    for role in ('x', 'y'):
        am = re.search(r'<XDFAXIS id="%s"[^>]*>.*?</XDFAXIS>' % role, blk, re.S)
        if not am:
            continue
        ab = am.group(0)
        em = re.search(r'mmedaddress="(0x[0-9A-Fa-f]+|[0-9]+)"', ab)
        ic = re.search(r'<indexcount>(\d+)</indexcount>', ab)
        if not em or not ic:
            continue
        n = int(ic.group(1))
        if not n:
            continue
        st = int(em.group(1), 0)
        v = [int.from_bytes(o[st + i * 2:st + i * 2 + 2], 'big') for i in range(n)]
        if any(x >= SENTINEL for x in v) or any(v[i] >= v[i + 1] for i in range(len(v) - 1)):
            dropped.append((desc, role, st, n))
            blk = blk.replace(ab, MINIMAL % role, 1)
            changed = True
    out.append(text[pos:m.start()])
    out.append(blk)
    pos = m.end()
out.append(text[pos:])

open(DST, 'w', encoding='utf-8').write(''.join(out))

root = ET.parse(DST).getroot()
print('dropped %d untrustworthy axis references:' % len(dropped))
for d, r, st, n in dropped:
    print('   %-30s %s @0x%06X n=%d' % (d, r, st, n))
print('wrote %s : %d tables, parses OK' % (DST, len(root.findall('XDFTABLE'))))