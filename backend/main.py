from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import shap
import dice_ml

app = FastAPI()

feature_cols = joblib.load("models/feature_cols.pkl")
biased_model = joblib.load("models/biased_model.pkl")
fair_model = joblib.load("models/fair_model.pkl")
background_data = pd.read_csv("models/features.csv")[feature_cols].sample(100, random_state=42)

for col in ['education', 'marital_status', 'age']:
    if col in background_data.columns:
        background_data[col] = background_data[col].replace(99, np.nan).fillna(background_data[col].median())

biased_explainer = shap.TreeExplainer(biased_model, background_data)
fair_explainer = shap.TreeExplainer(fair_model, background_data)

PREMIUM_CAP_RATIO = 2.0

class HouseholdProfile(BaseModel):
    sex: int
    age: int
    education: int
    marital_status: int
    household_size: int
    roof_type: int
    floor_type: int
    wall_type: int
    cooking_fuel: int
    water_source: int
    toilet_type: int
    owns_computer: int
    owns_motorcycle: int
    owns_car: int
    income_farming: int
    income_employed: int
    income_casual: int
    income_selfemployed: int
    livelihood: int
    county: int

@app.get("/")
def root():
    return {"status": "SHA Fair Scoring API is running"}

@app.post("/predict")
def predict(profile: HouseholdProfile):
    input_df = pd.DataFrame([profile.dict()])[feature_cols]

    biased_premium = float(biased_model.predict(input_df)[0])
    fair_premium = float(fair_model.predict(input_df)[0])

    cap_breached = biased_premium > (PREMIUM_CAP_RATIO * fair_premium)
    overcharge_pct = round(((biased_premium - fair_premium) / fair_premium) * 100, 1)

    biased_shap = biased_explainer.shap_values(input_df)[0]
    biased_shap_dict = dict(zip(feature_cols, [round(float(v), 4) for v in biased_shap]))

    fair_shap = fair_explainer.shap_values(input_df)[0]
    fair_shap_dict = dict(zip(feature_cols, [round(float(v), 4) for v in fair_shap]))

    return {
        "biased_premium": round(biased_premium, 2),
        "fair_premium": round(fair_premium, 2),
        "overcharge_pct": overcharge_pct,
        "cap_breached": cap_breached,
        "biased_shap": biased_shap_dict,
        "fair_shap": fair_shap_dict
    }
@app.post("/appeal")
def appeal(profile: HouseholdProfile):
    input_df = pd.DataFrame([profile.dict()])[feature_cols].astype(float)
    biased_pred = float(biased_model.predict(input_df)[0])

    full_data = pd.read_csv("models/features.csv")[feature_cols].copy()
    for col in ['education', 'marital_status', 'age']:
        if col in full_data.columns:
            full_data[col] = full_data[col].replace(99, np.nan).fillna(full_data[col].median())
    full_data = full_data.astype(float)

    # force input values into the dataset so DiCE always sees them as valid
    full_data = pd.concat([full_data, input_df], ignore_index=True)
    full_data["target"] = biased_model.predict(full_data[feature_cols]).astype(float)

    continuous_features = [
        'age', 'household_size', 'income_farming', 'income_employed',
        'income_casual', 'income_selfemployed'
    ]

    data = dice_ml.Data(
        dataframe=full_data,
        continuous_features=continuous_features,
        outcome_name='target'
    )

    model_wrapper = dice_ml.Model(model=biased_model, backend="sklearn", model_type="regressor")
    exp = dice_ml.Dice(data, model_wrapper, method="genetic")

    cf = exp.generate_counterfactuals(
        input_df,
        total_CFs=3,
        desired_range=[0.0, round(biased_pred * 0.7, 2)]
    )

    cf_df = cf.cf_examples_list[0].final_cfs_df
    return {"counterfactuals": cf_df.to_dict(orient="records")}