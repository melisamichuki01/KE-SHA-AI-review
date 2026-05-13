import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

API_URL = "http://backend:8000"

# ---- PAGE CONFIG ----
st.set_page_config(page_title="SHA Fair Premium Scorer", page_icon="🏥", layout="wide")
st.title("🏥 SHA Fair Premium Scorer")
st.markdown("Enter a household profile to see what the biased algorithm charges versus what a fair model would charge.")

# ---- SESSION STATE INIT ----
for key, default in {
    "result": None,
    "profile": None,
    "appeal_result": None,
    "appeal_requested": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---- FEATURE LABEL DECODER ----
FEATURE_LABELS = {
    "sex": {0: "Unknown", 1: "Male", 2: "Female"},
    "education": {0: "Unknown", 1: "None", 2: "Primary", 3: "Secondary", 4: "Tertiary"},
    "marital_status": {0: "Unknown", 1: "Married", 2: "Single", 3: "Widowed/Divorced"},
    "roof_type": {0: "Unknown", 1: "Iron Sheets", 2: "Tiles", 3: "Concrete", 4: "Asbestos",
                  5: "Grass/Thatch", 6: "Mud/Dung", 7: "Tin", 8: "Wood", 9: "Makeshift",
                  10: "Stone", 11: "Decra", 12: "Other", 13: "None"},
    "floor_type": {0: "Unknown", 1: "Tiles/Cement", 2: "Wood Planks", 3: "Vinyl",
                   4: "Earth/Sand", 5: "Dung", 6: "Stone", 7: "Bamboo", 8: "Other", 9: "None"},
    "wall_type": {0: "Unknown", 1: "Stone/Brick", 2: "Cement Blocks", 3: "Corrugated Iron",
                  4: "Wood Planks", 5: "Mud/Adobe", 6: "Grass", 7: "Bamboo", 8: "Cardboard",
                  9: "Tin", 10: "Plastic", 11: "Asbestos", 12: "Stone Unplastered",
                  13: "Burnt Brick", 14: "Glass", 15: "Other", 16: "Makeshift", 17: "None"},
    "cooking_fuel": {0: "Unknown", 1: "Electricity", 2: "LPG/Gas", 3: "Biogas",
                     4: "Kerosene", 5: "Charcoal", 6: "Wood", 7: "Crop Residue",
                     8: "Dung", 9: "Other"},
    "water_source": {0: "Unknown", 1: "Piped Indoor", 2: "Piped Outdoor", 3: "Public Tap",
                     4: "Borehole", 5: "Protected Well", 6: "Unprotected Well",
                     7: "Protected Spring", 8: "Unprotected Spring", 9: "Rainwater",
                     10: "Tanker Truck", 11: "Surface Water", 12: "Bottled Water",
                     13: "Vendor", 14: "Other", 15: "None"},
    "toilet_type": {0: "Unknown", 1: "Flush to Sewer", 2: "Flush to Septic",
                    3: "VIP Latrine", 4: "Pit Latrine with Slab",
                    5: "Pit Latrine without Slab", 6: "Composting Toilet",
                    7: "Bucket", 8: "Hanging Toilet", 9: "None/Bush"},
    "owns_computer": {0: "No", 1: "Yes"},
    "owns_motorcycle": {0: "No", 1: "Yes"},
    "owns_car": {0: "No", 1: "Yes"},
    "livelihood": {0: "Unknown", 1: "Farming", 2: "Employed", 3: "Casual",
                   4: "Self-employed", 5: "Other", 6: "None"},
}

def decode_counterfactual(row: dict) -> tuple:
    premium = f"KES {row['target']:,.0f}"
    decoded = {}
    for key, value in row.items():
        if key == "target":
            continue
        int_val = int(round(float(value))) if value is not None else 0
        label = key.replace("_", " ").title()
        if key in FEATURE_LABELS:
            decoded[label] = FEATURE_LABELS[key].get(int_val, str(int_val))
        elif key in ["income_farming", "income_employed", "income_casual", "income_selfemployed"]:
            decoded[label] = f"KES {int(float(value)):,}"
        elif key == "county":
            decoded["County Code"] = int(float(value))
        elif key in ["age", "household_size"]:
            decoded[label] = int(float(value))
        else:
            decoded[label] = value
    return premium, decoded

# ---- SIDEBAR INPUTS ----
st.sidebar.header("Household Profile")

sex = st.sidebar.selectbox("Sex of Household Head", [1, 2], format_func=lambda x: {1: "Male", 2: "Female"}[x])
age = st.sidebar.slider("Age of Household Head", 18, 90, 35)
education = st.sidebar.selectbox("Education Level", [1, 2, 3, 4], format_func=lambda x: {1: "None", 2: "Primary", 3: "Secondary", 4: "Tertiary"}[x])
marital_status = st.sidebar.selectbox("Marital Status", [1, 2, 3], format_func=lambda x: {1: "Married", 2: "Single", 3: "Widowed/Divorced"}[x])
household_size = st.sidebar.slider("Household Size", 1, 15, 4)
roof_type = st.sidebar.selectbox("Roof Type (code)", list(range(1, 14)))
floor_type = st.sidebar.selectbox("Floor Type (code)", list(range(1, 10)))
wall_type = st.sidebar.selectbox("Wall Type (code)", list(range(1, 18)))
cooking_fuel = st.sidebar.selectbox("Cooking Fuel (code)", list(range(1, 10)))
water_source = st.sidebar.selectbox("Water Source (code)", list(range(1, 16)))
toilet_type = st.sidebar.selectbox("Toilet Type (code)", list(range(1, 10)))
owns_computer = st.sidebar.selectbox("Owns Computer", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
owns_motorcycle = st.sidebar.selectbox("Owns Motorcycle", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
owns_car = st.sidebar.selectbox("Owns Car", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
income_farming = st.sidebar.number_input("Farming Income (KES)", min_value=0, value=0, step=1000)
income_employed = st.sidebar.number_input("Employment Income (KES)", min_value=0, value=0, step=1000)
income_casual = st.sidebar.number_input("Casual Work Income (KES)", min_value=0, value=0, step=1000)
income_selfemployed = st.sidebar.number_input("Self-Employment Income (KES)", min_value=0, value=0, step=1000)
livelihood = st.sidebar.selectbox("Primary Livelihood", [1, 2, 3, 4], format_func=lambda x: {1: "Farming", 2: "Employed", 3: "Casual", 4: "Self-employed"}[x])
county = st.sidebar.number_input("County Code", min_value=1, max_value=47, value=1)

profile = {
    "sex": sex, "age": age, "education": education, "marital_status": marital_status,
    "household_size": household_size, "roof_type": roof_type, "floor_type": floor_type,
    "wall_type": wall_type, "cooking_fuel": cooking_fuel, "water_source": water_source,
    "toilet_type": toilet_type, "owns_computer": owns_computer, "owns_motorcycle": owns_motorcycle,
    "owns_car": owns_car, "income_farming": income_farming, "income_employed": income_employed,
    "income_casual": income_casual, "income_selfemployed": income_selfemployed,
    "livelihood": livelihood, "county": int(county)
}

# ---- SCORE BUTTON ----
if st.sidebar.button("Score This Household", type="primary"):
    st.session_state["result"] = None
    st.session_state["appeal_result"] = None
    st.session_state["appeal_requested"] = False
    with st.spinner("Running models..."):
        try:
            response = requests.post(f"{API_URL}/predict", json=profile, timeout=30)
            response.raise_for_status()
            st.session_state["result"] = response.json()
            st.session_state["profile"] = profile
        except Exception as e:
            st.error(f"Could not reach the backend. Error: {e}")

# ---- HELPER: SHAP CHART ----
def shap_chart(shap_dict, title, bar_color):
    features = list(shap_dict.keys())
    values = list(shap_dict.values())
    sorted_pairs = sorted(zip(values, features))
    vals, feats = zip(*sorted_pairs)
    colors = [bar_color if v > 0 else "#4a90d9" for v in vals]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.barh(feats, vals, color=colors)
    ax.axvline(0, color="white", linewidth=0.8)
    ax.set_title(title, color="white", fontsize=11, pad=10)
    ax.tick_params(colors="white", labelsize=8)
    ax.set_facecolor("#0e1117")
    fig.patch.set_facecolor("#0e1117")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")
    plt.tight_layout()
    return fig

# ---- MAIN DISPLAY ----
if st.session_state["result"] is not None:
    result = st.session_state["result"]
    saved_profile = st.session_state["profile"]

    biased = result["biased_premium"]
    fair = result["fair_premium"]
    overcharge = result["overcharge_pct"]
    cap_breached = result["cap_breached"]
    biased_shap = result["biased_shap"]
    fair_shap = result["fair_shap"]

    # metrics row
    col1, col2, col3 = st.columns(3)
    col1.metric("Biased Model Premium", f"KES {biased:,.0f}")
    col2.metric(
        "Fair Model Premium",
        f"KES {fair:,.0f}",
        delta=f"{overcharge:+.1f}% vs fair",
        delta_color="inverse"
    )
    col3.metric(
        "Cap Breach",
        "YES" if cap_breached else "NO",
        delta="Flagged" if cap_breached else "Within range",
        delta_color="inverse" if cap_breached else "normal"
    )

    if cap_breached:
        st.error(
            f"This household was overcharged by {overcharge}%. "
            f"The biased premium exceeds twice the fair premium. "
            f"This household qualifies for an appeal."
        )
    elif overcharge > 0:
        st.warning(f"Overcharge of {overcharge}% detected but within the cap threshold.")
    else:
        st.success(f"The biased model charges less than the fair model for this profile ({overcharge}%).")

    st.divider()

    # SHAP charts
    st.subheader("What drove these premiums?")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.pyplot(shap_chart(biased_shap, "Biased Model: Feature Impact", "#e05c5c"))
    with chart_col2:
        st.pyplot(shap_chart(fair_shap, "Fair Model: Feature Impact", "#5ce07a"))

    st.divider()

    # appeal section
    st.subheader("Appeal Pipeline")
    st.markdown(
        "DiCE generates three alternative household profiles that would result in a premium "
        "at least 30% lower under the biased model. This exposes which features the algorithm "
        "is penalising and what a fairer assignment would look like."
    )

    if st.button("Generate Appeal Counterfactuals", type="secondary"):
        st.session_state["appeal_requested"] = True
        st.session_state["appeal_result"] = None

    if st.session_state["appeal_requested"] and st.session_state["appeal_result"] is None:
        with st.spinner("Running DiCE simulation. This may take 20 to 40 seconds..."):
            try:
                appeal_response = requests.post(
                    f"{API_URL}/appeal",
                    json=saved_profile,
                    timeout=120
                )
                appeal_response.raise_for_status()
                st.session_state["appeal_result"] = appeal_response.json()
                st.session_state["appeal_requested"] = False
            except Exception as e:
                st.error(f"Appeal request failed. Error: {e}")
                st.session_state["appeal_requested"] = False

    if st.session_state["appeal_result"] is not None:
        appeal_data = st.session_state["appeal_result"]
        if "counterfactuals" in appeal_data and appeal_data["counterfactuals"]:
            st.markdown("**Three profiles that would reduce the premium by at least 30%:**")
            for i, row in enumerate(appeal_data["counterfactuals"]):
                premium, decoded = decode_counterfactual(row)
                with st.expander(f"Appeal Profile {i+1}: Estimated Premium {premium}", expanded=True):
                    col_a, col_b = st.columns(2)
                    items = list(decoded.items())
                    mid = len(items) // 2
                    with col_a:
                        for k, v in items[:mid]:
                            st.markdown(f"**{k}:** {v}")
                    with col_b:
                        for k, v in items[mid:]:
                            st.markdown(f"**{k}:** {v}")
            st.caption(
                "These profiles show what feature combinations the algorithm rewards with lower premiums. "
                "Age and household size showing as 0 is a DiCE optimisation artefact, not a real profile recommendation. "
                "Focus on the housing, fuel, and water features as the meaningful signals."
            )
        else:
            st.warning("DiCE could not generate counterfactuals for this profile. Try a different household configuration.")

else:
    st.info("Configure a household profile in the sidebar and click 'Score This Household' to run the models.")