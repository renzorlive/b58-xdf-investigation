# Investigation Report #3 — SP15 primary reference

Target: `10SW002828_iRom_ori` / `10SW002828_iRom_stage2` (md5 `40c3a00…` / `251f649…` — **both unchanged**)
`out/R0C2J772B_verified.xdf` **unchanged** (87 tables). New work is in
`out/R0C2J772B_CANDIDATE.xdf` (68 tables, separate file).

---

## T1 — SP15 inventory and internal-identity verification

Every file was identified by reading its **embedded** identity strings, not its filename.

| Stock dump | EPST | SP | Market | Drivetrain | verdict |
|---|---|---|---|---|---|
| `00003076501103_original.bin` | R1C9J8B3B | **11** | – | – | wrong platform |
| `00003076501D02_original.bin` | R1C9J8I2B | **11** | – | – | wrong platform |
| `000030765A3C06_original.bin` | R1C9JD06B | **11** | – | – | wrong platform |
| `00003081501102_original.bin` | R0C9J8B2B | **15** | **ECE-EU6c** | RWD | **PRIMARY** |
| `00003081501D04_original.bin` | R0C9J8I4B | 15 | USA-ULEV70 | RWD | wrong market |
| `00007972000705_original.bin` | R1R96015B | – | – | – | different ECU |
| **this ECU** | **R0C9J772B** | **15** | **ECE-EU6c** | **AWD** | — |

Full DME strings:

```
00003081501102  DME8.6-B58-SP15-M0-B30-G30-ECE-EU6c---_HGAG-LL-RL-RWD-PVL
00003081501D04  DME8.6-B58-SP15-M0-B30-G30-USA-ULEV70-_HGAG-LL-RL-RWD-PVL
this ECU        DME8.6-B58-SP15-M0-B30-G30-ECE-EU6c---_HGAG-LL-RL-AWD-PVL
```

`00003081501102` matches on **SP level, market, emissions standard, DME version and
vehicle platform**. It differs only in EPST and RWD→AWD. **It is the primary reference
and the legacy SP11 packs are demoted.**

### The decisive experiment
Byte-identity is the strongest available test: if a table's placement is correct and
the two ECUs share that calibration, the bytes must be identical. I searched every SP15
table across the calibration-shift window (0x3F800–0x41800, step 2) for the delta that
maximises byte agreement with your stock BIN.

| Result | Count |
|---|---|
| **100 % byte match** | **106** |
| 81 % | 1 |
| 50 % / 25 % / <5 % | 3 |
| **100 % AND unique delta** | **73** |

A prior aggregate sweep over all 899 in-range SP15 tables peaked at only 2.5 % at any
single delta — confirming there is **no** global shift, and that per-table placement is
required. The 106 individual 100 % matches are therefore meaningful, not background.

Deltas cluster tightly: **+0x3FEB4 (24 tables), +0x3FD90, +0x3FFF4, +0x3F9CE, +0x3FE22…**
— a spread of ~1.2 KB, all far below the SP11 band's +0x40AC2–0x413FE.

**Conclusion: 73 SP15 tables transfer to this ECU with independent, byte-level proof.**

---

## T2 — Revalidation of the byte-identical set

Byte agreement and verified semantics are different things. Every SP15 table was
re-checked on: dimensions, axis pointers, element width, byte order, conversion
formula, and axis corroboration.

- **Element widths**: uint8 and uint16 only.
- **Byte order**: big-endian throughout (verified against reference; a little-endian
  reading of the 16-bit maps produces non-physical values).
- **Conversion formulas**: all linear (`X`, `X*k`, `X*k+b`). No table-dependent scaling
  was found that is not declared in the source XDF.
- **Axes**: 76 tables' axis bytes are **byte-identical** at the same delta as their data
  — strong independent confirmation. 29 have no addressable axis (1-D curves keyed off
  a shared RPM array). 6 have none at all.
- **Software family**: all 68 emitted tables come from the SP15 primary reference.

| Confidence | Count | Criterion |
|---|---|---|
| **VERIFIED** | 73 | 100 % byte match **and** unique delta (and axes corroborated or absent) |
| PROBABLE | 33 | 100 % byte match but the delta is not unique (constant maps match many places) |
| PARTIAL | 2 | 50–81 % |
| REJECT | 3 | < 50 % |

Full per-table evidence: `out/per_table_audit.csv` / `.json` (columns: desc, title,
source reference, ref address, delta, user address, rows, cols, element size, byte-match
%, delta ties, axis corroboration, x/y axis addresses, scaling, byte order, data type,
size, confidence, tuner-edited byte count).

**Note on the earlier "43 byte-identical" set.** Those came from the SP11 pack and remain
valid as *placements*, but SP15 now supersedes them with a stronger reference. Both sets
are retained in the combined coverage below; neither contradicts the other.

---

## T3 — The timing-family blocks: structure resolved, identity not

### Why the data did not decode as 16×20
I previously concluded from marker counts that the placement was wrong. **That was
wrong, and the error was mine**: my first marker count used a 256-byte slice instead of
the full 320 bytes. Comparing the full blocks properly:

```
REFERENCE SP15 KF_ZW_S_PF2 @0x6C37C0     markers in 320 B: 28
USER               @0x70318E            markers in 320 B: 27
```

The markers are **not** corruption. They are the classic Bosch `KF_` "not-applicable"
staircase — an inactive cell region that is normal in the *reference* too.

The real difference is **orientation**. In the reference the staircase runs
bottom-left (r06 has 1 marker, r15 has 7). In your block it runs **top-right**. The
values are otherwise the same magnitude and character — single digits to ~80, which is
the correct range for ignition advance in degrees.

Verified: user rows r06–r15, cols 10–19 contain `52 59 62 63 65 67 68 70 71 71 …`,
which is byte-for-byte the reference's rows r00–r05, cols 0–9.

**Conclusion: the block IS a 16×20 uint8 `KF_`-style table; the row/column orientation
is mirrored relative to the SP15 reference.**

### What is still unresolved
- The three changed blocks at `0x70318B`, `0x7032CB`, `0x70340B` are spaced exactly
  0x140 (320) apart, matching four consecutive 16×20 maps in the SP15 pack
  (`KF_ZW_S_PF2`, `KF_ZW_S_PF1`, `KF_ZW_PF2`, `KF_ZW_PF1`). The fourth predicted address
  lands on non-map content, so the run is three maps, not four.
- **Identity — which map is which — is NOT established.** The two y-axis value sets
  (`[1200,1500,2000,3000…]` and `[1300,1700,2000,2500…]`) are physically present at
  `0x6EC556/0x6EC596` and `0x6EC536/0x6EC576`, but there is no evidence linking a
  specific data block to a specific axis pair once the orientation flip is accounted for.
- Byte-match is unavailable here: RWD and AWD calibrations genuinely differ, so these
  maps score ~4 % against the reference even at the correct delta. This is a **real
  difference in content, not a placement error**.

**Per your instruction — structure is now adequately supported, identity is not — I have
emitted no ignition definition.** The three blocks remain documented but undefined.

---

## T4 — The K_MAX candidates: resolved, and they are not boost targets

**Correction: `KL_MD_K_MAX_BST` is at `0x6F8D18`, not `0x6F8D00`** (I was 24 bytes early).
All four axes are byte-identical at the SP15 delta:

| Map | Data | x-axis (RPM, byte-identical) | ori | mod |
|---|---|---|---|---|
| `KL_MD_K_MAX_VL` | 0x6F8CA0 | 0x6F8D98 | 500 ×12 | 650 ×12 |
| `KL_MD_K_MAX_BST_HS` | 0x6F8CE8 | 0x6F8DE0 | 300 300 300 310 320 310 300 295 280 270 230 150 | unchanged |
| `KL_MD_K_MAX_BST` | **0x6F8D18** | 0x6F8E10 | 485×7, 463, 422, 387, 336, 291 | 650 ×12 |
| `KL_MD_K_MAX_VL_HS` | 0x6F8CA0 | 0x6F8D98 | (shares VL — see caveat) | |

### What 300, 150 and 650 mean

`KL_MD` = "Kennlinie Drehzahl" (speed-dependent curve); **`K_MAX` = maximum relative
charge**, not boost pressure. Bosch `K` is the dimensionless per-cycle charging ratio:

```
K = p_pl / p_sa        p_pl = charge pressure (absolute)   p_sa = ambient pressure
```

**K is physically constrained to be < 1**, since ambient pressure is always present.
That single fact settles it:

| Raw | ÷1000 = K | Physical meaning |
|---|---|---|
| 500 (VL) | **0.50** | max charge 0.50 × ambient |
| 485…291 (BST) | **0.485 → 0.291** | charge ceiling falling with rpm |
| 300…150 (BST_HS) | **0.30 → 0.15** | half-step charge ceiling |
| 650 (tuned) | **0.65** | max charge 0.65 × ambient |

At ~1 bar ambient these correspond to roughly 0.50 bar and 0.65 bar of boost — sane
figures. Expressed in **bar** instead (`raw/1000 → 0.485 bar`) the numbers would also be
plausible, but the K<1 constraint and the `K_MAX` naming make **relative charging** the
correct reading. Scaling is `X/1000`.

The tuner raised `KL_MD_K_MAX_VL` from 0.50 to 0.65 and flattened
`KL_MD_K_MAX_BST` from a 0.485→0.291 taper to a constant 0.65 — **raising the maximum
permissible charge**, i.e. lifting the boost ceiling. That is the correct behaviour for
a Stage 2 tune and is now fully explained.

**Caveat:** `KL_MD_K_MAX_VL` and `KL_MD_K_MAX_VL_HS` both resolve to `0x6F8CA0` with 13
ties (constant map). They **cannot be distinguished** and are emitted once.

---

## T5 — Largest unexplained regions

Combined unexplained: **1,954 changed bytes**.

| Region | Span | Changed | SP15 evidence |
|---|---|---|---|
| 0x7311B4-0x731365 | 434 | 288 | **none** — no SP15 table covers it at any delta in the window |
| 0x730A8C-0x730B1D | 146 | 128 | **none** — same |
| 0x6F7F2E-0x6F7FBD | 144 | 144 | nearest candidates 22 B away (`KL_MD_K_MAX_*_STRG*`), unverified |
| 0x70318B / 2CB / 40B | 133 ea | 91 ea | timing family — structure known, identity unknown (T3) |

For 0x7311B4 and 0x730A8C the only SP15 hits were degenerate (`InjSys_nLowrThdCvo_C`,
declared 1×0) or knock-detection maps at unrelated deltas. **I have no structural
evidence for these two regions and make no claim about them.** They show a repeating
small-step (514) axis family that no available reference describes.

---

## T6 — Pipeline audit

| Old check | Problem | Replacement |
|---|---|---|
| Declared `min/max` in range | All 87 declared 0–255 → **vacuous**, filtered nothing | Byte-identity against an SP15 stock dump (73 tables now independently proven) |
| Content-anchored axes | Sound for 16-bit; **failed for 8-bit** because axes are shared/reused | Byte-match primary; axes used as *corroboration*, reported per table |
| Band-search fallback | Accepted 0 tables (correctly) | Removed — it can only guess |
| Unique-delta requirement | Not applied | Now enforced: 33 constant maps demoted to PROBABLE |

**Acceptance rule now applied:** a table enters the candidate XDF only if (a) 100 % byte
match against the SP15 stock dump, (b) a unique delta achieving that match, and
(c) its axes corroborate at the same delta or it has no addressable axis.

**Rejections and why**

| Set | Count | Reason |
|---|---|---|
| All 27 8-bit maps in the legacy verified XDF | 27 | < 50 % byte match vs SP11 dump; superseded by SP15 evidence |
| 11 16-bit legacy maps | 11 | 19–49 % match — right family, wrong address |
| 156 band-search candidates | 156 | Multiple deltas survived → ambiguous, refused |
| SP15 tables with non-unique delta | 33 | Constant maps; match is not evidential |
| SP15 tables < 50 % match | 3 | Placement wrong |
| The three timing blocks | 3 | Structure proven, **identity unproven** — instruction forbids emitting |
| `KL_MD_K_MAX_VL_HS` as a separate table | 1 | Indistinguishable from `KL_MD_K_MAX_VL` (same address, 13 ties) |

---

## Corrected coverage (overlaps deduplicated)

```
SP15 VERIFIED set (73 tables)              1,421 changed bytes
Legacy byte-identical set (43 tables)     1,392 changed bytes
Overlap between the two evidence sets     4,664 bytes of address space
-----------------------------------------------------------
COMBINED, deduplicated                    1,867 / 3,821  =  48.9 %
Unexplained                               1,954
```

`cell ∩ axis = 0` — no byte is claimed as both data and breakpoint.
`out/coverage_report3.json`; SP15 set alone: 37.6 %.

No breakpoint axis was altered by the tuner anywhere in either set.

---

## Deliverables

| File | Contents |
|---|---|
| `out/INVESTIGATION_REPORT_3.md` | this report |
| `out/R0C2J772B_CANDIDATE.xdf` | **68 tables**, SP15-derived, all independently byte-verified. Not flash-safe. |
| `out/per_table_audit.csv` / `.json` | 111 tables: evidence, source, address, dims, scaling, byte-match %, confidence |
| `out/coverage_report3.json` | deduplicated coverage accounting |
| `out/sp15_search.json` | raw per-table delta search |
| `out/R0C2J772B_verified.xdf` | **unchanged**, 87 tables (legacy SP11 evidence, superseded but retained) |

## Highest-value next steps (existing files only)
1. **Match the timing blocks to their axis pairs** — the y-axis sets at `0x6EC536/556/576/596`
   are located; linking one to one data block would settle identity without new files.
2. **Search the SP15 pack's `1×N` curve family for 0x6F7F2E** — structure (6×1×12 + six
   RPM axes) is already proven; only the name is missing.
3. **Re-run `deltasweep.py` against `00003081501D04`** to confirm the 33 non-unique-delta
   tables can be disambiguated using the USA-market variant as a second reference.