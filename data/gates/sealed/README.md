# Sealed coding data

These files are kept compressed so their contents are not shown in diffs. **Do not open them before the matching recode is finished.** They are opened only by the scoring script.

| File | What | Sealed | Open after |
|---|---|---|---|
| `g2_first_pass_codes.csv.gz` | G2 first-pass eligibility codes (200 records) | 2026-10-17; sha256 of the uncompressed CSV `8d3990013a913e799c4ba71e9d17c0cb886643fbac9f2ca909d3a0079f342e23` | G2 recode complete (opens 2026-10-31) |
| `f2_first_pass_codes.csv.gz` | G2 on F2 first-pass eligibility codes (100 records) | 2026-10-17; sha256 of the uncompressed CSV `e3325317c069b42e7be5851605c43ab011868b1395a7c7a39398449d00b48d2f` | F2 recode complete (opens 2026-10-31) |
| `g4_first_pass_codes.csv.gz` | G4 first-pass citation-context codes (100 pairs) | 2026-10-19; sha256 of the uncompressed CSV `e695971119482b2bf6cd3485973796870b018ea76b6a897080bc8ad30f054ec4` | G4 recode complete (opens 2026-11-02); the group key stays unopened until then too |

**Opened 2026-11-02:** `g2_first_pass_codes.csv.gz` and `f2_first_pass_codes.csv.gz`, after their recodes were completed and their hashes verified. The codes are now in `data/gates/g2_coding_sheet.csv` and `f2_coding_sheet.csv`.

**Opened 2026-11-02:** `g4_first_pass_codes.csv.gz`, after the G4 recode was completed and its hash verified. The codes are now in `data/gates/g4_context_sheet.csv`. The group key `g4_group_key.csv` was opened at the same time.
