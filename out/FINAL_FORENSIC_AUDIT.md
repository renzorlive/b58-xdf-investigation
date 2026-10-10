# FINAL_FORENSIC_AUDIT

Strictly read-only. No BIN, no legacy verified XDF, and no candidate XDF was modified.
One concrete integrity defect was found; it is reported below with the corrective patch
supplied **separately**, as instructed.

---

## 1 — Candidate integrity

Parsed with `forensic.py`, which imports **nothing** from the project's own modules
(no `xdfread`, no `regen_candidate`), so a generator bug cannot mask itself.

```
REGION start=0x0 size=0x7c0000      size matches BIN (8126464): True
definitions: 71     unique Bosch names: 71
HARD DEFECTS (structural): 0
  - duplicate definitions ............ 0
  - data out of file bounds ......... 0
  - missing z axis .................. 0
```

Provenance recorded in the header: SP15 primary reference `R0C9J8B2B` (byte-verified),
`KL_MD_K_MAX_*` from the DAMOS A2L. Every non-K_MAX definition's geometry matches the
source XDF exactly.

**Formula differences vs source: 2 — both are the intended corrections from report 5.**

| Definition | Source | Emitted | Status |
|---|---|---|---|
| `KL_NEL_TMOT` | `X/2.55` | `X*0.390625` | intended (A2L `COEFFS 0 64 0 0 0 25` → 25/64) |
| `KF_LAMIN_H` | `(X*0.0002441406)*14.7` | `X*0.0002441406*14.7` | intended, identical value |

### Formula grammar
27 distinct formulas. **0 outside the parser-safe set** `[X0-9.*/]` — no parentheses, no
`+`/`-` offsets, no division by X, no non-linear terms. By contrast the shipped community
packs contain 123 formulas including `X/1.333 - (48)` and
`1/(X*0.000011518903) * 80.11750567498999`, which are **not** safe for a limited parser.
The candidate is strictly safer than the packs it derives from.

**Target editor:** no XDF editor (TunerPro / ECUFlash) is installed in this environment,
so I could not execute a round-trip load. The grammar check above is static, not a
substitute for a real load test. That remains an open item.

---

## 2 — INTEGRITY DEFECT FOUND: 10 untrustworthy axis references

Applying a sanity test to **all 107** addressable axis definitions (values must be
non-negative, below 60000, and strictly increasing) — **10 fail**, one per affected table:

| Table | Axis | Address | Reads as |
|---|---|---|---|
| `KL_NEL_TMOT` | x | `0x6C4CC4` | `[65336, 0, 100, 190, …]` |
| `KF_EDA_ANZ_SPORT_MD_EM1_IST` | x | `0x6C9D44` | `[63536, 64536, 0, 1000, 2000, 2500]` |
| `KF_FTRANSVL` | y | `0x6D8662` | `[0, 6554, 13107, …]` sentinel-ish |
| `KF_HUBESTM` | y | `0x6DC246` | `[62536, 63536, 64536, 0, 1000, 3000]` |
| `BMWtchdiag_pct_WgPHi_M` | x | `0x6DDCB4` | `[63136, 63936, 64736, 0]` |
| `BMWtqe_tqc_FlApplStgNorm_T` | x | `0x6E6900` | `[1000, 1000, 1000, …]` non-monotonic |
| `KF_MD_RES_NST_KEY` | y | `0x6E6F5C` | `[63536, 2000, 5000, 9000]` |
| `KF_ST_RKBAS_VVT` | y | `0x6F9C28` | `[62536, 63036, 63536, …]` |
| `KF_ST_RKBAS_GD` | y | `0x6F9D92` | `[62036, 63536, 64536, 0, 1000, …]` |
| `KL_ENA_NREG_DSC` | x | `0x6FED38` | fails monotonicity |

Values ≥ 60000 (`0xEA60+`) are Bosch sentinels, not breakpoints. These addresses are
inherited from the community source XDF and are wrong for this ECU. **The data
definitions for all 10 tables are byte-verified and unaffected** — only the axis pointers
are bad.

### Corrective patch — supplied separately, NOT applied

`patch_drop_bad_axes.py` → `out/R0C2J772B_CANDIDATE_axesclean.xdf`

It performs the smallest possible change: replaces each of the 10 bad `<XDFAXIS>` blocks
with a minimal address-less axis, leaving all 71 data definitions byte-for-byte identical.

```
candidate (current)  tables=71 cells=9369 axes=1692 covered=1507 (39.44 %)
axesclean (patched)  tables=71 cells=9369 axes=1522 covered=1505 (39.39 %)
```

The 2-byte coverage difference is precisely the two changed bytes that fell inside
untrustworthy axes. **`out/R0C2J772B_CANDIDATE.xdf` was left untouched.**

---

## 3 — Coverage, recomputed from the BINs

```
MD5 10SW002828_iRom_ori    = 40c3a007f425858e11cd9b0961dd321b   (matches baseline)
MD5 10SW002828_iRom_stage2 = 251f649b87413ec83d01ef7a53bed2af   (matches baseline)
sizes: 8,126,464 / 8,126,464
changed-byte mask computed directly from the two files: 3,821
```

| Quantity | Value |
|---|---|
| candidate definitions | 71 |
| distinct data-cell bytes | 9,369 |
| distinct axis bytes | 1,692 |
| **cell ∩ axis overlap** | **0** |
| changed bytes covered by **data cells** | **1,458** (38.16 %) |
| changed bytes covered by **axes only** | **49** |
| of which inside *untrustworthy* axes | 2 |
| **TOTAL (union, deduplicated)** | **1,507 / 3,821 = 39.44 %** |
| after the axis patch | 1,505 / 3,821 = 39.39 % |
| **uncovered** | **2,314** |

**Why 71 VERIFIED definitions cover only 1,507 of 3,821 changed bytes.** The two numbers
measure different things. 71 is a count of *tables*; 1,507 is a count of *modified bytes
that fall inside those tables*. The candidate's data cells total 9,369 bytes, i.e. only
**2.5 % of the 382 KB calibration block** — and the 3,821 changed bytes are spread across
**75 separate regions** spanning `0x6C0201`–`0x7BFCFF`. A table can be perfectly verified
and still contain no modified bytes; most of the tuner's edits are in regions no verified
definition reaches. The 20 edited-but-covered tables sit in 9 of the 75 regions.

Uncovered ranges (reproducible): **`out/uncovered_changed_bytes.json`** — 75 ranges, each
with start, end, span and changed-byte count.

### Correction to an earlier statement

In `INVESTIGATION_REPORT.md` I wrote *"no breakpoint axis was altered by the tuner"*,
computed from the legacy verified set. That was wrong. Recomputed from the candidate's
axis definitions, **49 changed bytes fall in axis ranges** — including a genuine, clean
rescale of the `KF_LABAS_1/2` load axis at `0x6FA6CE` from
`[2000, 3000, …, 18000]` to `[1600, 2400, …, 14400]` (0.8×, 34 bytes = 17 points).
The tuner did move breakpoints.

---

## 4 — Ignition exclusion preserved

The three candidate blocks at `0x70318B`, `0x7032CB`, `0x70340B` are **not assigned** to
any Bosch variable, in the candidate or in any generated artifact. They decode to
physically valid ignition data at ×0.5 °/LSB and share byte sequences with the SP15
reference, but:

- `KF_ZW_S_PF2` sits at a different address in **every one of the 13 local SP15 A2Ls**,
  spanning `0x6C37C0`–`0x6C456C` — a 3,500-byte window.
- This ECU's EPST is `R0C9J772B`, which appears in **none** of those 13 files.
- No arrangement test reproduced the reference layout in the user's image.

**Evidence required to identify them, in order of strength:**
1. A stock dump or DIATX P/N carrying EPST `R0C9J772B` — enables content-anchoring of the
   20-point `Nkw_opt` axis and 16-point `%` axis, which would pin the base address exactly.
2. The XDF/A2L filename the tuner actually used — pins the whole address space at once.
3. A Damos/A2L for `R0C9J772B` — would give the conversion and axis ordering authoritatively.
4. Failing all of the above: a manual, independently cross-checked sweep of the
   `0x703000`–`0x704000` region against the 13 SP15 reference images. Adequate but slow,
   and it would still rest on inference rather than provenance.

---

## 5 — Integrity checks

| Item | Result |
|---|---|
| `10SW002828_iRom_ori` | `40c3a007f425858e11cd9b0961dd321b`, 8,126,464 B, mtime 2026-10-08 13:12 |
| `10SW002828_iRom_stage2` | `251f649b87413ec83d01ef7a53bed2af`, 8,126,464 B, mtime 2026-10-07 16:16 |
| Both hashes vs report-5 baseline | **match** |
| BIN mtimes vs today | **unchanged — not written to at any point** |
| `out/R0C2J772B_verified.xdf` | `a9cf2244711a8b573ed94dbdff01ef10`, 87 tables, mtime 2026-10-10 11:28 |
| Legacy XDF mtime vs candidate (11:28 vs 12:25) | **no write after creation — unchanged** |
| Flash-like files (`.bin/.hex/.s19`) in tree | **none** |
| Modified BIN / flash-ready calibration | **none created** |

I should be transparent that I have **no pre-recorded hash of the legacy verified XDF**
from before this session; its immutability rests on its mtime (11:28, before the
candidate's 12:25) and on the fact that no script writes to it. That is weaker than a
hash comparison and I am not claiming otherwise.

### Working tree
Root: 2 BINs (untouched), `B58 Tuning Guide.md`, `BMW-XDFs-master.zip` (664 MB),
`ref/`, `mgflasher-map-packs/`, and 15 analysis scripts. Nothing was cleaned up.
`out/` holds 8 reports/XDFs and 17 JSON/CSV artifacts, listed in the tree.

---

## Conclusions

**Verified — XDF structure and conversion semantics**
71 definitions, 0 structural defects, 0 duplicates, 0 out-of-range, 27 linear formulas all
inside the parser-safe set, and 59 of 65 formulas cross-checked to an A2L `COMPU_METHOD`
with 6 documented unit conversions. **One defect found: 10 bad axis references, patch
supplied but not applied.**

**Changed bytes explained by current definitions**
1,507 of 3,821 (39.44 %); 1,458 via data cells, 49 via axes; 0 double-counted.
After the axis patch: 1,505 (39.39 %).

**Unresolved modifications**
**2,314 changed bytes in 75 ranges** (`out/uncovered_changed_bytes.json`). No definition
exists in any local file for `0x7311B4`, `0x730A8C`, `0x6FB116` or `0x6F1BA0`.
**I make no claim that these modifications are correct, safe, or benign.** They are
unexplained, and unexplained is not the same as harmless — they include what appear to be
a load-axis rescale and three large ignition-scale blocks. Nothing here should be treated
as authorisation to flash.

**Evidence still required for the ignition maps**
An artifact carrying EPST `R0C9J772B` — a stock dump, a DIATX P/N, the tuner's own XDF/A2L
filename, or an `R0C9J772B` Damos file. Absent that, the 3,500-byte SP15 address spread
makes any assignment a guess, and guessing is precisely what this audit exists to prevent.

**Stop condition:** met for formulas and coverage. The candidate is retained as an
**analysis tool**, not a tuning artefact. Ignition maps and unexplained regions remain
excluded.