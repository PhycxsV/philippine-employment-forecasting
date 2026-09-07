"""
Development inspection script (NOT official analytical evidence).

Purpose: programmatically audit the raw PSA CSV so that Stage 1 findings
(structure, data quality, observation frequency, candidate modelling windows)
are established from the actual file rather than assumed.

Anything material discovered here must later be reproduced inside the main
notebook, which remains the source of truth.
"""

from pathlib import Path

import numpy as np
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 50)

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "data" / "Rates Key Employment Indicators- April 2005 to June 2026.csv"

SEP = "=" * 78


def header(title: str) -> None:
    print(f"\n{SEP}\n{title}\n{SEP}")


# ---------------------------------------------------------------- raw file --
header("A. RAW FILE STRUCTURE")

raw_lines = CSV.read_text(encoding="utf-8-sig").splitlines()
print(f"File               : {CSV.relative_to(ROOT)}")
print(f"Total lines in file: {len(raw_lines)}")
print(f"Line 1 (title row) : {raw_lines[0]}")
print(f"Line 2 (header row): {raw_lines[1][:120]}...")
print(f"Line 3 (first data): {raw_lines[2]}")
print(f"Last line          : {raw_lines[-1]}")

# Row 0 is a title banner, row 1 is the real header.
df = pd.read_csv(CSV, skiprows=1, na_values=["."], encoding="utf-8-sig")

print(f"\nParsed shape (rows, cols): {df.shape}")
print("\nColumn names and dtypes:")
print(df.dtypes.to_string())

# ------------------------------------------------------- annual vs monthly --
header("B. ROW TYPES ('Month' column values)")

print(df["Month"].value_counts().to_string())
annual_mask = df["Month"].str.strip().str.lower() == "annual"
print(f"\n'Annual' aggregate rows : {int(annual_mask.sum())}")
print(f"Calendar-month rows     : {int((~annual_mask).sum())}")
print(f"Years covered           : {df['Year'].min()} to {df['Year'].max()}")

monthly_rows = df.loc[~annual_mask].copy()
annual_rows = df.loc[annual_mask].copy()

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
    "December": 12,
}
monthly_rows["month_num"] = monthly_rows["Month"].str.strip().map(MONTHS)
print(f"\nUnmapped month labels   : {int(monthly_rows['month_num'].isna().sum())}")
monthly_rows["Date"] = pd.to_datetime(
    dict(year=monthly_rows["Year"], month=monthly_rows["month_num"], day=1)
)
monthly_rows = monthly_rows.sort_values("Date").reset_index(drop=True)

print(f"Calendar grid span      : {monthly_rows['Date'].min():%Y-%m} to "
      f"{monthly_rows['Date'].max():%Y-%m}")
expected = pd.date_range(monthly_rows["Date"].min(), monthly_rows["Date"].max(), freq="MS")
print(f"Expected months in span : {len(expected)}")
print(f"Rows on calendar grid   : {len(monthly_rows)}")
print(f"Calendar grid complete  : {len(expected) == len(monthly_rows)}")

# ------------------------------------------------------------ target column --
header("C. TARGET VARIABLE")

TARGET = "Employment Rate Both sexes"
print(f"Target variable: {TARGET!r}")
print(f"Present in file: {TARGET in df.columns}")
print(f"dtype after parsing '.' as NaN: {df[TARGET].dtype}")

obs = monthly_rows.loc[monthly_rows[TARGET].notna()].copy()
print(f"\nCalendar-month rows with an observed value : {len(obs)}")
print(f"Calendar-month rows that are blank ('.')   : {int(monthly_rows[TARGET].isna().sum())}")
print(f"First observed date : {obs['Date'].min():%Y-%m}  value={obs[TARGET].iloc[0]:.3f}")
print(f"Last observed date  : {obs['Date'].max():%Y-%m}  value={obs[TARGET].iloc[-1]:.3f}")

print("\nFirst 8 observed rows:")
print(obs[["Year", "Month", TARGET]].head(8).to_string(index=False))
print("\nLast 8 observed rows:")
print(obs[["Year", "Month", TARGET]].tail(8).to_string(index=False))

# ------------------------------------------------------------ missingness ---
header("D. MISSING VALUES (all columns, calendar-month rows only)")

miss = pd.DataFrame({
    "n_missing": monthly_rows[df.columns.drop(["Year", "Month"])].isna().sum(),
    "n_present": monthly_rows[df.columns.drop(["Year", "Month"])].notna().sum(),
})
miss["pct_missing"] = (100 * miss["n_missing"] / len(monthly_rows)).round(2)
print(miss.to_string())

print("\nDo all 12 indicator columns share the SAME missing pattern as the target?")
indicator_cols = list(df.columns.drop(["Year", "Month"]))
same_pattern = all(
    monthly_rows[c].isna().equals(monthly_rows[TARGET].isna()) for c in indicator_cols
)
print(f"  -> {same_pattern}  (missingness is row-level, i.e. 'month not surveyed')")

# Missing values inside the observed span vs. trailing not-yet-published months
span = monthly_rows[(monthly_rows["Date"] >= obs["Date"].min())
                    & (monthly_rows["Date"] <= obs["Date"].max())]
trailing = monthly_rows[monthly_rows["Date"] > obs["Date"].max()]
leading = monthly_rows[monthly_rows["Date"] < obs["Date"].min()]
print(f"\nBlank months BEFORE first observation (Jan-Mar 2005)   : {len(leading)}")
print(f"Blank months INSIDE observed span (unsurveyed months)  : "
      f"{int(span[TARGET].isna().sum())}")
print(f"Blank months AFTER last observation (not yet published): {len(trailing)}")

# -------------------------------------------------------------- duplicates --
header("E. DUPLICATES")

print(f"Fully duplicated rows (all columns) : {int(df.duplicated().sum())}")
print(f"Duplicated (Year, Month) keys       : "
      f"{int(df.duplicated(subset=['Year', 'Month']).sum())}")
print(f"Duplicated observation Dates        : {int(obs['Date'].duplicated().sum())}")
print(f"Duplicated (Date, target) pairs     : "
      f"{int(obs.duplicated(subset=['Date', TARGET]).sum())}")
rep = obs[TARGET].duplicated(keep=False)
print(f"\nRepeated target VALUES (legitimate coincidence, not row duplicates): "
      f"{int(rep.sum())} rows")
if rep.any():
    print(obs.loc[rep, ["Date", TARGET]]
          .assign(Date=lambda d: d["Date"].dt.strftime("%Y-%m"))
          .to_string(index=False))

# ---------------------------------------------------------- invalid values --
header("F. VALIDITY RANGE CHECK")

v = obs[TARGET]
print(f"min={v.min():.3f}  max={v.max():.3f}")
print(f"Values outside [0, 100]        : {int(((v < 0) | (v > 100)).sum())}")
print(f"Non-finite values              : {int((~np.isfinite(v)).sum())}")
print(f"Employment + Unemployment ~100 : ")
chk = (obs[TARGET] + obs["Unemployment Rate Both sexes"])
print(f"   sum min={chk.min():.4f}  max={chk.max():.4f}  "
      f"max |dev from 100| = {(chk - 100).abs().max():.4f}")

# ------------------------------------------------------------- frequency ----
header("G. FREQUENCY AUDIT — gaps between consecutive OBSERVED dates")

d = obs["Date"].reset_index(drop=True)
gap = (d.dt.year * 12 + d.dt.month).diff()
gap_tbl = gap.value_counts().sort_index().rename_axis("gap_months").to_frame("count")
print(gap_tbl.to_string())

print("\nGap sequence by year (months between consecutive observations):")
tmp = pd.DataFrame({"Date": d, "gap": gap})
tmp["Year"] = tmp["Date"].dt.year
for yr, g in tmp.groupby("Year"):
    seq = ",".join("-" if pd.isna(x) else str(int(x)) for x in g["gap"])
    mths = ",".join(g["Date"].dt.strftime("%b"))
    print(f"  {yr}: n={len(g):2d}  months=[{mths}]  gaps=[{seq}]")

# --------------------------------------------- longest continuous monthly ---
header("H. LONGEST CONTINUOUS MONTHLY RUN (gap == 1 throughout)")

run_id = (gap != 1).cumsum()
runs = []
for rid, idx in run_id.groupby(run_id).groups.items():
    idx = list(idx)
    runs.append((d.iloc[idx[0]], d.iloc[idx[-1]], len(idx)))
runs_df = pd.DataFrame(runs, columns=["start", "end", "n"]).sort_values("n", ascending=False)
print("All contiguous monthly runs (length >= 2), longest first:")
print(runs_df[runs_df["n"] >= 2]
      .assign(start=lambda x: x["start"].dt.strftime("%Y-%m"),
              end=lambda x: x["end"].dt.strftime("%Y-%m"))
      .to_string(index=False))

best = runs_df.iloc[0]
print(f"\nLongest run: {best['start']:%Y-%m} .. {best['end']:%Y-%m}  n={best['n']}")
print(f"Runs to end of data? {best['end'] == d.max()}")

# Does the longest run reach the end of the dataset?
tail_runs = runs_df[runs_df["end"] == d.max()]
print("\nRun(s) that terminate at the last observation:")
print(tail_runs.assign(start=lambda x: x["start"].dt.strftime("%Y-%m"),
                       end=lambda x: x["end"].dt.strftime("%Y-%m")).to_string(index=False))

# -------------------------------------------------- quarterly comparability --
header("I. QUARTERLY SURVEY-ROUND STRUCTURE")

obs2 = obs.copy()
obs2["m"] = obs2["Date"].dt.month
print("Observation count by calendar month across whole history:")
print(obs2["m"].value_counts().sort_index()
      .rename(index=lambda i: pd.Timestamp(2000, i, 1).strftime("%b")).to_string())

ROUNDS = [1, 4, 7, 10]  # Jan / Apr / Jul / Oct classic LFS rounds
print(f"\nClassic PSA LFS survey rounds = {ROUNDS} (Jan, Apr, Jul, Oct)")
q = obs2[obs2["m"].isin(ROUNDS)].sort_values("Date").reset_index(drop=True)
print(f"Observations falling on those rounds: {len(q)}")
qgap = (q["Date"].dt.year * 12 + q["Date"].dt.month).diff()
print("Gaps between consecutive round observations:")
print(qgap.value_counts().sort_index().rename_axis("gap_months").to_frame("count").to_string())
print(f"Span: {q['Date'].min():%Y-%m} .. {q['Date'].max():%Y-%m}")

bad = q.loc[qgap.notna() & (qgap != 3), "Date"]
print(f"Breaks in the 3-month cadence: {len(bad)}")
if len(bad):
    print("  at:", ", ".join(bad.dt.strftime("%Y-%m")))

# Longest unbroken quarterly-round run
qrun = (qgap != 3).cumsum()
qruns = []
for rid, idx in qrun.groupby(qrun).groups.items():
    idx = list(idx)
    qruns.append((q["Date"].iloc[idx[0]], q["Date"].iloc[idx[-1]], len(idx)))
qruns_df = pd.DataFrame(qruns, columns=["start", "end", "n"]).sort_values("n", ascending=False)
print("\nContiguous quarterly-round runs:")
print(qruns_df.assign(start=lambda x: x["start"].dt.strftime("%Y-%m"),
                      end=lambda x: x["end"].dt.strftime("%Y-%m")).to_string(index=False))

# Which years lack a full set of 4 rounds?
per_year = obs2[obs2["m"].isin(ROUNDS)].groupby(obs2["Date"].dt.year)["m"].apply(
    lambda s: sorted(s.tolist()))
print("\nRounds present per year:")
for yr, ms in per_year.items():
    names = ",".join(pd.Timestamp(2000, m, 1).strftime("%b") for m in ms)
    flag = "" if len(ms) == 4 else "   <-- incomplete"
    print(f"  {yr}: [{names}]{flag}")

# ---------------------------------------------------------- descriptives ----
header("J. DESCRIPTIVE OVERVIEW OF TARGET (all observed values)")

print(v.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).round(3).to_string())

print("\nBy era (descriptive only, no regime claim):")
eras = {
    "2005-2019 (pre-COVID)": (obs2["Date"] < "2020-01-01"),
    "2020-2021 (COVID/recovery)": (obs2["Date"] >= "2020-01-01") & (obs2["Date"] < "2022-01-01"),
    "2022-2026 (post)": (obs2["Date"] >= "2022-01-01"),
}
rows = []
for name, m in eras.items():
    s = obs2.loc[m, TARGET]
    rows.append(dict(Era=name, n=len(s), mean=round(s.mean(), 3), sd=round(s.std(), 3),
                     min=round(s.min(), 3), max=round(s.max(), 3)))
print(pd.DataFrame(rows).to_string(index=False))

print("\n10 lowest observed values:")
print(obs2.nsmallest(10, TARGET)[["Date", TARGET]]
      .assign(Date=lambda x: x["Date"].dt.strftime("%Y-%m")).to_string(index=False))
print("\n10 highest observed values:")
print(obs2.nlargest(10, TARGET)[["Date", TARGET]]
      .assign(Date=lambda x: x["Date"].dt.strftime("%Y-%m")).to_string(index=False))

# -------------------------------------------------- outliers (whole series) --
header("K. OUTLIER SCREEN (IQR fence, whole observed series — context only)")

q1, q3 = v.quantile([0.25, 0.75])
iqr = q3 - q1
lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
print(f"Q1={q1:.3f} Q3={q3:.3f} IQR={iqr:.3f}  fences=[{lo:.3f}, {hi:.3f}]")
out = obs2[(obs2[TARGET] < lo) | (obs2[TARGET] > hi)]
print(f"Flagged points: {len(out)}")
if len(out):
    print(out[["Date", TARGET]].assign(Date=lambda x: x["Date"].dt.strftime("%Y-%m"))
          .to_string(index=False))

header("L. ANNUAL ROWS — availability check")
print(f"Annual rows total          : {len(annual_rows)}")
print(f"Annual rows with a value   : {int(annual_rows[TARGET].notna().sum())}")
print(f"Annual value year range    : {annual_rows.loc[annual_rows[TARGET].notna(), 'Year'].min()}"
      f" .. {annual_rows.loc[annual_rows[TARGET].notna(), 'Year'].max()}")

print("\nDONE.")
