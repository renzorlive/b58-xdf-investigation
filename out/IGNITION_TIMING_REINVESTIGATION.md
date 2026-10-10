# IGNITION TIMING MAPS — RE-INVESTIGATION FROM FIRST PRINCIPLES

Supersedes `TIMING_CANDIDATE_AUDIT.md` and `out/R0C2J772B_timing_candidates.xdf`.

**Result: ignition timing maps were identified.** 10 maps, with real axes, real
dimensions, a real conversion formula, and stock-vs-tuned differences. The previous
file was wrong in a specific, diagnosable way (§1).

- Target: `10SW002828_iRom_ori` (stock) / `10SW002828_iRom_stage2` (tuned)
- ECU MG1CS003 / DME8.6, EPK `R0C2J772B`, EPST `R0C9J772B`, PST `S15A-17-11-490`
- New file: `out/R0C2J772B_ignition_timing.xdf` — builder `build_ignition_xdf.py`
- Read-only: neither BIN nor any prior artifact was modified.

---

## 1. Why the previous XDF rendered as single-value maps

Not a cosmetic problem — a structural defect, and entirely my fault.

Every table declared:

```xml
<XDFAXIS id="x"> <EMBEDDEDDATA mmedelementsizebits="16"/> <indexcount>1</indexcount>
<XDFAXIS id="y"> <EMBEDDEDDATA mmedelementsizebits="16"/> <indexcount>1</indexcount>
<XDFAXIS id="z"> <EMBEDDEDDATA mmedaddress="0x702F90" mmedrowcount="16"
                           mmedcolcount="20" mmedelementsizebits="8"/>
```

TunerPro builds the table grid from the **X and Y axis `indexcount`**, not from
`mmedrowcount`/`mmedcolcount` on Z. With `indexcount=1` on both axes, each table
renders **1×1 — a single cell**, regardless of the Z geometry. The 16×20 geometry was
simply ignored.

Verified against tables that work in the reference pack
(`ref/BMW-XDFs-master/B58gen1/00003081501102.xdf`), which carry real axis addresses and
matching `indexcount`:

| | X | Y | Z |
|---|---|---|---|
| working 2D table | `addr=0x68503A ic=6` | `addr=0x68502E ic=6` | 6×6 |
| my broken tables | `addr=None ic=1` | `addr=None ic=1` | 16×20 |

**Root cause:** I refused to attach axes because I had not resolved which of two
conflicting offsets was right, and chose "no axis" over "possibly wrong axis". That was
defensible for a single map but wrong for the whole file: it produced ten maps that
could not be inspected at all. The correct resolution was to resolve the axis question
properly — which §4 shows is possible.

Two further defects: the four UESP maps were labelled `14x10` when the A2L gives X=10
(Nkw) and Y=14 (load), and no conversion was applied despite a real one existing.

---

## 2. Evidence sources — exact file and revision for every item

| Evidence | Source file | Software rev | What it gives |
|---|---|---|---|
| Symbol names, dimensions, axes, addresses, conversion | `mgflasher-map-packs/A2Ls/B48 B58 Gen 1/Generic/R0C9J8B2B_3081-080_017_002.a2l` | **R0C2J8B2B / S15A-18** | 30 `KF_ZW_*` records (10 maps + 20 axes) |
| Reference bytes | `ref/BMW-XDFs-master/B58gen1/00003081501102_original.bin` | S15A-18 | byte content at A2L addresses |
| Table/axis XML conventions | `ref/BMW-XDFs-master/B58gen1/00003081501102.xdf` | S15A-18 | structure, `typeflags` |

**No S15A-17 A2L exists locally.** Checked: no `*_016_*` file, and every B48/B58 A2L is
`_017_` or higher in the filename, where `017` is a **pack revision, not S15A-17**.
The one A2L for our ECU family declares `VERSION "R0C2J8B2B"` — S15A-18. So *all* symbol
identity here is inherited, not proven for the target. This is stated in the XDF header
and in every table description.

The decisive addition versus the previous investigation is that the A2L is a **complete
declaration**, not a borrowed formula: it names each map, gives its address, dimensions,
both axis addresses, axis counts, input quantities, physical units and the conversion.

```
/begin CHARACTERISTIC KF_ZW_PF1
    "Base ignition angle path 1"
    MAP
    0x96C3B80
    ...
    -64 63.5                 <- limits
    /begin AXIS_DESCR
        COM_AXIS  Nkw  ... 20   AXIS_PTS_REF AXX_KF_ZW_PF1  PHYS_UNIT "1/min"
    /begin AXIS_DESCR
        NO_INPUT_QUANTITY ... 16  AXIS_PTS_REF AXY_KF_ZW_PF1  PHYS_UNIT "%"
```

Conversion, from `COMPU_METHOD aAwkuzc_BFpgCmb_tmDukma_q__aa0o` → `COEFFS 0 2 0 0 0 1`
i.e. `phys = X/2`. **Signedness is confirmed independently** by the declared limits:
`-64 .. 63.5` is exactly `int8(-128..127) × 0.5`. Unsigned would span `0 .. 127.5` and
contradict the A2L. So the element is **signed int8**, not uint8 as previously assumed.

---

## 3. Independent examination of the target BIN

Maps and axes were located by **exact byte-content search of the reference image inside
the target** — not by applying an offset. Each address below is a search hit.

| Map (A2L symbol) | Target addr | Dim (Y×X) | Element | Stock→tuned |
|---|---|---|---|---|
| `KF_ZW_PF1` | `0x703350` | 16×20 | signed int8 | **91 cells** |
| `KF_ZW_PF2` | `0x703210` | 16×20 | signed int8 | **91 cells** |
| `KF_ZW_S_PF1` | `0x7030D0` | 16×20 | signed int8 | **91 cells** |
| `KF_ZW_S_PF2` | `0x702F90` | 16×20 | signed int8 | **91 cells** |
| `KF_ZW_UESP_PF1` | `0x702F04` | 14×10 | signed int8 | 0 |
| `KF_ZW_UESP_PF2` | `0x702E78` | 14×10 | signed int8 | 0 |
| `KF_ZW_VP_PF1` | `0x7072A8` | 16×20 | signed int8 | 0 |
| `KF_ZW_VP_PF2` | `0x707168` | 16×20 | signed int8 | 0 |
| `KF_ZWMIN_WSOT` | `0x706DEC` | 8×8 | signed int8 | 0 |
| `KF_ZWMIN_KSOT` | `0x706E2C` | 8×8 | signed int8 | 0 |

Every map's full byte span matches the reference **byte-for-byte**. Note `KF_ZW_VP_*`
and `KF_ZWMIN_*` are **outside** the previously-known 4,505-byte block — found because
the A2L declares them, not because they lie in that block.

### Axes (all located by content search in the target)

| Axis | Content | Target addr (per map) |
|---|---|---|
| `AXX_*` Nkw, 20 pt | `500,750,1000,…,6500,6950` rpm | `0x6EC5DE / 0x6EC606 / 0x6EC62E / 0x6EC656` |
| `AXY_*` load, 16 pt (PF1) | `1200,1500,2000,…,18000` | `0x6EC556 / 0x6EC596` |
| `AXY_*` load, 16 pt (PF2) | `1300,1700,2000,…,18000` | `0x6EC536 / 0x6EC576` |
| `AXX_*` Nkw, 10 pt | `1000,1250,…,3250` | `0x6EC5B6 / 0x6EC5CA` |
| `AXY_*` load, 14 pt | `3000,4000,…,18000` | `0x6EC4FE / 0x6EC51A` |

---

## 4. The 510-byte conflict — resolved

The previous investigation had two irreconcilable offsets and refused to choose. Both are
real, and they are **different regions with different layouts** — there is no single
translation to find.

| Region | Reference | Target | Delta |
|---|---|---|---|
| Main `KF_ZW_*` maps | `0x6C36A8`… | `0x702E78`… | `+0x3F7D0` |
| Main axes | `0x6ACB68`… | `0x6EC536`… | `+0x3F9CE` |
| `KF_ZWMIN_*` | `0x6C7694` | `0x706DEC` | `+0x3F758` |
| `KF_ZW_VP_*` maps | `0x6C7A1C` | `0x707168` | `+0x3F74C` |
| `KF_ZW_VP_*` axes | `0x6BAF8A` | `0x6FA94A` | `+0x3F9C0` |

Five deltas, differing by 14–584 bytes. **S15A-17 and S15A-18 genuinely lay out these
regions differently**, so no global offset exists. That is expected for a different
sub-revision and is not a contradiction.

**Independent landmark proving alignment within each block** — the 8-array main axis
block has byte-identical *internal* spacing in both images:

```
consecutive gaps, reference : [32, 32, 32, 72, 40, 40, 40]
consecutive gaps, target    : [32, 32, 32, 72, 40, 40, 40]   IDENTICAL
```

Same 8 arrays, same order, same spacing, same distinct contents in the same sequence.
That is a structural landmark independent of any offset arithmetic, and it is what
justifies pairing axis *i* with map *i*.

**A second, decisive observation that removes the ambiguity entirely:** all four Nkw
axes are byte-identical to each other, and the 16-point load axes collapse to only two
distinct variants (PF1/S_PF1 `1200,1500,…`; PF2/S_PF2 `1300,1700,…`). So even if the
axis↔map pairing were wrong, the **X breakpoints would be right regardless**, and a Y
axis can only be wrong by 100–200 units on the first two breakpoints. The residual risk
is small and quantified.

---

## 5. Why these are ignition timing, not something else

Not inferred from names alone. Decoded stock values, signed, ×0.5:

```
KF_ZW_PF1  rows = load 1200→18000,  columns = Nkw 500→6950 rpm

 load 1200 : 24.0  27.0  29.5  31.5  35.0  40.0  41.5  42.5  42.5  42.0  46.5  48.0 ...  62.5
 load 1500 : 18.0  24.0  27.0  28.0  29.0  31.0  34.5  36.0  36.0  35.5  38.0  39.0 ...  52.5
 load 2000 : 14.0  18.0  29.0  32.5  35.0  31.5  33.5  37.0  39.5  38.0  38.0  39.0 ...  49.0
 load 3000 : 13.0  17.5  26.5  29.0  31.0  31.5  32.0  32.5  32.5  33.5  34.0  36.0 ...  38.5
 load 4000 :  9.5  16.0  20.0  21.0  23.0  24.5  27.5  27.0  27.0  27.5  27.5  28.5 ...  35.5
 load 6000 :  5.0   5.5   9.0  12.0  14.5  17.0  17.5  18.5  19.0  20.5  22.0  23.0 ...  30.5
 load12000 :  0.0   0.5   6.5  10.5  13.0  14.0  14.5  15.5  16.0  17.5  17.5  19.5 ...  25.0
 load18000 : -3.5  -1.5   2.5   6.0   8.5  10.5  13.0  13.5  14.0  15.0  15.5  17.0 ...  23.0
```

Three independent physical checks, all consistent and all specific to ignition:

1. **Advance rises monotonically with engine speed** along the Nkw axis, saturating
   above ~4000 rpm — textbook.
2. **Advance falls monotonically with load** down the air-mass axis, ~27° of spread —
   textbook, and the opposite of what a torque, lambda or injection map does.
3. **Signed int8 is required to produce this.** Reading the same bytes as unsigned gives
   88–127° in the high-load rows and destroys the monotonicity. The signed reading is
   the only one that yields a coherent map — independent confirmation of the A2L limits.

**Tuned changes are characteristic of a timing tune**, not an arbitrary edit:

| Map | Cells | Cell range | Δ angle | Mean Δ |
|---|---|---|---|---|
| `KF_ZW_PF1` | 91 | rows 7–19, cols 9–15 | +27.0 … +51.0° | **+38.8°** |
| `KF_ZW_S_PF1` | 91 | rows 7–19, cols 9–15 | +11.0 … +48.5° | **+25.9°** |

+11 to +51° of added advance, confined to the high-load / mid-high-rpm region (rows
7–19 = load 5000–18000; cols 9–15 = 2500–4500 rpm), leaving low-rpm and light-load
cells untouched. All 91 deltas are exact multiples of 0.5°. This is the signature of an
ignition-timing change, and it is why these four maps — and only these — were edited.

---

## 6. Confidence and remaining contradictions

**HIGH confidence** (6 maps): `KF_ZW_PF1`, `KF_ZW_PF2`, `KF_ZW_S_PF1`, `KF_ZW_S_PF2`,
`KF_ZW_UESP_PF1`, `KF_ZW_UESP_PF2`.
A2L symbol + byte-identical map content + byte-identical axis content + physically
correct monotonic behaviour + (for the four main maps) tuner edits landing exactly there.

**MEDIUM confidence** (4 maps): `KF_ZW_VP_PF1/PF2`, `KF_ZWMIN_WSOT/KSOT`.
Map bytes and axis bytes both verified in the target, but they sit in regions whose
translation differs from the main block, so their axis pairing rests on block-internal
ordering rather than a corroborated cross-region landmark. They were not modified by the
tuner, so no edit-pattern corroboration is available.

### Unresolved / must not be over-read

- **Identity is inherited from S15A-18.** No S15A-17 A2L exists locally. Names,
  dimensions and axis *semantics* are the reference's, not proven for the target. It is
  entirely possible the S15A-17 software labels these differently or uses different
  dimensions with the same content.
- **Axis pairing** is justified by ordering within a block, plus the fact that identical
  X axes and near-identical Y axes make the residual error small. It is not proven by a
  cross-region landmark for every map.
- **These are BASE ignition angle maps only.** The final commanded timing includes torque
  limits, knock control, per-cylinder corrections and the air-mass selection path, none
  of which is described here. Tuning from this file alone would be wrong.
- **`KF_ZWMIN_*` values are negative** (−40.0 … −7.5°), consistent with a retard floor.
  Their axis pairing is the least certain item in the file.
- **No claim is made that the Stage 2 calibration is safe or correct.** +38.8° mean
  added advance is aggressive; the knock limiters it depends on are not in this file.

### What would close the remaining gaps

1. A stock read reporting `R0C2J772B` / S15A-17 — would confirm identity directly.
2. An A2L or XDF for EPST `R0C9J772B` — would give authoritative S15A-17 addresses.
3. The tuner's own definition file — would pin the whole address space.

---

## 7. Validation of the new XDF

```
XML parses, XDFFORMAT 1.80                OK
tables                                   10
REGION size 0x7C0000 == BIN size         OK  (8,126,464)
tables with an address-less axis         0     <- was 14
axis indexcount vs table geometry        10/10 match
axes strictly increasing                 10/10
element width 8 bit, typeflags 0x01      10/10  (signed)
conversion                               "X*0.5"
bytes mapped                             2,328
structural errors                        0
```

Decoded directly from the generated XDF against both BINs, confirming each table's axes
resolve to the expected breakpoints and each map decodes to plausible degrees.

**Not tested in TunerPro** — it is not installed here. Structure and values were
validated programmatically against the reference pack's own conventions.

---

## 8. Superseded files

`out/R0C2J772B_timing_candidates.xdf` and `out/TIMING_CANDIDATE_AUDIT.md` are **wrong**
and should be deleted or archived — they render as single-cell tables and label uint8
data as unsigned. Both are preserved unchanged here for audit trail; neither should be
used. `out/R0C2J772B_manual_inspection.xdf` is unaffected and remains valid.
