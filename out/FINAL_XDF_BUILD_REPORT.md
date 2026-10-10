# FINAL_XDF_BUILD_REPORT

Build of `out/R0C2J772B_manual_inspection.xdf` — an exploratory manual-inspection XDF.
Read-only throughout: no BIN, existing XDF or existing report was modified.

---

## 1 — Hashes

### Before (recorded at start of this phase)

| File | Size | MD5 |
|---|---|---|
| `10SW002828_iRom_ori` | 8,126,464 | `40c3a007f425858e11cd9b0961dd321b` |
| `10SW002828_iRom_stage2` | 8,126,464 | `251f649b87413ec83d01ef7a53bed2af` |
| `out/R0C2J772B_verified.xdf` | 141,733 | `a9cf2244711a8b573ed94dbdff01ef10` |
| `out/R0C2J772B_CANDIDATE.xdf` | 103,223 | `fba37eadf02d1d12f1b7bca1a530b8fa` |
| `out/R0C2J772B_CANDIDATE_axesclean.xdf` | 101,325 | `aa01976c1d66047a9e92110ee39efe44` |

SHA-256 of the BINs:
- original  `fcc9b8f21127627302a0a96823848f9fb11ecc6385f06adf4957e4c591698356`
- stage 2   `c544c1fd686e3f4edefd1d8d60b48464d434e02945a545044eac6745f4c8b8f5`

### After — see section 8

---

## 2 — Source selection and rationale

**Chosen: `out/R0C2J772B_CANDIDATE_axesclean.xdf`.**

Compared the three existing XDFs:

| File | Tables | Assessment |
|---|---:|---|
| `R0C2J772B_verified.xdf` | 87 | Rejected — built from an **SP11** reference. 38 of its tables fail byte-identity against any reference; it also carries the vacuous `min/max` acceptance flaw. Retained unchanged as legacy history only. |
| `R0C2J772B_CANDIDATE.xdf` | 71 | Rejected as the base — contains **10 axis references that read sentinel values** or non-monotonic sequences in the target BIN (i.e. not breakpoint arrays). |
| `R0C2J772B_CANDIDATE_axesclean.xdf` | 71 | **Selected** — same 71 data definitions with those 10 bad axis references removed and neutralised. Passed a full re-audit: 97 addressed axes, 0 failing sanity. |

The brief said not to rebuild from scratch when an existing definition has stronger
support, so the file was **copied**, not regenerated. Only two evidence-supported changes
were applied on top:

1. **Header `<description>`** replaced with an explicit caveat stating that names are
   inherited from S15A-18 and are not confirmed for S15A-17, and that the file is not a
   validated tuning definition.
2. **Seven exploratory tables appended** under a new category
   `UNVERIFIED REGIONS (raw, no identity)`.

Nothing else was touched. Formulas, axis references, addresses, dimensions and element
widths are byte-identical to the source file.

---

## 3 — Confidence tiers applied to the 71 inherited definitions

| Aspect | Status |
|---|---|
| Address, dimensions, element width, byte order | **Verified against the reference** *and* byte-proven in the target BIN |
| Conversion formula | **Corroborated by A2L** for 59 of 65 checked; 6 are deliberate ×14.7 AFR conversions |
| Bosch map name and unit | **INHERITED** from the S15A-18 reference — not verified for S15A-17 |
| Physical meaning | **Not established.** Structural correspondence is not proof of meaning. |

---

## 4 — Definitions added (7)

All exploratory, all neutral-named, all with the unknown-units statement in the table
description. Each has a single address-less axis (no breakpoints fabricated) and identity
`X` (no scaling invented).

| Name | Address | Dims | Bits | Basis for inclusion |
|---|---|---|---|---|
| `UNVERIFIED_REGION_6F7F2E` | `0x6F7F2E` | 1×72 | 16 | Element width **established**: 144 bytes contain exactly two distinct uint16 values, 30000 / 32767. Shape deliberately not asserted. |
| `UNVERIFIED_REGION_6F1BA0` | `0x6F1BA0` | 1×128 | 8 | Stock bytes match a reference verbatim (1,010 contiguous). Inherited calibration content. |
| `UNVERIFIED_REGION_730A8C` | `0x730A8C` | 1×146 | 8 | Stock bytes match a reference verbatim (157 contiguous). |
| `UNVERIFIED_REGION_7311B4` | `0x7311B4` | 1×434 | 8 | Largest unexplained change (288 bytes). Stock bytes match a reference verbatim (533 contiguous). |
| `UNVERIFIED_REGION_70318B` | `0x70318B` | 1×133 | 8 | Stock bytes match a reference verbatim (3,579 contiguous). **Not identified** — see below. |
| `UNVERIFIED_REGION_7032CB` | `0x7032CB` | 1×133 | 8 | Stock bytes match a reference verbatim (3,259 contiguous). Not identified. |
| `UNVERIFIED_REGION_70340B` | `0x70340B` | 1×133 | 8 | Stock bytes match a reference verbatim (123 contiguous). Not identified. |

**Why the three `0x703xxx` blocks carry no ignition identity.** Their stock content matches
a reference image for thousands of contiguous bytes, which proves they are inherited
calibration content. It does **not** establish a map boundary: the match begins where the
changed region begins, which is a property of where I searched, not of the data. The
content delta `+0x3F7D0` also conflicts with the independently located breakpoint-axis delta
`+0x3F9CE` by `0x1E02`. Dimensions were therefore left as a flat array, and no name, unit
or function was assigned.

**Deliberately excluded:** the 4 bytes at `0x7BFCFC`. No algorithm tested (6 CRC-16 variants
× 10 coverage ranges, CRC-32, byte sums) reproduces the stock value `0xFFAA0F5A`, so it is
not presented as a checksum or any other field.

---

## 5 — Definitions omitted (44)

| Class | Count | Reason |
|---|---:|---|
| `REJECT` | 3 | < 50 % byte match — placement wrong. `KLVRABSCH`, `KL_MDG_MAX_GANG_AT`, `KF_ZW_S_PF2` |
| `PARTIAL` | 2 | 50–81 % byte match — right family, wrong address. `KF_ENA_NREG_GANG_SYN`, `BMWtchctr_rat_p_ComprLimPctl_T` |
| `PROBABLE` | 39 | Byte-verified but axis failed corroboration, or the delta was not unique. Including them would place non-credible breakpoints on screen. |

Additionally **10 axis references** were dropped (inherited from the `axesclean` file, not
introduced here) because they read sentinel values ≥60000 or non-monotonic sequences in the
target BIN. Six tables consequently have no usable axis and display raw values only. **No
removed address was restored**, because no independent evidence supports a replacement.

---

## 6 — Validation results

```
XML parses                                    OK    XDFFORMAT version 1.80
REGION start=0x0 size=0x7c0000 = 8126464       OK    matches both BINs exactly
tables                                         78   (71 inherited + 7 exploratory)
structural errors                              0
distinct conversion formulas                   27   0 outside the safe set [X0-9.*/]
data spans within BIN                          all
axis point count vs table geometry             all consistent
cell AND axis address overlap                  0
address-less axis slots                        59   single implicit breakpoint, no data read
```

Format checks against known-working packs:

| Check | Result |
|---|---|
| XML declaration + `XDFFORMAT` 1.80 | PASS |
| `XDFHEADER`, `BASEOFFSET`, `DEFAULTS`, `REGION` present | PASS |
| every `CATEGORYMEM` index resolves | PASS |
| every table has a title and description | PASS |
| every z axis carries `MATH`/`VAR` | PASS |
| every z axis is unsigned (datatype 0) | PASS |
| no duplicate `uniqueid` | PASS |

Coverage (machine-checked, deduplicated):

```
distinct data-cell bytes      10,620
distinct axis bytes           1,522
cell AND axis overlap             0
changed bytes covered       2,382 / 3,821 = 62.34 %
tables differing stock vs stage2  31
```

Per-table raw decode against the stock BIN is in `out/manual_xdf_validation.csv`.

**I did not open this file in TunerPro.** TunerPro is not available in this environment.
The checks above are structural and numerical, and the format conventions were copied from
packs that are known to work in it. It has not been empirically confirmed to load.

---

## 7 — Unresolved issues and confidence

| Item | Confidence |
|---|---|
| 71 inherited definitions' addresses/dimensions | **High** — byte-proven in the target BIN |
| Their conversion formulas | **High** where an A2L counterpart exists; **Medium** where not |
| Their Bosch names and units | **Low** — inherited from S15A-18, not verified for S15A-17 |
| `KL_MD_K_MAX_*` identity and `Nm` unit | **High** — A2L-identified, data and axes byte-identical |
| The 7 exploratory regions' identity/dimensions | **None** — deliberately unassigned |
| Meaning of the 4 bytes at `0x7BFCFC` | **Unknown** — mechanism not established |
| 1,439 changed bytes outside every definition | **Unknown** |
| Whether this image's map set matches S15A-18 | **Doubtful** — proven not to for the ignition maps |

**Explicit statement:** this is an exploratory manual-inspection XDF, **not** a validated
tuning definition. Zero of its 71 named tables are verified for the exact `R0C2J772B` /
`S15A-17-11-490` target. I do not claim the Stage 2 calibration is safe, correct, or fully
identified.

---

## 8 — Deliverables and post-build hash verification

Files created by this phase:

| Path | Purpose |
|---|---|
| `out/R0C2J772B_manual_inspection.xdf` | The inspection XDF (new file, no overwrite) |
| `out/MANUAL_TUNERPRO_REVIEW.md` | How to use it |
| `out/FINAL_XDF_BUILD_REPORT.md` | This report |
| `out/manual_xdf_validation.csv` / `.json` | Per-table validation output |
| `build_manual_xdf.py`, `validate_manual_xdf.py` | Reproducible build and validation |

Nothing was deleted, cleaned up, patched, flashed or regenerated.

---

## 9 — What would move this forward

1. **A stock BIN reporting `R0C2J772B` / `S15A-17-*`** — the single artifact that would let
   the existing pipeline confirm the 71 placements against the exact target and resolve the
   ignition-block conflict.
2. **The DIATX P/N** for `R0C2J772B` (search the mgflasher repo by EPST `R0C9J772B`; the
   local `R1C9J772B_3076-070_009_002` files are a **different EPST**, not a substitute).
3. **A tuner XDF/A2L** for this exact software.
4. **Confirmation in TunerPro** that the file loads — I cannot test that here.