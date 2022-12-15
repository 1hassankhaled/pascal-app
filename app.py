# python imports
import os
import ssl
from time import sleep
import dash
from dash import html, Input, Output, State, ctx, dcc, DiskcacheManager, CeleryManager
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeSwitchAIO, load_figure_template
# project modules
from config import *


# This loads the "cyborg" themed figure template from dash-bootstrap-templates library,
# adds it to plotly.io and makes it the default figure template.
load_figure_template(["bootstrap", "cyborg"])

# for long callbacks use Celery or diskcache
if 'REDIS_URL' in os.environ:
    # Use Redis & Celery if REDIS_URL set as an env variable
    from celery import Celery

    celery_app = Celery(__name__,
                        broker=os.environ['REDIS_URL'],
                        backend=os.environ['REDIS_URL'],
                        broker_use_ssl={
                            'ssl_cert_reqs': ssl.CERT_NONE
                        },
                        redis_backend_use_ssl={
                            'ssl_cert_reqs': ssl.CERT_NONE
                        },
                        imports=['pages.home_view', 'pages.replay_view']
                        )
    background_callback_manager = CeleryManager(celery_app)

else:
    # Diskcache for non-production apps when developing locally
    import diskcache

    cache = diskcache.Cache("./cache")
    background_callback_manager = DiskcacheManager(cache)

# instantiate main dash app
app = dash.Dash(name=__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
                use_pages=True,
                background_callback_manager=background_callback_manager)




# navbar logo
LOGO = "assets/vectorstock_21659340.png"
# load pages
pages = list(dash.page_registry.values())
# load themes
template_theme1 = "bootstrap"
template_theme2 = "cyborg"
url_theme1 = dbc.themes.BOOTSTRAP
url_theme2 = dbc.themes.CYBORG
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
toggle_global_theme = ThemeSwitchAIO(aio_id="theme", themes=[url_theme1, url_theme2], )


# create navbar icons
home_icon = html.Span([html.I(className='fa-solid fa-house'),
                       html.Div('Home', style=dict(paddingLeft='0.3vw', display='inline-block')),
                       ])
replay_icon = html.Span([html.I(className='fa-solid fa-rotate-right'),
                         html.Div('Replay', style=dict(paddingLeft='0.3vw', display='inline-block')),
                         ])
live_icon = html.Span([html.I(className='fa-solid fa-hourglass-start'),
                       html.Div('Live', style=dict(paddingLeft='0.3vw', display='inline-block')),
                       ])
backtest_icon = html.Span([html.I(className='fa-solid fa-ruler'),
                           html.Div('Test', style=dict(paddingLeft='0.3vw', display='inline-block')),
                           ])
analysis_icon = html.Span([html.I(className="fa-solid fa-magnifying-glass-chart"),
                           html.Div('Analysis', style=dict(paddingLeft='0.3vw', display='inline-block')),
                           ])

# create navbar Dash layout
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=True),
    dbc.Row(dcc.Loading(
        id="loading-nav",
        fullscreen=True,
        children=[html.Div([html.Div(id="loading-output")])],
        type="cube", style={"z-index": 1})),
    dbc.Row(dbc.Col(dbc.Nav(
        [html.Img(src=LOGO, height="50px", style={"margin-left": "4rem"}),
         dbc.NavbarBrand("Pascal", className="navbar-brand mb-0 h1",
                         style={
                             "font-size": "36px",
                             "padding-right": "14rem",
                             "padding-left":
                                 MARGIN_SIZE[
                                     SEL_SIZE]}),
         dbc.NavItem([dbc.NavLink(children=home_icon, id="home-nav-link", active=True, href=pages[0]["relative_path"],
                                  style={"font-size": TEXT_SIZE[SEL_SIZE]}),
                      dbc.Tooltip("Visit main page", target="home-nav-link", placement="bottom")]),
         dbc.NavItem(
             [dbc.NavLink(children=replay_icon, id="replay-nav-link", active=False, href=pages[1]["relative_path"],
                          style={"font-size": TEXT_SIZE[SEL_SIZE]}),
              dbc.Tooltip("Replay market page", target="replay-nav-link", placement="bottom")]),
         dbc.NavItem([html.Span(dbc.NavLink("Live", "live-nav-link", active=False, disabled=True, href="#",
                                            style={"font-size": TEXT_SIZE[SEL_SIZE]}), id="live-span"),
                      dbc.Tooltip("Under construction", target="live-span", placement="bottom")]),
         dbc.NavItem([html.Span(dbc.NavLink("Backtest", "backtest-nav-link", active=False, disabled=True, href="#",
                                            style={"font-size": TEXT_SIZE[SEL_SIZE]}), id="backtest-span"),
                      dbc.Tooltip("Under construction", target="backtest-span", placement="bottom")]),
         dbc.NavItem([html.Span(dbc.NavLink("Analysis", "analysis-nav-link", active=False, disabled=True, href="#",
                                            style={"font-size": TEXT_SIZE[SEL_SIZE]}), id="analysis-span"),
                      dbc.Tooltip("Under construction", target="analysis-span", placement="bottom")]),
         #dbc.NavItem(
         #    dbc.NavLink("Help", id="help-nav-link", href="#", active=False, style={"font-size": TEXT_SIZE[SEL_SIZE]}),
         #    style={"margin-right": MARGIN_SIZE[SEL_SIZE]}),
         toggle_global_theme,
         ], pills=True, justified=True,
        style={"margin-bottom": MARGIN_SIZE[SEL_SIZE], "padding": MARGIN_SIZE[SEL_SIZE],
               "box-shadow": "0.3rem 0.5rem 0.5rem gray"
               # "box-shadow": "inset 0 -3em 3em rgba(0, 0, 0, 0.1), 0 0 0 1px rgb(255, 255, 255), "
               #              "0.3em 0.3em 1em rgba(0, 0, 0, 0.3)"
               },
    ), ), justify=True, align="start", ),
    dash.page_container], fluid=True, )


# callback to activate link for navbar clicks or url change
@app.callback(Output("home-nav-link", "active"),
              Output("replay-nav-link", "active"),
              Output("loading-nav", "children"),
              [Input("home-nav-link", "n_clicks"),
               Input("replay-nav-link", "n_clicks"),
               Input("url", "pathname")],
              prevent_initial_call=True)
def activate_link(n_clicks1, n_clicks2, url_pathname):
    if ctx.triggered_id == "home-nav-link" or url_pathname=='/':
        return True, False, " "
    elif ctx.triggered_id == "replay-nav-link" or url_pathname=='/replay-view':
        return False, True, " "


# run app server
server = app.server

if __name__ == "__main__":
    app.run_server(debug=True)
