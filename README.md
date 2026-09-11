# 💰 Dynamic Price Optimization

> **An end-to-end retail Data Science project for demand modeling, price simulation, and revenue optimization.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Streamlit]([https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)](https://streamlit.io/](https://dynamic-price-optimization-lgtqpk8g9psaczuxfggvxj.streamlit.app/))
[![Scikit--learn](https://img.shields.io/badge/Scikit--learn-ML-orange?logo=scikit-learn)](https://scikit-learn.org/)
[![SQL](https://img.shields.io/badge/SQL-Data%20Extraction-informational?logo=microsoftsqlserver)](https://www.microsoft.com/sql-server)

## 🎯 Project Overview

Retail pricing is a decision problem: **what price should a product have under a specific market scenario?**

This project builds an end-to-end workflow that uses historical retail sales data to:

- analyze pricing and demand behavior
- engineer time-based and categorical features
- model positive demand
- simulate multiple candidate prices
- estimate expected revenue
- identify the best candidate price for a defined product/store scenario
- present the result through an interactive Streamlit dashboard

The project is designed as a **Data Science portfolio project**, combining SQL, Python, machine learning, business analysis, and deployment.

---

## 🚀 Live Demo

**Streamlit App:** `YOUR_STREAMLIT_APP_URL`

The public demo uses a lightweight **20,000-row synthetic dataset** with the same project schema so the application can be deployed publicly without exposing the original large dataset.

> The synthetic dataset is for demonstration/deployment only. The main analysis was performed using the original retail data.

---

## 🧠 Business Problem

### Question

**Can we estimate demand at different prices and identify the price that maximizes expected revenue?**

Because the dataset does not contain unit cost / COGS, the optimization target is:

```text
Expected Revenue = Candidate Price × Predicted Demand
```

This is therefore **Revenue Optimization**, not Profit Optimization.

---

## 🔄 Project Workflow

```text
SQL Server
   ↓
Data Extraction & Cleaning
   ↓
Exploratory Data Analysis
   ↓
Feature Engineering
   ↓
Demand Modeling
   ↓
Price Elasticity Analysis
   ↓
Candidate Price Simulation
   ↓
Expected Revenue Optimization
   ↓
Interactive Streamlit Dashboard
```

---

## 📊 Key Findings

The analysis produced several important business observations:

- Approximately **83% of analyzed sales rows have zero sales**, which supports a two-stage modeling strategy: sale probability first, then positive demand.
- **Price-sales correlation is weak at product-store level**, so simple correlation is not sufficient for pricing decisions.
- Products have very different price scales, so price outliers should be evaluated **per product** rather than using one global threshold.
- **Stock is strongly associated with sales activity**, making inventory availability an important demand signal, although this association should not be interpreted as causation.
- Sales vary over time, so **month, year, and day-of-week effects** should be considered.

---

## 🤖 Modeling

### Stage 1 — Sale Probability

A Logistic Regression model was used to estimate the probability that a row has positive sales.

**ROC-AUC ≈ 0.816** on the time-based test set.

### Stage 2 — Positive Demand

A Gradient Boosting model was trained on rows where:

```python
sales > 0
```

with `log(price)` explicitly included as a feature.

Reported performance:

- **MAE ≈ 1.336**
- **R² ≈ 0.263**

### Expected Demand

The two-stage concept is:

```text
Expected Demand
= P(Sale > 0) × E(Sales | Sale > 0)
```

---

## 📈 Price Elasticity

For the analyzed **P0017 scenario**, the model-based elasticity was approximately:

```text
-0.132
```

Interpretation:

> A 1% price increase corresponded to approximately a 0.132% decrease in predicted demand in that specific scenario.

⚠️ This is **predictive/model-based elasticity, not causal elasticity**.

---

## 💡 Pricing Simulation

The simulation:

1. selects a product and store
2. defines a scenario date
3. sets stock and promotion context
4. tests a range of candidate prices
5. predicts demand for each price
6. calculates expected revenue
7. selects the highest-revenue candidate within the tested range

The result is **scenario-based decision support**.

It should not be interpreted as a universal optimal price.

---

## 🖥️ Interactive Dashboard

The Streamlit application contains four main sections:

### 🏠 Executive Dashboard
- total rows
- products and stores
- positive-sale rate
- observed revenue
- monthly revenue trend
- top products by revenue
- key business findings

### 🎯 Price Optimizer
- product/store selection
- promotion context
- scenario date
- stock level
- candidate price range
- recommended price
- predicted demand
- expected revenue
- revenue comparison vs. current price
- model-based elasticity

### 📈 Analytics
- product-store price/sales correlation distribution
- monthly demand pattern
- data-quality snapshot

### 🤖 Model
- MAE
- RMSE
- R²
- training/test sizes
- modeling methodology
- limitations

---

## 🗂️ Repository Structure

```text
dynamic-price-optimization/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── create_demo_sample.py
│
├── data/
│   ├── demo_data.csv
│   └── README.txt
│
└── notebooks/
    └── price_optimization_documented.ipynb
```

---

## 🧰 Tech Stack

| Area | Tools |
|---|---|
| Data extraction | SQL Server / SQL |
| Data analysis | Python, Pandas, NumPy |
| Visualization | Matplotlib |
| Machine Learning | Scikit-learn |
| Demand model | Gradient Boosting |
| Classification | Logistic Regression |
| Feature encoding | OneHotEncoder, StandardScaler |
| Deployment | Streamlit |
| Version control | Git / GitHub |

---

## ▶️ Run Locally

Clone the repository:

```bash
git clone https://github.com/m7moudsmsm14-cmyk/dynamic-price-optimization.git
cd dynamic-price-optimization
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the dashboard:

```bash
streamlit run app.py
```

---

## ☁️ Streamlit Deployment

The app can be deployed using Streamlit Community Cloud.

Use:

```text
Repository: m7moudsmsm14-cmyk/dynamic-price-optimization
Branch: main
Main file: app.py
```

After deployment, add the generated public Streamlit URL to the **Live Demo** section above.

---

## ⚠️ Limitations & Future Improvements

### Current limitations

1. No unit-cost / COGS field → revenue is optimized instead of profit.
2. The demand model explains only a moderate portion of positive-sales variance.
3. Tree-based predictions can be step-like across price values.
4. Observed/model-based elasticity may be affected by promotion, stock, seasonality, store, and product differences.
5. The optimizer is scenario-based and should be validated before production use.

### Possible next steps

- add COGS and optimize profit
- use a stronger two-stage model end-to-end
- test XGBoost / LightGBM
- add lag and rolling demand features
- estimate causal price elasticity
- validate pricing policies with controlled experiments
- add business constraints such as minimum/maximum margin
- add automated model monitoring

---

## 👤 Author

**Mahmoud Samy**

Data Science Portfolio Project — Retail Dynamic Pricing & Revenue Optimization

---

## 📌 Disclaimer

This project is intended for **analysis, demonstration, and portfolio purposes**.

Pricing recommendations are model-based scenario estimates and should not be treated as automatic production pricing decisions without additional validation, business constraints, and causal/experimental analysis.
