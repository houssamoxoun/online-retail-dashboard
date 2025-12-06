from dash import Dash, dcc, html
import plotly.express as px
import pandas as pd

# 1. Initialize the Dash app
app = Dash(__name__)

# 2. Get Data
# Plotly Express has built-in datasets for practice.
# Here we use 'gapminder' containing country data like GDP, population, etc.
df = px.data.gapminder().query("year==2007")

# 3. Create the Map Figure
# 'iso_alpha' is the 3-letter country code (required for accurate mapping)
fig = px.choropleth(
    df,
    locations="iso_alpha",  # Column containing country codes
    color="lifeExp",  # Column defining the color intensity
    hover_name="country",  # Column to display on hover
    color_continuous_scale=px.colors.sequential.Plasma,
    title="Global Life Expectancy (2007)",
    projection="natural earth"  # Options: 'equirectangular', 'mercator', 'orthographic', etc.
)

# 4. Define the App Layout
app.layout = html.Div([
    html.H1("World Map in Dash", style={'textAlign': 'center'}),

    # The map is rendered inside this component
    dcc.Graph(
        id='life-exp-map',
        figure=fig,
        style={'height': '80vh'}  # Make the map take up 80% of the viewport height
    )
])

# 5. Run the App
# ✅ NEW WAY (Correct)
if __name__ == '__main__':
    app.run(debug=True)