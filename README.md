# FireSafe Space: Combustion Insights Dashboard

An interactive, AI-powered dashboard that **summarizes, ranks and interprets** NASA's microgravity combustion investigations (from the PSI repository) to support fire safety for human space exploration. Built for the 2026 NASA Space Apps Challenge.

**Live app:** https://firesafe-space.streamlit.app/
**Demo video:** <your YouTube link>

## The problem
NASA has years of ISS flame and fire experiments, but the data is hard to find, compare and interpret. Fire is one of the most dangerous risks in spacecraft, and future Moon habitats will likely use 30%+ oxygen, which makes materials far more flammable.

## What it does
- **Ranking:** choose a need (Moon base, spacecraft, detection, suppression, predictive modeling, Earth applications) and see investigations ranked by relevance. Weights are adjustable.
- **Summaries:** fuel, oxygen, airflow, hardware and measurements for each investigation, plus key findings.
- **Compare:** radar chart and side-by-side table of up to four investigations.
- **Insights and gaps:** highlights what the data covers and what is missing, such as partial-gravity (lunar) combustion data.
- **Ask AI:** ask questions in plain language. Answers are generated from the experiment database (Gemini, or Claude if configured), with a built-in rule-based fallback when no key is set.
- **Earth benefits:** how space fire research improved smoke detectors, firefighter gear and extinguishers.

## How ranking works
Each investigation is scored 0 to 5 on eight criteria (habitat relevance, high-oxygen coverage, material flammability, detection, suppression, predictive-model data, Earth applications, partial-gravity relevance). The ranking is the weighted average for the selected need. The scores are our own editable judgments based on NASA's descriptions, not official NASA numbers.

## Data and limitations
- 14 investigations from NASA's combustion science fact sheets and the PSI challenge resources. **8 are verified** against NASA fact sheets (marked ✅ in the app); the rest are marked ⚠️ and need further checking.
- We did not process raw PSI data files. The dashboard is built on curated experiment metadata.
- PSI currently has no partial-gravity combustion data, so lunar-gravity conclusions are not possible yet.

## Run locally
```
pip install -r requirements.txt
python -m streamlit run app.py
```
Optional AI: set `GEMINI_API_KEY` (free key from Google AI Studio) or `ANTHROPIC_API_KEY`. In Streamlit Cloud, add it under Secrets. Never commit keys to the repo.

## Sources
- [PSI Combustion Science repository](https://psi.nasa.gov/physci/repo/search?q=combustion)
- [NASA Combustion Science](https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/)
- [A Researcher's Guide to ISS Combustion Science](https://www.nasa.gov/missions/station/a-researchers-guide-to-combustion-science/)

## Author
Abdul Manan, BS Artificial Intelligence, Emerson University Multan
