# AXIS_AND_METADATA_AUDIT

Read-only forensic pass. Baseline: `out/TUNER_DELTA_FORENSIC_REPORT.md`,
`out/tuner_delta_regions.csv`.

**Read-only verified.** Both BIN MD5s unchanged; all XDFs unchanged; nothing patched,
renamed, regenerated, flashed or cleaned up. Files written by this pass:
`out/AXIS_AND_METADATA_AUDIT.md`, `out/axis_overlap_regions.csv`.

---

## 1 — Changed regions overlapping candidate cells or axes

19 of the 89 changed regions overlap a candidate definition. Per-region offsets and
before/after hex for all of them are in `out/axis_overlap_regions.csv`.

**Evidence boundary, stated once and applied throughout.** Per
`R0C2_TARGET_COMPATIBILITY_AUDIT.md`, **zero** candidate definitions are verified for the
exact `R0C2J772B` / `S15A-17-11-490` target. Every linkage below is **address overlap
against a byte-proven S15A-18 reference** (`C2J8B2B` / `S15A-18-03-510`). The Bosch names
are **inherited**, not proven for this image. Two columns are kept apart throughout:
`overlap_kind` (byte-proven placement) and `name_confidence` (inherited identity).

| Region | Range | Chg | Overlap kind | Definitions (inherited name) |
|---|---|---:|---|---|
| 3 | `0x6C54CD` | 1 | axis only | `KL_MDRED_NKW` x |
| 5 | `0x6C9CAE-0x6C9D5B` | 52 | cell + axis | `KF_EDA_ANZ_SPORT_MDK_IST` |
| 7 | `0x6CD31E-0x6CD3A1` | 132 | cell | `KF_FMS_HFMPL_MN/MX` |
| 12 | `0x6D9DC6-0x6D9DF5` | 48 | cell | `KL_RF_MAX`, `KL_RF_MAX_UESP` |
| 13 | `0x6DA1E6-0x6DA209` | 36 | cell | `KL_LAMX` |
| 14 | `0x6DDBE6-0x6DDC27` | 59 | cell | `BMWtchdiag_pct_WgPHi_M/WgPLo_M` |
| 16 | `0x6DE03A-0x6DE0B3` | 114 | cell | `BMWtchsp_rat_p_CmprMax_M/CmprPmp_T` |
| 18 | `0x6E2EAC-0x6E2EB5` | 10 | axis only | `KF_MDIOP_1_TQE` x |
| 19 | `0x6E68DC-0x6E68FF` | 36 | cell | `BMWtqe_tqc_FlApplStgNorm_T` |
| 22 | `0x6EED12-0x6EED73` | 90 | PROBABLE | `BMWchas_lam_InjSng_M` |
| 23 | `0x6EEDDA-0x6EEE3B` | 90 | PROBABLE | `BMWchas_lam_InjSngThr_M` |
| 24 | `0x6EEEE2-0x6EEF43` | 90 | cell | `BMWchas_lam_InjMpl_M` |
| 25 | `0x6EEFAA-0x6EF00B` | 90 | cell | `BMWchas_lam_InjMplThr_M` |
| 33 | `0x6F8CA0-0x6F8D2F` | 96 | cell | `KL_MD_K_MAX_VL/VL_HS/RST/RST_HS/BST/BST_HS` |
| 34 | `0x6FA260-0x6FA45D` | 301 | cell | `KF_LABAS_2` |
| 35 | `0x6FA4C4-0x6FA6EF` | 366 | cell **+ axis** | `KF_LABAS_1`, `KF_LABAS_2` + y |
| 36 | `0x6FB116-0x6FB181` | 72 | cell | `KF_FMS_DKPSRPL_MN/MX` |
| 38 | `0x6FC899-0x6FC8A1` | 8 | cell | `K_EDA_MD_ANZ_BS_SCAL_CODE`, `K_EDA_P_ANZ_SPORT_BS_SCAL_CODE` |
| 39 | `0x6FCA5C-0x6FCA95` | 36 | PROBABLE | `BMWchas_st_OpmBasc_M` |

---

## 2 — The shared axis at `0x6FA6CE`: fully characterised

**Element width** 16-bit · **byte order** big-endian · **point count** 17 (matches the
source XDF: y-axis at `0x6BAD0E`, `indexcount=17`, `mmedelementsizebits=16`).
Monotonic strictly increasing in **both** images.

| idx | stock | Stage 2 | delta | ratio |
|---:|---:|---:|---:|---:|
| 0 | 2000 | 1600 | −400 | 0.800000 |
| 1 | 3000 | 2400 | −600 | 0.800000 |
| … | … | … | … | … |
| 16 | 18000 | 14400 | −3600 | 0.800000 |

**The transformation is exactly `new = old × 0.8`, applied uniformly to all 17 points, with
zero rounding error** — every stock value is a multiple of 1000, so ×0.8 is exact in
integers. Verified numerically against the Stage 2 image: all 17 match exactly.

**Definitions sharing this axis: exactly two.** `KF_LABAS_1` (data `0x6FA45E`, 17×18) and
`KF_LABAS_2` (data `0x6FA1FA`, 17×18). The map is 17 rows × 18 columns, so the 17-point
y-axis is the row axis and the 18-point x-axis at `0x6FA6F0` is the column axis. **The
x-axis was not changed.**

**Physical meaning: not determined.** The source pack labels the y-axis with no unit and the
value range 2000–18000 admits several readings. I am not assigning a physical quantity to
this axis. What is proven is the arithmetic (×0.8, exact) and that it affects exactly two
inherited-named maps.

---

## 3 — `0x7BFCFC`–`0x7BFCFF`: negative result, field NOT identified as a checksum

```
ori    0x7BFCFC  FF AA 0F 5A
stage2 0x7BFCFC  AD 63 60 DD
```

Context: four bytes in a run of erased `FF` padding (`0x7BFCF0`–`0x7BFCFB` all `FF`),
immediately before a fixed 16-byte block at `0x7BFD00` that is **identical** in both images.

**Test performed.** Because the field is 4 bytes and adjacent to the calibration, I tested
whether any standard algorithm over plausible coverage ranges reproduces the **stock** value
`0xFFAA0F5A` — the value is known, and the stock image is known, so a match would be
decisive. Grounded, bounded test:

- 6 CRC-16 variants (ARC, CCITT-FALSE, XMODEM, MODBUS, KERMIT, BUYPASS) ×
  10 coverage ranges (`0x0–0x7C0000`, `0x6C0000–0x740000`, `0x680000–0x780000`,
  `0x600000–0x7C0000`, `0x6C0000–0x7BFD00`, `0x0–0x6C0000`, `0x600000–0x6C0000`,
  `0x700000–0x7C0000`, `0x6BFC00–0x7BFCFC`, `0x0–0x7BFCFC`)
- CRC-32 over the same ranges
- plain 32-bit byte sums over the whole image and over the calibration block

**Result: no match.** Also non-matches: whole-image sum `0x3E2B7C11`, calibration-block sum
`0x01B60E71`, against target `0xFFAA0F5A`.

**Cross-image check not possible.** The SP15 reference image is `0x780100` bytes and does
not extend to offset `0x7BFCFC`, so the field cannot be compared against another
software version.

**Conclusion: this field is NOT identified.** Its position and size remain *consistent
with* a checksum or signature, but no reproducible calculation validates that, so per the
evidence standard it is recorded as: *changed, 4 bytes, outside the calibration block, in
erased padding, preceding an unchanged fixed block, mechanism unknown.* I make no claim
that the tuner computed it, or that it validates anything.

---

## 4–5 — The 69 unidentified regions: content correspondences proven

I searched each priority region's stock bytes for verbatim matches in the local reference
images. **All seven priority regions match**, and the matches are long:

| Region | Reference image | Offset | Delta | Continuous identical run | Falls inside SP15 XDF map span? |
|---|---|---|---|---:|---|
| `0x730A8C` | `…81501102` | `0x6F1CA4` | `+0x3EDE8` | 157 B | no |
| `0x6F1BA0` | `…81501102` | `0x6B234C` | `+0x3F854` | **1,010 B** | no |
| `0x6F7F2E` | `…81501102` | `0x6B88E8` | `+0x3F646` | 166 B | no |
| `0x70318B` | `…81501102` | `0x6C39BB` | `+0x3F7D0` | **3,579 B** | yes — `KF_ZW_S_PF1` (0x6C3900+0xBB) |
| `0x7032CB` | `…81501102` | `0x6C3AFB` | `+0x3F7D0` | **3,259 B** | yes — `KF_ZW_PF2` (0x6C3A40+0xBB) |
| `0x70340B` | `…81501102` | `0x6C39BB` | `+0x3FA50` | 123 B | yes — `KF_ZW_S_PF1` (0x6C3900+0xBB) |
| `0x7311B4` | `…81501102` | `0x6F23A0` | `+0x3EE14` | 533 B | no |

**What this proves.** All seven regions contain **inherited calibration content** present
verbatim in the S15A-18 reference — they are not code, datalog structures or arbitrary
data. This is stronger evidence than anything available previously, and it is reproducible
(byte-substring search).

**The Stage 2 versions of these blocks are found nowhere in any reference** (with one
exception below) — the tuner's edits are novel content, not a stock-value write.

### The three ignition-scale blocks — identity still NOT assigned

The stock correspondence lands **inside** named SP15 map spans, at +`0xBB` into a 16×20 map.
I am **not** assigning ignition identities, for three concrete reasons:

1. **The +0xBB offset is an artifact of where I started the search.** The match begins at
   the first changed byte of each region, so the reference hit lands at the same relative
   position. That does not establish where a map boundary is.
2. **The deltas conflict.** The content correspondence gives `+0x3F7D0`. The breakpoint
   axes located at `0x6EC5DE`/`0x6EC536` earlier give `+0x3F9CE`. These differ by
   `0x1E02` and cannot both be correct — so either those axes are shared with other maps
   (as suspected in the forensic audit), or the content hit is coincidental in position.
   Unresolved.
3. Blocks 1 and 3 share 129/133 stock bytes and both hit the *same* reference address,
   while blocks are spaced exactly `0x140` (320 B) apart in the target. Consistent with
   consecutive 320-byte maps, but a 320-byte spacing is dimension evidence, which the brief
   excludes as a basis for naming.

### `0x6F7F2E`

**Element width determined: 16-bit.** The 144 bytes contain exactly two distinct uint16
values — `0x7530` = 30,000 (stock) and `0x7FFF` = 32,767 (Stage 2). 72 cells. Consistent
with 6 × 12 curves of 12 points each, matching six 12-point axes found at `0x6F8022`+24k.
**No map name assigned.** Its stock content is present at reference `0x6B88E8`, and notably
the *Stage 2* pattern (`7FFF` repeats) also occurs at reference `0x699F42` — so the saturated
value is not unique to the tuner's edit. No local reference names this span.

### Regions with no reliable identification — negative results recorded

`0x730A8C`, `0x6F1BA0`, `0x7311B4` and the remaining 62 unidentified regions: content
correspondence to reference calibration is **proven**, but **no reference maps them**
(`NOT inside any SP15 XDF map span`). They therefore cannot be named from local evidence.
`0x7311B4` (288 changed bytes) remains the largest single unexplained region.

---

## 6 — Count reconciliation

```
recomputed difference mask (direct byte comparison) : 3,821
out/tuner_delta_regions.csv rows                     : 89
sum of changed_bytes column                          : 3,821
changed bytes inside recorded region spans           : 3,821 / 3,821
per-region counts agree                              : True
RECONCILED                                           : True
```

**Region span ≠ changed bytes.** Spans total considerably more than 3,821 because most
regions contain unchanged bytes between changed ones (e.g. region 35 spans 555 B but contains
366 changed). The CSV's `changed_bytes` column is the count used throughout; `span` is
recorded separately and is never used as a byte count.

---

## What remains unknown

1. **The mechanism and meaning of the 4 bytes at `0x7BFCFC`** — no algorithm reproduces the
   stock value; the reference image does not reach that offset.
2. **The identities of the three ignition-scale blocks**, despite proven content
   correspondence, because the map-boundary inference is unsupported and the content delta
   conflicts with the axes delta.
3. **The identities of `0x7311B4`, `0x730A8C`, `0x6F1BA0`, `0x6F7F2E`** — content proven as
   inherited calibration; unnamed in every local reference.
4. **62 further unidentified regions**, 2,090 bytes total (54.7 % of all changes).
5. **The physical meaning of the `0x6FA6CE` axis.** The ×0.8 rescale is proven; the quantity
   is not identified.
6. **Whether the candidate definitions' names are correct for this image.** They are
   inherited from an S15A-18 reference, and this image is S15A-17.

**I do not claim the Stage 2 calibration is safe, correct, or fully identified.** The single
artifact that would materially change conclusions remains a stock BIN reporting
`R0C2J772B` / `S15A-17-*`, or any XDF/A2L/DAMOS file carrying that EPST.