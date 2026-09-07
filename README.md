# Forecasting Philippine Employment Conditions for PEME Operational Planning

This project forecasts the Philippine Employment Rate using official Philippine Statistics Authority (PSA) Labour Force Survey data and translates the forecast into an external planning signal for clinics offering Pre-Employment Medical Examination (PEME) services.

The model forecasts **Employment Rate**. It does **not** directly forecast PEME demand, patient volume, inventory need, staffing requirements, or clinic revenue.

---

## Business Problem

Clinics that provide PEME services operate in an environment where national hiring conditions can influence examination activity, but clinic-level demand is not observed in public macroeconomic data. Managers still need an external view of whether employment conditions are likely to soften, hold, or firm over the next several months.

The research question is:

> What is the expected future trend in the Philippine employment rate, and how can that forecast support operational planning attention for clinics offering PEME services?

National employment conditions may provide useful external context because stronger employment is consistent with broader hiring activity, and PEME is often required before engagement. That link is indirect. The forecast supports **attention**; clinic records support **action**.

---

## Dataset

| Attribute | Detail |
| --- | --- |
| Source organisation | Philippine Statistics Authority (PSA) |
| Source database | OpenSTAT — Labor Force Survey (LFS) |
| Target variable | Employment Rate (both sexes) |
| Observed survey months | 129 |
| Calendar span | April 2005 – June 2026 |
| Primary monthly modelling window | January 2021 – June 2026 (n = 66) |
| Quarterly robustness series | April 2005 – April 2026 (n = 85) |

Data-quality checks found no true missing measurements, no duplicated survey dates, and Employment Rate + Unemployment Rate summing to 100% for all observations. The main complication was structural rather than corrupt: observation frequency changed over time.

Older history followed a quarterly survey schedule (typically January, April, July, October). Continuous monthly reporting began in January 2021. Unsurveyed months were **not** interpolated and treated as real observations. Mixing quarterly and monthly points into one equally spaced forecasting series would have produced inconsistent lag and horizon meanings.

---

## Analytical Challenge

The dataset required careful time-series preparation before modelling:

- Changing observation frequency (quarterly, then monthly)
- Unequal calendar spacing across the full history
- Distinguishing unsurveyed months from failed measurements
- A large COVID-era disruption (April 2020 Employment Rate = 82.395%) and post-recovery level shift
- Preservation of temporal order to avoid data leakage
- A short continuous monthly sample (about 5.5 years), which limited model complexity

These constraints shaped window design, candidate selection, and validation. The analysis was not limited to fitting a single SARIMA model to an unexamined CSV file.

---

## Analytical Approach

1. Data acquisition and validation  
2. Data-quality audit  
3. Time-index and frequency assessment  
4. Exploratory data analysis  
5. Stationarity and autocorrelation analysis  
6. Seasonality assessment (including permutation calibration)  
7. Baseline forecasting  
8. Candidate model development  
9. Chronological holdout validation  
10. Rolling-origin validation  
11. Residual diagnostics  
12. Final forecasting  
13. Recovery-window sensitivity analysis  
14. Consistently sampled quarterly robustness analysis  
15. Business-signal interpretation (Employment Condition and Operational Attention)

---

## Forecasting Models

Models evaluated on the monthly series:

| Family | Model |
| --- | --- |
| Benchmark | Naive (random walk) |
| Benchmark | Seasonal naive |
| Benchmark | Random walk with drift |
| Exponential smoothing | Simple exponential smoothing (SES) |
| Exponential smoothing | Holt (damped trend) |
| Exponential smoothing | Holt-Winters (damped, additive) |
| ARIMA | ARIMA(0, 1, 1) |
| SARIMA | SARIMA(0, 1, 1)(1, 0, 0)[12] |

**Final selected model:** `SARIMA(0, 1, 1)(1, 0, 0)[12]`

Selection used more than one metric. On the 12-month chronological holdout, SARIMA achieved the lowest MAE (0.831 pp), about 19.5% better than the naive benchmark (1.032 pp). Under rolling-origin validation across 13 origins, **seasonal naive** attained a slightly lower MAE (0.529 pp vs 0.571 pp for SARIMA). Seasonal naive does not supply forecast intervals. SARIMA was selected as the reported model because it ranked first on holdout accuracy, remained close under rolling-origin validation, beat the naive benchmark under both schemes, and provided uncertainty intervals needed for the planning signal.

---

## Model Evaluation

Evaluation respected chronological order. Random train/test shuffling is inappropriate for this series because it would allow future information to enter estimation.

| Design element | Specification |
| --- | --- |
| Holdout | Final 12 months (July 2025 – June 2026) |
| Training | Preceding 54 monthly observations |
| Secondary check | Expanding-window rolling origin (13 origins, horizons 1–12) |
| Metrics | MAE, RMSE, MAPE, relative MAE vs naive |
| Residual checks | Ljung-Box, residual mean, Jarque-Bera, ARCH-LM, Levene |

### Holdout comparison (selected metrics)

| Rank | Model | MAE | RMSE | MAPE | Beats naive |
| ---: | --- | ---: | ---: | ---: | --- |
| 1 | SARIMA(0, 1, 1)(1, 0, 0)[12] | 0.831 | 0.928 | 0.875 | Yes |
| 2 | Seasonal naive | 0.910 | 1.005 | 0.957 | Yes |
| 3 | SES (level only) | 0.937 | 1.083 | 0.987 | Yes |
| 4 | ARIMA(0, 1, 1) | 0.938 | 1.084 | 0.988 | Yes |
| 5 | Naive (random walk) | 1.032 | 1.169 | 1.087 | — |

Final residual diagnostics for the selected model did not identify major remaining autocorrelation, bias, or variance instability at the 0.05 significance level. Short-sample results are still interpreted cautiously.

---

## Final Forecast

Latest observed Employment Rate: **95.140%** (June 2026).  
Reported horizon: **July 2026 – December 2026** (6 months).  
Mean forecast level: **94.778%** (**−0.362** percentage points vs the latest observation).  
Overall direction: modest softening (falling), not a sharp contraction.

| Period | Forecast | Lower Bound | Upper Bound |
| --- | ---: | ---: | ---: |
| Jul 2026 | 94.264 | 93.215 | 95.313 |
| Aug 2026 | 95.105 | 93.942 | 96.268 |
| Sep 2026 | 95.168 | 93.902 | 96.435 |
| Oct 2026 | 94.477 | 93.115 | 95.839 |
| Nov 2026 | 94.828 | 93.376 | 96.280 |
| Dec 2026 | 94.828 | 93.292 | 96.364 |

Forecast intervals widen with horizon. Analytic 95% intervals are conservative relative to observed out-of-sample error, so band confidence for the planning signal also uses an empirical error range from rolling-origin validation.

---

## Robustness and Sensitivity

**Recovery-window sensitivity.** A trimmed monthly window that excluded the early COVID-recovery months was compared with the full monthly window. Month-by-month forecast gaps were at most **0.017** percentage points, well below one-month forecast uncertainty. Window choice did not materially change the operational reading.

**Quarterly robustness.** A consistently sampled quarterly series (View C, n = 85) was modelled separately with ARIMA(0, 1, 1). Both monthly and quarterly forecasts pointed in a falling direction, with a level gap of **0.214** percentage points. The long history did not contradict the monthly conclusion; because the series partially overlaps the monthly era, the check is treated as absence of contradiction rather than fully independent confirmation.

---

## Business Interpretation

Two separate readings are produced from the forecast:

| Layer | Labels | Role |
| --- | --- | --- |
| Employment Condition | Subdued, Below Normal, Above Normal, Elevated | Statistical position of Employment Rate vs recent norms |
| Operational Attention | LOW, NORMAL, ELEVATED, HIGH PRECAUTION | External planning cue for the clinic |

For July–December 2026, the dominant reading under the current-regime reference is **Subdued** Employment Condition with Operational Attention **LOW**; August–September classify as **Below Normal** / **NORMAL** and are uncertain under the empirical error range.

Working rule:

> The forecast supports attention; clinic records support action.

The model does **not** directly predict PEME demand, PEME patient volume, inventory requirements, reorder quantities, staffing requirements, clinic revenue, or hiring volume. Operational decisions still require internal information such as historical PEME volume, inventory consumption, current inventory, staffing capacity, equipment readiness, and supplier lead times.

---

## Tools and Technologies

- Python  
- Jupyter Notebook  
- pandas  
- NumPy  
- Matplotlib  
- SciPy  
- statsmodels  

---

## Key Skills Demonstrated

- Data cleaning and validation  
- Exploratory data analysis  
- Mixed-frequency time-series preparation  
- Statistical diagnostics (stationarity, autocorrelation, seasonality)  
- Univariate forecasting  
- Chronological and rolling-origin validation  
- Forecast error evaluation  
- Residual diagnostics  
- Sensitivity and robustness analysis  
- Cautious business interpretation  
- Reproducible notebook workflow  

---

## Repository Structure

```text
philippine-employment-forecasting/
├── README.md
├── MBAN625_Employment_Forecasting.ipynb
├── data/                  # local PSA extract used by the notebook
├── outputs/               # regenerated tables and figures after Run All
└── development/           # optional exploratory scripts (not required to run the analysis)
```

The complete analysis lives in `MBAN625_Employment_Forecasting.ipynb`. Supporting `outputs/` artifacts are produced when the notebook is executed end to end.

---

## Reproducibility

The notebook reads a local CSV extract placed under `data/`:

`Rates Key Employment Indicators- April 2005 to June 2026.csv`

Data are attributed to the Philippine Statistics Authority (PSA) OpenSTAT Labor Force Survey. The notebook does **not** download PSA data automatically.

To reproduce:

1. Clone the repository.  
2. Place the PSA CSV in `data/` using the filename expected by the notebook (or update the path if using a locally renamed copy).  
3. Install Python packages used by the notebook (`pandas`, `numpy`, `matplotlib`, `scipy`, `statsmodels`, and Jupyter).  
4. Open `MBAN625_Employment_Forecasting.ipynb` from the project root.  
5. Restart Kernel and Run All.

---

## Data Attribution

Employment indicators are published by the **Philippine Statistics Authority (PSA)** through **OpenSTAT (Labor Force Survey)**. This project analyzes publicly released aggregate statistics and does not claim ownership of PSA data. Users should consult PSA for current access terms and the most recent releases.

---

## Limitations

- Employment Rate is not equivalent to hiring volume or PEME demand.  
- National conditions may not represent an individual clinic or local market.  
- The continuous monthly modelling window is relatively short (n = 66).  
- Forecast uncertainty increases with horizon.  
- Clinic-level operational data are not available in this dataset.  
- Univariate models cannot anticipate major external shocks on the scale of April 2020.

---

## Potential Extension

Future work could combine the employment forecast with clinic-level data such as historical PEME volume, inventory consumption, staffing, supplier lead times, equipment capacity, and operational capacity. That integration could support more direct clinic-level demand and operations forecasting. It is not implemented in this repository.
