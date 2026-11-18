"""An example analysis for TWO ALREADY-HARMONIZED annual series.

Supply tidy annual data with exactly one row per year and a numeric 'value' column:
  data/iceland_matched.csv:  Year,value
  data/sweden_matched.csv:   Tid,value

Use the real data downloaded with pxweb_client.py and filter/aggregate to
matching measures first. In particular, DO NOT reuse the preview CSVs from
01_explore_and_fetch.py: those choose arbitrary first-category slices.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt
import pandas as pd
from pxweb_client import comparable_time_series

p = Path("data")
ice_path = p / "iceland_matched.csv"
swe_path = p / "sweden_matched.csv"
if not (ice_path.exists() and swe_path.exists()):
    raise SystemExit(
        "Prepare data/iceland_matched.csv (Year,value) and "
        "data/sweden_matched.csv (Tid,value) with the SAME metric and time definition. "
        "See README.md."
    )

ice = pd.read_csv(ice_path, dtype={"Year": str})
swe = pd.read_csv(swe_path, dtype={"Tid": str})
joined = comparable_time_series(ice, swe, "Year", "Tid", period_to_year=True)
if len(joined) < 4:
    raise ValueError("At least four overlapping annual observations are recommended")
print("Years in common:", joined["period"].min(), "to", joined["period"].max())

# Example for population STOCKS or other positive level series:
for country in ("Iceland", "Sweden"):
    joined[country + "_yoy"] = joined[country].pct_change() * 100

r_levels = joined[["Iceland", "Sweden"]].corr().iloc[0, 1]
r_growth = joined[["Iceland_yoy", "Sweden_yoy"]].corr().iloc[0, 1]
print(f"Level correlation: {r_levels:.3f} (typically dominated by shared trends)")
print(f"YoY percentage-change correlation: {r_growth:.3f} (descriptive, not causal)")

ax = joined.plot(x="period", y=["Iceland_yoy", "Sweden_yoy"], marker="o", figsize=(9, 5))
ax.set(title="Year-over-year change — comparable indicator", xlabel="Year", ylabel="Change (%)")
ax.grid(alpha=0.25)
plt.tight_layout()
p.mkdir(exist_ok=True)
plt.savefig(p / "growth_comparison.png", dpi=170)
joined.to_csv(p / "matched_analysis.csv", index=False)
print("Saved data/growth_comparison.png and data/matched_analysis.csv")
