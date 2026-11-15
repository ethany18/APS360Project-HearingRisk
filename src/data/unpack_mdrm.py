"""Task 1, step 1: merge and unzip the MDRM split archive onto Colab's local disk.

The MDRM release (Qin & Yang, 2019) is a split zip: ACL19_Release.zip plus parts .z01, .z02, ...
This script follows docs/plan.md, Task 1:
    zip -s0 ACL19_Release.zip --out ACL19_Release_All.zip
    unzip -q ACL19_Release_All.zip -d <dst>

It reads from Drive (a folder or a shortcut) and writes only to local disk (/content/...), never to Drive.
Safe to re-run: if <dst> already holds call folders it does nothing (use --force to redo).

Also works if the Drive folder holds an already-extracted copy (call folders instead of zips): then
it copies the folders.

Usage (Colab):
    python -m src.data.unpack_mdrm \
        --src /content/drive/MyDrive/HearingRisk/raw/mdrm --dst /content/data/mdrm
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time

CALL_DIR_RE = re.compile(r"^.+_\d{8}$")


def count_call_dirs(root, limit=None):
    """Count directories named CompanyName_YYYYMMDD under root (stops early at `limit`)."""
    n = 0
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__MACOSX"]
        hits = [d for d in dirnames if CALL_DIR_RE.match(d)]
        n += len(hits)
        if limit is not None and n >= limit:
            return n
        dirnames[:] = [d for d in dirnames if not CALL_DIR_RE.match(d)]
    return n


def run(cmd):
    print("+", " ".join(f'"{c}"' if " " in c else c for c in cmd), flush=True)
    subprocess.run(cmd, check=True)


def human_gb(nbytes):
    return f"{nbytes / 1e9:.2f} GB"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--src", required=True, help="Drive folder with the MDRM zip parts (or extracted folders)")
    p.add_argument("--dst", required=True, help="Local output folder, e.g. /content/data/mdrm")
    p.add_argument("--tmp", default="/content/tmp_mdrm", help="Local scratch folder for zip parts and merged zip")
    p.add_argument("--no-local-copy", action="store_true",
                   help="Merge straight from Drive instead of copying the parts to local disk first")
    p.add_argument("--force", action="store_true", help="Unpack even if dst already has call folders")
    args = p.parse_args(argv)

    if not os.path.isdir(args.src):
        sys.exit(f"ERROR: source folder not found: {args.src}\n"
                 "Check the Drive path / shortcut (HearingRisk/raw/mdrm) and that Drive is mounted.")

    if os.path.isdir(args.dst) and count_call_dirs(args.dst, limit=1) > 0 and not args.force:
        print(f"{args.dst} already contains call folders ({count_call_dirs(args.dst)}); skipping. "
              "Use --force to unpack again.")
        return 0

    os.makedirs(args.dst, exist_ok=True)
    entries = sorted(os.listdir(args.src))
    zips = [e for e in entries if e.lower().endswith(".zip")]
    parts = [e for e in entries if re.search(r"\.z\d{2,}$", e.lower())]
    print(f"Source {args.src}: {len(entries)} entries, zips={zips}, parts={parts}")
    t0 = time.time()

    if not zips:
        n_src = count_call_dirs(args.src)
        if n_src == 0:
            sys.exit("ERROR: no .zip files and no CompanyName_YYYYMMDD folders found in the source. "
                     "Stop and tell Claude Code what the folder contains (ls output).")
        print(f"No zip found; copying {n_src} already-extracted call folders (slow on Drive).")
        run(["cp", "-r", os.path.join(args.src, "."), args.dst])
    else:
        if len(zips) > 1:
            print(f"WARNING: more than one .zip in source; using all of them in order: {zips}")
        os.makedirs(args.tmp, exist_ok=True)
        for z in zips:
            stem = z[:-4]
            my_parts = [e for e in parts if e.startswith(stem + ".")]
            work = args.src
            if not args.no_local_copy:
                # Copy the few large parts to local disk: more reliable than merging through the Drive mount.
                for f in my_parts + [z]:
                    dst_f = os.path.join(args.tmp, f)
                    src_f = os.path.join(args.src, f)
                    if not (os.path.exists(dst_f) and os.path.getsize(dst_f) == os.path.getsize(src_f)):
                        print(f"Copying {f} ({human_gb(os.path.getsize(src_f))}) to local disk")
                        shutil.copyfile(src_f, dst_f)
                work = args.tmp
            if my_parts:
                merged = os.path.join(args.tmp, stem + "_All.zip")
                run(["zip", "-q", "-s0", os.path.join(work, z), "--out", merged])
                if not args.no_local_copy:
                    for f in my_parts + [z]:
                        os.remove(os.path.join(args.tmp, f))
            else:
                merged = os.path.join(work, z)
            run(["unzip", "-q", "-o", merged, "-d", args.dst])
            if merged.startswith(args.tmp):
                os.remove(merged)
        shutil.rmtree(args.tmp, ignore_errors=True)

    macosx = os.path.join(args.dst, "__MACOSX")
    if os.path.isdir(macosx):
        shutil.rmtree(macosx)
    n = count_call_dirs(args.dst)
    print(f"Done in {time.time() - t0:.0f} s: {n} call folders under {args.dst}")
    if n == 0:
        sys.exit("ERROR: unpacked, but no CompanyName_YYYYMMDD folders found. Tell Claude Code the layout.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
