"""
NSE sec_list_DDMMYYYY.csv -> Pine Seeds converter
--------------------------------------------------
Run this each day after downloading NSE's daily security-wise price
band file (format: Symbol,Series,Security Name,Band,Remarks).

It appends one row per symbol into data/BAND/<SYMBOL>.csv in
Pine-Seeds-compliant shape (date,open,high,low,close,volume), where
the "close" value is the band % (0 = No Band / F&O-style stock).

Usage (from repo root):
    python scripts/nse_band_to_pine_seeds.py incoming/sec_list_03082026.csv

The date is parsed from the filename itself (DDMMYYYY), matching
NSE's naming convention. If your filename differs, pass --date explicitly:

    python scripts/nse_band_to_pine_seeds.py incoming/my_file.csv --date 2026-08-03
"""

import argparse
import re
import pandas as pd
from pathlib import Path

BAND_DIR = Path(__file__).resolve().parent.parent / "data" / "BAND"
BAND_DIR.mkdir(parents=True, exist_ok=True)


def parse_date_from_filename(filename: str) -> str:
    """Extract DDMMYYYY from names like sec_list_03082026.csv -> 2026-08-03"""
    match = re.search(r"(\d{2})(\d{2})(\d{4})", filename)
    if not match:
        raise ValueError(
            f"Could not parse date from filename '{filename}'. "
            f"Pass --date YYYY-MM-DD explicitly instead."
        )
    dd, mm, yyyy = match.groups()
    return f"{yyyy}-{mm}-{dd}"


def band_to_number(band_value: str) -> float:
    """Convert NSE's Band column into a numeric %, using 0 for 'No Band' (F&O-style)."""
    s = str(band_value).strip()
    if s.lower() == "no band":
        return 0.0
    try:
        return float(s)
    except ValueError:
        return float("nan")


def append_row(symbol: str, date_str: str, band_pct: float) -> str:
    file_path = BAND_DIR / f"{symbol}.csv"
    row = f"{date_str},{band_pct},{band_pct},{band_pct},{band_pct},0"

    if file_path.exists():
        with open(file_path, "r") as f:
            lines = f.read().splitlines()
        if lines and lines[-1].split(",")[0] == date_str:
            return "skip"

    with open(file_path, "a") as f:
        f.write(row + "\n")
    return "ok"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", help="Path to NSE sec_list_DDMMYYYY.csv")
    parser.add_argument("--date", help="Override date as YYYY-MM-DD", default=None)
    args = parser.parse_args()

    date_str = args.date or parse_date_from_filename(Path(args.csv_file).name)
    print(f"Using date: {date_str}")

    df = pd.read_csv(args.csv_file)
    df.columns = [c.strip() for c in df.columns]  # normalize header whitespace

    required_cols = {"Symbol", "Band"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Input file is missing required column(s): {missing}")

    ok_count, skip_count, err_count = 0, 0, 0

    for _, r in df.iterrows():
        symbol = str(r["Symbol"]).strip().upper()
        band_pct = band_to_number(r["Band"])

        if pd.isna(band_pct):
            print(f"[error] {symbol}: unrecognized band value '{r['Band']}'")
            err_count += 1
            continue

        result = append_row(symbol, date_str, band_pct)
        if result == "ok":
            ok_count += 1
        else:
            skip_count += 1

    print(f"\nDone. {ok_count} appended, {skip_count} skipped (already recorded), {err_count} errors.")
    print(f"Now: git add data/BAND && git commit -m 'band update {date_str}' && git push")


if __name__ == "__main__":
    main()
