import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd

# 1. Load the dataset
# Ensure 'rfm.csv' is in the same directory as this script
df = pd.read_csv('rfm.csv')

# 2. Initialize the Dash app
app = dash.Dash(__name__)

# 3. Create the Interactive Figures

# Objective 1: PCA Visualization (2D Scatter)
fig_pca = px.scatter(
    df,
    x='PCA1',
    y='PCA2',
    color='Segment',
    title='Objective 1: Customer Segmentation - PCA Visualization',
    template='plotly_white',
    hover_data=['CustomerID', 'Recency', 'Frequency', 'Monetary']
)

# Objective 2: 3D Customer Segmentation (RFM Features)
fig_3d = px.scatter_3d(
    df,
    x='Recency',
    y='Frequency',
    z='Monetary',
    color='Segment',
    title='Objective 2: 3D Customer Segmentation (RFM Features)',
    template='plotly_white',
    hover_data=['CustomerID'],
    opacity=0.7
)

# Update layout for better 3D view sizing
fig_3d.update_layout(margin=dict(l=0, r=0, b=0, t=40))

# 4. Define the Dashboard Layout
app.layout = html.Div([
    html.H1("Customer Segmentation Dashboard", style={'textAlign': 'center'}),

    # Section for PCA Visualization
    html.Div([
        dcc.Graph(figure=fig_pca)
    ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),

    # Section for 3D Visualization
    html.Div([
        dcc.Graph(figure=fig_3d)
    ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),

    html.Div([
        html.P("Hover over points to see Customer ID and details. Drag to rotate the 3D plot.")
    ], style={'textAlign': 'center', 'marginTop': '20px'})
])

# 5. Run the Server
if __name__ == '__main__':
    app.run(debug=True)