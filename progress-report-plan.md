# Progress Report Plan — Hearing Risk (written Nov 15, 2026; last updated Nov 15, 2:35 PM)

**Due:** Fri Nov 20 (confirm the exact time on Quercus). Late within 24 h = -20%; after that = 0.
**Format:** LaTeX, course template, **max 3 pages of main text** (more than 3 = -20%, more than 4 = zero), unlimited references. The rubric wants figures and tables to carry the content, with minimal text.
**Worth:** 20 points = 5 (Brief Project Description) + 15 (Notable Contribution: Data Processing, Baseline Model, Primary Model).

This file is the hand-off document. A copy lives in the GitHub repo as `docs/plan.md`; Claude Code works from that copy. **If this file changes, re-upload it to the repo.**

---

## 0. Workflow: who does what

| Tool | Job |
|---|---|
| **Claude Code (cheaper model)**, in the GitHub repo | Writes all code and the report. Tests on a tiny synthetic sample. Pushes to a task branch and opens a pull request; never touches `main`. One task from section 4 per session. |
| **User** | Reviews every pull request (code and commit message) and merges it. Runs Colab. |
| **Google Colab**, run by the user | Everything that touches real data or needs a GPU. Runs scripts from the repo; no code is edited in the notebook. |
| **Claude chat (stronger model)**, in the APS360 project | Changes of plan, diagnosing a model that will not learn, final review of the PDF against the rubric. |

**The loop**
1. Claude Code writes code on a branch `task-N-short-name`, smoke-tests it on fake data, pushes the branch and opens a pull request (PR) into `main`. It ends the session with the PR link, a short summary of what changed, and a proposed one-line commit message.
2. **User reviews the PR on GitHub:** "Files changed" tab shows every added/removed line. If something is wrong or unclear, tell Claude Code in the same session; it updates the branch.
3. **User merges with "Squash and merge".** GitHub shows an editable box for the final commit title and message: this is the only commit that lands on `main`, and the user controls its wording. Delete any `Co-authored-by` lines GitHub pre-fills in that box. Then delete the branch (GitHub offers a button).
4. User opens `notebooks/colab_run.ipynb` in Colab: mount Drive → `git pull` (main) → copy data to local disk → run the script named for the task.
5. Scripts write metrics (`results/*.json`) and figures (`results/figures/*.pdf`). User uploads these to `main` (GitHub "Add file → Upload files", writing their own commit message). On a crash, paste the error into Claude Code; the fix arrives as a new PR.
6. Claude Code reads `results/` and `PROGRESS.md`, then does the next task.

One-time GitHub setting (user): repo Settings → General → Pull Requests → tick "Allow squash merging", untick the other two merge types, and tick "Automatically delete head branches".

**Where context lives**
| Place | Contents | Read by |
|---|---|---|
| GitHub repo | code; `CLAUDE.md` (standing rules); `docs/plan.md` (this file); `PROGRESS.md` (session log); `results/`; `report/` (`main.tex`, `aps360.sty`, `references.bib`, figures) | Claude Code, every session |
| Google Drive `HearingRisk/` | `raw/` audio, `processed/` spectrograms and CSVs, `checkpoints/` | Colab only |
| APS360 project (claude.ai) | rubrics, this plan, decisions | Claude chat |

The repo is the source of truth. Claude Code has no memory between sessions; `CLAUDE.md` + `PROGRESS.md` are what carry state. `CLAUDE.md`, `PROGRESS.md` and `docs/plan.md` are working files and are **removed before final submission (Task 10)**.

**GitHub access (checked Nov 15):** the user's current Claude account sees `ethany18/APS360Project-HearingRisk` with push access.

**Colab habits (COLAB REMINDER — Claude Code must repeat these to the user whenever a task says "COLAB REMINDER")**
1. **Copy data off Drive first.** Reading tens of thousands of small files directly from Drive is very slow. At the start of every Colab session, copy/unzip to `/content/data/` and read from there. Keep processed spectrograms on Drive as one file per call (or a few large archives), never one file per clip.
2. **Checkpoint to Drive every epoch**, and make every long script resumable (`--resume`). Free Colab disconnects when idle and caps session length.
3. **Turn the GPU on** (Runtime → Change runtime type → T4) before training, and off for CPU-only tasks to save quota.
4. **Write outputs to Drive or commit them before closing the tab.** Anything left on `/content/` is lost.
5. Keep the tab open and active during long runs.

**Drive storage is tight.** The user's Drive cannot hold the FinCall-Surprise audio (52 GB). Raw datasets are reached through **shortcuts** to the owners' shared folders (shortcuts use no storage; Colab reads through them). Only processed outputs are written to the user's Drive, so keep them small.

## 0.1 How to proceed (user steps, in order)

1. **Data access:** FinCall-Surprise shortcut is done (`HearingRisk/raw/FinCall-Surprise`). For MDRM, either copy the 5 zip parts into `HearingRisk/raw/mdrm/` if there is 5.7 GB free, or add a shortcut to the MDRM shared folder there (details in Task 0).
2. **Claude Code write access:** done. Apply the one-time GitHub merge setting from section 0.
3. **Put the context into the repo** (upload through GitHub's web page):
   - this file → `docs/plan.md`
   - proposal `main.tex`, `references.bib`, `figures/pipeline.*`, `aps360.sty` → `report/` (from `proposal_overleaf.zip`)
4. **Open Claude Code on the repo, pick the cheaper model, and paste the first-session prompt** from section 0.2. That session creates `CLAUDE.md`, `PROGRESS.md`, the folder layout and the Colab notebook, writes Task 1's code, and opens a PR.
5. **Review and squash-merge the PR** (loop steps 2–3), then run in Colab what the session told you to run.
6. **For every later session, paste:** `Read CLAUDE.md, docs/plan.md and PROGRESS.md. Do Task N. Stop when its outputs and checks are done.`
7. **Come back to Claude chat** at the two escalation points in Task 7 and for Task 9 (upload the compiled PDF and `results/*.json`).

## 0.2 First-session prompt for Claude Code

```
Set up this repo for the APS360 progress report. Read docs/plan.md fully first.
Work on a new branch named setup-and-task-1. Do not commit or push to main.
1. Create CLAUDE.md with exactly the content in section 0.3 of docs/plan.md. Do this before any commit,
   and follow its Git rules from the very first commit.
2. Create PROGRESS.md with a heading and an empty dated log.
3. Create the folder layout from section 3 and a .gitignore that excludes data/, checkpoints, *.wav, *.mp3, *.npy, *.npz.
4. Create requirements.txt and notebooks/colab_run.ipynb with cells: mount Drive; clone or pull the repo
   (branch set by a BRANCH variable, default main); pip install; copy data from Drive to /content/data;
   one clearly marked cell where the user pastes the command for the current task; a final cell that
   copies results/ back to Drive.
5. Write the Task 1 code and smoke-test it on a small synthetic folder you generate.
6. Push the branch and open a pull request into main. Then give me: the PR link, a summary of each file,
   a proposed one-line commit message for the squash merge, exactly what to run in Colab after I merge,
   and the COLAB REMINDER list.
Data locations on Drive: MDRM at HearingRisk/raw/mdrm (may be a shortcut); FinCall-Surprise is a shortcut at
HearingRisk/raw/FinCall-Surprise containing mp3_2019.zip, mp3_2020.zip, mp3_2021.zip.
```

## 0.3 Content of `CLAUDE.md`

```
# Hearing Risk — APS360 project
Predict post-earnings-call stock volatility from executive speech. Individual course project.

## Start of every session
1. Read docs/plan.md and PROGRESS.md.
2. Do only the task the user names (or the next unfinished one). One task per session.

## Git rules
- NEVER commit to, push to, or merge into main. The user reviews and merges everything.
- Work on a new branch named task-N-short-name, created from the latest main.
- When the task's code is ready, push the branch and open a pull request into main. Do not merge it.
- Do NOT add "Co-Authored-By", "Claude-Session", "Generated with Claude Code" or any other attribution
  or session lines to commit messages or pull request descriptions. Plain descriptive messages only.
- If the user asks for changes after reviewing, add commits to the same branch.

## Rules
- Never invent a number. Every number in report/ comes from a file in results/.
- You cannot run on real data or a GPU. Smoke-test on small synthetic data, then give the user the exact
  Colab command to run. The user runs it and brings back results/ or the error text.
- Whenever a task in docs/plan.md says COLAB REMINDER, repeat the Colab habits list from section 0 to the user.
- All long-running scripts: read data from /content/data, checkpoint to Drive each epoch, support --resume.
- Drive storage is tight: raw data is read through shortcuts and never copied to the user's Drive; keep
  processed outputs small and report their total size.
- Seed 0. Save the config next to every result.
- Hyperparameters are chosen on validation only. Test is run once per model.
- Split is chronological. Never shuffle calls across time.
- Stop and ask the user if: a download fails, more than 10% of calls would be dropped, or training loss
  does not decrease.
- A model that fails to beat the past-volatility baseline is an acceptable result; report it honestly.
- Keep label formula and mel settings identical to report/main.tex (proposal) unless recorded in PROGRESS.md.
- report/main.tex: main text must be at most 3 pages. Check the page count after every compile.

## End of every session
1. Append to PROGRESS.md (on the branch): date, task, what was done, output files, problems, what the user
   must run next.
2. Push the branch and open the pull request.
3. Tell the user: the PR link; what each changed file does, in plain language; a proposed one-line commit
   message for the squash merge; the exact Colab command to run after merging.
```

---

## 1. Scope decision for this report

**Train and evaluate everything on MDRM only (2017). FinCall-Surprise is located and counted, not processed.**

Reasons:
- MDRM audio is already cut into one clip per transcript sentence, so no forced alignment is needed. WhisperX alignment of 2,688 full calls does not fit in five days.
- The rubric asks for "all or most of the data" obtained, a baseline, and one quantitative plus one qualitative result per model. MDRM alone delivers all of these.

Consequences the executor must respect:
- MDRM is one year, so the year-based split from the proposal cannot be used yet. **Split for this report: sort calls by date; first 70% train, next 15% validation, last 15% test.** Never shuffle across time.
- MDRM contains only the sentences of the most-spoken executive (usually the CEO). There are no analyst questions or speaker-role labels. Do not claim Q&A tagging on MDRM.
- MDRM folders are named `CompanyName_YYYYMMDD` (e.g. `3M Company_20170425`), not by ticker. A name-to-ticker map has to be built (Task 2).

**Plan for never-before-seen test data (rubric requires this to be stated):**
1. FinCall-Surprise 2021 calls: a different dataset, different years, different firms in part; untouched until the final report.
2. A small self-collected set (about 20 calls from 2025–2026 investor-relations webcasts, processed with the same pipeline). The rubric says self-collected new data is preferred, so include this in the plan.

**FinCall-Surprise facts (verified Nov 15):**
- Audio on the authors' Google Drive: `mp3_2019.zip` 18.14 GB, `mp3_2020.zip` 14.21 GB, `mp3_2021.zip` 19.83 GB (52.2 GB total). Slide zips (`ppt_*`) are not used.
- Transcripts are in the GitHub repo: `transcripts_2019.json`, `transcripts_2020.json`, `transcripts_2021.json`, keyed by call ID with fields `input` (transcript), `mp3_id`, `ppt_id`, `label` (0/1 earnings surprise).
- Repo license: Apache-2.0.
- **Open item for after Nov 20:** the README does not mention ticker or call date fields. Volatility labels need both; check the JSON keys/IDs and transcript headers.

## 2. Rubric → what must appear in the report

| Rubric item | Pts | Evidence that earns it | Produced by |
|---|---|---|---|
| Brief description: goal, motivation, why deep learning, **input and output shown** | 5 | 1 short paragraph + Fig. 1 (pipeline with input "sentence audio clips + past volatility" and output "log volatility at 3/7/15/30 days") | Task 8 |
| Data: sources, cleaning steps reproducible by a classmate | part of 15 | Numbered cleaning steps with every parameter | Tasks 1–4 |
| Data: statistics | | Table 1: calls, firms, sentences, hours, per split; label mean/std per horizon | Task 4 |
| Data: one cleaned training sample | | Fig. 2: one log-mel spectrogram + its transcript sentence + the call's label | Task 4 |
| Data: plan for never-seen test data | | The two-part plan in section 1 | Task 8 |
| Data: challenges | | 2–3 real ones (see Task 4) | Task 8 |
| Baseline: reasonable, simple, not random | | Past-volatility regression; eGeMAPS + ridge | Tasks 5–6 |
| Baseline: quantitative result | | Table 2: test MSE per horizon | Tasks 5–6 |
| Baseline: qualitative result | | Fig. 3: predicted vs. actual scatter; a sentence on which firms it misses | Task 5 |
| Baseline: challenges | | e.g. delisted tickers, feature extraction time | Task 8 |
| Primary: architecture more detailed than proposal | | Table 3 or diagram: layer-by-layer shapes, **parameter count**, optimizer, LR, batch, epochs, seed | Task 7 |
| Primary: quantitative result | | Fig. 4: train/val loss curves; row in Table 2 | Task 7 |
| Primary: qualitative result | | Top-3 attended sentences for one test call, or analysis of the worst-predicted calls | Task 7 |
| Primary: challenges | | Overfitting on 400 training calls, memory, etc. | Task 8 |
| Feasibility argument (handout intro) | | Small schedule table to Dec 8 with what is done / left | Task 8 |
| "Visual elements professional" (appears in every item) | | Vector PDF figures, readable font at print size, booktabs tables | Task 8 |

## 3. Rules and repo layout

The standing rules are in `CLAUDE.md` (section 0.3). Repo layout:
```
CLAUDE.md  PROGRESS.md  requirements.txt  .gitignore      (first two removed in Task 10)
docs/plan.md                                               (removed in Task 10)
data/            (gitignored; real data lives on Google Drive)
src/data/        inventory.py, ticker_map.py, labels.py, build_manifest.py, melspec.py
src/models/      baseline_pastvol.py, baseline_egemaps.py, cnn_attn.py, train.py
notebooks/       colab_run.ipynb
results/         *.json, figures/*.pdf
report/          main.tex, aps360.sty, references.bib, figures/
```
Drive layout: `HearingRisk/raw/mdrm/` (copy or shortcut), `HearingRisk/raw/FinCall-Surprise` (shortcut), `HearingRisk/processed/`, `HearingRisk/checkpoints/`, `HearingRisk/results/`.

## 4. Tasks

"Where" says who runs it. Claude Code always writes the code first, on a branch, as a PR the user merges.

### Task 0 — User only (today)
- MDRM: the Drive link is in the README at https://github.com/GeminiLn/EarningsCall_Dataset (5 zip parts, about 5.7 GB). Copy into `HearingRisk/raw/mdrm/` if space allows; otherwise add a shortcut to the shared folder there. No license is stated; the README asks for citation of Qin & Yang (2019).
- FinCall-Surprise: **done** — shortcut at `HearingRisk/raw/FinCall-Surprise`.
- Steps 2–4 of section 0.1.
- Re-read the course AI-tool policy. The rubric says the project description must be "in your own words".

### Task 1 — Unpack and inventory MDRM — Colab CPU — **COLAB REMINDER (first Colab use)**
- Merge and unzip onto `/content/data/mdrm/`: `zip -s0 ACL19_Release.zip --out ACL19_Release_All.zip` then `unzip -q`.
- Write `inventory.csv` (to Drive `processed/` and repo `results/`): one row per call with folder name, company name, date, number of text lines, number of audio files, total audio seconds.
- **Check:** about 572 calls, about 89k clips; text-line count equals audio-file count per call. List mismatches.

### Task 2 — Company name → ticker map — Claude Code + user
- Fuzzy-match folder company names (from `inventory.csv`) against a 2017 S&P 500 constituent list; write `ticker_map.csv` (folder, company, ticker, match_score, verified).
- Print all matches with score below 0.9 for the **user to verify by hand**. Handle renamed/acquired firms (ticker as of 2017 vs. what yfinance serves today).
- **Check:** every call has a ticker or an explicit `dropped_reason`.

### Task 3 — Labels and past volatility — Colab CPU (or user's laptop)
- For each call, pull daily adjusted close from yfinance (2016-10 to 2018-03). Cache to parquet.
- For τ in {3, 7, 15, 30}: target = log realized volatility over the τ trading days after the call, using the exact formula and timing convention in the proposal; past volatility = the same quantity over the τ trading days before the call.
- Write `labels.csv`. Drop calls with missing prices; log how many and why.
- **Check:** no NaN/inf; label histogram per horizon saved to `results/figures/label_hist.pdf`; unit test on one hand-computed call.

### Task 4 — Manifest, split, spectrograms, data figures — Colab CPU, long — **COLAB REMINDER (habits 1, 2, 4)**
- Apply the filter from the proposal (drop calls with fewer than 20 usable sentences; drop clips shorter than 0.5 s or unreadable).
- Chronological 70/15/15 split → `manifest.csv` (call_id, ticker, date, split, clip path, sentence text).
- Compute log-mel for every clip (16 kHz, 64 mel bands, 25 ms window, 10 ms hop, 8 s crop), **one file per call**, variable length, written to Drive `processed/mel/`. Script must skip calls already done (resumable).
- **Storage:** before the full run, process 20 calls and extrapolate the total size. Ask the user how much Drive space is free. Use float16 if it fits; otherwise uint8-quantized (and record it); if still too large, cap at the first 64 sentences per call (and record it).
- Standardize with train-set mean/std only.
- Outputs: `results/data_stats.json` (calls, firms, sentences, hours, per split; label mean/std), **Table 1** as LaTeX, **Fig. 2** (one spectrogram + sentence + label).
- Challenges to record as they actually occur: ticker mapping, delisted tickers, corrupt clips, storage size.
- FinCall-Surprise count (no audio download): load the three `transcripts_YYYY.json` files from the GitHub repo, count calls per year, add to `data_stats.json` with the audio zip sizes from section 1 (supports "all or most of the data obtained").

### Task 5 — Baseline 1: past volatility — Colab CPU or laptop, minutes
- Per horizon, OLS: target ~ past volatility, fit on train. Also the naive "predict past volatility unchanged" and "predict train mean" for reference.
- Outputs: `results/baseline_pastvol.json` (train/val/test MSE and R² per horizon), **Fig. 3** predicted-vs-actual scatter on test (30-day horizon), list of 5 worst-predicted test calls.

### Task 6 — Baseline 2: eGeMAPS + ridge — Colab CPU, 1–3 h — **COLAB REMINDER (habits 1, 2, 4)**
- `opensmile` Python package, eGeMAPSv02 functionals (88 features) per clip → mean and std over the call → standardize → ridge, alpha chosen on validation from {0.1, 1, 10, 100, 1000}. Include past volatility as a feature.
- Extraction must be resumable and save per-call features to Drive.
- Output: `results/baseline_egemaps.json`. If extraction cannot finish in time, run on a fixed 30-clip sample per call and say so.

### Task 7 — Primary model: spectrogram CNN + attention pooling — Colab GPU — **COLAB REMINDER (all five habits)**
- Sentence encoder: 4 conv blocks (Conv3×3 → BatchNorm → ReLU → MaxPool2), channels 16/32/64/128, global average pool → 128-d.
- Call level: attention pooling over sentence vectors → concatenate past volatility (4 values) → MLP → 4 outputs. Loss: MSE averaged over horizons. Audio-only (text branch comes after the report).
- Training: sample K=32 sentences per call per step (all sentences at eval, in chunks), batch 8 calls, Adam, LR 1e-3, weight decay 1e-4, dropout 0.3, early stopping on validation, max 40 epochs. Checkpoint to Drive every epoch; `--resume` supported.
- **Order of work:** (a) overfit 16 training calls to near-zero loss as a sanity check; (b) full run; (c) at most 3 further runs changing one thing each (LR, dropout, K).
- Outputs: `results/cnn_attn.json` (metrics + config + **parameter count**), **Fig. 4** learning curves, layer/shape table, **qualitative result**: top-3 attention sentences with text for 2 test calls, plus comparison of worst-predicted calls against baseline 1.
- **Escalate to Claude chat (stronger model)** if (a) fails or validation loss never falls below the train-mean predictor. Bring the learning curves and `cnn_attn.json`.

### Task 8 — Write the report (`report/main.tex`) — Claude Code, then user edits
Start from the proposal's `main.tex` (keeps the template fixes: `\usepackage{aps360}` lower-case, blanked `\@noticestring`).

Page budget (3.0 pages total, aim for 2.9):
| Section | Space | Contents |
|---|---|---|
| 1 Brief Project Description | 0.6 p | 1 paragraph + Fig. 1 (reuse proposal pipeline figure; grey out parts not yet built; label input and output) |
| 2 Data Processing | 0.9 p | sources; numbered cleaning steps; Table 1; Fig. 2; never-seen test plan; challenges |
| 3 Baseline Model | 0.6 p | two baselines in 4–5 lines; Table 2 (all models × 4 horizons, test MSE); Fig. 3; one qualitative observation; challenges |
| 4 Primary Model | 0.8 p | layer table with parameter count and training settings; Fig. 4; qualitative result; challenges; 5-row feasibility schedule to Dec 8 |

- Figures side by side where possible; all vector PDF from matplotlib with font size ≥ 8 pt at final size; tables with `booktabs`.
- The user rewrites section 1 and all "challenges" sentences in their own words.
- Compile (Overleaf, or Claude Code if LaTeX is installed), **count pages**, check every number against `results/*.json`.

### Task 9 — Review — Claude chat, stronger model
Upload the compiled PDF and `results/*.json`. Grade against section 2 line by line; check numbers against JSON; check page count; list required fixes.

### Task 10 — Repo cleanup before final submission (Dec, not this week)
- Delete `CLAUDE.md`, `PROGRESS.md`, `docs/plan.md`.
- Write a proper `README.md`: what the project is, setup, how to reproduce each result, results table, citations for datasets.
- Optional, user decides: squash history into one commit so removed files are not in the history either.
- If the course requires AI-tool disclosure, that goes in the report regardless of repo contents.

## 5. Schedule

| Day | Tasks | Needs user |
|---|---|---|
| Sun Nov 15 | 0, setup session, 1, start 2 | MDRM access, context upload, first PR review, first Colab run |
| Mon Nov 16 | 2, 3, 5 | verify low-score ticker matches |
| Tue Nov 17 | 4, start 6 | start the long Colab jobs early in the day |
| Wed Nov 18 | 7 (sanity check + full run), finish 6 | look at learning curves |
| Thu Nov 19 | 7 extra runs, 8 draft | rewrite text in own words |
| Fri Nov 20 | 9, fixes, submit by early evening | submit on Quercus |

PR review adds a few minutes per task. If a deadline day gets tight, review can be a skim, but keep the squash-merge step so `main` stays clean.

**Cut order if time runs short:** drop Task 6 first (baseline 1 alone satisfies the rubric), then the extra runs in Task 7. Never cut: Table 1, Fig. 2, Table 2, Fig. 4, parameter count, one qualitative result per model, never-seen test plan, challenges.

## 6. After the report (to Dec 8)
Resolve ticker/date for FinCall-Surprise calls → WhisperX alignment, one year's zip at a time on Colab's temporary disk → retrain with year split (train 2017+2019, val 2020, test 2021) → FinBERT text branch and fusion → ablations → pretrained wav2vec 2.0/HuBERT comparison → self-collected test calls → final report → Task 10.
