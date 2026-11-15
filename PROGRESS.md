# Hearing Risk — progress log

Session log, newest entry last. Each entry: date, task, what was done, output files, problems,
what the user must run next.

## Log

### 2026-11-15 — Setup + Task 1 (branch `setup-and-task-1`)
- **Done:** created `CLAUDE.md` (verbatim from plan section 0.3), this log, folder layout from plan section 3,
  `.gitignore` additions (data/, checkpoints, *.wav, *.mp3, *.npy, *.npz), `requirements.txt`,
  `notebooks/colab_run.ipynb`, and Task 1 code: `src/data/unpack_mdrm.py`, `src/data/inventory.py`.
- **Smoke test (synthetic, not real data):** 4 fake calls (wav + mp3) packed as an 8-part split zip.
  Merge + unzip worked; re-run skipped correctly; inventory found 4 calls, flagged the planted
  3-lines-vs-4-clips mismatch and the planted corrupt clip. Drive-side source left untouched.
- **Output files (after Colab run):** `results/inventory.csv`, `results/inventory_mismatches.csv`,
  `results/inventory_summary.json`; `inventory.csv` also copied to Drive `HearingRisk/processed/`.
- **Problems / unknowns:** exact MDRM file layout inside the zip (text file name, audio format) not yet
  seen; the code finds `CompanyName_YYYYMMDD` folders at any depth, prefers `Text.txt`, and accepts
  wav/mp3/flac/m4a/ogg. mp3 header durations include encoder padding (a few hundredths of a second per clip).
- **User runs next:** merge the PR, then in Colab run `notebooks/colab_run.ipynb` top to bottom (CPU runtime,
  `BRANCH="main"`, `COPY_MDRM_RAW=True`); the task cell is pre-filled with the Task 1 command. Upload the
  three `results/inventory*` files to `main`. Check: about 572 calls, about 89k clips, mismatches listed.
