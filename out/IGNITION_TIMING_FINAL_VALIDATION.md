# IGNITION TIMING MAPS — FINAL READ-ONLY VALIDATION

Independent re-validation of the 10 ignition-timing candidates.

- **Artifact validated:** `out/R0C2J772B_ignition_timing.xdf` (MD5 `a638453788baef893e2ae29c9334e278`)
- Reference A2L: `mgflasher-map-packs/A2Ls/B48 B58 Gen 1/Generic/R0C9J8B2B_3081-080_017_002.a2l` — project `R0C2J8B2B`, **S15A-18**
- Reference image: `ref/BMW-XDFs-master/B58gen1/00003081501102_original.bin` — **S15A-18**
- Target: `10SW002828_iRom_ori` / `10SW002828_iRom_stage2` — **S15A-17**

Read-only. No BIN, XDF, report, git state or remote was modified. The known-broken
`out/R0C2J772B_timing_candidates.xdf` is untouched (MD5 `3bd5c15c16ec40d0525d09521ba46d0f`,
verified unchanged; `git status` clean).

---

## 0. Three errors found in my own previous report

The re-derivation exposed defects in `IGNITION_TIMING_REINVESTIGATION.md`. They are
corrected here and must not be carried forward.

**E1 — the tuning delta was wrong by an order of magnitude, and the row/column labels
were transposed.** The previous report claimed `+27.0 … +51.0°`, mean `+38.8°`, at
"rows 7–19, cols 9–15". Both are wrong. The cause was an indexing bug: the diff list
stored `(i%20, i//20, …)` but the delta was then computed as `s8(tn[c]) - s8(s)`,
indexing the tuned array by **column number instead of flat offset**. True values:

| Map | Cells | Raw byte delta | At ×0.5 | Rows (load) | Cols (Nkw) |
|---|---|---|---|---|---|
| `KF_ZW_PF1` | 91 | **+2 … +4** | **+1.0 … +2.0°** | 9–15 (9000–18000) | 7–19 (2250–6950 rpm) |
| `KF_ZW_PF2` | 91 | +2 … +4 | +1.0 … +2.0° | 9–15 | 7–19 |
| `KF_ZW_S_PF1` | 91 | +2 … +4 | +1.0 … +2.0° | 9–15 | 7–19 |
| `KF_ZW_S_PF2` | 91 | +2 … +4 | +1.0 … +2.0° | 9–15 | 7–19 |

Delta distribution is only two values: **31 cells +2, 60 cells +4**. The tune is a
modest +1 to +2° advance, not a +38° one.

**E2 — the "+0.5° increments" check is vacuous and was presented as corroboration.**
Since `phys = int8(raw) × 0.5` and an int8 difference is always an integer, *every*
delta is automatically a multiple of 0.5°. The test can never fail and proves nothing.
The only non-vacuous related observation: **all 91 raw deltas are even** (91 even, 0 odd),
so no changed cell lands on a half-degree boundary — weak, and equally consistent with
an even-valued additive edit.

**E3 — "unsigned destroys the monotonicity" is false.** Measured over `KF_ZW_PF1`:

| Reading | Rises with Nkw | Falls with load |
|---|---|---|
| signed | 236 / 285 | 266 / 320 |
| unsigned | 228 / 285 | 259 / 320 |

The unsigned reading preserves monotonic *direction* almost as well. The real argument
for signedness is **magnitude** (§5), which is a plausibility argument, not proof.

---

## 1. Artifact identification

`out/R0C2J772B_ignition_timing.xdf` exists, parses as `XDFFORMAT` v1.80, and contains
exactly the 10 expected tables. Verified against a fresh XML parse, not against the
builder's constants and not against the previous audit.

---

## 2. Per-map validation against A2L and target BIN

The A2L was **re-parsed from scratch** (399 `CHARACTERISTIC`, 291 `AXIS_PTS`) and the
XDF checked field by field.

| Map | TGT addr | Dim | Geom XDF↔A2L | Map bytes ↔ REF | Axis bytes ↔ REF | In BIN | esz | signed | formula |
|---|---|---|---|---|---|---|---|---|---|
| `KF_ZW_PF1` | `0x703350` | 16×20 | OK | OK | OK | OK | 8 | `0x01` | `X*0.5` |
| `KF_ZW_PF2` | `0x703210` | 16×20 | OK | OK | OK | OK | 8 | `0x01` | `X*0.5` |
| `KF_ZW_S_PF1` | `0x7030D0` | 16×20 | OK | OK | OK | OK | 8 | `0x01` | `X*0.5` |
| `KF_ZW_S_PF2` | `0x702F90` | 16×20 | OK | OK | OK | OK | 8 | `0x01` | `X*0.5` |
| `KF_ZW_UESP_PF1` | `0x702F04` | 14×10 | OK | OK | OK | OK | 8 | `0x01` | `X*0.5` |
| `KF_ZW_UESP_PF2` | `0x702E78` | 14×10 | OK | OK | OK | OK | 8 | `0x01` | `X*0.5` |
| `KF_ZW_VP_PF1` | `0x7072A8` | 16×20 | OK | OK | OK | OK | 8 | `0x01` | `X*0.5` |
| `KF_ZW_VP_PF2` | `0x707168` | 16×20 | OK | OK | OK | OK | 8 | `0x01` | `X*0.5` |
| `KF_ZWMIN_WSOT` | `0x706DEC` | 8×8 | OK | OK | OK | OK | 8 | `0x01` | `X*0.5` |
| `KF_ZWMIN_KSOT` | `0x706E2C` | 8×8 | OK | OK | OK | OK | 8 | `0x01` | `X*0.5` |

**Structural problems: 0.** Geometry means X `indexcount` = 20/10/8 matching Z
`mmedcolcount`, and Y `indexcount` = 16/14/8 matching Z `mmedrowcount`, per A2L.

Axis deltas (A2L reference address → XDF target address) are uniform *within* each block,
which independently confirms block alignment:

```
main 6 maps + UESP axes : +260558 (0x3F9CE)   all 12 axes
KF_ZW_VP_* axes         : +260544 (0x3F9C0)
KF_ZWMIN_* axes         : +260556 (0x3F758)
```

---

## 3. Raw byte facts vs S15A-18-dependent interpretation

**Independent of the A2L — these are raw facts:**

- Each map's exact byte span is **unique** in the target: exactly one occurrence for all
  eight main/UESP/VP maps.
- `KF_ZWMIN_WSOT` and `KF_ZWMIN_KSOT` are **byte-identical to each other**, in the
  reference *and* in the target. Each occurs at both addresses.
- The six maps `0x702E78–0x703490` form one **contiguous 1,560-byte block** with no gaps,
  byte-identical to reference `0x6C36A8–0x6C3CC0`. The 64 bytes before and after are
  identical to the reference too, so the block boundaries are clean — the maps occupy a
  self-consistent region, not an arbitrary slice.
- The four main maps are a contiguous 1,280-byte sub-block, byte-identical to reference.
- **The tuner changed the identical 91 cell positions in all four main maps.**
- Stock → tuned: 91 changed cells in each of the four main maps; 0 in the other six.
- Raw deltas: **+2 or +4 only**, in all four.
- No changed cell crosses the 127/128 sign boundary.

**Dependent on the S15A-18 A2L — these are interpretations:**

- That the element is **signed int8**.
- That `phys = X × 0.5` and the unit is **degrees**.
- That X is **Nkw (rpm)** and Y is **load (%)**.
- That the symbols are named `KF_ZW_*` and mean what the names say.

None of these can be established for S15A-17 from local evidence (§6).

---

## 4. Spans, overlaps, boundaries

- All ten map spans and all axis spans lie inside the 8,126,464-byte target.
- **No overlap between the ten maps.** The six-map block is exactly packed:
  `UESP_PF2 (140) | UESP_PF1 (140) | S_PF2 (320) | S_PF1 (320) | PF2 (320) | PF1 (320)`
  with zero gaps, matching the reference arrangement exactly.
- No map overlaps an unrelated region. The strongest available check is that the block is
  packed and reference-identical with matching clean boundaries.
- **The old broken file did overlap.** Its `702F18` table (140 B at `0x702F18–0x702FA4`)
  straddles `KF_ZW_UESP_PF1` and `KF_ZW_S_PF2`; its `702F04` table is misaligned by 0x14
  from the true `KF_ZW_UESP_PF1`. Independent confirmation that the old file must not be
  used.

---

## 5. Signedness — evidence, honestly weighed

| Evidence | Weight |
|---|---|
| A2L declares limits `-64 63.5`; `int8(-128..127)×0.5` reproduces exactly; unsigned gives `0..127.5` and contradicts | **Strong, but S15A-18 only** |
| Magnitude: unsigned would imply up to **127.5° advance** in `KF_ZW_PF1`; B58 max ≈ 65–70°. Signed gives max 62.5° | **Plausibility only**, but independent of the A2L |
| Monotonicity | **Does not discriminate** (E3) |

27–28 cells per main map hold values > 127, so this is not a corner case — under an
unsigned reading roughly 9% of each map would display as > 63.5°, exceeding the A2L's own
declared ceiling. Signedness is **well supported but not proven** for the target.

---

## 6. What cannot be established for S15A-17

No S15A-17 A2L or XDF exists locally. Verified: no `*_016_*` A2L anywhere; every B48/B58
A2L carries `VERSION "R0C2J8B2B"` or an `R1`/`R0C9` family equivalent; the `_017_` in
filenames is a **pack revision, not S15A-17**. The only available declaration is S15A-18.

Consequently, **for the target none of the following is established**, only inherited:

1. Symbol identity — that `0x703350` is "base ignition angle path 1".
2. Signedness of the element.
3. The ×0.5 scaling and the degree unit.
4. Axis semantics — that X is engine speed and Y is load.
5. Dimensions — that the map is 16×20 and not, say, 16×20 of something else.

What *is* target-established, independent of the A2L: the addresses, byte extents,
element width, axis array contents and locations, block packing, and the tuned deltas.
Those were each verified by content comparison against the target itself.

---

## 7. Are the +1…+2° changes confirmed physical timing changes?

**No — they are the result of applying the reference conversion formula to the target
bytes.** Being precise about the distinction:

- **Confirmed (A2L-independent):** 91 cells changed in each of the four main maps, at
  identical positions, in a contiguous rectangle (load 9000–18000, 2250–6950 rpm), by a
  uniform raw `+2` or `+4`, with nothing else touched, and with no sign-boundary crossing.
- **Not confirmed:** that this means "1 to 2 degrees of ignition advance". That requires
  `×0.5`, which comes only from the S15A-18 A2L.
- **Corroborating but circumstantial:** the rectangle is exactly what a timing tune would
  target — high load, mid-to-high rpm, leaving light-load and low-rpm cells untouched.
  And the magnitude is plausible for a conservative tune.

Had the true scaling been ×1.0 the change would be +2…+4°; at ×0.25 it would be
+0.5…+1.0°. The **shape** of the edit is confirmed; the **number of degrees** is inherited.

Note also that the sign of the change depends on signedness: since no cell crosses the
127/128 boundary, both readings agree the bytes increased, and the physical direction
(increasing the stored advance magnitude) is the same either way.

---

## 8. Confidence, validated separately

### HIGH — 6 maps (`KF_ZW_PF1`, `KF_ZW_PF2`, `KF_ZW_S_PF1`, `KF_ZW_S_PF2`, `KF_ZW_UESP_PF1`, `KF_ZW_UESP_PF2`)

Retained, with the *reasoning* corrected per E1–E3. Established without relying on
plausibility: unique address in target, byte-exact match to reference, byte-exact axis
arrays, zero-gap packing in a reference-identical block with clean boundaries, uniform
within-block axis delta, and — for the four main maps — an identical 91-cell edit
signature. The claim these are *ignition timing* still rests on the S15A-18 A2L plus a
magnitude-plausibility argument, not on target-local proof.

### MEDIUM — 4 maps (`KF_ZW_VP_PF1`, `KF_ZW_VP_PF2`, `KF_ZWMIN_WSOT`, `KF_ZWMIN_KSOT`)

Not upgraded. Reasons, now precisely stated:

- `KF_ZW_VP_*` and `KF_ZWMIN_*` sit in blocks whose translation delta (+260544,
  +260556) differs from the main block (+260558). Uniform within each block, so alignment
  is internally sound — but there is no cross-block landmark tying them to the same
  software feature.
- Neither group was modified by the tuner, so **no edit-pattern corroboration exists**.
- `KF_ZWMIN_WSOT` and `KF_ZWMIN_KSOT` are byte-identical to each other in both images.
  The two addresses are certainly correct as an adjacent pair, but **which is WSOT and
  which is KSOT cannot be determined from content** — only from reference ordering.
  Functionally interchangeable, so the risk is cosmetic labelling only.
- Their axis arrays are themselves identical within each pair, so the pairing carries no
  additional risk.

---

## 9. Verdict

### **PARTIALLY VALIDATED**

Sufficient for **exploratory display**: the file is well-formed, all ten tables have real
axes and correct geometry, every address and byte span is verified unique and in-bounds
against the target, and the maps occupy a clean, packed, reference-identical region.

**Not** sufficient to assert identity, units or calibration validity:

- Identity, signedness, scaling, axis semantics and dimensions are **inherited from an
  S15A-18 A2L** and cannot be established for the S15A-17 target.
- The "+1…+2 degrees" figure is a **derived interpretation**, not a target-local fact; the
  shape of the edit is confirmed, the degrees are borrowed.
- Three quantitative claims in my previous report were wrong and are corrected in §0.

Explicitly **not** established and not to be relied on: that these maps are the final
commanded ignition timing (they are base maps; torque limits, knock control, per-cylinder
corrections and air-mass path selection are not described), or that the Stage 2
calibration is safe or correct.

### Recommendations

1. Use `R0C2J772B_ignition_timing.xdf`; **do not use** `R0C2J772B_timing_candidates.xdf`
   (single-cell rendering, wrong element type, misaligned addresses).
2. Do not flash or tune from this file. Display only.
3. Treat the four `KF_ZW_VP_*` / `KF_ZWMIN_*` tables as provisional.
4. To close the gap: a stock read reporting `R0C2J772B`/S15A-17, or an A2L/XDF for EPST
   `R0C9J772B`, would allow direct verification of every inherited property.
