"""Task 2: map each MDRM call folder's company name to a stock ticker.

Inputs
    results/inventory.csv                      one row per call (Task 1)
    src/data/reference/sp500_2017.csv          S&P 500 names/tickers, 2017-2020 snapshots (build_sp500_ref.py)
    src/data/reference/ticker_overrides.csv    hand-set tickers where the fuzzy match is wrong or the matched
                                               list row carries a post-2017 ticker
    src/data/reference/ticker_history.csv      what happened to a 2017 ticker later (renamed / delisted /
                                               check) and which ticker yfinance should be asked for today

Matching
    Names are normalised (lower case, '&' -> 'and', punctuation removed, legal suffixes such as Inc/Corp/Co/
    plc/Ltd/The dropped), then compared with rapidfuzz WRatio. match_score = best score / 100 (0..1);
    second_score is the runner-up company, as a check on ambiguity. Matches below --review-below (0.9)
    are printed and marked verified = no until the user checks them by hand.

Outputs (in --out-dir, default results/)
    ticker_map.csv           one row per call:
        folder, company, date, ticker, yf_ticker, ticker_status, match_name, match_score, second_score,
        method, verified, note, dropped_reason   (+ yf_rows, yf_first, yf_last, yf_ok with --check-yf)
        ticker        = ticker the firm traded under at the time of the 2017 call
        yf_ticker     = ticker to request from yfinance today (blank if delisted)
        ticker_status = same | renamed | delisted | check   (check = unsure whether still listed)
        verified      = auto (score >= 0.9, no override) | no (user must check) | yes (user confirmed)
    ticker_map_review.csv    the rows the user must verify by hand (score < 0.9 or overridden)
    ticker_map_summary.json  counts, the config, and (with --check-yf) how many calls have no prices

Hand verification: open ticker_map.csv, check each verified = no row, and set it to yes (or fix the
ticker and add a line to ticker_overrides.csv, then re-run). Re-running keeps 'yes' marks for unchanged
rows if --keep-verified is given an older ticker_map.csv.

--check-yf (Colab, needs internet): asks yfinance for daily prices 2016-10-01..2018-03-31 for every
yf_ticker (and the 2017 ticker of delisted firms, in case Yahoo still serves it) and records rows found.
This is a preview for Task 3; it drops nothing.

Usage
    python -m src.data.ticker_map                       # matching only (runs anywhere)
    python -m src.data.ticker_map --check-yf            # + yfinance availability check (Colab)
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

import pandas as pd
from rapidfuzz import fuzz, process

HERE = os.path.dirname(os.path.abspath(__file__))
REF_DIR = os.path.join(HERE, "reference")
STOPWORDS = {"inc", "incorporated", "corp", "corporation", "co", "company", "cos", "the", "plc", "ltd",
             "limited", "nv", "sa", "ag", "lp", "class", "a"}
PRICE_START, PRICE_END = "2016-10-01", "2018-03-31"   # window used by Task 3 (docs/plan.md)
MIN_PRICE_ROWS = 300                                   # ~18 months of trading days is ~375


def normalise(name):
    s = name.lower().replace("&", " and ").replace("'s", "s")
    s = s.replace("int'l", "international").replace("serv.", "service")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(w for w in s.split() if w not in STOPWORDS)


def fuzzy_match(companies, ref):
    """Best and runner-up match for each company name. Runner-up skips rows of the same ticker."""
    ref = ref.reset_index(drop=True)
    choices = ref["name"].map(normalise).tolist()
    rows = []
    for c in companies:
        hits = process.extract(normalise(c), choices, scorer=fuzz.WRatio, limit=10)
        best = hits[0]
        best_ticker = ref.at[best[2], "ticker"]
        second = next((h for h in hits[1:] if ref.at[h[2], "ticker"] != best_ticker), None)
        rows.append({
            "company": c,
            "match_ticker": best_ticker,
            "match_name": ref.at[best[2], "name"],
            "match_score": round(best[1] / 100, 3),
            "second_name": ref.at[second[2], "name"] if second else "",
            "second_score": round(second[1] / 100, 3) if second else 0.0,
        })
    return pd.DataFrame(rows)


def build_map(inventory, ref, overrides, history, review_below):
    companies = sorted(inventory["company"].unique())
    m = fuzzy_match(companies, ref)
    m["ticker"] = m["match_ticker"]
    m["method"] = "fuzzy"
    m["note"] = ""
    ov = overrides.set_index("company")
    ref_names = ref.drop_duplicates("ticker", keep="first").set_index("ticker")["name"]
    for i, r in m.iterrows():
        if r.company in ov.index:
            t = ov.at[r.company, "ticker"]
            m.at[i, "ticker"] = t
            m.at[i, "method"] = "override"
            m.at[i, "note"] = ov.at[r.company, "reason"]
            # Show the reference row of the hand-set ticker and its score, not the rejected fuzzy pick.
            if t != r.match_ticker:
                name = ref_names.get(t, "")
                m.at[i, "match_name"] = name
                m.at[i, "match_score"] = round(fuzz.WRatio(normalise(r.company), normalise(name)) / 100, 3) \
                    if name else 0.0
    m["verified"] = "auto"
    m.loc[(m.match_score < review_below) | (m.method == "override"), "verified"] = "no"

    hist = history.set_index("ticker")
    m["ticker_status"] = "same"
    m["yf_ticker"] = m["ticker"]
    for i, r in m.iterrows():
        if r.ticker in hist.index:
            h = hist.loc[r.ticker]
            m.at[i, "ticker_status"] = h["status"]
            m.at[i, "yf_ticker"] = h["yf_ticker"] if isinstance(h["yf_ticker"], str) else ""
            m.at[i, "note"] = "; ".join(x for x in (m.at[i, "note"], h["event"]) if x)
    # yfinance uses '-' for share classes (BRK.B -> BRK-B).
    m["yf_ticker"] = m["yf_ticker"].str.replace(".", "-", regex=False)
    m["dropped_reason"] = ""
    m.loc[m.ticker.isna() | (m.ticker == ""), "dropped_reason"] = "no ticker match"

    out = inventory[["folder", "company", "date"]].merge(m, on="company", how="left")
    cols = ["folder", "company", "date", "ticker", "yf_ticker", "ticker_status", "match_name",
            "match_score", "second_name", "second_score", "method", "verified", "note", "dropped_reason"]
    return out[cols].sort_values(["date", "folder"]).reset_index(drop=True)


def keep_verified(new, old_path):
    """Carry over 'yes' marks from an older ticker_map.csv when folder and ticker are unchanged."""
    old = pd.read_csv(old_path, dtype=str, keep_default_na=False)
    yes = set(zip(old.loc[old.verified == "yes", "folder"], old.loc[old.verified == "yes", "ticker"]))
    hit = [(f, t) in yes for f, t in zip(new.folder, new.ticker)]
    new.loc[hit, "verified"] = "yes"
    return new


def check_yfinance(tmap):
    """Count daily price rows yfinance returns for each ticker in the Task 3 window."""
    import yfinance as yf
    asks = set(tmap.loc[tmap.yf_ticker != "", "yf_ticker"])
    asks |= set(tmap.loc[tmap.ticker_status == "delisted", "ticker"].str.replace(".", "-", regex=False))
    found = {}
    for t in sorted(asks):
        try:
            h = yf.Ticker(t).history(start=PRICE_START, end=PRICE_END, auto_adjust=False)
            h = h.dropna(subset=["Close"]) if len(h) else h
        except Exception as e:  # network errors, unknown symbol
            print(f"  {t}: error {e}", file=sys.stderr)
            h = pd.DataFrame()
        found[t] = (len(h), str(h.index.min().date()) if len(h) else "", str(h.index.max().date()) if len(h) else "")
        print(f"  {t:6} {found[t][0]:4d} rows {found[t][1]} {found[t][2]}")

    def pick(r):
        cands = [r.yf_ticker] if r.yf_ticker else []
        if r.ticker_status == "delisted":
            cands.append(r.ticker.replace(".", "-"))
        for t in cands:
            if found.get(t, (0,))[0] >= MIN_PRICE_ROWS:
                return pd.Series({"yf_ticker": t, "yf_rows": found[t][0], "yf_first": found[t][1],
                                  "yf_last": found[t][2], "yf_ok": True})
        best = max(cands, key=lambda t: found.get(t, (0,))[0]) if cands else ""
        f = found.get(best, (0, "", ""))
        return pd.Series({"yf_ticker": r.yf_ticker, "yf_rows": f[0], "yf_first": f[1], "yf_last": f[2],
                          "yf_ok": False})

    extra = tmap.apply(pick, axis=1)
    tmap = tmap.drop(columns=["yf_ticker"]).join(extra)
    return tmap


def rel(path):
    return os.path.relpath(path) if os.path.isabs(path) else path


def summarise(tmap, args, inventory):
    per_firm = tmap.drop_duplicates("company")
    s = {
        "n_calls": int(len(tmap)),
        "n_companies": int(per_firm.shape[0]),
        "n_calls_with_ticker": int((tmap.dropped_reason == "").sum()),
        "n_calls_dropped": int((tmap.dropped_reason != "").sum()),
        "dropped_reasons": tmap.loc[tmap.dropped_reason != "", "dropped_reason"].value_counts().to_dict(),
        "n_companies_score_below_review": int((per_firm.match_score < args.review_below).sum()),
        "n_companies_overridden": int((per_firm.method == "override").sum()),
        "n_companies_to_verify": int((per_firm.verified == "no").sum()),
        "companies_by_ticker_status": per_firm.ticker_status.value_counts().to_dict(),
        "calls_by_ticker_status": tmap.ticker_status.value_counts().to_dict(),
        "match_score": {"min": float(per_firm.match_score.min()),
                        "median": float(per_firm.match_score.median())},
        "all_calls_have_ticker_or_reason": bool(((tmap.ticker.fillna("") != "") |
                                                 (tmap.dropped_reason != "")).all()),
        "inventory_calls_covered": bool(set(tmap.folder) == set(inventory.folder)),
    }
    if "yf_ok" in tmap:
        no_px = tmap[~tmap.yf_ok]
        s["yfinance_check"] = {
            "window": [PRICE_START, PRICE_END], "min_rows": MIN_PRICE_ROWS,
            "n_calls_without_prices": int(len(no_px)),
            "pct_calls_without_prices": round(100 * len(no_px) / len(tmap), 1),
            "companies_without_prices": sorted(no_px.company.unique().tolist()),
        }
    s["config"] = {
        "script": "src/data/ticker_map.py",
        "inventory": rel(args.inventory), "reference": rel(args.reference),
        "overrides": rel(args.overrides), "history": rel(args.history),
        "scorer": "rapidfuzz.fuzz.WRatio on normalised names", "stopwords": sorted(STOPWORDS),
        "review_below": args.review_below, "check_yf": args.check_yf,
        "created": dt.datetime.now().isoformat(timespec="seconds"),
    }
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inventory", default="results/inventory.csv")
    ap.add_argument("--reference", default=os.path.join(REF_DIR, "sp500_2017.csv"))
    ap.add_argument("--overrides", default=os.path.join(REF_DIR, "ticker_overrides.csv"))
    ap.add_argument("--history", default=os.path.join(REF_DIR, "ticker_history.csv"))
    ap.add_argument("--out-dir", default="results")
    ap.add_argument("--review-below", type=float, default=0.9)
    ap.add_argument("--keep-verified", default=None, help="older ticker_map.csv whose 'yes' marks to keep")
    ap.add_argument("--check-yf", action="store_true", help="query yfinance for price availability")
    args = ap.parse_args()

    inventory = pd.read_csv(args.inventory)
    ref = pd.read_csv(args.reference)
    overrides = pd.read_csv(args.overrides, dtype=str)
    history = pd.read_csv(args.history, dtype=str, keep_default_na=False)
    tmap = build_map(inventory, ref, overrides, history, args.review_below)
    if args.keep_verified and os.path.exists(args.keep_verified):
        tmap = keep_verified(tmap, args.keep_verified)
    if args.check_yf:
        tmap = check_yfinance(tmap)

    os.makedirs(args.out_dir, exist_ok=True)
    tmap.to_csv(os.path.join(args.out_dir, "ticker_map.csv"), index=False)
    review = tmap[tmap.verified == "no"].drop_duplicates("company")
    review.to_csv(os.path.join(args.out_dir, "ticker_map_review.csv"), index=False)
    summary = summarise(tmap, args, inventory)
    with open(os.path.join(args.out_dir, "ticker_map_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print(f"{summary['n_calls']} calls, {summary['n_companies']} companies; "
          f"{summary['n_calls_with_ticker']} calls with a ticker, {summary['n_calls_dropped']} dropped")
    print("Companies by ticker status:", summary["companies_by_ticker_status"])
    print(f"\nVERIFY BY HAND ({len(review)} companies: score < {args.review_below} or overridden):")
    for r in review.itertuples():
        print(f"  {r.company!r:28} -> {r.ticker:6} (match {r.match_name!r}, score {r.match_score:.2f}, "
              f"runner-up {r.second_name!r} {r.second_score:.2f}) [{r.method}] {r.note}")
    if "yfinance_check" in summary:
        y = summary["yfinance_check"]
        print(f"\nyfinance: {y['n_calls_without_prices']} calls ({y['pct_calls_without_prices']}%) have no "
              f"prices: {y['companies_without_prices']}")
        if y["pct_calls_without_prices"] > 10:
            print("WARNING: more than 10% of calls would be dropped in Task 3. Stop and decide on a "
                  "price source for delisted firms before Task 3.")
    if not summary["all_calls_have_ticker_or_reason"]:
        sys.exit("CHECK FAILED: some calls have neither a ticker nor a dropped_reason")


if __name__ == "__main__":
    main()
