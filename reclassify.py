"""Reclassify the 87 verified tables using reference byte-identity, and emit a
separate candidate XDF containing only independently supported new findings.

Nothing here writes to R0C2J772B_verified.xdf or to either BIN.
"""
import re
import json
import xdfread
import verify

BASE = 'ref/BMW-XDFs-master/B58gen1/00003076501103.xdf'
BASE_REF = 'ref/BMW-XDFs-master/B58gen1/00003076501103_original.bin'
ORI = '10SW002828_iRom_ori'
MOD = '10SW002828_iRom_stage2'

# New findings, each with the evidence that supports its ADDRESS.
NEW = [
    dict(desc='KL_MD_K_MAX_BST', title='Speed-dependent boost curve of the combustion engine',
         addr=0x6F8D00, axis=0x6F8DF8, rows=1, cols=12, esz=16,
         axis_vals=[1000, 1250, 1550, 2300, 3800, 4600, 5400, 5500, 5800, 6000, 6500, 7000],
         addr_conf='VERIFIED',
         ev='RPM axis found in user BIN at predicted address; delta +0x410FA (3076-050) and '
            '+0x41710 (mgflasher) both land on it; 12/12 cells changed by tuner',
         sem_conf='UNRESOLVED'),
    dict(desc='KL_MD_K_MAX_BST_HS', title='Speed-dependent boost curve (half step)',
         addr=0x6F8CE8, axis=0x6F8DE0, rows=1, cols=12, esz=16,
         axis_vals=[1000, 1250, 1550, 2300, 3800, 4600, 5400, 5500, 5800, 6000, 6500, 7000],
         addr_conf='VERIFIED',
         ev='RPM axis found in user BIN at predicted address; identical delta +0x410FA; not edited by tuner',
         sem_conf='UNRESOLVED'),
    dict(desc='KL_MD_K_MAX_VL', title='Speed-dependent full-load curve',
         addr=0x6F8CA0, axis=0x6F8D98, rows=1, cols=12, esz=16,
         axis_vals=[1000, 1250, 1300, 2500, 3500, 4500, 4750, 5000, 5500, 6000, 6500, 7000],
         addr_conf='VERIFIED',
         ev='distinct 12-point RPM axis found at predicted address; 12/12 cells changed by tuner',
         sem_conf='UNRESOLVED'),
    dict(desc='UNRESOLVED_1x12_x6', title='Six 1x12 curves saturated 30000->32767 (identity unknown)',
         addr=0x6F7F2E, axis=0x6F8022, rows=1, cols=12, esz=16, count=6,
         axis_vals=[1000, 1250, 1550, 2300, 3800, 4600, 5400, 5500, 5800, 6000, 6500, 7000],
         addr_conf='STRUCTURAL',
         ev='144 B = exactly 6 curves x 12 u16; six identical 12-point RPM axes at 0x6F8022+24k; '
            'nearest pack candidates (KL_MD_K_MAX_*_STRG family) land 22 B away at 0x6F7F18',
         sem_conf='UNRESOLVED'),
]

CATEGORY_XML = ('    <CATEGORY index="0x%x" name="%s" />\n')


def build_candidate_xdf(bin_size, out):
    hdr = ['<?xml version="1.0" encoding="utf-8"?>\n',
           '<XDFFORMAT xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xmlns:xsd="http://www.w3.org/2001/XMLSchema" version="1.80">\n',
           '  <XDFHEADER>\n', '    <flags>0x1</flags>\n',
           '    <description>CANDIDATE ONLY - addresses independently corroborated, '
           'map semantics not fully resolved. Not flash-safe.</description>\n',
           '    <BASEOFFSET offset="0" subtract="0" />\n',
           '    <DEFAULTS datasizeinbits="16" sigdigits="3" outputtype="1" signed="0" '
           'lsbfirst="0" float="0" />\n',
           '    <REGION type="0xFFFFFFFF" startaddress="0x0" size="%s" regioncolor="0x0" '
           'regionflags="0x0" name="Binary File" desc="bin edited by this XDF" />\n' % hex(bin_size)]
    for i, c in enumerate(['Boost candidate', 'Boost candidate', 'Boost candidate', 'Unresolved']):
        hdr.append(CATEGORY_XML % (i, c))
    hdr.append('  </XDFHEADER>\n')

    body = []
    uid = 0x2000
    for cat, d in enumerate(NEW):
        n = d.get('count', 1)
        for k in range(n):
            addr = d['addr'] + k * d['cols'] * d['esz'] // 8
            axis = d['axis'] + k * d['cols'] * 2
            av = d['axis_vals']
            body.append(f'''  <XDFTABLE uniqueid="0x{uid:x}" flags="0x0">
    <title>{d['title']}{' [%d]' % (k + 1) if n > 1 else ''}</title>
    <description>{d['desc']}</description>
    <CATEGORYMEM index="0" category="{cat}" />
    <XDFAXIS id="x" uniqueid="0x0">
      <EMBEDDEDDATA mmedtypeflags="0x01" mmedaddress="0x{axis:X}" mmedelementsizebits="16" mmedrowcount="1" mmedcolcount="{d['cols']}" mmedmajorstridebits="0" mmedminorstridebits="0" />
      <units>1/min</units>
      <indexcount>{d['cols']}</indexcount>
      <decimalpl>0</decimalpl>
      <datatype>0</datatype>
      <unittype>0</unittype>
      <embedinfo type="1" />
      <MATH equation="X"><VAR id="X" /></MATH>
    </XDFAXIS>
    <XDFAXIS id="y" uniqueid="0x0">
      <EMBEDDEDDATA mmedelementsizebits="16" mmedmajorstridebits="0" mmedminorstridebits="0" />
      <indexcount>1</indexcount>
      <decimalpl>0</decimalpl>
      <datatype>0</datatype>
      <unittype>0</unittype>
      <MATH equation="X"><VAR id="X" /></MATH>
    </XDFAXIS>
    <XDFAXIS id="z" uniqueid="0x0">
      <EMBEDDEDDATA mmedaddress="0x{addr:X}" mmedelementsizebits="{d['esz']}" mmedrowcount="{d['rows']}" mmedcolcount="{d['cols']}" mmedmajorstridebits="0" mmedminorstridebits="0" />
      <decimalpl>2</decimalpl>
      <outputtype>1</outputtype>
      <datatype>0</datatype>
      <unittype>0</unittype>
      <embedinfo type="1" />
      <MATH equation="X"><VAR id="X" /></MATH>
    </XDFAXIS>
  </XDFTABLE>
''')
            uid += 1
    out.write(''.join(hdr) + ''.join(body) + '</XDFFORMAT>\n')


def main():
    import os
    ref = open(BASE_REF, 'rb').read()
    u = open(ORI, 'rb').read()
    m = open(MOD, 'rb').read()
    acc, tabs, med = verify.run(BASE, BASE_REF, ORI, 0x6C0000, 0x740000)

    out = {'VERIFIED': [], 'PARTIAL': [], 'REJECT': []}
    for i, tb, off, how, sc in acc:
        z = tb.z
        n = z.byte_span()
        a = ref[z.address:z.address + n]
        b = u[z.address + off:z.address + off + n]
        match = (sum(1 for x, y in zip(a, b) if x == y) / n) if len(a) == n and len(b) == n else 0.0
        tuned = sum(1 for k in range(z.address + off, z.address + off + n) if u[k] != m[k])
        rec = dict(desc=tb.desc, title=tb.title, user_addr=hex(z.address + off),
                   rows=z.rowcount, cols=z.colcount, esize=z.esize_bits,
                   match=round(match, 4), tuned=tuned, size=n)
        out['VERIFIED' if match == 1.0 else ('PARTIAL' if match >= 0.5 else 'REJECT')].append(rec)

    print('RECLASSIFICATION of the 87 by reference byte-identity:')
    for k in ('VERIFIED', 'PARTIAL', 'REJECT'):
        print('   %-9s %d' % (k, len(out[k])))
    tot = sum(1 for r in out['VERIFIED'] if r['tuned'])
    print('   of which VERIFIED and edited by the tuner: %d' % tot)

    # coverage using only byte-verified tables
    def spans(rec, ref_xdf_addr=None):
        return set(range(rec['user_addr'] and int(rec['user_addr'], 16),
                         int(rec['user_addr'], 16) + rec['size']))
    diff = set(i for i in range(len(u)) if u[i] != m[i])
    for label in ('VERIFIED', 'VERIFIED+PARTIAL', 'VERIFIED+PARTIAL+new'):
        cells = set()
        use = ['VERIFIED'] if label == 'VERIFIED' else ['VERIFIED', 'PARTIAL']
        for k in use:
            for rec in out[k]:
                cells |= spans(rec)
        if label.endswith('new'):
            for d in NEW:
                n = d.get('count', 1)
                cells |= set(range(d['addr'], d['addr'] + n * d['cols'] * d['esz'] // 8))
        print('   coverage[%s] = %d / 3821 = %.1f%%'
              % (label, len(diff & cells), 100 * len(diff & cells) / 3821))

    json.dump(out, open('out/reclassified.json', 'w'), indent=1)
    with open('out/R0C2J772B_CANDIDATE.xdf', 'w') as fh:
        build_candidate_xdf(len(u), fh)
    print('\nwrote out/reclassified.json')
    print('wrote out/R0C2J772B_CANDIDATE.xdf')


if __name__ == '__main__':
    main()