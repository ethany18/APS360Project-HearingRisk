"""Task 1, step 2: inventory the unpacked MDRM dataset.

Finds every call folder named CompanyName_YYYYMMDD under --root and writes one row per call:
    folder, company, date, n_text_lines, n_audio_files, audio_seconds,
    n_unreadable_audio, n_text_files, lines_match_audio, rel_path

Outputs (all in --out-dir, default results/):
    inventory.csv              one row per call, sorted by date then folder
    inventory_mismatches.csv   calls where text-line count != audio-file count (or other problems)
    inventory_summary.json     totals, checks against the expected ~572 calls / ~89k clips, and the config
If --copy-to is given (Drive HearingRisk/processed/), inventory.csv is copied there as well.

Text lines: non-empty lines of the call's transcript .txt file (Text.txt if present).
Audio seconds: read from file headers (no decoding), summed over the call's clips.

Usage (Colab):
    python -m src.data.inventory --root /content/data/mdrm --out-dir results \
        --copy-to /content/drive/MyDrive/HearingRisk/processed
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
import time
from multiprocessing import Pool

import pandas as pd

CALL_DIR_RE = re.compile(r"^(?P<company>.+)_(?P<date>\d{8})$")
AUDIO_EXTS = (".wav", ".mp3", ".flac", ".m4a", ".ogg")
EXPECTED_CALLS = 572
EXPECTED_CLIPS = 89_000  # "about 89k" in docs/plan.md


def find_call_dirs(root):
    """Return sorted paths of all CompanyName_YYYYMMDD folders (does not descend into them)."""
    found = []
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != "__MACOSX" and not d.startswith("."))
        keep = []
        for d in dirnames:
            if CALL_DIR_RE.match(d):
                found.append(os.path.join(dirpath, d))
            else:
                keep.append(d)
        dirnames[:] = keep
    return sorted(found)


def audio_duration(path):
    """Duration in seconds from the file header, or None if unreadable."""
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext in (".wav", ".flac", ".ogg"):
            import soundfile as sf
            info = sf.info(path)
            return info.frames / info.samplerate if info.samplerate else None
        if ext == ".mp3":
            from mutagen.mp3 import MP3
            return MP3(path).info.length
        import mutagen
        f = mutagen.File(path)
        return f.info.length if f is not None else None
    except Exception:
        return None


def count_text_lines(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return sum(1 for line in fh if line.strip())


def inventory_call(args):
    call_dir, root = args
    folder = os.path.basename(call_dir)
    m = CALL_DIR_RE.match(folder)
    company, raw_date = m.group("company"), m.group("date")
    try:
        date = dt.datetime.strptime(raw_date, "%Y%m%d").date().isoformat()
    except ValueError:
        date = ""

    text_files, audio_files = [], []
    for dirpath, dirnames, filenames in os.walk(call_dir):
        dirnames[:] = [d for d in dirnames if d != "__MACOSX"]
        for f in filenames:
            if f.startswith("._"):  # macOS resource-fork junk
                continue
            low = f.lower()
            full = os.path.join(dirpath, f)
            if low.endswith(".txt"):
                text_files.append(full)
            elif low.endswith(AUDIO_EXTS):
                audio_files.append(full)

    preferred = [t for t in text_files if os.path.basename(t).lower() == "text.txt"]
    text_file = (preferred or sorted(text_files) or [None])[0]
    n_lines = count_text_lines(text_file) if text_file else 0

    total, n_bad = 0.0, 0
    for a in audio_files:
        d = audio_duration(a)
        if d is None:
            n_bad += 1
        else:
            total += d

    return {
        "folder": folder,
        "company": company,
        "date": date,
        "n_text_lines": n_lines,
        "n_audio_files": len(audio_files),
        "audio_seconds": round(total, 3),
        "n_unreadable_audio": n_bad,
        "n_text_files": len(text_files),
        "lines_match_audio": n_lines == len(audio_files),
        "rel_path": os.path.relpath(call_dir, root),
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default="/content/data/mdrm", help="Unpacked MDRM folder")
    p.add_argument("--out-dir", default="results", help="Where to write the CSV/JSON outputs")
    p.add_argument("--copy-to", default=None, help="Extra folder to copy inventory.csv to (Drive processed/)")
    p.add_argument("--workers", type=int, default=os.cpu_count() or 2)
    args = p.parse_args(argv)

    if not os.path.isdir(args.root):
        sys.exit(f"ERROR: {args.root} does not exist. Run src.data.unpack_mdrm first.")

    t0 = time.time()
    call_dirs = find_call_dirs(args.root)
    if not call_dirs:
        sys.exit(f"ERROR: no CompanyName_YYYYMMDD folders under {args.root}.")
    print(f"Found {len(call_dirs)} call folders under {args.root}; reading with {args.workers} workers")

    with Pool(args.workers) as pool:
        rows = pool.map(inventory_call, [(c, args.root) for c in call_dirs], chunksize=4)

    df = pd.DataFrame(rows).sort_values(["date", "folder"], kind="mergesort").reset_index(drop=True)

    dup = df["folder"].duplicated(keep=False)
    problems = (~df["lines_match_audio"]) | (df["n_unreadable_audio"] > 0) | (df["n_text_files"] != 1) \
        | (df["date"] == "") | dup
    mism = df[problems].copy()
    reasons = []
    for _, r in mism.iterrows():
        why = []
        if not r["lines_match_audio"]:
            why.append(f"text_lines={r['n_text_lines']} != audio_files={r['n_audio_files']}")
        if r["n_unreadable_audio"] > 0:
            why.append(f"{r['n_unreadable_audio']} unreadable audio")
        if r["n_text_files"] != 1:
            why.append(f"{r['n_text_files']} text files")
        if r["date"] == "":
            why.append("bad date in folder name")
        if dup.loc[_]:
            why.append("duplicate folder name")
        reasons.append("; ".join(why))
    mism["problem"] = reasons

    os.makedirs(args.out_dir, exist_ok=True)
    inv_path = os.path.join(args.out_dir, "inventory.csv")
    mism_path = os.path.join(args.out_dir, "inventory_mismatches.csv")
    sum_path = os.path.join(args.out_dir, "inventory_summary.json")
    df.to_csv(inv_path, index=False)
    mism.to_csv(mism_path, index=False)

    n_calls = len(df)
    n_clips = int(df["n_audio_files"].sum())
    dates = df.loc[df["date"] != "", "date"]
    summary = {
        "n_calls": n_calls,
        "n_companies": int(df["company"].nunique()),
        "n_text_lines": int(df["n_text_lines"].sum()),
        "n_audio_files": n_clips,
        "n_unreadable_audio": int(df["n_unreadable_audio"].sum()),
        "audio_hours": round(float(df["audio_seconds"].sum()) / 3600, 3),
        "clips_per_call": {
            "min": int(df["n_audio_files"].min()),
            "median": float(df["n_audio_files"].median()),
            "max": int(df["n_audio_files"].max()),
        },
        "date_min": dates.min() if len(dates) else None,
        "date_max": dates.max() if len(dates) else None,
        "n_calls_line_audio_mismatch": int((~df["lines_match_audio"]).sum()),
        "n_calls_with_any_problem": int(len(mism)),
        "checks": {
            "expected_calls_approx": EXPECTED_CALLS,
            "expected_clips_approx": EXPECTED_CLIPS,
            "calls_within_5pct": abs(n_calls - EXPECTED_CALLS) <= 0.05 * EXPECTED_CALLS,
            "clips_within_5pct": abs(n_clips - EXPECTED_CLIPS) <= 0.05 * EXPECTED_CLIPS,
            "all_lines_match_audio": bool(df["lines_match_audio"].all()),
        },
        "config": {
            "script": "src/data/inventory.py",
            "root": args.root,
            "audio_extensions": list(AUDIO_EXTS),
            "text_line_rule": "non-empty lines of Text.txt (or the only .txt) in the call folder",
            "duration_source": "file headers (soundfile for wav/flac, mutagen for mp3)",
            "created": dt.datetime.now().isoformat(timespec="seconds"),
            "runtime_seconds": round(time.time() - t0, 1),
        },
    }
    with open(sum_path, "w") as fh:
        json.dump(summary, fh, indent=2)

    if args.copy_to:
        os.makedirs(args.copy_to, exist_ok=True)
        shutil.copy2(inv_path, os.path.join(args.copy_to, "inventory.csv"))
        print(f"Copied inventory.csv to {args.copy_to}")

    print(json.dumps({k: v for k, v in summary.items() if k != "config"}, indent=2))
    if len(mism):
        print(f"\n{len(mism)} calls with problems (full list in {mism_path}):")
        with pd.option_context("display.max_rows", 50, "display.width", 200, "display.max_colwidth", 60):
            print(mism[["folder", "n_text_lines", "n_audio_files", "problem"]].head(50).to_string(index=False))
    else:
        print("\nNo mismatches: every call has text-line count == audio-file count.")
    print(f"\nWrote {inv_path}, {mism_path}, {sum_path} in {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
