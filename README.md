# 🏥 KE-SHA-AI-Review: Fair Premium Scoring for Kenya's Social Health Authority

> > Built by **Melisa Michuki** | Creator, MLlabwithMel | Data & AI Educator

---

## The Problem

In 2023, Kenya launched the Social Health Authority (SHA) to replace NHIF. Over 30 million Kenyans registered. Fewer than 5 million are paying.

The gap is not apathy. It is a pricing algorithm.

SHA uses a Proxy Means Testing (PMT) model to estimate household income from observable assets: roof material, cooking fuel, toilet type, wall material. The model then assigns premiums. The problem is that PMT models are known to systematically overcharge the poor. They penalise households that *look* poor by asset proxy while missing actual income. The result is that a Q1 household (the poorest quintile) gets assigned a premium they cannot afford, drops out, and the system loses them entirely.

This project builds what should have been built before deployment: a fair scoring system with full explainability and an appeal pipeline.

---

## What This Project Does

| Component | What it shows |
|---|---|
| Biased model | Replicates the PMT failure using real Kenyan household data (World Bank LSMS-ISA) |
| Bias audit | Quantifies overcharge by income quintile, shows Q1 households overcharged by up to 134% |
| Drift detection | PSI-based monitoring showing 60% column drift across cohorts |
| Vintage simulation | Lapse rate analysis showing 59% payment rate baked in from month one |
| SHAP explainability | Per-prediction feature attribution for both biased and fair models |
| Fair model | Fairness-constrained retraining with before/after comparison |
| DiCE appeal pipeline | Counterfactual generation showing what profile changes would lower a premium |
| Deployed app | FastAPI backend + Streamlit frontend + Docker Compose |

---

## Project Structure

```
KE-SHA-AI-review/
├── backend/
│   ├── Dockerfile
│   ├── main.py               # FastAPI app: /predict and /appeal endpoints
│   ├── requirements.txt
│   └── models/
│       ├── biased_model.pkl
│       ├── fair_model.pkl
│       ├── feature_cols.pkl
│       └── features.csv
├── frontend/
│   ├── Dockerfile
│   ├── app.py                # Streamlit UI
│   └── requirements.txt
└── docker-compose.yml
```

---

## Data Source

**World Bank LSMS-ISA Kenya Household Survey**

This project uses the Kenya Integrated Household Budget Survey microdata from the World Bank Living Standards Measurement Study. The data contains household-level expenditure, asset ownership, housing characteristics, and income source variables across all 47 Kenyan counties.

Features used:

| Feature | Description |
|---|---|
| `sex` | Sex of household head |
| `age` | Age of household head |
| `education` | Highest education level |
| `marital_status` | Marital status |
| `household_size` | Number of household members |
| `roof_type` | Roof material (13 categories) |
| `floor_type` | Floor material (9 categories) |
| `wall_type` | Wall material (17 categories) |
| `cooking_fuel` | Primary cooking fuel (9 categories) |
| `water_source` | Primary water source (15 categories) |
| `toilet_type` | Toilet facility type (9 categories) |
| `owns_computer` | Computer ownership |
| `owns_motorcycle` | Motorcycle ownership |
| `owns_car` | Car ownership |
| `income_farming` | Income from farming (KES) |
| `income_employed` | Income from employment (KES) |
| `income_casual` | Income from casual work (KES) |
| `income_selfemployed` | Income from self-employment (KES) |
| `livelihood` | Primary livelihood category |
| `county` | County code (1-47) |

---

## Setup and Installation

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git

### Clone the repository

```bash
git clone https://github.com/your-username/KE-SHA-AI-review.git
cd KE-SHA-AI-review
```

### Add your model files

Place the following files inside `backend/models/`:

```
backend/models/
├── biased_model.pkl
├── fair_model.pkl
├── feature_cols.pkl
└── features.csv
```

These are generated from the Colab training notebooks (Phases 1-5). If you are running the full pipeline from scratch, run the notebooks in order before deploying.

### Build and run

```bash
docker-compose up --build
```

This builds both containers and starts the services. First build takes 5-10 minutes depending on your connection.

### Access the app

| Service | URL |
|---|---|
| Streamlit app | http://localhost:8501 |
| FastAPI docs | http://localhost:8000/docs |

---

## How to Use the App

1. Open `http://localhost:8501`
2. Use the sidebar to configure a household profile
3. Click **Score This Household**
4. The app returns:
   - Biased model premium vs fair model premium
   - Overcharge percentage
   - Cap breach flag (triggered when biased premium exceeds 2x fair premium)
   - SHAP feature attribution charts for both models
5. Click **Generate Appeal Counterfactuals** to run the DiCE pipeline
6. The appeal section returns three alternative profiles that would reduce the premium by at least 30%, decoded into plain English labels

### Testing a Q1 household

Use these values to see a typical low-income household profile:

| Field | Value |
|---|---|
| Sex | Female |
| Age | 45 |
| Education | None |
| Marital Status | Widowed/Divorced |
| Household Size | 6 |
| Roof Type | 3 (Concrete) |
| Floor Type | 4 (Earth/Sand) |
| Wall Type | 5 (Mud/Adobe) |
| Cooking Fuel | 5 (Charcoal) |
| Water Source | 6 (Unprotected Well) |
| Toilet Type | 5 (Pit Latrine without Slab) |
| All income fields | 0 |
| Livelihood | Farming |
| County | 1 |

---

## API Reference

### `POST /predict`

Returns premium predictions and SHAP values for both models.

**Request body:**
```json
{
  "sex": 2,
  "age": 45,
  "education": 1,
  "marital_status": 3,
  "household_size": 6,
  "roof_type": 3,
  "floor_type": 4,
  "wall_type": 5,
  "cooking_fuel": 5,
  "water_source": 6,
  "toilet_type": 5,
  "owns_computer": 0,
  "owns_motorcycle": 0,
  "owns_car": 0,
  "income_farming": 0,
  "income_employed": 0,
  "income_casual": 0,
  "income_selfemployed": 0,
  "livelihood": 1,
  "county": 1
}
```

**Response:**
```json
{
  "biased_premium": 13244.93,
  "fair_premium": 14460.55,
  "overcharge_pct": -8.4,
  "cap_breached": false,
  "biased_shap": { "sex": -1.6, "age": 1042.6, ... },
  "fair_shap": { "sex": -12.4, "age": 937.4, ... }
}
```

### `POST /appeal`

Generates DiCE counterfactual profiles that would reduce the biased premium by at least 30%.

Same request body as `/predict`. Returns three alternative household configurations with decoded feature labels and estimated premiums.

---

## Key Findings

- The biased PMT model is technically functional with Gini coefficients above 0.49 across all income quintiles. High discrimination does not mean fair pricing.
- The top drivers of premium inflation are `toilet_type`, `household_size`, `age`, and `cooking_fuel`, all asset proxies with no direct relationship to ability to pay.
- The `county` feature is penalised 4x more heavily in the biased model than in the fair model (-1,628 vs -395 SHAP value), exposing geographic discrimination embedded in the original PMT logic.
- Every cohort in the vintage simulation sits at a 59% payment rate from month one. The lapse is not caused by economic shocks. It is baked in at the point of premium assignment.

---

## Limitations

- **PMT label noise:** The target variable is estimated expenditure, not actual income. PMT models inherit the noise of the survey instrument they are trained on.
- **DiCE artefacts:** The genetic counterfactual method sometimes sets `age` and `household_size` to 0 as optimisation artefacts. These are not real profile recommendations. The meaningful signals are in housing material, fuel, and water source features.
- **Label mapping approximation:** The housing feature codes (roof type, wall type, etc.) are mapped to English labels based on standard LSMS codebook conventions. Some county-specific variations may not be perfectly captured.
- **Static model:** The deployed models are trained on a single survey wave. Premium fairness in a live system requires continuous monitoring and retraining as household conditions change.
- **Scope:** This project models the premium assignment problem. It does not cover claim processing fairness, provider reimbursement equity, or benefit coverage gaps, all of which are separate failure modes in the SHA system.

---

## Challenges

- PMT features are highly correlated (households with earth floors tend to also use charcoal and lack flush toilets), making it difficult to isolate individual feature contributions cleanly.
- DiCE's random counterfactual method rejects query instances with feature values outside the training distribution. Switching to the genetic method and explicitly appending the query instance to the background dataset resolved this.
- The sklearn version mismatch (1.6.1 trained, 1.7.2 in Docker) produced `InconsistentVersionWarning` on model load. The models loaded and performed correctly despite the warning, but retraining inside the container environment is the clean long-term fix.

---

## Future Work

- **Retraining pipeline:** Automate model retraining on new survey waves with drift detection as the trigger.
- **County-level dashboard:** Aggregate overcharge rates by county and display on a choropleth map of Kenya.
- **Benefit coverage audit:** Extend the fairness analysis from premium assignment to claim approval rates by income quintile.
- **Oracle labels:** Replace PMT-estimated expenditure with actual income verification data where available, reducing label noise.
- **Appeal tracking:** Build a persistent appeal log that records which households appealed, what counterfactuals were generated, and whether the appeal resulted in a premium adjustment.
- **Mobile interface:** A lightweight mobile-first version of the Streamlit app for field use by community health workers doing household assessments.

---

## About

**Melisa Michuki** is a data and AI educator and consultant based in Nairobi, Kenya. She is building **MLlabwithMel**,an independent platform for applied machine learning education with a focus on real-world African use cases. She teaches data science, machine learning, SQL, and Tableau at GoMyCode, and is co-lead of Codebar Nairobi.

This project is part of the MLlabwithMel structured ML sprint: 10 real-world projects built and deployed end to end.


- 💼 LinkedIn: [linkedin.com/in/melisa-michuki](https://linkedin.com/in/melisa-michuki)
- 🐙 GitHub: [github.com/melisa-michuki](https://github.com/melisa-michuki)

---

*This project is for research and educational purposes. It is not affiliated with or endorsed by the Social Health Authority of Kenya.*
