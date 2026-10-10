# Investigation report #2 — targeted analysis of unresolved regions

Target: `10SW002828_iRom_ori` / `10SW002828_iRom_stage2` (8,126,464 B, md5 `40c3a00…` / `251f649…`, both unchanged)
Neither BIN modified. `out/R0C2J772B_verified.xdf` unchanged (still 87 tables).
New candidate definitions are in **`out/R0C2J772B_CANDIDATE.xdf`** (9 tables, separate file).

---

## 0. The finding that changes the headline

I audited the 87 tables against the reference stock dump byte-for-byte at the
corresponding XDF addresses. This was possible because the reference dump and the
user's stock BIN should be identical wherever the placement is correct.

| Class | Count | Meaning |
|---|---|---|
| **VERIFIED** | **43** | 100 % byte-identical to the reference stock dump |
| PARTIAL | 6 | 50–90 % match — same map, different content/version |
| **REJECT** | **38** | < 50 % match — placement is wrong |

**Every one of the 27 eight-bit maps failed.** All 43 survivors are 16-bit.

Two root causes, both now confirmed:

1. **The declared-range check I used was vacuous.** All 87 tables declare
   `min=0.000000 max=255.000000`, so *any* byte passes. That test filtered nothing.
   The real filter was content-anchoring of the breakpoint axes, which is sound — but
   for 8-bit maps in this software the axes are shared/reused and do not uniquely
   determine the data address.
2. **The reference pack is SP11, the ECU is SP15.** Base pack `00003076501103` has
   EPST `R1C9J8B3B`, SP**11**; the ECU is `R0C9J772B`, SP**15**. The 16-bit
   fuel/boost/lambda area happens to be byte-identical across those versions; the
   timing area is not.

**Corrected coverage** (each changed byte counted once):

```
87 tables as previously reported      1,771 / 3,821 = 46.3 %   (was inflated)
43 byte-verified only                 1,392 / 3,821 = 36.4 %
+ 6 partial                           1,430 / 3,821 = 37.4 %
+ new candidates below                1,622 / 3,821 = 42.4 %
```

The earlier 46.3 % was wrong and is retracted. 42.4 % is the honest figure for
everything defensible. 15 of the 43 verified tables were edited by the tuner.

---

## P1 — The three "ignition" candidates at 0x70318B / 0x7032CB / 0x70340B

### First: a correction to report #1
I previously described these as showing "duplicated rows". That was an artefact of my
printing loop. There is **no exact byte period** in the block. The real structure is
different, and it is not a plain 16×20 table.

### What is now established
Content-searching the SP15 pack (`00003081501102.xdf`, EPST R0C9J8B2B, SP15) found the
ignition axes **physically present in your BIN**:

| Axis | Values (20 pts) | Found in user BIN at |
|---|---|---|
| x (RPM) | 500, 750, 1000, 1250, 1500, 1750, 2000, 2250, 2500, 2750, 3000, 3250, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 6950 | 0x6EC5DE, 0x6EC606, 0x6EC62E, 0x6EC656 |
| y, PF1/S_PF1 | 1200, 1500, 2000, 3000 … 18000 (16 pts) | 0x6EC556, 0x6EC596 |
| y, PF2/S_PF2 | 1300, 1700, 2000, 2500 … 18000 (16 pts) | 0x6EC536, 0x6EC576 |

**All eight arrays give one delta, +0x3F9CE**, across four maps and two axis types.
This is far outside the +0x40AC2–0x413FE band used for the 16-bit block — which is
precisely why content-anchoring failed on these tables before.

Applying it:

| Map (SP15 pack) | Predicted | Changed | Verdict |
|---|---|---|---|
| `KF_ZW_S_PF2` (cold, path 2) | 0x70318E | 91/320 | real data |
| `KF_ZW_S_PF1` (cold, path 1) | 0x7032CE | 91/320 | real data |
| `KF_ZW_PF2` (main, path 2) | 0x70340E | 88/320 | real data |
| `KF_ZW_PF1` (main, path 1) | 0x70354E | 0/320 | **zeros/garbage — invalid** |

So three of four land on live data with change counts matching the diff regions
(91, 91, 88 ≈ the 91/91/91 observed).

### What is NOT resolved
The 320-byte block does **not** decode as a 16×20 8-bit map in any interpretation.
Values 0xF6–0xFD appear at structurally regular positions:

```
+0    31  34  34  37  37  39  40  39  40  46 247 248   2  11  16  20  23  25  27  28
+16   28  30  31  33  35  37  38  39  39  45 247 248   0   8  11  16  19  21  23  25
+32   25  26  27  28  30  31  33  34  36  39 246 248 252   1   6  10  15  17  19  21
```

Layout tests performed and rejected: 16×20 row-major (19 descending steps),
20×16 column-major (18), even/odd byte de-interleave (13 and 12). **None removes the
markers.** Either several smaller structures are packed here, or the encoding is not a
plain array.

**Verdict: address PROBABLE, layout UNRESOLVED, identity NOT ESTABLISHED.**
I am therefore **not** calling these ignition maps and **not** emitting them in the
candidate XDF. The +2…+4 changes are suggestive of added advance, but the axes are
shared by four maps so they prove a *timing-family* block, not which map is which.

---

## P2 — Boost candidates 0x6F8CA0 / 0x6F8CE8 / 0x6F8D00

### Address: VERIFIED by two independent packs

| Map | Data | Axis (RPM) | 3076-050 delta | mgflasher delta |
|---|---|---|---|---|
| `KL_MD_K_MAX_VL` | 0x6F8CA0 | 0x6F8D98 | +0x410FA | — |
| `KL_MD_K_MAX_BST_HS` | 0x6F8CE8 | 0x6F8DE0 | +0x410FA | — |
| `KL_MD_K_MAX_BST` | 0x6F8D00 | 0x6F8DF8 | +0x410FA | **+0x41710** |

Two independently authored packs land on the same address; both deltas lie inside the
independently-derived anchor range. Distinct valid RPM axes sit exactly where predicted.

### Semantics: DOWNGRADED — this is probably not a boost target

Scaling is **identity**, 16-bit (raw = displayed); the packs' declared min/max
(0–255 / −32768–32767) are both wrong for these values and carry no information.
The mgflasher entry labels the unit `lb·ft`.

| Map | ori | mod |
|---|---|---|
| `KL_MD_K_MAX_BST` | 300 300 300 310 320 310 300 295 280 270 230 150 | all 650 |
| `KL_MD_K_MAX_VL` | 500 ×12 | all 650 |

**The problem:** a speed-dependent boost curve must *rise* with RPM. This one falls
monotonically from 300 to 150 across 1000→7000 rpm, and the other is flat. Neither is
the shape of a boost target. `KL_MD_K_MAX_*` can legitimately denote a **maximum
torque / full-load limit curve** (`K_MAX` = maximum charge, not necessarily boost
pressure), which would explain a declining or flat shape.

So: **address VERIFIED, identity PROBABLE (name matches), semantic meaning UNRESOLVED.**
Flat 650 could be a low-boost/bypass setpoint, or a saturated value written by the tune
tool. **Do not treat these as boost targets without confirming the unit.**

---

## P3 — Injection timing 0x6CFFD4 / 0x6D0144 — still OPEN

| Candidate | Address | Anchor distance | Status |
|---|---|---|---|
| `KF_PHA_H_B1_W` (injection start angle, warm) | 0x6CFFD4 | 4,718 B | **EXTRAPOLATED** |
| `KF_PHA_H_B1_SK_PRE` (start angle, preventive) | 0x6D0144 | 5,086 B | **EXTRAPOLATED** |

Both sit far outside the span covered by any proven anchor, so the delta used is an
extrapolation across an unverified gap — not interpolation between evidence. Given what
P0 showed about unverified placements, these should be treated as **unconfirmed**.

I did not find an independent structural match for them in either pack, and as
instructed I have **not** promoted them on the strength of `Pha` in the name.
**Not emitted** in the candidate XDF. Open question: are their axes physically present
in the user BIN? That single test would settle it.

---

## P4 — 0x6F7F2E–0x6F7FBD revisited

### Structure: PROVEN
- 144 bytes = exactly **6 curves × 12 values × uint16**.
- **Six identical 12-point RPM axes** at `0x6F8022`, `0x6F803A`, `0x6F8052`, `0x6F806A`,
  `0x6F8082`, `0x6F809A` (24 B apart, 12 pts × 2 B) — one per curve.
  Values: `[1000, 1250, 1550, 2300, 3800, 4600, 5400, 5500, 5800, 6000, 6500, 7000]`.

### Change: real, not a sentinel
Stock is **30000** uniformly; tuned is **32767** uniformly, all 144 bytes.
`32767 = 2¹⁵−1` is the maximum of a 15-bit field. Two readings remain open:
- **Limit disabled** — the field is saturated to "no limit", the standard signature of
  a limiter being defeated by a tune tool.
- **Genuine large-value limit** — the maps hold a large physical quantity (e.g. Nm)
  and the tuner raised them.

The uniformity across all six curves and all 72 cells favours the sentinel reading, but
that is inference from pattern, not proof.

### Identity: UNRESOLVED
Nearest pack candidates land at `0x6F7F18` (22 B away) — the `KL_MD_K_MAX_BST_STRG_*` /
`KL_MD_K_MAX_RNSTART_STRG_*` / `KL_MD_K_MAX_VL_ECO_STRG_*` family, all 1×12. The size
and axis structure match perfectly; the 22-byte discrepancy is unexplained.
Emitted in the candidate XDF **as `UNRESOLVED_1x12_x6`**, explicitly not named.

---

## P5 — Reconciliation of the remaining bytes

After the byte-verified set + new candidates: **2,199 changed bytes in 80 regions**
unexplained. Ranked by structural evidence:

| # | Region | Span | Changed | Structural signature | Assessment |
|---|---|---|---|---|---|
| 1 | 0x70318B-0x70320F | 133 | 91 | 20-pt RPM axis + 16-pt axis present at 0x6EC5DE/0x6EC536, one delta | **Strongest** — timing family, layout unresolved (P1) |
| 2 | 0x7032CB-0x70334F | 133 | 91 | same, +320 B | same |
| 3 | 0x70340B-0x70348F | 133 | 91 | same, +640 B | same |
| 4 | 0x70304B-0x7030CF | 133 | 91 | same block, marker bytes | same family, one map earlier |
| 5 | 0x6F7F2E-0x6F7FBD | 144 | 144 | 6 × 1×12 + 6 matching RPM axes | **Structure proven** (P4), identity open |
| 6 | 0x6F8CA0-0x6F8D2F | 144 | 96 | 2 distinct 12-pt RPM axes at predicted addrs | **Address proven** (P2), semantics open |
| 7 | 0x7311B4-0x731365 | 434 | 288 | repeating 6-value groups, step-514 axis family; no matching axis found | Largest unexplained block; no anchor |
| 8 | 0x730A8C-0x730B1D | 146 | 128 | repeating 4-value groups ×5 | no anchor |
| 9 | 0x6C9CAE-0x6C9D5B | 174 | 52 | repeating 8-value groups incl. 0xF800/0xFC08 | no anchor |
| 10 | 0x6FB116-0x6FB181 | 108 | 72 | constant-ish `{51, 204, 255}` | likely encoded/flag data, not a map |

Items 1–6 together account for ~615 changed bytes and are where the remaining effort
belongs. Items 7–10 (≈ 900 bytes) have **no** supporting axis in the packs and I have
deliberately made no claim about them.

---

## Confidence table

| Candidate | Address conf. | Semantic conf. | Evidence | Unresolved |
|---|---|---|---|---|
| `KL_MD_K_MAX_BST` 0x6F8D00 1×12 | **VERIFIED** | UNRESOLVED | 12-pt RPM axis at predicted addr; two packs agree (+0x410FA, +0x41710); 12/12 changed | curve declines with RPM — contradicts "boost target"; unit `lb·ft` unverified |
| `KL_MD_K_MAX_BST_HS` 0x6F8CE8 1×12 | **VERIFIED** | UNRESOLVED | same delta, valid axis; unedited | as above |
| `KL_MD_K_MAX_VL` 0x6F8CA0 1×12 | **VERIFIED** | UNRESOLVED | distinct valid axis; 12/12 changed | flat 500→650 unexplained |
| 6× curves 0x6F7F2E 1×12 | **STRUCTURAL** | UNRESOLVED | 144 B = 6×12 u16; 6 matching RPM axes | identity unknown; 22 B offset from pack candidates; 30000→32767 = disable or genuine limit? |
| 0x70318E/2CE/40E 320 B blocks | PROBABLE | **NOT ESTABLISHED** | 8 axes, one delta +0x3F9CE | interior layout undecodable; 4th map invalid; which map is which unknown |
| `KF_PHA_H_B1_W` 0x6CFFD4 | WEAK | UNRESOLVED | extrapolated 4,718 B past anchors | no structural match; no axis located |
| `KF_PHA_H_B1_SK_PRE` 0x6D0144 | WEAK | UNRESOLVED | extrapolated 5,086 B | as above |
| 38 rejected tables (all 8-bit + 11 16-bit) | — | — | < 50 % byte match vs reference | removed from consideration |

## Rejected candidates and reasons

| Set | Count | Exact reason for rejection |
|---|---|---|
| 27 eight-bit maps in the verified XDF (`KF_ZW_*`, `KF_DZW*`, `KF_ZWMIN_*`, `KF_DZWT_*`) | 27 | 0.0–0.9 % byte match vs reference stock dump. SP11 reference addresses do not apply to SP15. |
| 11 sixteen-bit maps (`GKF_ESPR/ASPR_NORM_*` Vanos, `KF_FMS_HFMPL_MN`, `BMWchas_lam_InjMplThr_M`, …) | 11 | 19–49 % byte match — right family, wrong address or wrong version. |
| 156 band-search candidates (`out/candidates_disambiguated.json`) | 156 | Multiple deltas survived the axis test → ambiguous. Refused rather than guessed. |
| `KF_ZW_PF1` @ 0x70354E | 1 | All zeros / non-map content at the predicted address. |
| Ignition blocks as *editable maps* | 3 | Layout undecodable; would emit wrong row/column geometry. |
| `KF_PHA_H_B1_W`, `KF_PHA_H_B1_SK_PRE` | 2 | Extrapolated beyond the anchored span; no independent structural match. |

## Best next steps (no new files needed)
1. **Test the 0x6EC5DE / 0x6EC536 axes against the remaining 320-byte blocks** — the
   4th ignition map's address is the open question and the axes are already located.
2. **Locate the axes for `KF_PHA_H_B1_W`** in the user BIN by content search against
   the SP15 packs; a hit converts a WEAK candidate to VERIFIED.
3. **Resolve the 22-byte offset** between 0x6F7F2E and the `KL_MD_K_MAX_*_STRG` family
   by reading those curves' axes in the user BIN.
4. Treat the SP15 pack (`00003081501102`) as the new primary reference — its byte-match
   profile is the only one that agrees with this ECU.

## Artefacts
```
out/R0C2J772B_verified.xdf      UNCHANGED, 87 tables (43 verified / 6 partial / 38 reject)
out/R0C2J772B_CANDIDATE.xdf     NEW, 9 tables, not flash-safe
out/reclassified.json           per-table byte-match classification
out/audit_match.json            raw match percentages
out/INVESTIGATION_REPORT.md     report #1 (superseded coverage figure)
out/coverage.json               explained / unexplained byte lists
```