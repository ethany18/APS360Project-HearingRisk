"""Task 2, step 1: build the 2017 S&P 500 reference list used for company-name -> ticker matching.

Sources (pinned to exact commits so the list is reproducible):
  * datasets/s-and-p-500-companies, data/constituents.csv (Symbol, Name, Sector), licence ODC-PDDL:
      - snapshot of 2017-03-08 (commit 5bfe9b1): constituents early in 2017, tickers as used in 2017
      - snapshot of 2018-04-02 (commit 5dfdfbc): catches firms added or renamed during 2017 / early 2018
      - snapshot of 2020-05-10 (commit 5b0e007): catches firms that joined the index after the 2017
        calls (MDRM also covers some of these, e.g. Twitter, MSCI, Broadridge)
  * fja05680/sp500, sp500_ticker_start_end.csv (ticker, start_date, end_date), MIT licence:
      used only to flag whether a ticker was in the index at any time in 2017.
      Note: that file uses *current* tickers (e.g. BKNG back to 2009), so the flag can be False for a
      2017-era ticker that was later renamed (e.g. PCLN). It is informational only.

Output: src/data/reference/sp500_2017.csv with columns
    ticker, name, sector, snapshot, in_sp500_2017
One row per distinct (ticker, name) pair, labelled with the earliest snapshot it appears in, so a firm
renamed between snapshots (e.g. Dominion Resources -> Dominion Energy) has one row per name.

Usage:
    python -m src.data.build_sp500_ref            # writes src/data/reference/sp500_2017.csv
"""
import argparse
import io
import os
import urllib.request

import pandas as pd

RAW = "https://raw.githubusercontent.com"
SNAPSHOTS = [
    ("2017-03-08", f"{RAW}/datasets/s-and-p-500-companies/5bfe9b141ffee903c741b7f2c16ce050cb1cb324/data/constituents.csv"),
    ("2018-04-02", f"{RAW}/datasets/s-and-p-500-companies/5dfdfbc3b9f52802f89e72da6e050b5cafdec4a6/data/constituents.csv"),
    ("2020-05-10", f"{RAW}/datasets/s-and-p-500-companies/5b0e007b27ab6b0f0d406ec65dd05b7261e7fc24/data/constituents.csv"),
]
START_END = f"{RAW}/fja05680/sp500/a2430f2af0c79ddf0748e91de11bdeb1616ab5a7/sp500_ticker_start_end.csv"
YEAR_START, YEAR_END = pd.Timestamp("2017-01-01"), pd.Timestamp("2017-12-31")
DEFAULT_OUT = os.path.join(os.path.dirname(__file__), "reference", "sp500_2017.csv")


def fetch_csv(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return pd.read_csv(io.BytesIO(r.read()))


def in_index_2017(start_end):
    se = start_end.copy()
    se["start_date"] = pd.to_datetime(se["start_date"])
    se["end_date"] = pd.to_datetime(se["end_date"]).fillna(pd.Timestamp("2100-01-01"))
    active = se[(se.start_date <= YEAR_END) & (se.end_date >= YEAR_START)]
    return set(active["ticker"])


def build(snapshots, start_end):
    frames = []
    for date, df in snapshots:
        df = df.rename(columns={"Symbol": "ticker", "Name": "name", "Sector": "sector"})
        df["snapshot"] = date
        frames.append(df[["ticker", "name", "sector", "snapshot"]])
    ref = pd.concat(frames, ignore_index=True)
    ref["ticker"] = ref["ticker"].str.strip()
    ref["name"] = ref["name"].str.strip()
    # Keep the earliest snapshot's row for each distinct (ticker, name) pair.
    ref = ref.sort_values(["ticker", "snapshot"]).drop_duplicates(["ticker", "name"], keep="first")
    active = in_index_2017(start_end)
    ref["in_sp500_2017"] = ref["ticker"].isin(active)
    return ref.sort_values(["ticker", "snapshot"]).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()
    snaps = [(d, fetch_csv(u)) for d, u in SNAPSHOTS]
    ref = build(snaps, fetch_csv(START_END))
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    ref.to_csv(args.out, index=False)
    print(f"wrote {args.out}: {len(ref)} (ticker, name) rows, {ref.ticker.nunique()} tickers "
          f"({ref.loc[ref.in_sp500_2017, "ticker"].nunique()} tickers flagged in the index during 2017)")


if __name__ == "__main__":
    main()
