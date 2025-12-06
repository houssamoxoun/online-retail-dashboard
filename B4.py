import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd

# 1. Load Datasets
# Ensure files are in the same directory
df_cust = pd.read_csv('customer_revenue_clv.csv')
df_country = pd.read_csv('country_revenue.csv')
df_region = pd.read_csv('region_revenue.csv')
df_products = pd.read_csv('top_products_by_revenue.csv')

# --- Pre-processing ---
# Top 10 Customers
top10_cust = df_cust.nlargest(10, 'TotalRevenue')
top10_cust['CustomerID'] = top10_cust['CustomerID'].astype(str)

# 2. Initialize Dash App
app = dash.Dash(__name__)

# 3. Create Interactive Figures

# Objective 4.1: Distribution (Histogram)
fig_dist = px.histogram(
    df_cust,
    x='TotalRevenue',
    nbins=100,
    log_y=True, # Log scale for Y to see low-frequency high-value bins
    title='Distribution of Customers by Monetary Value',
    template='plotly_white',
    labels={'TotalRevenue': 'Total Revenue ($)'}
)

# Objective 4.2: Top Customers
fig_top_cust = px.bar(
    top10_cust,
    x='CustomerID',
    y='TotalRevenue',
    title='Top 10 Highest Revenue Customers',
    template='plotly_white',
    color='TotalRevenue',
    color_continuous_scale='Viridis'
)

# Objective 4.3: Revenue by Country (Map)
# Ideally, we'd use a choropleth map, but a bar chart is safer without ISO codes.
# Let's stick to a bar chart for clarity as requested by the "csv available" format.
fig_country = px.bar(
    df_country.sort_values('OrderValue', ascending=False).head(10),
    x='OrderValue',
    y='Country',
    orientation='h',
    title='Top 10 Countries by Revenue',
    template='plotly_white',
    color='OrderValue'
)
fig_country.update_layout(yaxis={'categoryorder': 'total ascending'})

# Objective 4.4: Revenue by Region (Pie Chart)
fig_region = px.pie(
    df_region,
    names='Region',
    values='OrderValue',
    title='Revenue Share by Region',
    hole=0.4 # Donut chart style
)

# Objective 4.5: Top Products
fig_products = px.bar(
    df_products.sort_values('TotalRevenue', ascending=True), # Sort for horizontal bar
    x='TotalRevenue',
    y='Description',
    orientation='h',
    title='Top 20 Products by Revenue',
    template='plotly_white',
    color='TotalRevenue',
    color_continuous_scale='Teal'
)

# 4. Layout
app.layout = html.Div([
    html.H1("Revenue Optimization Insights", style={'textAlign': 'center', 'marginBottom': '30px'}),

    # Row 1: Customer Insights
    html.Div([
        html.Div([dcc.Graph(figure=fig_dist)], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(figure=fig_top_cust)], style={'width': '48%', 'display': 'inline-block'}),
    ]),

    # Row 2: Geographic Insights
    html.Div([
        html.Div([dcc.Graph(figure=fig_country)], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(figure=fig_region)], style={'width': '48%', 'display': 'inline-block'}),
    ], style={'marginTop': '30px'}),

    # Row 3: Product Insights
    html.Div([
        dcc.Graph(figure=fig_products)
    ], style={'width': '98%', 'marginTop': '30px', 'marginBottom': '50px'})
])

# 5. Run Server
if __name__ == '__main__':
    app.run(debug=True)