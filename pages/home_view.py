import dash
from dash import html, Input, Output
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeSwitchAIO


dash.register_page(__name__, path="/")

layout = html.Div(
    dbc.Card(id="home-page-card",
        children=[
            html.Iframe(
                id="home-page-iframe",
                src="../assets/home_page_new.html",
                style={"height": "100vh",
                       "background-color": "black",
                       "font-color": "white",
                }
            )], style={
                       "height": "100vh",
                       "display": "flex",
                       "align": "center"}#"margin-left": "15%"},

    )
)


@dash.callback(Output("home-page-iframe", "className"),
               Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
               prevent_initial_callback=True
               )
def toggle_home_page_style(theme_name):
    # to do: figure out how to change home page to dark mode
    pass
