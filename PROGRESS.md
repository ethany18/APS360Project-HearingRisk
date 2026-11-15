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

### 2026-11-15 — Task 2: company name → ticker map (branch `task-2-ticker-map`)
- **Done:** `src/data/build_sp500_ref.py` builds `src/data/reference/sp500_2017.csv` (674 name/ticker rows,
  592 tickers) from three pinned snapshots of the public-domain `datasets/s-and-p-500-companies` list
  (2017-03-08, 2018-04-02, 2020-05-10), with a 2017-membership flag from `fja05680/sp500` (MIT).
  `src/data/ticker_map.py` fuzzy-matches the 280 MDRM company names (rapidfuzz WRatio on normalised
  names), applies hand-set overrides (`reference/ticker_overrides.csv`) and maps each 2017 ticker to what
  yfinance should be asked for today (`reference/ticker_history.csv`: renamed / delisted / check).
  Run here on the real `results/inventory.csv` (only names are needed, no audio).
- **Result (`results/ticker_map_summary.json`):** 572/572 calls have a ticker, 0 dropped. 279/280 names
  score ≥ 0.9 (median 1.0); 1 below 0.9 (XL Group, overridden to XL). 3 overrides total (XL Group → XL,
  Booking Holdings → PCLN, Tapestry → COH; the latter two are the 2017 tickers before renaming).
  Ticker status by company: 221 same, 19 renamed, 32 delisted, 8 check; by call: 460 / 33 / 63 / 16.
- **Output files:** `results/ticker_map.csv`, `results/ticker_map_review.csv`, `results/ticker_map_summary.json`.
- **Problems:** delisted firms (63 calls = 11.0%) are likely not served by yfinance, plus 16 calls whose
  status is unsure ("check": recent acquisitions, Mylan→Viatris, CBS→Paramount history). If yfinance
  cannot serve them, Task 3 would drop more than 10% of calls, which needs the user's decision
  (options: accept the drop, or use another price source for delisted firms, e.g. CRSP through WRDS via
  the U of T library). The ticker_history statuses come from general knowledge, not a live check; the
  `--check-yf` run in Colab confirms them. Smoke test of `--check-yf` used a fake yfinance module only.
- **User runs next:** (1) verify by hand the 3 rows in `results/ticker_map_review.csv` (set `verified`
  to `yes` in `results/ticker_map.csv`, or report a wrong ticker). (2) In Colab (CPU, `COPY_MDRM_RAW=False`):
  `!python -m src.data.ticker_map --check-yf --keep-verified results/ticker_map.csv` and upload the three
  `results/ticker_map*` files. (3) Decide what to do about calls without yfinance prices before Task 3.
