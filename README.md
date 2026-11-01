# Ad Campaign Funnel & Bidding Strategy A/B Test Analysis

Analyzes a real 40-day Facebook Ads A/B test comparing two bidding strategies — **Maximum Bidding**
(control) vs **Average Bidding** (test) — using the full funnel (Impression → Click → Purchase →
Earning) and proper statistical significance testing.

## What this project does
- Builds funnel metrics: CTR (Impression→Click), CVR (Click→Purchase), RPM (revenue per 1,000 impressions)
- Visualizes the cumulative funnel, daily distributions, and funnel-efficiency (CTR vs CVR) by strategy
- Tests normality (Shapiro-Wilk) to select the correct significance test per metric
- Runs independent t-tests / Mann-Whitney U tests on Purchases, Earnings, CTR, and CVR
- Translates statistical results into a business recommendation

## Key finding
Average Bidding converts less top-of-funnel traffic (lower CTR) but converts it far more efficiently
(higher CVR), producing a statistically significant **+31.8% lift in revenue** (p < 0.001) even though
the difference in raw purchase counts alone was not statistically significant. Recommendation: switch
to Average Bidding.

## Files
- `Ad_Campaign_Bidding_AB_Test_Analysis.ipynb` — full notebook with analysis, charts, and write-up
- `analysis.py` — script version of the same analysis
- `ab_testing.xlsx` — source dataset (Control/Test sheets, 40 daily observations each)
- `chart_funnel.png`, `chart_distributions.png`, `chart_ctr_cvr.png` — exported visualizations
- `summary_metrics.csv`, `funnel_totals.csv`, `significance_results.csv` — exported result tables

## Dataset
Public dataset from [ugursaricam/AB_testing_with_python](https://github.com/ugursaricam/AB_testing_with_python)
(Impression, Click, Purchase, Earning; Control = Maximum Bidding, Test = Average Bidding).

## Tools
Python, Pandas, NumPy, SciPy (Shapiro-Wilk, Levene's test, t-test, Mann-Whitney U), Matplotlib, Jupyter.

## How to run
```bash
pip install pandas numpy scipy matplotlib openpyxl jupyter
jupyter notebook Ad_Campaign_Bidding_AB_Test_Analysis.ipynb
```
