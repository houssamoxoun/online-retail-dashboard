import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import numpy as np

from sklearn.preprocessing import RobustScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# =============================================================================
# 1. LOAD & PREPARE DATA
# =============================================================================

# ---------------------
# Objective 1 + part of 4: RFM
# ---------------------
rfm = pd.read_csv("rfm.csv")  # 👉 make sure this exists in the same folder

# Expect at least these columns:
# CustomerID, Recency, Frequency, Monetary, (optional) BusinessModel
if "BusinessModel" not in rfm.columns:
    rfm["BusinessModel"] = "All"

rfm_numeric = rfm[["Recency", "Frequency", "Monetary"]].copy()

# Log-transform to reduce skew
rfm_log = rfm_numeric.apply(
    lambda x: np.log1p(x) if np.issubdtype(x.dtype, np.number) else x
)

# Scale
scaler = RobustScaler()
rfm_scaled = scaler.fit_transform(rfm_log)

# K-Means clustering for customer segments (used in PCA + 3D)
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
rfm["Cluster"] = kmeans.fit_predict(rfm_scaled)

# Map clusters → segments
cluster_stats = rfm.groupby("Cluster")[["Recency", "Frequency", "Monetary"]].mean()
cluster_stats.index = cluster_stats.index.astype(int)
segment_map = {}

champions = (
    cluster_stats["Monetary"].rank(ascending=False)
    + cluster_stats["Frequency"].rank(ascending=False)
    + cluster_stats["Recency"].rank(ascending=True)
).idxmin()
segment_map[int(champions)] = "Champions"

hibernating = (
    cluster_stats["Monetary"].rank(ascending=True)
    + cluster_stats["Frequency"].rank(ascending=True)
    + cluster_stats["Recency"].rank(ascending=False)
).idxmin()
segment_map[int(hibernating)] = "Hibernating"

freq_sorted = cluster_stats["Frequency"].sort_values(ascending=False)
for c in freq_sorted.index:
    if int(c) not in segment_map:
        segment_map[int(c)] = "Loyal Customers"
        break

remaining = [c for c in cluster_stats.index if int(c) not in segment_map]
if remaining:
    segment_map[int(remaining[0])] = "At Risk"

rfm["Segment"] = rfm["Cluster"].map(segment_map)

colors_map_segments = {
    "Champions": "#2ecc71",
    "Loyal Customers": "#3498db",
    "At Risk": "#f1c40f",
    "Hibernating": "#e74c3c",
}

# PCA for 2D visualization
pca = PCA(n_components=2)
pca_res = pca.fit_transform(rfm_scaled)
rfm["PC1"] = pca_res[:, 0]
rfm["PC2"] = pca_res[:, 1]

# ---------------------
# Objective 2: Product Bundling – co-purchased pairs
# ---------------------
# 👉 Update the filename / columns to match your data
pairs = pd.read_csv("product_pairs.csv")
# Assumed columns: ProductA, ProductB, Count
pairs["Pair"] = pairs["ProductA"] + " & " + pairs["ProductB"]
pairs_top10 = pairs.sort_values("Count", ascending=False).head(10)

# ---------------------
# Objective 3: Sales Trends – all from CSVs
# ---------------------
# 👉 Update filenames & column names as needed

# 3.1 Daily sales trend
daily_sales = pd.read_csv("daily_sales.csv", parse_dates=["Date"])
# Needs columns: Date, Revenue

# 3.2 Monthly sales trend
monthly_sales = pd.read_csv("monthly_sales.csv")
# Needs columns: Month, Revenue

# 3.3 Monthly revenue by top 3 categories
monthly_cat = pd.read_csv("monthly_category_revenue.csv")
# Needs columns: Month, Category, Revenue
# (Optionally ensure only top 3 categories)
top3_cats = (
    monthly_cat.groupby("Category")["Revenue"]
    .sum()
    .sort_values(ascending=False)
    .head(3)
    .index
)
monthly_cat_top3 = monthly_cat[monthly_cat["Category"].isin(top3_cats)]

# 3.4 Weekday sales pattern
weekday_sales = pd.read_csv("weekday_sales.csv")
# Needs columns: Weekday, Revenue
# Optional order
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday_sales["Weekday"] = pd.Categorical(weekday_sales["Weekday"], categories=weekday_order, ordered=True)
weekday_sales = weekday_sales.sort_values("Weekday")

# 3.5 Slow-moving items
slow_movers = pd.read_csv("slow_movers.csv")
# Assumed columns: Product, DaysToSell (or similar metric)
slow_movers_top = slow_movers.sort_values("DaysToSell", ascending=False).head(20)

# ---------------------
# Objective 4: Revenue Optimization Insights
# ---------------------
# 4.1 Distribution of customers by MonetaryValue = from rfm
# 4.2–4.5 from separate CSVs

revenue_cust = pd.read_csv("revenue_by_customer.csv")
# Needs columns: CustomerID, Revenue
revenue_cust_top = revenue_cust.sort_values("Revenue", ascending=False).head(30)

revenue_country = pd.read_csv("revenue_by_country.csv")
# Needs columns: Country, Revenue

revenue_region = pd.read_csv("revenue_by_region.csv")
# Needs columns: Region, Revenue

revenue_product = pd.read_csv("revenue_by_product.csv")
# Needs columns: Product, Revenue
revenue_product_top20 = revenue_product.sort_values("Revenue", ascending=False).head(20)

# =============================================================================
# 2. BUILD ALL FIGURES
# =============================================================================

# ---------- Objective 1 ----------
fig_pca = px.scatter(
    rfm,
    x="PC1",
    y="PC2",
    color="Segment",
    symbol="BusinessModel",
    hover_data=["CustomerID", "Recency", "Frequency", "Monetary", "BusinessModel"],
    color_discrete_map=colors_map_segments,
    title="Customer Segmentation – PCA (RFM)",
    template="plotly_white",
)

fig_rfm_3d = px.scatter_3d(
    rfm,
    x="Recency",
    y="Frequency",
    z="Monetary",
    color="Segment",
    hover_data=["CustomerID", "BusinessModel"],
    color_discrete_map=colors_map_segments,
    title="3D Customer Segmentation (RFM Features)",
    template="plotly_white",
    height=650,
)

# ---------- Objective 2 ----------
fig_pairs = px.bar(
    pairs_top10,
    x="Pair",
    y="Count",
    title="Top 10 Co-purchased Product Pairs",
    text_auto=True,
    template="plotly_white",
)
fig_pairs.update_layout(xaxis_tickangle=-45)

# ---------- Objective 3 ----------

# 3.1 Daily trend
fig_daily = px.line(
    daily_sales,
    x="Date",
    y="Revenue",
    title="Daily Sales Trend",
    template="plotly_white",
)

# 3.2 Monthly trend
fig_monthly = px.bar(
    monthly_sales,
    x="Month",
    y="Revenue",
    title="Monthly Sales Trend",
    template="plotly_white",
)

# 3.3 Monthly revenue by top 3 categories
fig_monthly_cat = px.bar(
    monthly_cat_top3,
    x="Month",
    y="Revenue",
    color="Category",
    barmode="group",
    title="Monthly Revenue – Top 3 Categories",
    template="plotly_white",
)

# 3.4 Weekday sales pattern
fig_weekday = px.bar(
    weekday_sales,
    x="Weekday",
    y="Revenue",
    title="Weekday Sales Pattern",
    template="plotly_white",
)

# 3.5 Slow movers
fig_slow = px.bar(
    slow_movers_top,
    x="Product",
    y="DaysToSell",
    title="Slow-Moving Items (Top 20 by Days to Sell)",
    template="plotly_white",
)
fig_slow.update_layout(xaxis_tickangle=-60)

# ---------- Objective 4 ----------

# 4.1 Distribution of customers by MonetaryValue
fig_monetary_dist = px.histogram(
    rfm,
    x="Monetary",
    nbins=50,
    title="Distribution of Customers by Monetary Value",
    template="plotly_white",
)

# 4.2 Revenue by customers (top 30)
fig_rev_cust = px.bar(
    revenue_cust_top,
    x="CustomerID",
    y="Revenue",
    title="Revenue by Customer (Top 30)",
    template="plotly_white",
)
fig_rev_cust.update_layout(xaxis_tickangle=-60)

# 4.3 Revenue by country
fig_rev_country = px.bar(
    revenue_country.sort_values("Revenue", ascending=False),
    x="Country",
    y="Revenue",
    title="Revenue by Country",
    template="plotly_white",
)
fig_rev_country.update_layout(xaxis_tickangle=-45)

# 4.4 Revenue by region
fig_rev_region = px.bar(
    revenue_region.sort_values("Revenue", ascending=False),
    x="Region",
    y="Revenue",
    title="Revenue by Region",
    template="plotly_white",
)

# 4.5 Revenue by product (top 20)
fig_rev_product = px.bar(
    revenue_product_top20,
    x="Product",
    y="Revenue",
    title="Revenue by Product (Top 20)",
    template="plotly_white",
)
fig_rev_product.update_layout(xaxis_tickangle=-60)

# =============================================================================
# 3. DASH APP LAYOUT
# =============================================================================

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = html.Div(
    style={"backgroundColor": "#f4f6f7", "padding": "20px"},
    children=[
        # HEADER
        html.Div(
            style={"textAlign": "center", "marginBottom": "30px"},
            children=[
                html.H1("Retail Analytics – Advanced Insights Dashboard", style={"color": "#2c3e50"}),
                html.P(
                    "Objectives: Customer Segmentation • Product Bundling • Sales Trends • Revenue Optimization",
                    style={"color": "#7f8c8d"},
                ),
            ],
        ),

        # TABS FOR OBJECTIVES
        dcc.Tabs(
            [
                # ---------------- Objective 1 ----------------
                dcc.Tab(
                    label="🎯 Objective 1 – Customer Segmentation",
                    children=[
                        html.Div(
                            style={"padding": "20px"},
                            children=[
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            className="six columns",
                                            style={"backgroundColor": "#fff", "padding": "15px", "borderRadius": "5px"},
                                            children=[dcc.Graph(figure=fig_pca)],
                                        ),
                                        html.Div(
                                            className="six columns",
                                            style={"backgroundColor": "#fff", "padding": "15px", "borderRadius": "5px"},
                                            children=[dcc.Graph(figure=fig_rfm_3d)],
                                        ),
                                    ],
                                )
                            ],
                        )
                    ],
                ),

                # ---------------- Objective 2 ----------------
                dcc.Tab(
                    label="🧩 Objective 2 – Product Bundling",
                    children=[
                        html.Div(
                            style={"padding": "20px"},
                            children=[
                                html.Div(
                                    style={"backgroundColor": "#fff", "padding": "15px", "borderRadius": "5px"},
                                    children=[dcc.Graph(figure=fig_pairs)],
                                )
                            ],
                        )
                    ],
                ),

                # ---------------- Objective 3 ----------------
                dcc.Tab(
                    label="📈 Objective 3 – Sales Trend Analysis",
                    children=[
                        html.Div(
                            style={"padding": "20px"},
                            children=[
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            className="six columns",
                                            style={"backgroundColor": "#fff", "padding": "15px", "borderRadius": "5px"},
                                            children=[dcc.Graph(figure=fig_daily)],
                                        ),
                                        html.Div(
                                            className="six columns",
                                            style={"backgroundColor": "#fff", "padding": "15px", "borderRadius": "5px"},
                                            children=[dcc.Graph(figure=fig_monthly)],
                                        ),
                                    ],
                                ),
                                html.Br(),
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            className="six columns",
                                            style={"backgroundColor": "#fff", "padding": "15px", "borderRadius": "5px"},
                                            children=[dcc.Graph(figure=fig_monthly_cat)],
                                        ),
                                        html.Div(
                                            className="six columns",
                                            style={"backgroundColor": "#fff", "padding": "15px", "borderRadius": "5px"},
                                            children=[dcc.Graph(figure=fig_weekday)],
                                        ),
                                    ],
                                ),
                                html.Br(),
                                html.Div(
                                    style={"backgroundColor": "#fff", "padding": "15px", "borderRadius": "5px"},
                                    children=[dcc.Graph(figure=fig_slow)],
                                ),
                            ],
                        )
                    ],
                ),

                # ---------------- Objective 4 ----------------
                dcc.Tab(
                    label="💰 Objective 4 – Revenue Optimization",
                    children=[
                        html.Div(
                            style={"padding": "20px"},
                            children=[
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            className="six columns",
                                            style={"backgroundColor": "#fff", "padding": "15px", "borderRadius": "5px"},
                                            children=[dcc.Graph(figure=fig_monetary_dist)],
                                        ),
                                        html.Div(
                                            className="six columns",
                                            style={"backgroundColor": "#fff", "padding": "15px", "borderRadius": "5px"},
                                            children=[dcc.Graph(figure=fig_rev_cust)],
                                        ),
                                    ],
                                ),
                                html.Br(),
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            className="six columns",
                                            style={"backgroundColor": "#fff", "padding": "15px", "borderRadius": "5px"},
                                            children=[dcc.Graph(figure=fig_rev_country)],
                                        ),
                                        html.Div(
                                            className="six columns",
                                            style={"backgroundColor": "#fff", "padding": "15px", "borderRadius": "5px"},
                                            children=[dcc.Graph(figure=fig_rev_region)],
                                        ),
                                    ],
                                ),
                                html.Br(),
                                html.Div(
                                    style={"backgroundColor": "#fff", "padding": "15px", "borderRadius": "5px"},
                                    children=[dcc.Graph(figure=fig_rev_product)],
                                ),
                            ],
                        )
                    ],
                ),
            ]
        ),
    ],
)

# =============================================================================
# 4. RUN APP
# =============================================================================
if __name__ == "__main__":
    print("🚀 Dashboard running at http://127.0.0.1:8050/")
    app.run(debug=True)
