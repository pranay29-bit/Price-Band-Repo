# NSE Price Band — Pine Seeds Feed

Daily NSE price-band (circuit filter) data, published for TradingView's
Pine Seeds service.

## Repo structure

```
.
├── incoming/                        # drop each day's raw NSE file here (not committed long-term, just staging)
├── scripts/
│   └── nse_band_to_pine_seeds.py    # converts a raw NSE file into Pine Seeds format
├── data/
│   └── BAND/
│       ├── RELIANCE.csv             # one file per symbol, Pine-Seeds-compliant
│       ├── TCS.csv
│       └── ...
├── pine/
│   └── circuit_band_pine_seeds.pine # Pine Script that reads the seeded data on a chart
└── .github/workflows/
    └── validate-data.yml            # auto-checks data/BAND files are well-formed on push
```

## Data format

Each `data/BAND/<SYMBOL>.csv` is a Pine-Seeds-compliant OHLCV file:

```
date,open,high,low,close,volume
2026-08-03,20.0,20.0,20.0,20.0,0
```

Since a price band isn't naturally OHLCV data, the band % is repeated as
open = high = low = close, with volume fixed at 0. This lets Pine Seeds
treat it like a normal daily series, and your Pine Script reads the
`close` value as the band %. `0` means "No Band" (F&O-eligible stock).

## Daily workflow (manual)

1. Download NSE's daily security-wise price band file
   (`sec_list_DDMMYYYY.csv`, columns: `Symbol,Series,Security Name,Band,Remarks`)
   and place it in `incoming/`.

2. Run the converter from the repo root:
   ```bash
   pip install pandas
   python scripts/nse_band_to_pine_seeds.py incoming/sec_list_03082026.csv
   ```
   This appends today's row to every symbol's file in `data/BAND/`.
   Re-running it for the same date is safe — it skips duplicates.

3. Commit and push:
   ```bash
   git add data/BAND
   git commit -m "band update 2026-08-03"
   git push
   ```

4. The `validate-data.yml` GitHub Action runs automatically on push and
   checks every touched file is well-formed (6 fields per row, dates
   strictly increasing, numeric OHLCV values). If it fails, fix the
   flagged file before Pine Seeds ingests it.

## One-time setup with TradingView

This repo publishing data does not automatically appear on TradingView —
you need to register it once:

1. Make this repo **public** on GitHub.
2. Submit it via TradingView's Pine Seeds request form
   (search "TradingView Pine Seeds" in their help center for the current form/link).
3. Once approved, TradingView assigns a seed prefix, e.g.
   `SEED_yourprefix_BAND`. Your symbols become accessible as
   `SEED_yourprefix_BAND:RELIANCE`, etc.
4. In `pine/circuit_band_pine_seeds.pine`, set the "Band Seed Prefix"
   input to that assigned prefix.

## Notes / limitations

- Pine Seeds only supports **daily-or-lower-frequency** updates — there's
  no intraday refresh.
- If you are sourcing the raw file directly from NSE, check NSE's terms
  of use regarding redistribution before making this repo public, since
  the underlying data originates from their published feed.
