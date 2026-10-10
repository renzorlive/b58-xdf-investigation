"""Build out/R0C2J772B_manual_inspection.xdf - exploratory inspection definition.

Starts from out/R0C2J772B_CANDIDATE_axesclean.xdf (the best-supported existing file)
and APPENDS neutral exploratory tables for the prioritised unidentified regions.
Nothing existing is modified.
"""
import re
import os
import hashlib

SRC = 'out/R0C2J772B_CANDIDATE_axesclean.xdf'
DST = 'out/R0C2J772B_manual_inspection.xdf'
CAT = 0x64  # new category index, appended after the existing ones

CAVEAT = (
    'EXPLORATORY MANUAL-INSPECTION XDF - NOT A VALIDATED TUNING DEFINITION. '
    'Target: MG1CS003 / DME8.6, EPK R0C2J772B, EPST R0C9J772B, PST S15A-17-11-490. '
    'Tables 1-71 are placed by BYTE IDENTITY against an S15A-18 reference image '
    '(C2J8B2B / R0C9J8B2B / S15A-18-03-510). That is a DIFFERENT software sub-revision '
    'from this image, so: addresses, dimensions, element widths and byte order are '
    'evidence-backed for THIS bin; the Bosch map NAMES and their units are INHERITED and '
    'are NOT confirmed for S15A-17. A name showing here is not proof of what the map is. '
    'Conversion formulas were cross-checked against the DAMOS A2L where available. '
    'Tables prefixed UNVERIFIED_REGION_ have no established identity, units or dimensions '
    'whatsoever - they are raw byte windows added so you can compare stock vs Stage 2 by '
    'hand. Use for inspection only. Do not flash.'
)

# name, address, count, element bits, evidence note
EXPLORATORY = [
    ('UNVERIFIED_REGION_6F7F2E', 0x6F7F2E, 72, 16,
     'Element width 16-bit is established: the 144 bytes contain exactly two distinct '
     'uint16 values, 30000 (stock) and 32767 (Stage 2). 72 cells. A 6x12 grouping is '
     'consistent with six 12-point ascending arrays found nearby at 0x6F8022+24k, but that '
     'linkage is NOT established, so this is presented as a flat 72-point array. '
     'Identity, units and function unknown.'),
    ('UNVERIFIED_REGION_6F1BA0', 0x6F1BA0, 128, 8,
     'Stock bytes match a local reference image verbatim (offset 0x6B234C, delta +0x3F854, '
     '1010 contiguous identical bytes), so this is inherited calibration content. '
     'No reference names this span. Element width, dimensions, identity and units unknown; '
     'shown as raw bytes.'),
    ('UNVERIFIED_REGION_730A8C', 0x730A8C, 146, 8,
     'Stock bytes match a local reference image verbatim (offset 0x6F1CA4, delta +0x3EDE8). '
     'No reference names this span. Element width, dimensions, identity and units unknown; '
     'shown as raw bytes.'),
    ('UNVERIFIED_REGION_7311B4', 0x7311B4, 434, 8,
     'Largest unidentified changed region (288 of 3821 bytes). Stock bytes match a local '
     'reference image verbatim (offset 0x6F23A0, delta +0x3EE14, 533 contiguous identical '
     'bytes), so it is inherited calibration content, not code or datalog. No reference '
     'names this span. Element width, dimensions, identity and units unknown; shown as raw '
     'bytes.'),
    ('UNVERIFIED_REGION_70318B', 0x70318B, 133, 8,
     'Stock bytes match a local reference image verbatim (offset 0x6C39BB, delta +0x3F7D0, '
     '3579 contiguous identical bytes). NOT identified as ignition: the match starts where '
     'the changed region starts, which does not establish a map boundary, and the content '
     'delta +0x3F7D0 conflicts with the independently located breakpoint-axis delta '
     '+0x3F9CE. No dimensions asserted. Shown as raw bytes; identity and units unknown.'),
    ('UNVERIFIED_REGION_7032CB', 0x7032CB, 133, 8,
     'Stock bytes match a local reference image verbatim (offset 0x6C3AFB, delta +0x3F7D0, '
     '3259 contiguous identical bytes). NOT identified as ignition - see the note on '
     'UNVERIFIED_REGION_70318B for why. No dimensions asserted. Identity and units unknown.'),
    ('UNVERIFIED_REGION_70340B', 0x70340B, 133, 8,
     'Stock bytes match a local reference image verbatim (offset 0x6C39BB, 123 contiguous '
     'identical bytes). NOT identified as ignition - see the note on '
     'UNVERIFIED_REGION_70318B. No dimensions asserted. Identity and units unknown.'),
]


def table_xml(uid, name, desc, addr, n, bits):
    return f'''  <XDFTABLE uniqueid="0x{uid:x}" flags="0x0">
    <title>{name} [UNVERIFIED]</title>
    <description>{desc}</description>
    <CATEGORYMEM index="0" category="{CAT}" />
    <XDFAXIS id="x" uniqueid="0x0">
      <EMBEDDEDDATA mmedelementsizebits="16" mmedmajorstridebits="0" mmedminorstridebits="0" />
      <indexcount>1</indexcount>
      <datatype>0</datatype>
      <unittype>0</unittype>
    </XDFAXIS>
    <XDFAXIS id="y" uniqueid="0x0">
      <EMBEDDEDDATA mmedelementsizebits="16" mmedmajorstridebits="0" mmedminorstridebits="0" />
      <indexcount>1</indexcount>
      <datatype>0</datatype>
      <unittype>0</unittype>
    </XDFAXIS>
    <XDFAXIS id="z" uniqueid="0x0">
      <EMBEDDEDDATA mmedaddress="0x{addr:X}" mmedelementsizebits="{bits}" mmedrowcount="1" mmedcolcount="{n}" mmedmajorstridebits="0" mmedminorstridebits="0" />
      <decimalpl>0</decimalpl>
      <outputtype>1</outputtype>
      <datatype>0</datatype>
      <unittype>0</unittype>
      <embedinfo type="1" />
      <MATH equation="X"><VAR id="X" /></MATH>
    </XDFAXIS>
  </XDFTABLE>
'''


def main():
    assert not os.path.exists(DST), 'refusing to overwrite an existing file'
    txt = open(SRC, encoding='utf-8').read()

    # global caveat into the header description
    txt = re.sub(r'<description>.*?</description>',
                 '<description>%s</description>' % CAVEAT, txt, count=1, flags=re.S)

    # append the exploratory category
    cat = '    <CATEGORY index="0x%x" name="UNVERIFIED REGIONS (raw, no identity)" />\n' % CAT
    txt = txt.replace('  </XDFHEADER>\n', cat + '  </XDFHEADER>\n', 1)

    uid = 0x9000
    extra = []
    for name, addr, n, bits, note in EXPLORATORY:
        esc = note.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        extra.append(table_xml(uid, name, esc, addr, n, bits))
        uid += 1

    txt = txt.replace('</XDFFORMAT>\n', ''.join(extra) + '</XDFFORMAT>\n')
    open(DST, 'w', encoding='utf-8').write(txt)
    print('wrote %s' % DST)
    print('  copied from : %s' % SRC)
    print('  appended    : %d exploratory tables' % len(extra))


if __name__ == '__main__':
    main()