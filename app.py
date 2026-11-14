import json, os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="FireSafe Space: Combustion Insights", page_icon="🔥", layout="wide")

CRITERIA = {
    "habitat": "Habitat relevance",
    "high_o2": "High-oxygen coverage",
    "material": "Material flammability",
    "detection": "Fire detection",
    "suppression": "Fire suppression",
    "modeling": "Predictive-model data",
    "earth": "Earth applications",
    "partial_g": "Partial-gravity proxy",
}
PROFILES = {
    "Moon base / pressurized rover": dict(habitat=3, high_o2=3, material=3, detection=1, suppression=1, modeling=2, earth=0, partial_g=2),
    "Spacecraft / space station": dict(habitat=3, high_o2=1, material=2, detection=2, suppression=2, modeling=1, earth=0, partial_g=0),
    "Fire detection": dict(habitat=2, high_o2=0, material=0, detection=5, suppression=0, modeling=1, earth=1, partial_g=0),
    "Fire suppression": dict(habitat=2, high_o2=1, material=0, detection=0, suppression=5, modeling=1, earth=0, partial_g=0),
    "Predictive modeling": dict(habitat=1, high_o2=1, material=2, detection=0, suppression=0, modeling=5, earth=0, partial_g=2),
    "Earth applications": dict(habitat=0, high_o2=0, material=0, detection=2, suppression=2, modeling=0, earth=5, partial_g=0),
}

@st.cache_data
def load():
    with open(os.path.join(os.path.dirname(__file__), "experiments.json")) as f:
        return json.load(f)

DATA = load()

def score(exp, weights):
    total = sum(weights.values()) or 1
    return round(100 * sum(exp["scores"][k] * w for k, w in weights.items()) / (5 * total), 1)

def interpret(exp, profile, rank, s):
    sc = exp["scores"]
    top = sorted(CRITERIA, key=lambda k: -sc[k])[:2]
    t = f"**{exp['id']}** ranks #{rank} for *{profile}* (score {s}/100). It studies {exp['fuel'].lower()} using {exp['hardware']}. "
    t += f"Strongest areas: {CRITERIA[top[0]].lower()} and {CRITERIA[top[1]].lower()}. {exp['objective']} "
    if exp["o2_max"]:
        t += f"Tested up to {exp['o2_max']}% oxygen, which matters because Moon habitats are expected to run at 30%+ oxygen. "
    if sc["partial_g"] == 0 and "Moon" in profile:
        t += "Gap: this gives microgravity data only, with no partial-gravity (lunar) data yet."
    return t

def _secret(name):
    v = os.environ.get(name)
    if not v:
        try:
            v = st.secrets[name]
        except Exception:
            v = None
    return v

GEMINI_MODELS = ["gemini-3.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-flash"]

def ask_ai(question, context):
    system = ("You are a NASA combustion fire-safety analyst. Answer only from the experiment data given. "
              "If the data does not cover something, say so. Note that PSI currently has no partial-gravity combustion data. "
              "Be concise: a short paragraph plus up to 5 bullet points, and name the experiment IDs you rely on.")
    prompt = f"Experiment data:\n{context}\n\nQuestion: {question}"

    gkey = _secret("GEMINI_API_KEY")
    if gkey:
        import requests
        models = [_secret("GEMINI_MODEL")] if _secret("GEMINI_MODEL") else GEMINI_MODELS
        last = None
        for m in models:
            try:
                r = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                    headers={"x-goog-api-key": gkey, "Content-Type": "application/json"},
                    json={"systemInstruction": {"parts": [{"text": system}]},
                          "contents": [{"role": "user", "parts": [{"text": prompt}]}]},
                    timeout=60)
                if r.status_code == 200:
                    parts = r.json()["candidates"][0]["content"]["parts"]
                    return "".join(p.get("text", "") for p in parts), f"Gemini ({m})"
                last = f"{m}: HTTP {r.status_code}"
            except Exception as ex:
                last = f"{m}: {ex}"
        st.warning(f"Gemini call failed ({last}). Trying other options.")

    akey = _secret("ANTHROPIC_API_KEY")
    if akey:
        import anthropic
        client = anthropic.Anthropic(api_key=akey)
        r = client.messages.create(model=os.environ.get("MODEL", "claude-sonnet-4-6"), max_tokens=700,
                                   system=system, messages=[{"role": "user", "content": prompt}])
        return r.content[0].text, "Claude"
    return None, None

# ---------- Sidebar ----------
st.sidebar.title("🔥 FireSafe Space")
st.sidebar.caption("Turning NASA microgravity combustion data into fire-safety insights")
profile = st.sidebar.selectbox("Fire-safety need", list(PROFILES))
weights = dict(PROFILES[profile])
with st.sidebar.expander("Adjust ranking weights"):
    for k, label in CRITERIA.items():
        weights[k] = st.slider(label, 0, 5, weights[k], key=f"w_{k}")
fam = st.sidebar.multiselect("Filter by family", sorted({e["family"] for e in DATA}))
q = st.sidebar.text_input("Search")

rows = []
for e in DATA:
    rows.append({"ID": e["id"], "Experiment": e["name"], "Family": e["family"], "Fuel": e["fuel"],
                 "Oxygen": e["o2"], "Airflow": e["airflow"], "Hardware": e["hardware"],
                 "Measures": e["measures"], "Area": ", ".join(e["areas"]), "Source": ("✅ " if e.get("verified") else "⚠️ ") + e.get("source", ""), "Score": score(e, weights)})
df = pd.DataFrame(rows).sort_values("Score", ascending=False).reset_index(drop=True)
df.index += 1
if fam: df = df[df["Family"].isin(fam)]
if q: df = df[df.apply(lambda r: q.lower() in " ".join(map(str, r.values)).lower(), axis=1)]
by_id = {e["id"]: e for e in DATA}

st.title("FireSafe Space: Combustion Insights Dashboard")
st.write("Summarize, rank, and interpret NASA ISS combustion investigations (PSI) for human space exploration fire safety.")

c1, c2, c3 = st.columns(3)
c1.metric("Investigations", len(DATA))
st.caption(f"{sum(1 for e in DATA if e.get('verified'))} of {len(DATA)} entries verified against NASA fact sheets (✅); ⚠️ entries still need checking.")
c2.metric("Top match", df.iloc[0]["ID"] if len(df) else "-")
c3.metric("Max oxygen tested", "85% (CFI-G)")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏆 Ranking", "⚖️ Compare", "🔍 Insights & gaps", "🤖 Ask AI", "🌍 Earth benefits", "📚 Sources"])

with tab1:
    st.subheader(f"Ranked for: {profile}")
    fig_rank = px.bar(df.head(14), x="Score", y="ID", orientation="h", color="Area", range_x=[0, 100])
    fig_rank.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig_rank, use_container_width=True)
    st.dataframe(df, use_container_width=True)
    if len(df):
        sel = st.selectbox("Explain an experiment", df["ID"])
        rank = int(df.reset_index().index[df.reset_index()["ID"] == sel][0]) + 1
        st.info(interpret(by_id[sel], profile, rank, float(df[df["ID"] == sel]["Score"].iloc[0])))
        if by_id[sel].get("details"):
            st.success("Key findings: " + by_id[sel]["details"])
        st.caption(f"Fuel: {by_id[sel]['fuel']} | Oxygen: {by_id[sel]['o2']} | Airflow: {by_id[sel]['airflow']} | Measures: {by_id[sel]['measures']}")

with tab2:
    picks = st.multiselect("Pick 2 to 4 investigations", [e["id"] for e in DATA], default=["BASS-II", "SAME", "FLEX"][:3])
    if picks:
        fig = go.Figure()
        labels = list(CRITERIA.values())
        for p in picks:
            vals = [by_id[p]["scores"][k] for k in CRITERIA]
            fig.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=labels + labels[:1], name=p, fill="toself", opacity=0.5))
        fig.update_layout(polar=dict(radialaxis=dict(range=[0, 5])))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(pd.DataFrame([{"ID": p, "Fuel": by_id[p]["fuel"], "Oxygen": by_id[p]["o2"], "Airflow": by_id[p]["airflow"],
                                    "Hardware": by_id[p]["hardware"], "Measures": by_id[p]["measures"]} for p in picks]).set_index("ID").T)

with tab3:
    st.subheader("Key insights")
    st.markdown("""
- **Moon habitats will likely use 30%+ oxygen at ≤10.2 psi**, over 40% more oxygen than Earth air, so materials burn much more easily. Prioritize experiments with high-oxygen coverage (CFI-G reached 85%).
- **No partial-gravity combustion data exists in PSI yet.** Microgravity and Earth-gravity results can bound the lunar case; E-FIELD mimics partial gravity with an electric field. LUCI and FM2 are expected to add data.
- **Detection and suppression are covered** by SAME/SAME-R and FLEX, but mostly at near-Earth oxygen levels. Gap: detection and suppression at Moon-base oxygen levels.
- **Solid-material flammability (BASS, BASS-II, Saffire)** is the key input for material selection.
- **Coming next:** NASA's FM2 will burn materials on the Moon at 1/6 gravity, and SoFIE and FLARE study ignition, extinction and flammability limits at reduced gravity. Their data is not in PSI yet.\n- **1g screening may not be conservative:** current NASA material screening (NASA-STD-6001 Test 1) uses 1g behaviour; BASS-II and BASS-M compare it with microgravity.\n- Rocket and propellant fires are outside PSI's scope.
""")
    cov = pd.DataFrame({"Criterion": list(CRITERIA.values()),
                        "Total coverage": [sum(e["scores"][k] for e in DATA) for k in CRITERIA]})
    st.plotly_chart(px.bar(cov, x="Criterion", y="Total coverage", title="Where PSI coverage is strong or thin"), use_container_width=True)

with tab4:
    st.subheader("Ask the analyst")
    question = st.text_input("Example: Which experiments should a Moon-base fire-safety engineer read first?")
    if question:
        ctx = json.dumps(DATA)
        try:
            ans, engine = ask_ai(question, ctx)
        except Exception as ex:
            ans, engine = None, None
            st.warning(f"AI call failed ({ex}). Showing rule-based answer.")
        if ans:
            st.caption(f"Answered by {engine} using the experiment database")
            st.markdown(ans)
        else:
            st.caption("No AI key found, using the built-in ranking engine.")
            for i, r in df.head(3).reset_index().iterrows():
                st.markdown(interpret(by_id[r["ID"]], profile, i + 1, r["Score"]))

with tab5:
    st.subheader("Space fire safety on Earth")
    st.markdown("""
- **Fine-water-mist extinguishers** developed for the ISS are used on Earth.
- **Smoke detector that tells smoke from dust** (1970s shuttle tech) cuts nuisance alarms, e.g. in mining.
- **Firefighter air tanks** adapted from spacesuit technology (1970s).
- **Firefighter protective clothing** improved with spacesuit technology (1980s).
""")

with tab6:
    st.markdown("""
Data: [PSI Combustion Science](https://psi.nasa.gov/physci/repo/search?q=combustion) ·
[NASA Combustion Science](https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/) ·
[Researcher's Guide to ISS Combustion Science](https://www.nasa.gov/missions/station/a-researchers-guide-to-combustion-science/)

**Method:** each investigation is scored 0 to 5 on eight criteria; rankings are the weighted average for the selected need. Scores are the team's editable judgments based on NASA's descriptions, and weights can be changed in the sidebar.
""")
