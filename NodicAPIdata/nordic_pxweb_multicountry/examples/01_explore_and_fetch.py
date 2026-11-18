"""Run from the project folder: python examples/01_explore_and_fetch.py

This downloads two *example slices*, NOT two harmonized population totals.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pxweb_client import IcelandPxWeb, SwedenPxWeb

ICELAND_POPULATION = "Ibuar/mannfjoldi/1_yfirlit/Yfirlit_mannfjolda/MAN00101.px"
SWEDEN_POPULATION = "TAB638"

out = Path("data")
out.mkdir(exist_ok=True)
is_api, se_api = IcelandPxWeb(), SwedenPxWeb()

print("\nICELAND: browse population overview")
print(is_api.browse("Ibuar/mannfjoldi/1_yfirlit/Yfirlit_mannfjolda").head(10).to_string(index=False))
print("\nICELAND: available variables")
print(is_api.variables(ICELAND_POPULATION).to_string(index=False))
selection_is = is_api.example_selection(ICELAND_POPULATION, last_n=5)
print("Iceland selected codes:", selection_is)
ice = is_api.fetch(ICELAND_POPULATION, selection_is)
print(ice.head().to_string(index=False))
ice.to_csv(out / "iceland_example.csv", index=False)

print("\nSWEDEN: population-related tables")
print(se_api.search("population", page_size=5).to_string(index=False))
print("\nSWEDEN: available variables")
print(se_api.variables(SWEDEN_POPULATION).to_string(index=False))
selection_se = se_api.example_selection(SWEDEN_POPULATION, last_n=5)
print("Sweden selected codes:", selection_se)
swe = se_api.fetch(SWEDEN_POPULATION, selection_se)
print(swe.head().to_string(index=False))
swe.to_csv(out / "sweden_example.csv", index=False)

print("\nSaved small *illustrative* extracts in ./data/")
print("DO NOT compare them until metric/category/time definitions match.")
