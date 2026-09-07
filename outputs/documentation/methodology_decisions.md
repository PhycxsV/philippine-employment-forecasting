# Methodology Decision Record

Generated from `MBAN625_Employment_Forecasting.ipynb` on 2026-09-07 03:03.
The notebook is the full analysis. This file is a compact decision log only.

## Target variable: Employment Rate (both sexes)

- **Evidence:** Complete for all 129 observed months; Employment + Unemployment = 100 with maximum deviation 0.000000
- **Rationale:** Most directly connected to national employment conditions relevant to clinics offering PEME services
- **Rejected alternative:** Unemployment Rate (exact arithmetic complement, no additional information); Participation Rate (measures labour-market entry, not employment)

## Exclude the 22 annual aggregate rows

- **Evidence:** Section 3.2: 22 rows labelled 'Annual' alongside 264 calendar-month rows
- **Rationale:** An annual summary is not a survey observation; retaining these rows would insert artificial data points between December and January of each year
- **Rejected alternative:** Retaining them as observations, which would corrupt all temporal computation

## Do not impute the 126 interior missing months

- **Evidence:** Section 3.5: absences are identical across all 12 indicators, indicating months in which the survey was not conducted
- **Rationale:** These are not failed measurements but months without a survey; imputation would fabricate over a decade of observations and corrupt the autocorrelation and variance evidence used for model selection
- **Rejected alternative:** Linear or seasonal interpolation to a continuous monthly series

## Retain the April 2020 outlier

- **Evidence:** Section 3.8: 82.395%, modified z-score -5.92, the only flagged observation
- **Rationale:** A genuine survey result recording the COVID-19 lockdown contraction; removing it would represent the series as far more stable than it is and understate genuine forecast risk
- **Rejected alternative:** Deletion or winsorisation of the pandemic trough

## Build the quarterly long-history series by selection, not averaging

- **Evidence:** Section 4.4: Jan/Apr/Jul/Oct occur 21-22 times each; selecting them yields 85 observations with zero cadence breaks
- **Rationale:** Averaging monthly observations into quarterly means would introduce an artificial reduction in variance exactly at the frequency transition, creating a processing artefact that could be mistaken for an economic change
- **Rejected alternative:** Three-month averaging of the monthly era

## Fix the recovery cut-point by a pre-specified rule

- **Evidence:** Section 9.2: pre-COVID reference 93.2786%; 10 months below it, forming a single contiguous leading block ending Oct 2021
- **Rationale:** The rule uses only pre-pandemic information and was fixed before any model was estimated, so the trimmed window cannot have been chosen to suit a result
- **Rejected alternative:** Selecting the cut-point by comparing forecast accuracy across candidate start dates

## Calibrate seasonal strength by permutation rather than by threshold

- **Evidence:** Section 10.4.1: observed 0.709 against a null mean of 0.226 and 95th percentile 0.473; permutation p < 0.001
- **Rationale:** The 0.64 convention was not established for 5-year samples and falls inside the null distribution here; Kruskal-Wallis (p = 0.059) has minimal power at ~5 observations per calendar month
- **Rejected alternative:** Accepting the 0.64 rule of thumb, or accepting the non-significant Kruskal-Wallis result, which imply opposite modelling decisions

## Differencing order d = 1 for ARIMA-family models

- **Evidence:** Section 10.2: ADF and KPSS agree on non-stationarity in levels (p = 0.215 / 0.010) and on stationarity after first differencing (p = 0.021 / 0.100)
- **Rationale:** Determined by evidence from two tests with opposing nulls, not by convention or by tuning
- **Rejected alternative:** Modelling levels directly, or applying seasonal differencing, which would consume 12 observations from a 54-month training set

## Final model: SARIMA(0, 1, 1)(1, 0, 0, 12)

- **Evidence:** Holdout MAE 0.8311 pp (rank 1 of 8); rolling-origin MAE 0.5714 pp (rank 2 of 8); Spearman agreement between schemes 0.976
- **Rationale:** Lowest rolling-origin error among models that beat the naive benchmark and supply uncertainty intervals; all residual diagnostics passed
- **Rejected alternative:** Seasonal naive, marginally better on rolling origin (by 0.042 pp) but supplying no uncertainty interval; Holt-Winters, over-parameterised for 54 training observations

## Report the forecast on the full monthly window (View B)

- **Evidence:** Section 21: forecasts from the two windows differ by at most 0.017 pp, against a one-month interval half-width of 1.049 pp
- **Rationale:** Uses all 66 available monthly observations, and the sensitivity analysis shows the alternative window would not change any operational conclusion
- **Rejected alternative:** View B-T, cleaner in composition but 10 observations shorter and statistically inconclusive when differenced

## Use the current regime as the Employment Condition reference

- **Evidence:** Section 22: current-regime median 95.51% against full-history median 93.43%, consistent with the 1.91 pp level shift verified on equally spaced data in Section 9.1
- **Rationale:** A reference spanning a superseded regime would classify nearly every forecast into the same band and could not discriminate between the conditions that actually vary
- **Rejected alternative:** The full 2005-2026 distribution, retained and reported alongside as secondary context rather than discarded

## Use an empirical error range for Employment Condition confidence

- **Evidence:** Section 18: model interval width is 1.5x to 2.9x the observed out-of-sample error spread across all horizons
- **Rationale:** The model's analytic intervals are conservative and span several activity bands; a range built from errors the model genuinely incurred reflects observed performance rather than an assumption of correct specification
- **Rejected alternative:** Using the 95% model interval alone, which would render every band assignment uncertain and the signal uninformative
