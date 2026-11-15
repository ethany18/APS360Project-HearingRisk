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
