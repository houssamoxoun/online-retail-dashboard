import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd

# 1. Load the dataset
# Ensure 'top10_product_pairs.csv' is in the same directory as this script
df = pd.read_csv('top10_product_pairs.csv')

# Create a readable label for the pair
df['Pair Name'] = df['ProductA_desc'].astype(str) + " + " + df['ProductB_desc'].astype(str)

# 2. Initialize the Dash app
app = dash.Dash(__name__)

# 3. Create the Interactive Figure
fig = px.bar(
    df,
    x='Frequency',
    y='Pair Name',
    orientation='h',  # Horizontal bar chart
    title='Top-10 Co-Purchased Product Pairs',
    labels={'Frequency': 'Co-Purchase Count', 'Pair Name': 'Product Combination'},
    color='Frequency',
    color_continuous_scale='Viridis',
    template='plotly_white'
)

# Invert y-axis to show the highest frequency at the top
fig.update_layout(yaxis={'categoryorder': 'total ascending'})

# 4. Define the Dashboard Layout
app.layout = html.Div([
    html.H1("Product Bundling Insights Dashboard", style={'textAlign': 'center'}),

    html.Div([
        html.P("This chart shows the most frequent product combinations found in transactions. "
               "These pairs are strong candidates for bundling promotions."),
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

    html.Div([
        dcc.Graph(figure=fig)
    ], style={'width': '90%', 'margin': '0 auto'}),
])

# 5. Run the Server
if __name__ == '__main__':
    app.run(debug=True)