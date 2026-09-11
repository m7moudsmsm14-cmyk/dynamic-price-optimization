import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

st.set_page_config(
    page_title="Dynamic Price Optimization",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; }
.hero {
    padding: 1.8rem 2rem 1.5rem;
    border: 1px solid rgba(128,128,128,.20);
    border-radius: 20px;
    margin-bottom: 1.2rem;
    background: linear-gradient(135deg, rgba(99,102,241,.12), rgba(16,185,129,.08));
}
.hero h1 { margin: 0; font-size: 2.5rem; letter-spacing: -1px; }
.hero p { margin: .35rem 0 0; opacity: .72; font-size: 1.05rem; }
.badge {
    display:inline-block; margin-top:.85rem; padding:.35rem .75rem;
    border:1px solid rgba(128,128,128,.25); border-radius:999px;
    font-size:.78rem; font-weight:800; letter-spacing:.7px;
}
.kpi {
    padding: 1rem 1.05rem;
    border: 1px solid rgba(128,128,128,.18);
    border-radius: 15px;
}
.note {
    padding: .85rem 1rem; border-left: 4px solid #6366f1;
    border-radius: 8px; background: rgba(99,102,241,.06);
}
.small { opacity: .65; font-size: .88rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>💰 Dynamic Price Optimization</h1>
    <p>Demand modeling → price simulation → revenue optimization</p>
    <div class="badge">BY MAHMOUD SAMY · DATA SCIENCE PORTFOLIO</div>
</div>
""", unsafe_allow_html=True)

REQUIRED_COLUMNS = [
    "product_id", "store_id", "date", "price", "sales", "stock", "promo_bin_1"
]

@st.cache_data
def clean_data(raw):
    df = raw.copy()
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for c in ["price", "sales", "stock"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["date", "sales", "stock", "price"]).copy()
    df = df[df["price"] > 0].copy()

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.day_of_week
    df["quarter"] = df["date"].dt.quarter
    return df

@st.cache_resource
def train_model(df):
    data = df[df["sales"] > 0].copy()
    if len(data) < 100:
        raise ValueError("Not enough positive-sales rows to train the demand model.")

    data["log_price"] = np.log(data["price"])

    features = [
        "log_price", "stock", "promo_bin_1", "product_id",
        "store_id", "year", "month", "day_of_week", "quarter"
    ]
    numeric_features = [
        "log_price", "stock", "year", "month", "day_of_week", "quarter"
    ]
    categorical_features = ["promo_bin_1", "product_id", "store_id"]

    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
    ])

    X, y = data[features], data["sales"]
    cutoff = data["date"].quantile(0.80)
    train_mask = data["date"] <= cutoff

    X_train, y_train = X.loc[train_mask], y.loc[train_mask]
    X_test, y_test = X.loc[~train_mask], y.loc[~train_mask]

    if len(X_train) < 50 or len(X_test) < 20:
        split = int(len(data) * 0.8)
        X_train, X_test = X.iloc[:split], X.iloc[split:]
        y_train, y_test = y.iloc[:split], y.iloc[split:]

    X_train_p = preprocessor.fit_transform(X_train)
    X_test_p = preprocessor.transform(X_test)

    # GradientBoostingRegressor expects dense input.
    X_train_p = X_train_p.toarray() if hasattr(X_train_p, "toarray") else X_train_p
    X_test_p = X_test_p.toarray() if hasattr(X_test_p, "toarray") else X_test_p

    model = GradientBoostingRegressor(
        n_estimators=300, learning_rate=0.05, max_depth=5, random_state=42
    )
    model.fit(X_train_p, y_train)

    pred = model.predict(X_test_p)
    metrics = {
        "mae": mean_absolute_error(y_test, pred),
        "rmse": np.sqrt(mean_squared_error(y_test, pred)),
        "r2": r2_score(y_test, pred),
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "positive_rows": len(data),
    }
    return model, preprocessor, features, metrics

def make_simulation(
    model, preprocessor, features,
    product, store, promo, stock, year, month, day_of_week, quarter,
    min_price, max_price, n_points=60
):
    prices = np.linspace(float(min_price), float(max_price), n_points)

    sim = pd.DataFrame({"price": prices})
    sim["log_price"] = np.log(sim["price"])
    sim["stock"] = float(stock)
    sim["promo_bin_1"] = promo
    sim["product_id"] = product
    sim["store_id"] = store
    sim["year"] = int(year)
    sim["month"] = int(month)
    sim["day_of_week"] = int(day_of_week)
    sim["quarter"] = int(quarter)

    Xp = preprocessor.transform(sim[features])
    Xp = Xp.toarray() if hasattr(Xp, "toarray") else Xp

    sim["predicted_demand"] = np.maximum(model.predict(Xp), 0)
    sim["expected_revenue"] = sim["price"] * sim["predicted_demand"]

    best = sim.loc[sim["expected_revenue"].idxmax()]
    elasticity = np.polyfit(
        np.log(sim["price"]),
        np.log(np.maximum(sim["predicted_demand"], 1e-8)),
        1
    )[0]
    return sim, best, elasticity

# ---------- Data ----------
DEMO_PATH = Path(__file__).parent / "data" / "demo_data.csv"

with st.sidebar:
    st.header("⚙️ Controls")
    uploaded = st.file_uploader("Upload sales CSV (optional)", type=["csv"])
    st.caption("Required: product_id, store_id, date, price, sales, stock, promo_bin_1")

if uploaded is not None:
    raw_df = pd.read_csv(uploaded)
    st.sidebar.success("Uploaded dataset loaded")
elif DEMO_PATH.exists():
    raw_df = pd.read_csv(DEMO_PATH)
    st.sidebar.success("20,000-row demo dataset loaded")
    st.sidebar.caption("Synthetic demo data for public deployment.")
else:
    st.error("No dataset found. Upload a CSV or add data/demo_data.csv.")
    st.stop()

try:
    df = clean_data(raw_df)
except Exception as e:
    st.error(f"Could not load the data: {e}")
    st.stop()

with st.sidebar:
    st.success(f"{len(df):,} clean rows")

with st.spinner("Training demand model..."):
    try:
        model, preprocessor, features, metrics = train_model(df)
    except Exception as e:
        st.error(f"Model training failed: {e}")
        st.stop()

# ---------- Executive KPIs ----------
positive_rate = (df["sales"] > 0).mean()
total_revenue = (df["price"] * df["sales"]).sum()
avg_price = df["price"].mean()
avg_sales = df["sales"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Rows", f"{len(df):,}")
k2.metric("Products", f"{df['product_id'].nunique():,}")
k3.metric("Stores", f"{df['store_id'].nunique():,}")
k4.metric("Positive-sale rate", f"{positive_rate*100:.1f}%")
k5.metric("Observed Revenue", f"{total_revenue:,.0f}")

st.markdown('<div class="note"><b>Business objective:</b> estimate demand under different prices and identify the candidate price that maximizes expected revenue for a defined product/store scenario.</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🏠 Executive Dashboard",
    "🎯 Price Optimizer",
    "📈 Analytics",
    "🤖 Model"
])

# ---------- Dashboard ----------
with tab1:
    st.subheader("Business Overview")
    left, right = st.columns(2)

    monthly = (
        df.assign(month_date=df["date"].dt.to_period("M").dt.to_timestamp())
          .groupby("month_date", as_index=False)
          .agg(sales=("sales", "sum"), revenue=("price", lambda s: 0))
    )
    # Revenue needs row-wise price * sales before aggregation.
    tmp = df.copy()
    tmp["revenue"] = tmp["price"] * tmp["sales"]
    monthly = (
        tmp.assign(month_date=tmp["date"].dt.to_period("M").dt.to_timestamp())
           .groupby("month_date", as_index=False)
           .agg(sales=("sales", "sum"), revenue=("revenue", "sum"))
    )

    with left:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(monthly["month_date"], monthly["revenue"], linewidth=2)
        ax.set_title("Monthly Observed Revenue")
        ax.set_xlabel("Date")
        ax.set_ylabel("Revenue")
        ax.grid(alpha=.2)
        fig.autofmt_xdate()
        st.pyplot(fig, clear_figure=True)

    with right:
        product_rev = (
            df.assign(revenue=df["price"] * df["sales"])
              .groupby("product_id")["revenue"].sum()
              .sort_values(ascending=False)
              .head(10)
              .sort_values()
        )
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(product_rev.index.astype(str), product_rev.values)
        ax.set_title("Top 10 Products by Observed Revenue")
        ax.set_xlabel("Revenue")
        st.pyplot(fig, clear_figure=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Average Price", f"{avg_price:.2f}")
    c2.metric("Average Sales / Row", f"{avg_sales:.2f}")
    c3.metric("Zero-sales rows", f"{(df['sales']==0).sum():,}")

    st.markdown("### Key Findings")
    st.write(
        "• About 83% of analyzed rows have zero sales, supporting a two-stage demand strategy "
        "(sale probability → positive demand)."
    )
    st.write(
        "• Price-sales correlation is weak at product-store level, so simple correlation alone "
        "is not sufficient for pricing decisions."
    )
    st.write(
        "• Stock is strongly associated with sales activity, while time effects such as month, "
        "year and day-of-week also matter."
    )

# ---------- Optimizer ----------
with tab2:
    st.subheader("Scenario-Based Price Optimizer")

    products = sorted(df["product_id"].astype(str).unique())
    product = st.selectbox("Product", products, key="opt_product")
    product_df = df[df["product_id"].astype(str) == product].copy()

    stores = sorted(product_df["store_id"].astype(str).unique())
    store = st.selectbox("Store", stores, key="opt_store")
    store_df = product_df[product_df["store_id"].astype(str) == store].copy()

    col1, col2, col3 = st.columns(3)
    with col1:
        promo_values = sorted(df["promo_bin_1"].fillna("None").astype(str).unique())
        default_promo = str(store_df["promo_bin_1"].dropna().iloc[0]) if not store_df["promo_bin_1"].dropna().empty else "None"
        promo = st.selectbox("Promotion bin", promo_values, index=promo_values.index(default_promo) if default_promo in promo_values else 0)
    with col2:
        scenario_date = st.date_input(
            "Scenario date",
            value=df["date"].max().date(),
            min_value=df["date"].min().date(),
            max_value=df["date"].max().date(),
        )
        scenario_date = pd.Timestamp(scenario_date)
    with col3:
        stock_default = float(store_df["stock"].median()) if not store_df["stock"].empty else 1.0
        stock = st.number_input("Stock", min_value=0.0, value=max(stock_default, 0.0), step=1.0)

    p1, p2 = st.columns(2)
    with p1:
        min_price = st.number_input(
            "Minimum candidate price",
            min_value=0.0001,
            value=max(float(product_df["price"].quantile(.10)), .0001),
            step=.01
        )
    with p2:
        max_price = st.number_input(
            "Maximum candidate price",
            min_value=0.0002,
            value=max(float(product_df["price"].quantile(.90)), min_price + .01),
            step=.01
        )

    if max_price <= min_price:
        st.error("Maximum candidate price must be greater than minimum candidate price.")
        st.stop()

    sim, best, elasticity = make_simulation(
        model, preprocessor, features,
        product, store, promo, stock,
        scenario_date.year, scenario_date.month,
        scenario_date.day_of_week, scenario_date.quarter,
        min_price, max_price
    )

    current_price = float(product_df["price"].median())
    current_row = sim.iloc[(sim["price"] - current_price).abs().argmin()]
    revenue_change = (
        best["expected_revenue"] / current_row["expected_revenue"] - 1
        if current_row["expected_revenue"] > 0 else np.nan
    )

    a, b, c, d = st.columns(4)
    a.metric("Recommended Price", f"{best['price']:.2f}")
    b.metric("Predicted Demand", f"{best['predicted_demand']:.2f}")
    c.metric("Expected Revenue", f"{best['expected_revenue']:.2f}")
    d.metric("vs. Current", f"{revenue_change*100:.1f}%" if np.isfinite(revenue_change) else "N/A")

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(sim["price"], sim["expected_revenue"], linewidth=2.5, label="Expected Revenue")
    ax.axvline(best["price"], linestyle="--", linewidth=1.5, label=f"Recommended = {best['price']:.2f}")
    ax.set_title("Expected Revenue Across Candidate Prices")
    ax.set_xlabel("Candidate Price")
    ax.set_ylabel("Expected Revenue")
    ax.grid(alpha=.2)
    ax.legend()
    st.pyplot(fig, clear_figure=True)

    if best["price"] >= max_price * .999:
        st.warning("The optimizer selected the upper boundary. The tested price range may be too narrow.")

    st.info(
        f"Model-based scenario elasticity ≈ {elasticity:.3f}. "
        "This is predictive, not causal."
    )

    st.dataframe(
        sim[["price", "predicted_demand", "expected_revenue"]]
        .sort_values("expected_revenue", ascending=False)
        .head(15)
        .style.format({
            "price": "{:.2f}",
            "predicted_demand": "{:.3f}",
            "expected_revenue": "{:.3f}",
        }),
        use_container_width=True
    )

# ---------- Analytics ----------
with tab3:
    st.subheader("Pricing & Demand Analytics")
    c1, c2 = st.columns(2)

    with c1:
        corr = (
            df.groupby(["product_id", "store_id"])
              .apply(lambda x: x["price"].corr(x["sales"]) if len(x) > 1 else np.nan)
              .dropna()
        )
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(corr, bins=30)
        ax.set_title("Distribution of Product-Store Price/Sales Correlation")
        ax.set_xlabel("Correlation")
        ax.set_ylabel("Product-store groups")
        st.pyplot(fig, clear_figure=True)

    with c2:
        monthly_sales = df.groupby("month")["sales"].mean()
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(monthly_sales.index, monthly_sales.values, marker="o")
        ax.set_title("Average Sales by Month")
        ax.set_xlabel("Month")
        ax.set_ylabel("Average Sales")
        ax.set_xticks(range(1, 13))
        ax.grid(alpha=.2)
        st.pyplot(fig, clear_figure=True)

    st.markdown("### Data Quality Snapshot")
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Missing values", f"{df[REQUIRED_COLUMNS].isna().sum().sum():,}")
    q2.metric("Date range", f"{df['date'].min().date()} → {df['date'].max().date()}")
    q3.metric("Median stock", f"{df['stock'].median():.1f}")
    q4.metric("Median price", f"{df['price'].median():.2f}")

# ---------- Model ----------
with tab4:
    st.subheader("Demand Model Performance")
    a, b, c, d = st.columns(4)
    a.metric("MAE", f"{metrics['mae']:.3f}")
    b.metric("RMSE", f"{metrics['rmse']:.3f}")
    c.metric("R²", f"{metrics['r2']:.3f}")
    d.metric("Positive-sales rows", f"{metrics['positive_rows']:,}")

    st.write(
        f"Training rows: {metrics['train_rows']:,} · "
        f"Test rows: {metrics['test_rows']:,}"
    )

    st.markdown("### Modeling Approach")
    st.markdown("""
    **1. Data preparation**  
    Clean sales data and engineer calendar features.

    **2. Positive-demand modeling**  
    Train Gradient Boosting only on rows where `sales > 0`.

    **3. Price representation**  
    Use `log(price)` so price has an explicit role in the demand model.

    **4. Scenario simulation**  
    Hold product, store, promotion, stock and time context fixed while varying candidate prices.

    **5. Revenue optimization**  
    `Expected Revenue = Candidate Price × Predicted Demand`
    """)

    st.markdown("### Important Limitations")
    st.warning(
        "The dataset has no unit-cost/COGS field, so this project optimizes revenue rather than profit. "
        "The pricing recommendation is scenario-based decision support, not an automatic production pricing rule."
    )

st.divider()
st.caption("Dynamic Price Optimization · Python · SQL · Scikit-learn · Streamlit · Mahmoud Samy")
