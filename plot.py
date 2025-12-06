import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

# =========================================================
# 1. LOAD DATA
# =========================================================
df_rfm = pd.read_csv("rfm.csv")

df_pairs = pd.read_csv("top10_product_pairs.csv")
df_pairs["Pair Name"] = (
    df_pairs["ProductA_desc"].astype(str) + " + " + df_pairs["ProductB_desc"].astype(str)
)

df_daily = pd.read_csv("daily_sales.csv")
df_monthly = pd.read_csv("monthly_sales.csv")
df_cat_monthly = pd.read_csv("category_monthly_sales.csv")
df_weekday = pd.read_csv("weekday_sales_pattern.csv")
df_product_stats = pd.read_csv("product_stats.csv")

df_cust = pd.read_csv("customer_revenue_clv.csv")
df_country = pd.read_csv("country_revenue.csv")
df_region = pd.read_csv("region_revenue.csv")
df_products = pd.read_csv("top_products_by_revenue.csv")

# =========================================================
# 2. PRE-PROCESSING
# =========================================================
segments = sorted(df_rfm["Segment"].dropna().unique().tolist())

# Daily label
if "Day" not in df_daily.columns:
    df_daily["Day"] = df_daily.index

# Month labels with real month names for monthly trend
month_map = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

if "Month" in df_monthly.columns:
    # If Month is numeric, map to names
    try:
        df_monthly["MonthLabel"] = df_monthly["Month"].astype(int).map(month_map)
    except ValueError:
        # If Month already text ("January"...), keep it
        df_monthly["MonthLabel"] = df_monthly["Month"].astype(str)
else:
    # No Month column: assume months in order
    df_monthly["MonthLabel"] = [
        month_map.get(i + 1, f"M{i+1}") for i in range(len(df_monthly))
    ]

# Category monthly
month_cols = [c for c in df_cat_monthly.columns if c != "Description"]
df_cat_monthly["Total"] = df_cat_monthly[month_cols].sum(axis=1)
top3_cats = df_cat_monthly.nlargest(3, "Total")["Description"].tolist()
df_top3 = df_cat_monthly[df_cat_monthly["Description"].isin(top3_cats)]
df_top3_melt = df_top3.melt(
    id_vars=["Description"],
    value_vars=month_cols,
    var_name="Month",
    value_name="Sales",
)

# Weekday order
df_weekday = df_weekday.sort_values("Hour")

# Slow movers flag
df_product_stats["Status"] = df_product_stats["DaysSinceLastSale"].apply(
    lambda x: "Slow Mover" if x > 90 else "Active"
)

# Top 10 customers
top10_cust = df_cust.nlargest(10, "TotalRevenue").copy()
top10_cust["CustomerID"] = top10_cust["CustomerID"].astype(str)

# Top 20 products for treemap
top20_products = df_products.nlargest(20, "TotalRevenue").copy()

# Co-purchase matrix for heatmap
pairs_matrix = df_pairs.pivot_table(
    index="ProductA_desc",
    columns="ProductB_desc",
    values="Frequency",
    fill_value=0,
)

# =========================================================
# 3. FIGURES (DARK THEME)
# =========================================================
PLOT_TEMPLATE = "plotly_dark"


def build_pca_fig(df):
    return px.scatter(
        df,
        x="PCA1",
        y="PCA2",
        color="Segment",
        template=PLOT_TEMPLATE,
        title="Customer Segmentation - PCA",
        hover_data=["CustomerID", "Recency", "Frequency", "Monetary"],
    )


def build_3d_fig(df):
    fig = px.scatter_3d(
        df,
        x="Recency",
        y="Frequency",
        z="Monetary",
        color="Segment",
        template=PLOT_TEMPLATE,
        title="3D Customer Segmentation (RFM Features)",
        hover_data=["CustomerID"],
        opacity=0.8,
    )
    fig.update_layout(margin=dict(l=0, r=0, b=0, t=40))
    return fig


# ---------- Objective 2 ----------
fig_pairs = px.bar(
    df_pairs,
    x="Frequency",
    y="Pair Name",
    orientation="h",
    color="Frequency",
    title="Top-10 Co-Purchased Product Pairs",
    labels={"Frequency": "Co-Purchase Count", "Pair Name": "Product Pair"},
    template=PLOT_TEMPLATE,
    color_continuous_scale="Viridis",
)
fig_pairs.update_layout(yaxis={"categoryorder": "total ascending"})

fig_pairs_heatmap = px.imshow(
    pairs_matrix,
    labels=dict(x="Product B", y="Product A", color="Frequency"),
    x=pairs_matrix.columns,
    y=pairs_matrix.index,
    title="Co-Purchase Frequency Heatmap",
    template=PLOT_TEMPLATE,
    color_continuous_scale="Viridis",
)

# ---------- Objective 3 ----------
fig_daily = px.line(
    df_daily,
    x="Day",
    y="OrderValue",
    title="Daily Sales Trend",
    template=PLOT_TEMPLATE,
    markers=True,
)

fig_monthly = px.line(
    df_monthly,
    x="MonthLabel",          # ✅ real month names
    y="OrderValue",
    title="Monthly Sales Trend",
    template=PLOT_TEMPLATE,
    markers=True,
)

fig_cat = px.line(
    df_top3_melt,
    x="Month",
    y="Sales",
    color="Description",
    title="Monthly Revenue by Top 3 Categories",
    template=PLOT_TEMPLATE,
    markers=True,
)

fig_heatmap = px.imshow(
    df_weekday.set_index("Hour").T,
    labels=dict(x="Hour of Day", y="Day of Week", color="Sales"),
    title="Weekday Sales Pattern",
    template=PLOT_TEMPLATE,
    color_continuous_scale="Viridis",
)

fig_slow = px.scatter(
    df_product_stats,
    x="DaysSinceLastSale",
    y="TotalRevenue",
    color="Status",
    hover_data=["Description", "StockCode", "TotalQty"],
    title="Slow-Moving Items: Recency vs Revenue",
    template=PLOT_TEMPLATE,
)

# ---------- Objective 4 ----------
fig_dist = px.histogram(
    df_cust,
    x="TotalRevenue",
    nbins=80,
    title="Distribution of Customers by Monetary Value",
    template=PLOT_TEMPLATE,
    log_y=True,
)

fig_top_cust = px.bar(
    top10_cust,
    x="CustomerID",
    y="TotalRevenue",
    title="Top 10 Customers by Revenue",
    template=PLOT_TEMPLATE,
    color="TotalRevenue",
    color_continuous_scale="Viridis",
)

fig_country = px.bar(
    df_country.sort_values("OrderValue", ascending=False).head(10),
    x="OrderValue",
    y="Country",
    orientation="h",
    title="Top 10 Countries by Revenue",
    template=PLOT_TEMPLATE,
    color="OrderValue",
)
fig_country.update_layout(yaxis={"categoryorder": "total ascending"})

fig_region = px.pie(
    df_region,
    names="Region",
    values="OrderValue",
    title="Revenue Share by Region",
    template=PLOT_TEMPLATE,
    hole=0.45,
)

fig_world = px.choropleth(
    df_country,
    locations="Country",
    locationmode="country names",
    color="OrderValue",
    hover_name="Country",
    color_continuous_scale="Viridis",
    template=PLOT_TEMPLATE,
    title="Global Revenue Heatmap",
)
fig_world.update_geos(
    showcoastlines=True,
    showland=True,
    showcountries=True,
    projection_type="natural earth",
)
fig_world.update_layout(margin=dict(l=0, r=0, t=50, b=0))

fig_products = px.bar(
    df_products.sort_values("TotalRevenue", ascending=True),
    x="TotalRevenue",
    y="Description",
    orientation="h",
    title="Top 20 Products by Revenue (Bar)",
    template=PLOT_TEMPLATE,
    color="TotalRevenue",
    color_continuous_scale="Teal",
)

fig_products_treemap = px.treemap(
    top20_products,
    path=["Description"],
    values="TotalRevenue",
    color="TotalRevenue",
    color_continuous_scale="Blues",
    title="Revenue Share by Top 20 Products (Treemap)",
    template=PLOT_TEMPLATE,
)
fig_products_treemap.update_layout(margin=dict(l=0, r=0, t=40, b=0))

# ---------- RFM defaults ----------
fig_pca_default = build_pca_fig(df_rfm)
fig_3d_default = build_3d_fig(df_rfm)

# =========================================================
# 4. DASH APP – LAYOUT
# =========================================================
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP],
)
server = app.server

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.Span(
                [
                    html.I(className="bi bi-bar-chart-line-fill me-2"),
                    "E-Commerce Intelligence Hub",
                ],
                className="navbar-brand mb-0 h1",
            ),
            dbc.Badge("v1.0", color="info", className="ms-2"),
        ]
    ),
    color="black",
    dark=True,
    className="mb-4 shadow",
)

sidebar = dbc.Card(
    [
        dbc.CardHeader(
            html.H5("Controls", className="mb-0"),
            className="bg-dark",
        ),
        dbc.CardBody(
            [
                html.Label("Business Objective", className="fw-bold"),
                dbc.RadioItems(
                    id="objective-radio",
                    options=[
                        {"label": "1. Customer Segmentation", "value": "obj1"},
                        {"label": "2. Product Bundling", "value": "obj2"},
                        {"label": "3. Sales Trends", "value": "obj3"},
                        {"label": "4. Revenue Optimization", "value": "obj4"},
                    ],
                    value="obj1",
                    className="mb-4",
                    inputClassName="me-2",
                    labelClassName="d-block mb-2",
                ),
                html.Div(
                    id="segment-filter-wrapper",
                    children=[
                        html.Label("RFM Segment Filter", className="fw-bold"),
                        dcc.Dropdown(
                            id="segment-filter",
                            options=[{"label": s, "value": s} for s in segments],
                            value=segments,
                            multi=True,
                            placeholder="Select segments…",
                        ),
                        html.Small(
                            "Only applies to Customer Segmentation view.",
                            className="text-muted",
                        ),
                    ],
                ),
            ]
        ),
    ],
    className="shadow-lg",
)

section_obj1 = dbc.Card(
    [
        dbc.CardHeader(
            [
                html.H4(
                    "Objective 1 – Customer Segmentation (RFM & PCA)",
                    className="mb-0",
                )
            ]
        ),
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Graph(id="pca-graph", figure=fig_pca_default),
                            md=6,
                        ),
                        dbc.Col(
                            dcc.Graph(id="rfm-3d-graph", figure=fig_3d_default),
                            md=6,
                        ),
                    ],
                    className="gy-4",
                ),
                html.P(
                    "Hover on points to inspect CustomerID and RFM values.",
                    className="text-muted mt-2",
                ),
            ]
        ),
    ],
    id="section-obj1",
    className="shadow-lg",
)

section_obj2 = dbc.Card(
    [
        dbc.CardHeader(
            html.H4(
                "Objective 2 – Product Bundling Insights",
                className="mb-0",
            )
        ),
        dbc.CardBody(
            [
                html.P(
                    "Top co-purchased product pairs – ideal for bundle design and recommendations.",
                    className="text-muted",
                ),
                dcc.Graph(figure=fig_pairs, style={"height": "420px"}),
                html.Hr(),
                html.H6("Co-Purchase Frequency Heatmap"),
                dcc.Graph(figure=fig_pairs_heatmap, style={"height": "500px"}),
            ]
        ),
    ],
    id="section-obj2",
    className="shadow-lg",
    style={"display": "none"},
)

section_obj3 = dbc.Card(
    [
        dbc.CardHeader(
            html.H4(
                "Objective 3 – Sales Trend Analysis",
                className="mb-0",
            )
        ),
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H6("Daily Sales"),
                                dcc.Graph(
                                    figure=fig_daily,
                                    style={"height": "380px"},
                                ),
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                html.H6("Monthly Sales"),
                                dcc.Graph(
                                    figure=fig_monthly,
                                    style={"height": "380px"},
                                ),
                            ],
                            md=6,
                        ),
                    ],
                    className="gy-4",
                ),
                html.Hr(),
                html.H6("Monthly Revenue by Top 3 Categories", className="mt-2"),
                dcc.Graph(figure=fig_cat, style={"height": "380px"}),
                html.Hr(),
                html.H6("Weekday Sales Pattern"),
                dcc.Graph(figure=fig_heatmap, style={"height": "380px"}),
                html.Hr(),
                html.H6("Slow-Moving Items"),
                html.P(
                    "Products with very high days since last sale are candidates for markdowns or removal.",
                    className="text-muted",
                ),
                dcc.Graph(figure=fig_slow, style={"height": "380px"}),
            ]
        ),
    ],
    id="section-obj3",
    className="shadow-lg",
    style={"display": "none"},
)

section_obj4 = dbc.Card(
    [
        dbc.CardHeader(
            html.H4(
                "Objective 4 – Revenue Optimization Insights",
                className="mb-0",
            )
        ),
        dbc.CardBody(
            [
                html.H6("Global Revenue Map"),
                html.P(
                    "Darker countries indicate higher total revenue. Hover to see exact values.",
                    className="text-muted",
                ),
                dcc.Graph(figure=fig_world, style={"height": "450px"}),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H6("Customer Monetary Distribution"),
                                dcc.Graph(figure=fig_dist, style={"height": "380px"}),
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                html.H6("Top 10 Customers by Revenue"),
                                dcc.Graph(figure=fig_top_cust, style={"height": "380px"}),
                            ],
                            md=6,
                        ),
                    ],
                    className="gy-4",
                ),
                html.Hr(),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H6("Top Countries by Revenue"),
                                dcc.Graph(figure=fig_country, style={"height": "380px"}),
                            ],
                            md=6,
                        ),
                        dbc.Col(
                            [
                                html.H6("Revenue Share by Region"),
                                dcc.Graph(figure=fig_region, style={"height": "380px"}),
                            ],
                            md=6,
                        ),
                    ],
                    className="gy-4",
                ),
                html.Hr(),
                html.H6("Top 20 Products by Revenue (Bar)", className="mt-2"),
                dcc.Graph(figure=fig_products, style={"height": "380px"}),
                html.Hr(),
                html.H6("Top 20 Products by Revenue (Treemap)", className="mt-2"),
                dcc.Graph(figure=fig_products_treemap, style={"height": "500px"}),
            ]
        ),
    ],
    id="section-obj4",
    className="shadow-lg",
    style={"display": "none"},
)

content = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(sidebar, md=3),
                dbc.Col(
                    html.Div(
                        id="content-wrapper",
                        children=[
                            section_obj1,
                            section_obj2,
                            section_obj3,
                            section_obj4,
                        ],
                    ),
                    md=9,
                ),
            ],
            className="g-4",
        )
    ],
    fluid=True,
)

app.layout = html.Div([navbar, content])

# =========================================================
# 5. CALLBACKS
# =========================================================
@app.callback(
    Output("section-obj1", "style"),
    Output("section-obj2", "style"),
    Output("section-obj3", "style"),
    Output("section-obj4", "style"),
    Output("segment-filter-wrapper", "style"),
    Input("objective-radio", "value"),
)
def toggle_sections(selected_obj):
    show_block = {"display": "block"}
    hide = {"display": "none"}

    style1 = show_block if selected_obj == "obj1" else hide
    style2 = show_block if selected_obj == "obj2" else hide
    style3 = show_block if selected_obj == "obj3" else hide
    style4 = show_block if selected_obj == "obj4" else hide
    seg_style = show_block if selected_obj == "obj1" else hide

    return style1, style2, style3, style4, seg_style


@app.callback(
    Output("pca-graph", "figure"),
    Output("rfm-3d-graph", "figure"),
    Input("segment-filter", "value"),
)
def update_rfm_plots(selected_segments):
    if not selected_segments:
        filtered = df_rfm
    else:
        filtered = df_rfm[df_rfm["Segment"].isin(selected_segments)]
    return build_pca_fig(filtered), build_3d_fig(filtered)


# =========================================================
# 6. RUN (LOCAL ONLY)
# =========================================================
if __name__ == "__main__":
    app.run(debug=True)
