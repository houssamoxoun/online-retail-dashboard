import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# 1. Load Datasets
# Ensure all CSV files are in the same directory
df_daily = pd.read_csv('daily_sales.csv')
df_monthly = pd.read_csv('monthly_sales.csv')
df_cat_monthly = pd.read_csv('category_monthly_sales.csv')
df_weekday = pd.read_csv('weekday_sales_pattern.csv')
df_product_stats = pd.read_csv('product_stats.csv')

# --- Pre-processing ---

# Daily: Add index as 'Day' since no date column exists
df_daily['Day'] = df_daily.index

# Monthly: Add generic Month labels
df_monthly['Month'] = [f"M{i + 1}" for i in range(len(df_monthly))]

# Top 3 Categories
month_cols = [c for c in df_cat_monthly.columns if c != 'Description']
df_cat_monthly['Total'] = df_cat_monthly[month_cols].sum(axis=1)
top3_cats = df_cat_monthly.nlargest(3, 'Total')['Description'].tolist()
df_top3 = df_cat_monthly[df_cat_monthly['Description'].isin(top3_cats)]
df_top3_melt = df_top3.melt(id_vars=['Description'], value_vars=month_cols, var_name='Month', value_name='Sales')

# Weekday: Sort by Hour
df_weekday = df_weekday.sort_values('Hour')

# Slow Movers: Define a threshold for coloring (e.g., > 90 days)
df_product_stats['Status'] = df_product_stats['DaysSinceLastSale'].apply(lambda x: 'Slow Mover' if x > 90 else 'Active')

# 2. Initialize Dash App
app = dash.Dash(__name__)

# 3. Layout
app.layout = html.Div([
    html.H1("Sales Trend Analysis Dashboard", style={'textAlign': 'center', 'marginBottom': '30px'}),

    # Row 1: Daily and Monthly Trends
    html.Div([
        html.Div([
            html.H3("Daily Sales Trend"),
            dcc.Graph(id='daily-trend', figure=px.line(df_daily, x='Day', y='OrderValue', title='Daily Sales'))
        ], style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            html.H3("Monthly Sales Trend"),
            dcc.Graph(id='monthly-trend',
                      figure=px.line(df_monthly, x='Month', y='OrderValue', markers=True, title='Monthly Sales'))
        ], style={'width': '48%', 'display': 'inline-block'})
    ]),

    # Row 2: Category Trends
    html.Div([
        html.H3("Monthly Revenue by Top 3 Categories"),
        dcc.Graph(id='category-trend',
                  figure=px.line(df_top3_melt, x='Month', y='Sales', color='Description', markers=True))
    ], style={'marginTop': '30px'}),

    # Row 3: Weekday Pattern (Heatmap)
    html.Div([
        html.H3("Weekday Sales Pattern (Heatmap)"),
        dcc.Graph(id='weekday-heatmap', figure=px.imshow(
            df_weekday.set_index('Hour').T,  # Transpose for Days on Y-axis, Hours on X-axis (standard reading)
            labels=dict(x="Hour of Day", y="Day of Week", color="Sales"),
            color_continuous_scale='Viridis'
        ))
    ], style={'marginTop': '30px'}),

    # Row 4: Slow Moving Items
    html.Div([
        html.H3("Identifying Slow-Moving Items"),
        html.P("Items with high 'Days Since Last Sale' are candidates for clearance."),
        dcc.Graph(id='slow-movers', figure=px.scatter(
            df_product_stats,
            x='DaysSinceLastSale',
            y='TotalRevenue',
            color='Status',
            hover_data=['Description', 'StockCode', 'TotalQty'],
            title='Inventory Performance: Recency vs Revenue',
            color_discrete_map={'Slow Mover': 'red', 'Active': 'blue'}
        ))
    ], style={'marginTop': '30px', 'marginBottom': '50px'})
])

# 4. Run Server
if __name__ == '__main__':
    app.run(debug=True)