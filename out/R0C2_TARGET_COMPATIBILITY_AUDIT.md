# R0C2 TARGET COMPATIBILITY AUDIT

Response to the clarification that the vehicle's intended ECU software is believed to be
`R0C2J772B`, and that the candidate XDF may have adapted definitions from a related
`R0C9…` variant.

**Read-only.** No BIN, XDF or calibration was patched, renamed, regenerated, flashed or
cleaned up. This document is the only file written. Nothing was deleted.

---

## 1 — Embedded software identifier, inspected independently

All offsets re-derived from `10SW002828_iRom_ori` by direct byte search. Decoding method:
ASCII byte-sequence match, cross-checked against the hex dump and the surrounding context
string. No reliance on any earlier report.

### The BIN carries **two** identifiers, in two namespaces

| Offset | Raw bytes | Decoded | Field |
|---|---|---|---|
| `0x08E526` | `52 30 43 32 4A 37 37 32 42` | `R0C2J772B` | inside EPK |
| `0x08E531` | `52 30 43 32 4A 37 37 32 42` | `R0C2J772B` | inside EPK |
| `0x707C9E` | `52 30 43 32 4A 37 37 32 42` | `R0C2J772B` | inside EPK (duplicate block) |
| `0x707CA9` | `52 30 43 32 4A 37 37 32 42` | `R0C2J772B` | inside EPK (duplicate block) |
| `0x6BFE36` | `23 45 50 53 54 3A 52 30 43 39 4A 37 37 32 42` | `#EPST:R0C9J772B` | EPST |
| `0x7BFEA0` | `23 45 50 53 54 3A 52 30 43 39 4A 37 37 32 42` | `#EPST:R0C9J772B` | EPST |
| `0x73A578` | `52 30 43 39 4A 37 37 32 42 43 44 48 58 34` | `R0C9J772BCDHX4` | Bosch block |
| `0x7BFEB6` | `52 30 43 39 4A 37 37 32 42 43 44 48 58 34` | `R0C9J772BCDHX4` | ID trailer |

Full context strings:

```
0x08E50D   53/1/MG1CS003/11/MG1CS003_BX8_R0C2J772B//R0C2J772B///
0x6BFE3C   #DME__8x0#D1#PST#EPST:R0C9J772B#S15A-17-11-490__S15C-17-11-490___
0x7BFEA0   ...#EPST:R0C9J772B______#R0C9J772BCDDHX4...
0x000164   10SW002828
```

Also embedded: hardware number `10SW002828` (`0x000164`, `0x010144`); ECU `MG1CS003`;
`#DME8.6-B58-SP15-M0-B30-G30-ECE-EU6c---_HGAG-LL-RL-AWD-PVL` (`0x7BFE3D`).

**Confidence: high.** Two independent identifier blocks (Bosch EPK at `0x08E50D` /
`0x707C9E` and the BMW EPST/PST block at `0x6BFE36` / `0x7BFEA0`) agree, are ASCII-plain,
and appear in duplicated flash copies — the signature of deliberate identification blocks,
not incidental text. Every `R` character is `0x52`, every digit/letter matches; there are no
near-miss variants of either string in the image.

**The clarification is corroborated: `R0C2J772B` is genuinely present in the BIN.**
It appears 4 times as the EPK (Bosch part key). The EPST is `R0C9J772B`. Both are real.

---

## 2 — Is `R0C2J772B` a *different* software from `R0C9J772B`? Tested empirically.

I did not assume either way. I extracted both fields from **every** stock image available.

| File | EPK (Bosch part key) | EPST | PST |
|---|---|---|---|
| `00003076501103_original.bin` | `R1`**C2**`J8B3B` | `R1`**C9**`J8B3B` | – |
| `00003076501D02_original.bin` | `R1`**C2**`J8I2B` | `R1`**C9**`J8I2B` | – |
| `000030765A3C06_original.bin` | `R1`**C2**`JD06B` | `R1`**C9**`JD06B` | – |
| `00003081501102_original.bin` | `R0`**C2**`J8B2B` | `R0`**C9**`J8B2B` | `S15A-18-03-510` |
| `00003081501D04_original.bin` | `R0`**C2**`J8I4B` | `R0`**C9**`J8I4B` | `S15A-18-07-510` |
| `00007972000705_original.bin` | `R1`**C2**`6015B` | `R1`**C9**`6015B` | – |
| **`10SW002828_iRom_ori` (target)** | `R0`**C2**`J772B` | `R0`**C9**`J772B` | **`S15A-17-11-490`** |

**The `C2` → `C9` substitution is universal and systematic.** In all 7 images the EPK uses
`C2` and the EPST uses `C9`, with an identical `J###B` software number. This is a
namespace difference in how the same software is written, not two different softwares.

**Consequence:** the reference packs are named by EPST (`R0C9J8B2B_3081-080_017_002`) and
the mgflasher A2L declares `VERSION "R0C2J8B2B"` — its own EPK form. Matching the target's
EPST `R0C9J772B` against those packs was namespace-correct, and **the specific concern that
definitions were taken from "a related R0C9 variant" does not hold at the naming level.**

**But the clarification surfaced a real, different risk — the S15 revision:**

```
target   R0C2J772B   S15A-17-11-490
ref      R0C2J8B2B   S15A-18-03-510
ref      R0C2J8I4B   S15A-18-07-510
```

The target is on **S15 revision 17**; both SP15 references are on **revision 18**. This is a
software-content difference inside the same platform, and it is the actual source of
uncertainty — not the `C2`/`C9` naming.

---

## 3 — Reference artifacts used to build/validate the candidate

| Path | MD5 (16) | Software ID | Provenance |
|---|---|---|---|
| `ref/BMW-XDFs-master/B58gen1/00003081501102.xdf` | `3110580438b22b04` | – (no embedded ID) | community pack; primary XDF |
| `ref/BMW-XDFs-master/B58gen1/00003081501102_original.bin` | `bcb970a18d374f84` | EPK `R0C2J8B2B` / EPST `R0C9J8B2B` / `S15A-18-03-510` | **primary stock image** — byte-verification source |
| `mgflasher-map-packs/A2Ls/B48 B58 Gen 1/Generic/R0C9J8B2B_3081-080_017_002.a2l` | `cb43b8aa50cdf259` | `VERSION "R0C2J8B2B"` | DAMOS; conversion + `KL_MD_K_MAX_*` identity |
| `ref/BMW-XDFs-master/B58gen1/00003076501103.xdf` | `00217d4176a16d45` | – | superseded SP11 pack |
| `ref/BMW-XDFs-master/B48gen1/…01103_original.bin` (actual path `B58gen1`) | `8b9573bf5009b1e4` | EPK `R1C2J8B3B` / EPST `R1C9J8B3B` | superseded SP11 image; legacy set only |

**Every reference is from the `C2J8B2B` / `C9J8B2B` software (S15A-18), or the SP11
`C2J8B3B` set. None is an artifact for `C2J772B` / `C9J772B`.**

---

## 4 — Reclassification of the 71 candidate definitions

The classification standard the clarification imposes: *not* target-verified merely because
address, shape or formula matches a related variant.

For each of the 71 definitions, what is actually evidenced **about the target BIN**:

- **Content**: the bytes at the emitted address in `10SW002828_iRom_ori` are **100 %
  byte-identical** to the reference definition's bytes. This is direct evidence about the
  target's own bytes, not a shape/formula resemblance.
- **Axes**: byte-identical to the reference at the same delta (97 addressed axes, all
  passing sanity).
- **Identity**: the Bosch variable name is **inherited from the reference pack**. The target
  BIN contains no per-map naming; nothing inside it says "this is `KF_LABAS_1`".
- **Software provenance**: no artifact exists for `C2J772B` / `S15A-17-11-490`.

| Class | Count | Meaning |
|---|---:|---|
| **Verified for exact `R0C2J772B`** | **0** | **No artifact for that software exists locally.** Content evidence is strong, but it is byte equality with an S15A-18 sibling image, not proof of target-specific provenance. |
| **Structurally corroborated, not proven for target** | **71** | Placement + content + axes all byte-proven **in the target BIN**; identity inherited from `R0C2J8B2B` / `S15A-18-03-510`. Residual risk: map-set membership may differ on S15 rev 17. |
| **Probable** | 41 | 39 `PROBABLE` + 2 `PARTIAL`: byte-verified but axis failed corroboration; deliberately not emitted. |
| **Rejected / unresolved** | 3 + 2,101 bytes | 3 `REJECT` definitions, and 2,101 changed bytes in 70 regions reaching no definition. |

### Transferability assessment, element by element

| Element | Transferable to `C2J772B`? | Evidence |
|---|---|---|
| **Data address** | **Yes, content-proven** | Target bytes at the address are byte-identical to the reference. Independent of naming. |
| **Breakpoint axes** | **Yes, content-proven** (97/97) | Axis bytes byte-identical at the same delta. |
| **Dimensions / element width** | **Yes** | Follows from the byte-identical span. |
| **Endianness** | **Yes** | Big-endian; little-endian yields non-physical values. |
| **Conversion formula** | **Yes, corroborated** | 59 formulas cross-checked against A2L `COMPU_METHOD`; 6 are documented unit conversions (×14.7 AFR). Formula is a property of the variable, not of the image. |
| **Map identity (Bosch name)** | **NOT proven for target** | Name comes from the reference pack. No target-side naming exists. |
| **Map-set membership** | **NOT proven for target** | Demonstrably differs: `KF_ZW_*` ignition maps exist in all 13 SP15 A2Ls but could not be located in the S15A-17 target. This is the concrete evidence that rev-17 membership differs. |

**The honest reading:** the *placement* of all 71 definitions is proven against the target's
own bytes and is about as strong as offline evidence gets. The *identification* — that the
calibration variable at that address is named `KF_LABAS_1` etc. — is inherited from a
software sibling and cannot be proven without an artifact for the target. Those are
different claims and this audit keeps them apart.

---

## 5 — Definitions usable only for exploratory analysis

**All 71.** Because zero definitions carry target-specific provenance, none may be used for
any decision whose consequence is safety-relevant. They remain valid as:

- a map of *where* calibration data sits in this image (content-proven);
- an aid to understanding the tuner's edits, where the changed bytes fall inside proven
  data regions.

They are **not** valid as evidence of what any given map *is*, and **not** valid as a basis
for modifying the ECU.

---

## 6 — Unresolved modified-byte regions

From `out/changed_bytes_inventory.csv` (89 regions, 3,821 changed bytes, verified
no double counting):

| Classification | Bytes | % |
|---|---:|---:|
| `VERIFIED_CELL` | 1,458 | 38.16 % |
| `VERIFIED_AXIS` | 47 | 1.23 % |
| `PROBABLE` | 215 | 5.63 % |
| `UNEXPLAINED` | 2,101 | 54.99 % |

Specifically preserved as unidentified:

| Region | Note |
|---|---|
| `0x70318B`, `0x7032CB`, `0x70340B` | ignition-scale blocks, **no Bosch name assigned** |
| `0x7311B4` (288 changed) | no definition in any local file |
| `0x730A8C` (128 changed) | no definition in any local file |
| `0x6FB116` (72 changed) | no definition in any local file |
| `0x6F1BA0` (44 changed) | no definition in any local file |
| `0x6F7F2E` (144 changed) | 6 × 1×12 curves saturated to 32767; structure only |

**No inference of safety, correctness or intended function has been drawn from any decoded
value.** Unidentified is not benign.

---

## 7 — Exact reference artifact needed

**One file, in descending order of value:**

1. **A stock BIN read from an ECU reporting `R0C2J772B` / `S15A-17-*`** — decisive. Would
   let the existing `deltasweep.py` / `align.py` pipeline run directly against the target
   software and confirm both the 71 placements *and* resolve the ignition maps that differ
   on S15 rev 17.
2. **The DIATX P/N for `R0C2J772B`** (format `R?C?J772B_<diatx>`) as reported by a bench
   tool — keys the correct pack in the mgflasher repository. Note the repository files are
   named by EPST, so the search key would be `R0C9J772B`; the closest local files are
   `R1C9J772B_3076-070_009_002` (XDF and A2L), which are **R1C9**, a different EPST, and are
   **not** a substitute.
3. **Any XDF / A2L / DAMOS file whose `VERSION` or EPST is `R0C2J772B` or `R0C9J772B`.**
4. **The definition file the tuner used.**

What would *not* help: the existing `R0C9J8B2B` / `R0C9J8I4B` SP15 images. They are already
exhausted, they are S15 rev 18, and their ignition-map membership demonstrably does not
match this image.

---

## Verdict

- **`R0C2J772B` is confirmed present in the target BIN** (EPK, 4 occurrences). The
  clarification is corroborated, not merely assumed.
- **`R0C2J772B` and `R0C9J772B` are the same software in two namespaces** — proven
  empirically across 7 images, not assumed. The candidate's use of `R0C9`-named references
  was therefore namespace-correct.
- **The real residual risk is different and now named**: the target runs **S15A-17**, both
  SP15 references run **S15A-18**. The ignition maps are concrete proof that map-set
  membership differs between them.
- **Zero of 71 definitions are verified for the exact target.** All 71 are structurally
  corroborated against the target's own bytes and are usable **only** for exploratory
  analysis. **1,458 changed bytes** are explained by content-proven data cells; **2,101
  bytes (55 %)** remain unexplained and carry no safety inference whatsoever.