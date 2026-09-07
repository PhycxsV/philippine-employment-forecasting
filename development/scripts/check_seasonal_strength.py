"""
Development check (NOT analytical evidence).

Question: the STL seasonal-strength measure returned ~0.71 for View B, which a
common rule of thumb would call "strong". But STL fits a flexible, time-varying
seasonal component, and with only ~5.5 annual cycles that component can absorb
ordinary noise. So: what seasonal strength does the SAME procedure produce on
data that provably has NO month-of-year effect?

Calibration by permutation: repeatedly shuffle the detrended values across
months (destroying any month effect while preserving the trend and the marginal
distribution), recompute seasonal strength, and compare the observed value with
that null distribution.

If material, this must be reproduced inside the notebook.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "data" / "Rates Key Employment Indicators- April 2005 to June 2026.csv"
TARGET = "Employment Rate Both sexes"
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"], start=1)}

df = pd.read_csv(CSV, skiprows=1, na_values=["."], encoding="utf-8-sig")
df = df[df["Month"] != "Annual"].copy()
df["Date"] = pd.to_datetime(dict(year=df["Year"], month=df["Month"].map(MONTHS), day=1))
obs = df.dropna(subset=[TARGET]).sort_values("Date").reset_index(drop=True)
s = pd.Series(obs[TARGET].values, index=pd.DatetimeIndex(obs["Date"]))
series_b = s["2021-01-01":].asfreq("MS")

PERIOD = 12
rng = np.random.default_rng(20260906)


def seasonal_strength(series, period=PERIOD, robust=True):
    res = STL(series, period=period, robust=robust).fit()
    var_r = np.var(res.resid, ddof=1)
    var_sr = np.var(res.seasonal + res.resid, ddof=1)
    return max(0.0, 1 - var_r / var_sr), res


obs_strength, res = seasonal_strength(series_b)
amplitude = float(res.seasonal.max() - res.seasonal.min())

print("=" * 70)
print("OBSERVED")
print("=" * 70)
print(f"n                     : {len(series_b)}  ({len(series_b)/12:.2f} annual cycles)")
print(f"Seasonal strength     : {obs_strength:.4f}")
print(f"Seasonal amplitude    : {amplitude:.4f} pp")
print(f"Series SD             : {series_b.std():.4f} pp")
print(f"Amplitude / series SD : {amplitude/series_b.std():.3f}")

# Average seasonal profile (how consistent is the month pattern year to year?)
seas = res.seasonal
prof = seas.groupby(seas.index.month).agg(["mean", "std"])
prof.index = [pd.Timestamp(2000, m, 1).strftime("%b") for m in prof.index]
print("\nSTL seasonal component by calendar month (mean +/- SD across years):")
print(prof.round(3).to_string())

# ---------------------------------------------------------------- null dist --
print("\n" + "=" * 70)
print("PERMUTATION NULL  (month labels destroyed, trend preserved)")
print("=" * 70)

trend = res.trend
detrended = (series_b - trend).values

N_PERM = 500
null_strengths = np.empty(N_PERM)
for i in range(N_PERM):
    shuffled = rng.permutation(detrended)
    fake = pd.Series(trend.values + shuffled, index=series_b.index)
    null_strengths[i], _ = seasonal_strength(fake)

pct = (null_strengths >= obs_strength).mean()
print(f"Permutations              : {N_PERM}")
print(f"Null mean strength        : {null_strengths.mean():.4f}")
print(f"Null median strength      : {np.median(null_strengths):.4f}")
print(f"Null 90th percentile      : {np.percentile(null_strengths, 90):.4f}")
print(f"Null 95th percentile      : {np.percentile(null_strengths, 95):.4f}")
print(f"Observed strength         : {obs_strength:.4f}")
print(f"Permutation p-value       : {pct:.4f}")
print()
if pct > 0.05:
    print(">>> The observed seasonal strength is NOT unusual for data with no month")
    print(">>> effect at this sample size. The 0.64 'strong seasonality' rule of thumb")
    print(">>> is MISLEADING here: STL manufactures a seasonal component from noise.")
else:
    print(">>> The observed seasonal strength exceeds what noise produces at this")
    print(">>> sample size, supporting a genuine month-of-year effect.")

# Sanity check: same calibration on the trimmed window
series_t = series_b["2021-11-01":]
obs_t, _ = seasonal_strength(series_t)
trend_t = STL(series_t, period=PERIOD, robust=True).fit().trend
detr_t = (series_t - trend_t).values
null_t = np.empty(300)
for i in range(300):
    fake = pd.Series(trend_t.values + rng.permutation(detr_t), index=series_t.index)
    null_t[i], _ = seasonal_strength(fake)
print(f"\nTrimmed window (n={len(series_t)}): observed {obs_t:.4f}, "
      f"null mean {null_t.mean():.4f}, perm p = {(null_t >= obs_t).mean():.4f}")
