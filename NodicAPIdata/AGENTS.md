# AGENTS.md — Nordic Statistical Data API Project

## Project purpose

Build a **reusable, easy-to-learn Python package** that retrieves official statistics from multiple national statistical offices and returns clean, analysis-ready `pandas.DataFrame` objects. The primary way to use the package is from **Jupyter notebooks**.

The long-term goal is to compare indicators across countries, explore trends and correlations, and create high-quality visualizations. **For this first milestone, focus on reliable API access, table discovery, metadata exploration, and data retrieval — not cross-country statistical analysis or dashboards yet.**

I am using this project to improve my own Python/API skills. Favor understandable code, examples, helpful error messages, and short explanations over clever abstractions. The package should be useful in real work, not just a demonstration.

## Existing starting point — inspect before modifying

I will provide the contents of `nordic_pxweb_multicountry.zip` in this Git repository. The starter ZIP contains:

- `pxweb_client.py` — PxWeb v1 and v2 clients, plus a JSON-stat-to-DataFrame converter.
- `sources.py` — registry of national/statistical sources and a `client_for()` factory.
- `denmark_client.py` — separate StatBank Denmark API adapter.
- `requirements.txt` — dependencies.
- `tutorial.ipynb` — an existing learning notebook.
- `examples/01_explore_and_fetch.py` and `examples/02_analyse_comparable_series.py`.
- `tests/test_client.py` and `tests/test_sources.py`.
- `README.md` and `MULTICOUNTRY.md`.

**First inspect the actual repository and run its existing tests.** The archive may be extracted into a nested folder; use the existing files, avoid duplicating the project, and reorganize only if it clearly improves maintainability. Preserve working behavior and update all imports/tests/examples when moving files.

The earlier starter was tested mainly with mocked/local responses. **Do not assume all registered live API endpoints, query parameters, and response formats are correct until verified.**

## Scope and priority

### Milestone 1 — make the API package work end to end

Implement and verify, in this order:

1. **Installable Python package.** Use a conventional `src/` layout and a `pyproject.toml` so notebooks and scripts can `import nordicstats` without `sys.path` hacks. Support Python 3.10+. Include clear setup instructions for Windows, macOS, and Linux. Prefer `pip install -e '.[dev,notebook]'` (or an equivalent documented command).
2. **Core API adapters.** Refine the existing PxWeb v1, PxWeb v2, and Denmark StatBank adapters. These have different request semantics; do not force incorrect common requests onto them.
3. **Reliable discovery and inspection.** Users must be able to list sources, find/browse tables, inspect table metadata, list variables, and inspect variable codes/labels **before** choosing data to download.
4. **Easy, controlled fetching.** Support explicit category-code selections, small preview selections, returned tidy DataFrames, and useful errors when a selection is invalid or too large.
5. **Notebook-driven walkthrough.** A fresh notebook should work from top to bottom in a clean environment and demonstrate discovery -> metadata -> selection -> fetch -> inspect -> save.
6. **Automated tests plus optional live smoke tests.** Unit tests should run offline; live integration tests should be clearly separated and run only when explicitly enabled.

Start with **Iceland, Sweden, Norway, Finland, and Denmark** for real end-to-end verification. Once these work, check the other existing configured PxWeb sources, including Estonia, Latvia, Greenland, Faroe Islands, Åland, and Slovenia. Switzerland and the Nordic Statistics Database may require special handling. Do not implement Eurostat, OECD, or Lithuania adapters during Milestone 1; keep them registered as planned/unavailable with honest capability reporting.

### Out of scope for Milestone 1

- Country-level comparisons, correlations, predictive modeling, dashboards, or a Streamlit app.
- Automatically matching different countries' statistical definitions.
- Downloading entire national databases or building a full historical catalogue by default.
- A large CLI or web application.
- Authentication systems or cloud infrastructure.

If you notice issues in these areas, document them under **Later milestones** rather than expanding the initial build.

## Desired notebook-facing API

Aim for this **simple public interface**. Adapt names if necessary, but document the final consistent interface and keep it stable:

```python
import nordicstats as ns

# What is available?
ns.list_sources()                          # DataFrame: key, name, country, API family, status
client = ns.client_for("sweden")           # Also iceland, norway, finland, denmark

# Find a table (v2 has a search API; v1 can browse directories)
tables = client.search("population", limit=10)   # If supported
# or
folders = client.browse()                  # If supported

# Inspect a selected table
meta = client.metadata("TABLE_ID_OR_PATH")
client.variables("TABLE_ID_OR_PATH")     # DataFrame with code, label, dimensions, time flag
client.value_codes("TABLE_ID_OR_PATH", "VARIABLE_CODE")

# Preview a SMALL, defensible subset — not necessarily an analytical total
selection = client.example_selection("TABLE_ID_OR_PATH", last_n=5)
df = client.fetch("TABLE_ID_OR_PATH", selection=selection)
df.head()
```

**Important:** `client.search()` and `client.browse()` need not be supported by every API family. Prefer clear capability differences and a friendly `NotImplementedError`/documented alternative over a misleading universal method. If a unified discovery method can be implemented safely, that is a bonus, not a blocker.

For an actual query, users should be able to replace the preview selection with exact metadata-derived codes:

```python
selection = {
    "SomeDimension": ["actual_code_from_metadata"],
    "TimeDimension": ["2022", "2023", "2024"],
}
result = client.fetch("TABLE_ID_OR_PATH", selection)
```

Do **not** present the placeholder codes above as real API values. The notebook must inspect live metadata to obtain them and must not silently select the first age/sex/region code and call it a national total.

### Returned DataFrame contract

- Default to **tidy/long format**: one row per observation, a numeric `value` column, and one column per statistical dimension.
- Preserve the provider's original dimension **codes by default**; provide a clear option to use labels or a separate code-to-label mapping. Labels may depend on language and are not safe join keys.
- Preserve missing values and any available status/quality flags; do not silently convert suppressed or unavailable values to zero.
- Preserve provenance: `source_key`, `table_id/path`, API URL, retrieval time (UTC), selections, units and relevant metadata, where supplied. Use `DataFrame.attrs` and/or a structured result/metadata method; explain that `DataFrame.attrs` may not survive CSV export.
- **Do not invent common units, countries, years, frequencies, or definitions.** DataFrame normalization is not statistical harmonization.
- For large selections, validate or estimate cell counts before downloading when possible; fail with an actionable message or offer an explicitly requested chunked retrieval strategy.

## Implementation expectations

- Keep HTTP details inside adapters; notebooks should not need raw `requests.get()`/`post()` calls.
- Use `requests.Session` (or an equally simple consistent alternative), explicit timeouts, descriptive exceptions, and bounded retries/backoff that respect HTTP 429/`Retry-After` and provider limits.
- URL-encode paths and parameters correctly, especially table IDs, category values, spaces, Unicode, and country-specific database names.
- Support PxWeb **v1** (directory navigation, table metadata, POST query payload) and **v2** (table search, table metadata, GET/POST data) separately; the JSON-stat parser may be shared.
- Denmark's StatBank uses a separate API. Adapt its `subjects`, `tables`, `tableinfo`, and `data` operations without pretending it is PxWeb.
- Build robust JSON-stat / JSON-stat2 decoding: dimension order, numeric/missing cells, sparse/dense values, optional statuses, labels and metadata. Prefer a small, well-tested implementation over unnecessary dependencies.
- Keep requests scoped and reasonably small. Do not run unbounded recursion against whole catalogues or download huge datasets in tests/notebooks.
- Consider optional local response caching, especially metadata (for interactive notebook usage). It should be transparent and possible to disable/refresh; skip this if it slows down core reliability.
- No secrets or credentials in source control, no disabled TLS verification, and no unapproved paid APIs.
- Avoid hardcoded agency names in generic PxWeb classes; provenance should come from `sources.py` or the source configuration.
- Keep type hints and docstrings for the public API, and write explanatory comments for tricky format/protocol behavior.
- Use relative project paths and create output folders as needed. Ignore `.venv/`, `.ipynb_checkpoints/`, caches, and downloaded data artifacts in Git by default; keep small fixtures tracked.

## Suggested structure (adapt to the existing repository)

```text
project-root/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── .gitignore
├── src/
│   └── nordicstats/
│       ├── __init__.py
│       ├── sources.py               # source registry + client factory
│       ├── client_base.py           # shared HTTP utilities / contracts as needed
│       ├── pxweb_v1.py
│       ├── pxweb_v2.py
│       ├── statbank_dk.py
│       └── jsonstat.py              # dataset -> tidy DataFrame
├── notebooks/
│   └── 01_explore_apis.ipynb
├── examples/
│   └── 01_explore_and_fetch.py
├── tests/
│   ├── fixtures/
│   ├── test_jsonstat.py
│   ├── test_adapters.py
│   └── test_live_smoke.py          # opt-in only
└── data/                           # ignored by Git, except .gitkeep if useful
```

Moving code into `src/nordicstats` is desirable, but prioritize a **working install + import** and avoid a major rewrite for cosmetic reasons. Maintain or intentionally migrate compatibility with `from sources import client_for`, `from pxweb_client import ...`, and the existing tests/examples, documenting any breaking change.

## Validation and acceptance criteria

Milestone 1 is complete only when all of these are true:

- [ ] A clean virtual environment can install the project using instructions in the README.
- [ ] `import nordicstats` works in a notebook without manual changes to `sys.path`.
- [ ] A user can list registered data sources and see whether each is working, unverified, special, or planned.
- [ ] The public API supports real **browse/search -> metadata -> variables/codes -> fetch** workflows for Iceland, Sweden, Norway, Finland, and Denmark, subject to any explicitly documented provider limitation.
- [ ] For each core provider, there is at least one **small live smoke-test query** using a real, documented or discovered table, with the result sanity-checked (nonempty data, expected columns, reasonable values) when networking is available.
- [ ] Unit tests with fixtures/mocked HTTP cover v1/v2/Denmark request building and JSON-stat parsing, including missing values, validation errors, and wrong response formats.
- [ ] Offline `pytest` succeeds by default; live network tests are opt-in (for example `RUN_LIVE_API_TESTS=1 pytest -m live`). Live tests must not break an offline CI environment.
- [ ] The notebook contains a **runnable worked example**, using actual verified table IDs/codes, that creates a tidy DataFrame, shows `.head()`, `.info()`, and basic descriptive statistics, and optionally saves CSV/Parquet.
- [ ] README clearly explains setup, installation, quick-start code, provider differences, failure modes, rate limits, and how to add a new source.
- [ ] Existing functionality is preserved or migration steps are documented; no claim of live validation is made unless tests actually ran.

If live access is blocked in your execution environment, still complete offline testing, label integration tests **not run**, and provide the exact commands I should run locally plus any logs/errors I can share for debugging. **Never mark mocked tests as proof a live endpoint works.**

## How to work as the Codex agent

1. Read this file, inspect all existing source/test/notebook files, and summarize the current architecture and concrete risks.
2. Run the existing tests and report their actual result before changing code.
3. Propose a short plan for Milestone 1, then implement it in focused, verifiable steps. Do not ask for approval for routine refactoring that stays within scope.
4. After each meaningful change, run relevant tests; update examples/docs alongside code.
5. Run available live smoke tests carefully, with small requests and provider rate limits respected. Distinguish live verification from offline assertions.
6. Finish with a concise report: files changed, how to install/use in a notebook, tests run/passed, providers actually verified, known limitations, and next recommended task.

Prefer frequent, small Git commits with descriptive messages **if Git is initialized and committing is appropriate**; do not push to a remote or change remote/repository settings without being asked. Do not delete original work to simplify migration without preserving functionality.

## Useful official reference documentation

- PxWebApi v2 user guide: https://www.pxtools.net/PxWebApi/documentation/user-guide/
- Sweden (SCB): https://www.scb.se/en/services/open-data-api/pxwebapi/
- Iceland (Statistics Iceland): https://statice.is/publications/open-data-access/
- Norway (SSB): https://www.ssb.no/en/api/pxwebapi
- Finland (Statistics Finland): https://stat.fi/en/services/statistical-data-services/open-data-and-interfaces/interface-use-of-databases
- Denmark (StatBank): https://www.dst.dk/en/Statistik/hjaelp-til-statistikbanken/api
- Latvia (v2): https://stat.gov.lv/en/api-un-kodu-vardnicas/api-v2

Before implementing or fixing provider-specific requests, consult the **current official API docs** rather than relying only on the starter's example URLs. Different providers can deploy different API versions, limits, languages and response options.

## Later milestones (do not implement yet)

1. Harmonized indicator catalogue with country-specific table IDs, variable mappings, definitions, frequencies, units, and reference dates.
2. Cross-country comparison functions with explicit comparability checks (e.g. Iceland's 1 January vs Sweden's 31 December population definitions).
3. Reproducible analysis notebooks (growth, inflation, wages, migration, correlation); avoid causal conclusions from correlation alone.
4. High-quality Plotly/matplotlib visualizations, then possibly a Streamlit dashboard.
5. Optional Eurostat, OECD/SDMX, and Lithuania adapters after the core clients are stable.

**Guiding principle:** *First make it trivial to find a table, understand its dimensions, and get trustworthy data into pandas. Only then build comparisons.*
