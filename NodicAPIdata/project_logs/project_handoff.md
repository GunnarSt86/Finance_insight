# Project handoff — Python-first data exploration

## Background
- I'm comfortable with **Python for data analysis, calculations, and modelling**, but a beginner in frontend development and relatively new to Linux Mint.
- My learning goal is to build small, complete projects: **fetch data from APIs → clean/join/analyse/model it → present interesting findings in an attractive, interactive interface → publish the result**.
- I prefer **incremental, hands-on guidance** with explanations of where code belongs, why tools are used, and small verifiable steps. I don't want a huge finished application all at once.

## What I learned in a previous project (Weather Insights)
- Created a **React + TypeScript** app using **Vite** on Linux Mint, edited in VS Code.
- Fetched Open-Meteo weather data using `fetch` / `async` / `await`; defined TypeScript types, handled loading/errors, and calculated summary statistics.
- Built interactive charts with **Recharts** and a responsive dashboard using plain CSS; added a city dropdown.
- Organized code into `src/components/`, `src/services/`, `src/types/`, `src/utils/` (and a basic `src/models/`).
- Used **Git and GitHub** to commit/push changes; deployed through **Vercel** with automatic deployments after pushes.
- Familiar commands: `npm run dev`, `npm run lint`, `npm run build`, `git status`, `git add -A`, `git commit -m "..."`, `git push`.
- Still learning frontend architecture, JavaScript/TypeScript, Git, deployment, and Linux commands, so explain unfamiliar concepts.

## New project direction
- This is a **separate project**, oriented more toward **Python analysis first**, not a continuation of the weather dashboard.
- I want to experiment with APIs/datasets, perform exploratory data analysis, correlations and perhaps statistical/ML modelling in Python (e.g. pandas, NumPy, plotting, scikit-learn where appropriate).
- **Only after discovering something interesting**, build a polished, understandable visualization or small interactive application. The presentation technology is **not decided**: help choose between Streamlit/Plotly, React, or Python API + React based on the actual need, rather than assuming a frontend stack upfront.
- I recently renamed a folder inside my Git repository from `my-new-project/` to `NodicAPIdata/`. The GitHub repository name itself was **not** to be changed. Git showed old paths as deleted and the new folder as untracked; the recommended workflow was `git add -A`, inspect `git status`, commit, then push. **Do not assume the push or deployment has been verified.**

## Preferred next steps
1. Confirm the new project's local folder/repository state and Python environment setup (venv/dependencies, optional Jupyter notebooks).
2. Choose an accessible API and define a small research question; verify historical coverage, usage limits, authentication and data quality.
3. Fetch and inspect data in Python; keep raw retrieval separate from cleaning and analysis.
4. Explore patterns and validate them carefully (missing values, temporal alignment, correlation vs causation, leakage).
5. Once results are interesting, design an interactive visualization and decide how to publish it.
6. Commit incremental milestones with Git and document how to reproduce the analysis.

**Style of assistance:** concise steps, code snippets with exact filenames/commands, explain the new ideas, and pause at useful checkpoints for troubleshooting.
