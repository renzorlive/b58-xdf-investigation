"""Build out/R0C2J772B_timing_candidates.xdf - read-only, refuses to overwrite."""
import os
import re

DST = 'out/R0C2J772B_timing_candidates.xdf'
ORI = '10SW002828_iRom_ori'
MOD = '10SW002828_iRom_stage2'
BIN = 8126464
DELTA = 0x3F7D0
AXIS_DELTA = 0x3F9CE
CAT = 0

CAVEAT = (
    'IGNITION-TIMING CANDIDATE SET - EXPLORATORY, FOR MANUAL INSPECTION ONLY. '
    'Target: MG1CS003 / DME8.6, EPK R0C2J772B, EPST R0C9J772B, PST S15A-17-11-490. '
    'WHAT IS PROVEN: a 4505-byte block of this image at 0x702DED-0x703F85 is BYTE-IDENTICAL '
    'to an S15A-18 reference image (C2J8B2B) at 0x6C361D-0x6C47B5, delta +0x3F7D0. '
    'WHAT IS NOT PROVEN: that any individual map below is ignition timing. The candidate '
    'names are reference labels carried over as HYPOTHESES, not confirmed identities. '
    'AXES ARE DELIBERATELY ABSENT: the 20-point Nkw and 16-point arrays that correspond to '
    'these maps in the reference were located in this image at a DIFFERENT relative offset '
    '(delta +0x3F9CE, 470 bytes adrift from the layout the content correspondence implies), '
    'so pairing them here would fabricate breakpoints. Values are shown RAW (identity). '
    'See out/TIMING_CANDIDATE_AUDIT.md.'
)

# label, target address, rows, cols, bits, ref address, ref label, changed cells
CANDS = [
    ('UNVERIFIED_TIMING_CANDIDATE_702F18', 0x702F18, 14, 10, 8, 0x6C36A8, 'KF_ZW_UESP_PF2 (spool, path 2)'),
    ('UNVERIFIED_TIMING_CANDIDATE_702F04', 0x702F04, 14, 10, 8, 0x6C3734, 'KF_ZW_UESP_PF1 (spool, path 1)'),
    ('UNVERIFIED_TIMING_CANDIDATE_702F90', 0x702F90, 16, 20, 8, 0x6C37C0, 'KF_ZW_S_PF2 (cold, path 2)'),
    ('UNVERIFIED_TIMING_CANDIDATE_7030D0', 0x7030D0, 16, 20, 8, 0x6C3900, 'KF_ZW_S_PF1 (cold, path 1)'),
    ('UNVERIFIED_TIMING_CANDIDATE_703210', 0x703210, 16, 20, 8, 0x6C3A40, 'KF_ZW_PF2 (main, path 2)'),
    ('UNVERIFIED_TIMING_CANDIDATE_703350', 0x703350, 16, 20, 8, 0x6C3B80, 'KF_ZW_PF1 (main, path 1)'),
    ('UNVERIFIED_TIMING_CANDIDATE_703490', 0x703490, 16, 20, 8, 0x6C3CC0, 'KF_ZW_VP_PF2? (unlabelled successor span)'),
]


def desc(label, refaddr, reflabel, rows, cols, bits, chg):
    e = (f'Raw candidate, {rows}x{cols} uint{bits}. Address and layout supported by the '
         f'4505-byte byte-identity correspondence (target +0x3F7D0 to reference '
         f'0x6C361D). The reference image declares the map occupying reference 0x{refaddr:X} '
         f'as "{reflabel}" - that label is a HYPOTHESIS transferred from an S15A-18 image, '
         f'NOT a confirmed identity for this S15A-17 image. NO AXES: the corresponding '
         f'breakpoint arrays could not be placed consistently (see header note), so no '
         f'breakpoints are shown rather than fabricated ones. Shown RAW: no conversion is '
         f'applied because no scaling has been established for this target. '
         f'Stage 2 differs from stock in {chg} cells of this map.')
    return e.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def main():
    assert not os.path.exists(DST), 'refusing to overwrite an existing file'
    o = open(ORI, 'rb').read()
    m = open(MOD, 'rb').read()

    hdr = ['<?xml version="1.0" encoding="utf-8"?>\n',
           '<XDFFORMAT xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xmlns:xsd="http://www.w3.org/2001/XMLSchema" version="1.80">\n',
           '  <XDFHEADER>\n    <flags>0x1</flags>\n',
           f'    <description>{CAVEAT}</description>\n',
           '    <BASEOFFSET offset="0" subtract="0" />\n',
           '    <DEFAULTS datasizeinbits="16" sigdigits="3" outputtype="1" signed="0" '
           'lsbfirst="0" float="0" />\n',
           '    <REGION type="0xFFFFFFFF" startaddress="0x0" size="0x7C0000" '
           'regioncolor="0x0" regionflags="0x0" name="Binary File" '
           'desc="bin edited by this XDF" />\n',
           f'    <CATEGORY index="0x{CAT:X}" name="TIMING CANDIDATES (unverified identity)" />\n',
           '  </XDFHEADER>\n']

    body = []
    for i, (label, addr, rows, cols, bits, refaddr, reflabel) in enumerate(CANDS):
        chg = sum(1 for k in range(rows * cols) if o[addr + k] != m[addr + k])
        body.append(f'''  <XDFTABLE uniqueid="0x{i:x}" flags="0x0">
    <title>{label}</title>
    <description>{desc(label, refaddr, reflabel, rows, cols, bits, chg)}</description>
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
      <EMBEDDEDDATA mmedaddress="0x{addr:X}" mmedelementsizebits="{bits}" mmedrowcount="{rows}" mmedcolcount="{cols}" mmedmajorstridebits="0" mmedminorstridebits="0" />
      <decimalpl>0</decimalpl>
      <outputtype>1</outputtype>
      <datatype>0</datatype>
      <unittype>0</unittype>
      <embedinfo type="1" />
      <MATH equation="X"><VAR id="X" /></MATH>
    </XDFAXIS>
  </XDFTABLE>
''')

    open(DST, 'w', encoding='utf-8').write(''.join(hdr) + ''.join(body) + '</XDFFORMAT>\n')
    print('wrote', DST, '-', len(CANDS), 'candidate tables')
    for label, addr, rows, cols, bits, refaddr, reflabel in CANDS:
        span = rows * cols * bits // 8
        assert addr + span <= BIN, label
        chg = sum(1 for k in range(rows * cols) if o[addr + k] != m[addr + k])
        print('  0x%06X %2dx%-3d u%-2d span=%-4d ref=0x%06X stage2-differs=%-4d %s'
              % (addr, rows, cols, bits, span, refaddr, chg, reflabel))


if __name__ == '__main__':
    main()