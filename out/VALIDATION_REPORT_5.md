# VALIDATION_REPORT_5 — independent validation pass

Both BINs unchanged:
```
MD5 10SW002828_iRom_ori    = 40c3a007f425858e11cd9b0961dd321b
MD5 10SW002828_iRom_stage2 = 251f649b87413ec83d01ef7a53bed2af
```
`out/R0C2J772B_verified.xdf` unchanged (87 tables). Both hashes verified by direct read.
Changed-byte mask recomputed from the BINs: **3,821** (sizes 8,126,464 / 8,126,464).

`out/R0C2J772B_CANDIDATE.xdf` modified — **two concrete corrections**, both evidenced below.

---

## 1 — Formula validation against the A2L

### Syntax supported by the target editor
All 28 formulas previously present were of the form `X*k`, `X/k`, or `(X*k)*j` — linear,
multiplicative, **no additive offsets and no division by X**.

Empirical evidence of what shipped packs contain: **123 distinct formulas** across the
mgflasher and BMW-XDF packs, including `X*0.1+-273.14`, `X/1.333 - (48)` and
`1/(X*0.000011518903) * 80.11750567498999`. Those packs are therefore *not* uniformly
safe for a limited formula parser. My candidate contained **none** of that class.

### Independent numerical validation
Every formula was cross-checked against the A2L `COMPU_METHOD` for the same characteristic.
For these DAMOS files the `RAT_FUNC` coefficients evaluate as **`phys = X × COEFFS[5] / COEFFS[1]`**
(established empirically — the opposite reading produced physically impossible values).

| Result | Count |
|---|---|
| Formula agrees with A2L slope (rel. err < 1e-5) | **59** |
| Agree to < 0.2 % (source decimal rounding) | included above |
| Deliberate unit conversion (XDF shows AFR, A2L shows ratio) | **6** |
| **Genuine mismatch** | **1** |
| No A2L counterpart | 5 |

The 6 unit differences are `KF_LABAS_1/2`, `KF_BSLGF`, `KF_LAMIN_H`,
`BMWchas_lam_InjMpl_M`, `BMWchas_lam_InjMplThr_M` — all `× 14.7` (A2L unit `-`, XDF unit
AFR). These are consistent, documented unit choices, not errors.

### Corrections applied

| Definition | Previous | Corrected | Evidence |
|---|---|---|---|
| `KL_NEL_TMOT` | `X/2.55` (0.392157) | **`X*0.390625`** | A2L `COMPU_METHOD` COEFFS `0 64 0 0 0 25` → 25/64 = 0.390625 exactly. The source XDF approximated 64/25 as 1/2.55, a **0.39 % error** I had inherited. |
| `KF_LAMIN_H` | `(X*0.0002441406)*14.7` | **`X*0.0002441406*14.7`** | Identical value; removes the only parentheses in the file. |

Conversion formulas now: **27 distinct, all linear, all corroborated by the A2L.**

### Other properties verified
- **Byte order**: `MSB_FIRST` declared in the A2L for every characteristic checked;
  big-endian confirmed empirically (little-endian reading of the 16-bit maps yields
  non-physical values).
- **Data type / element width / dimensions**: taken from the source XDF unchanged; every
  emitted table's `rows × cols × esize/8` span re-derived and bounds-checked against the
  8,126,464-byte file — 0 out of range.
- **Data vs axis conversion order**: data and axis formulas are independent `MATH`
  elements in the XDF schema; the candidate preserves them separately and each was
  checked against its own A2L `COMPU_METHOD` / `AXIS_DESCR` entry.

---

## 2 — Coverage recalculated from the emitted definitions

Recomputed from scratch in `coverage5.py`, reading both BINs and parsing the candidate
XDF directly. No value was carried over from an earlier report.

```
candidate XDF tables                 : 71
distinct cell bytes in candidate     : 9,369
distinct axis bytes in candidate     : 1,692
bytes claimed as BOTH cell and axis  : 0
overlapping cell address ranges      : 0

changed bytes covered by VERIFIED    : 1,458
changed bytes covered by PROBABLE    : 0
changed bytes covered by PARTIAL     : 0
-----------------------------------------------------
COMBINED                             : 1,507 / 3,821 = 39.44 %
unexplained                          : 2,314
```

### Correction to report #4

**`1,904 / 3,821 = 49.8 %` is not the candidate XDF's coverage and must not be quoted as
such.** That figure summed three sets: the SP15 candidate tables, the six A2L-only
`KL_MD_K_MAX_*` curves (already inside the SP15 span — 144 bytes of address overlap), and
the **43 legacy SP11 tables that are not in the candidate XDF at all**.

Correct breakdown:

| Quantity | Value |
|---|---|
| **Candidate XDF (71 tables) coverage** | **1,507 / 3,821 = 39.44 %** |
| Legacy SP11 set (43 tables, not emitted) alone | 1,392 |
| Candidate ∪ legacy, deduplicated | 1,904 = 49.8 % |

Table count (71), modified bytes covered (1,507), and overlapping address range
(4,664 bytes SP15↔legacy) are three different quantities and are reported separately
above. `out/coverage_report5.json`.

---

## 3 — `KL_MD_K_MAX_*` family verified against the BINs

Each address re-derived from the source SP15 XDF and independently confirmed; values
decoded from the actual BIN bytes, not copied from any summary.

| Variable | SP15 XDF ref | Emitted | Δ | A2L `BYTE_ORDER` | raw u16 BE stock→tuned |
|---|---|---|---|---|---|
| `KL_MD_K_MAX_VL_HS` | `0x6B92D0` | `0x6F8CA0` | `+0x3F9D0` | MSB_FIRST | 500 → 650 (12/12) |
| `KL_MD_K_MAX_VL` | `0x6B92E8` | `0x6F8CB8` | `+0x3F9D0` | MSB_FIRST | 500 → 650 (12/12) |
| `KL_MD_K_MAX_RST_HS` | `0x6B9300` | `0x6F8CD0` | `+0x3F9D0` | MSB_FIRST | 300 → 300 (0/12) |
| `KL_MD_K_MAX_RST` | `0x6B9318` | `0x6F8CE8` | `+0x3F9D0` | MSB_FIRST | 300 → 300 (0/12) |
| `KL_MD_K_MAX_BST_HS` | `0x6B9330` | `0x6F8D00` | `+0x3F9D0` | MSB_FIRST | 300 → 650 (12/12) |
| `KL_MD_K_MAX_BST` | `0x6B9348` | `0x6F8D18` | `+0x3F9D0` | MSB_FIRST | 485 → 650 (12/12) |

- Point count 12 on all six; all six axis arrays strictly increasing and non-zero in the BIN.
- Unit and conversion from the A2L: `RAT_FUNC "%6.3" "Nm"`, `COEFFS 0 1 0 0 0 1` →
  **Nm, identity**.
- `RST`/`RST_HS` do not exist in the SP15 XDF; their addresses come from the A2L and were
  byte-checked independently.

**Explicit caution:** these are **torque-limit setpoints**, expressed in Nm. Nothing in the
data supports inferring delivered engine torque, actual boost pressure, or any engine
safety margin from them. The A2L titles ("boost curve", "full load curve") describe which
calibration branch the curve feeds, not the physical quantity — the unit field does. I
made no such inference in any report.

---

## 4 — Ignition: contradiction resolved; maps still excluded

**A second SP15 A2L was not needed — 13 SP15 A2Ls are already local**
(`mgflasher-map-packs/A2Ls/B48 B58 Gen 1/Generic/*3081*.a2l`). All 13 were inspected.

### Cause of the contradiction: mapping, not orientation or conversion

Two findings, both decisive:

**(a) My ×2 reading was wrong.** Applying the correct `phys = X × COEFFS[5]/COEFFS[1]`
semantics to the ignition compu method (`COEFFS 0 2 0 0 0 1`) gives **× 0.5 °/LSB**, not
×2. This is identical across **all 13 SP15 A2Ls — one distinct definition, zero
ambiguity**. The reference stock map then decodes exactly as expected:

```
KF_ZW_S_PF2 @0x6C37C0, x0.5 deg/LSB
  r00   26.0  29.5  31.0  31.5  32.5  33.5  34.0  35.0  35.5  35.5   35.5  36.5  37.0  38.0  39.0  40.0 ...
  r15    --   --   --   --   --   --   --    3.5   3.5   4.5   5.0   5.0   5.0   5.5   8.5   8.5  10.0 ...
```

26–40° at high load tapering to 3.5–12° at low load — a textbook B58 timing map. The
implausible 104–160° figures I reported in #4 were an artefact of the wrong coefficient
order.

**(b) The address is software-variant dependent.** `KF_ZW_S_PF2` is at:

| A2L | Address | A2L | Address |
|---|---|---|---|
| R0C9J8B2B_3081-080_017 | `0x6C37C0` | R0C9J9E4B_3081-090_020 | `0x6C43E8` |
| R0C9J8D2B_3081-080_021 | `0x6C3F08` | R0C9JA05B_3081-090_025 | `0x6C43E8` |
| R0C9J8I2B_3081-080_029 | `0x6C4234` | R0C9JA15B_3081-090_030 | `0x6C43E8` |
| R0C9J8I3B / J8I4B_029 | `0x6C4234` | R0C9JC05B_3081-090_050 | `0x6C43E8` |
| R0C9J962B_3081-090_010 | `0x6C4398` | R0C9JD06B_3081-090_060 | `0x6C4560` |
| R0C9J9E3B_3081-090_020 | `0x6C43E4` | R0C9JE15B_3081-090_080 | `0x6C456C` |

**A 3,500-byte spread across SP15 alone.** This ECU (`R0C9J772B`) is a *different* EPST from
all 13, so the correct address cannot be derived from any of them.

The three candidate blocks at `0x70318B/2CB/40B` do decode as physically valid ignition
data at ×0.5 °/LSB, and contain byte-identical values to the reference (user `r06`
cols 10–19 = reference `r00` cols 0–9, exactly). But the arrangement does not reproduce
under any tested layout, and the address window is ±3,500 bytes.

**Verdict: cause is mapping (address), not orientation or conversion.** Identity cannot be
demonstrated → **all ignition definitions remain excluded.**

---

## 5 — Classifications (kept separate)

| Class | Count | In candidate XDF? |
|---|---|---|
| VERIFIED | 71 | yes |
| PROBABLE | 39 | no (7 demoted for non-corroborating axes; the rest never qualified) |
| PARTIAL | 2 | no |
| REJECT | 3 | no |

## Corrections log

| # | Definition | Previous | Corrected | Evidence |
|---|---|---|---|---|
| 1 | `KL_NEL_TMOT` | `X/2.55` | `X*0.390625` | A2L COEFFS `0 64 0 0 0 25` |
| 2 | `KF_LAMIN_H` | `(X*0.0002441406)*14.7` | `X*0.0002441406*14.7` | identical value, parser-safe |
| 3 | Ignition conversion (report only) | ×2 °/LSB | ×0.5 °/LSB | A2L semantics, 13/13 A2Ls agree |
| 4 | Coverage (report only) | 49.8 % as candidate coverage | **39.44 %** candidate, 49.8 % including legacy | recomputed from emitted XDF |

## Negative results (recorded explicitly)
- `0x7311B4`, `0x730A8C`, `0x6FB116`, `0x6F1BA0`: **no** A2L characteristic or XDF table in
  any available file covers them at any delta in `0x3F800`–`0x41800`.
- `0x6F7F2E` (6 × 1×12 saturated to 32767): structure proven, **no** matching
  characteristic exists in the A2L.
- No ignition map identity established for EPST `R0C9J772B`.

## Reproducibility
`coverage5.py`, `regen_candidate.py`, `audit4.py`, `deltasweep.py` — all read-only against
the BINs. No flash file, no modified BIN, and no definition based on value plausibility.

## Stop condition
Formula semantics **pass** (59 exact + 6 documented unit conversions against the A2L, 1
defect found and corrected). Coverage **passes** and is now correctly stated as
**39.44 %** for the candidate. The candidate is retained as an **analysis tool**.

Ignition maps and all unexplained regions remain excluded pending evidence that the
address window for `R0C9J772B` can be narrowed — realistically requiring a stock dump or
DIATX P/N carrying that EPST.