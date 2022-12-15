# python imports
import math
import pickle
import time
from time import sleep
import datetime
import json

# dash, plotly imports
from typing import Tuple, List, Union, Dict, Any

import dash
import dash_bootstrap_components as dbc
import dash_extendable_graph as deg
import numpy as np
import pandas
import pandas as pd
import plotly.graph_objects
import plotly.graph_objects as go
from dash import ctx, callback, Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate
from dash_bootstrap_templates import ThemeSwitchAIO

# project imports
from plotly.graph_objs import Figure

import MySubplots
from config import *
from database_utilities import get_contract_location, read_date_from_db, read_indicators_from_db

# this is storage for user's trading history
trading_hist_df = pd.DataFrame()

# register page for dash url access
dash.register_page(__name__, path='/replay-view')


def precompute_vprof(input_date: datetime.date, min_intervals=5) -> None:
    """
    This function is used to pre-compute overnight volume profile data as it is resource heavy to do it during runtime.
    Function has no return value but simply stores volume profile data in database.
    @rtype: None
    @param input_date: datetime.date object
    @param min_intervals: interval in minutes for which to calculate volume profile data
    @return: None
    """
    base_dir = 'database/indicators/'
    midnight = datetime.time(0, 0)
    df = read_indicators_from_db(input_date, midnight, datetime.time(23, 59, 59))
    for h in range(5, 24):
        for m in range(0, 60, min_intervals):
            curr_time_dt = datetime.time(hour=h, minute=m)
            curr_time_str = curr_time_dt.strftime("%H-%M")
            [volume_profile, bins] = np.histogram(
                df[4][midnight:curr_time_dt], bins=33, weights=df[7][midnight:curr_time_dt].abs())
            volume_profile_ser = pd.Series(index=bins[:-1], data=volume_profile)
            index_frac = [math.modf(i)[0] for i in volume_profile_ser.index]
            index_whole = [math.modf(i)[1] for i in volume_profile_ser.index]
            new_frac = list(map(lambda x: (0 if x < 0.25
                                           else 0.25 if x < 0.50
            else 0.50 if x < 0.75 else 0.75), index_frac))
            new_index = [a + b for a, b in zip(index_whole, new_frac)]
            volume_profile_ser.index = new_index
            #  file name and path
            file_path = base_dir + get_contract_location(input_date)
            print("storing volume profile data in ", file_path + "volume_profile_{}.pkl".format(curr_time_str))
            file = open(file_path + "volume_profile_{}.pkl".format(curr_time_str), 'wb')
            pickle.dump(volume_profile_ser, file)
            file.close()


def layout():
    """
    This function creates layout for dash app Replay view.
    It is a lot of code but in summary there are 3 parts:
        1) side navbar on the rhs
        2) price chart in middle (Plotly figure)
        3) volume profile on the lhs (Plotly figure)
    """
    global market_data

    # read default dataframe
    market_data = read_date_from_db(default_visible_date)

    input_data = read_indicators_from_db(input_date=default_visible_date,
                                         starting_time=premark_open_time,
                                         ending_time=RTH_open_time)
    data, layout_price_chart = MySubplots.plotly_subplots_realtime(*input_data, visible_traces, theme_name="bootstrap")

    # volume profile
    precompute_vprof(default_visible_date, min_intervals=1)
    # volume profile
    #  file name and path
    base_dir = 'database/indicators/'
    file_path = base_dir + get_contract_location(default_visible_date)

    # current time is every 1mins
    curr_time_str = RTH_open_time.strftime("%H-%M")
    file = open(file_path + "volume_profile_{}.pkl".format(curr_time_str), 'rb')
    volume_profile_new = pickle.load(file)
    vp_data, vp_layout = MySubplots.volume_profile_plot(volume_profile_new, theme_name="bootstrap")
    vp_figure = go.Figure(data=vp_data, layout=vp_layout)

    print("reading pickle for dates picker ")
    pkl_file = open('database/database/market_data/tick_data/2022166b/dates_arr.pkl', 'rb')
    day_options = pickle.load(pkl_file)
    pkl_file.close()
    day_options = list(set(day_options))
    day_options = [datetime.datetime.strptime(day_option, "%m/%d/%Y").date() for day_option in day_options]
    day_options.sort()
    print("formatting time options for calendar picker")
    # open source database only contains 9/1/22
    day_options_disabled = pd.date_range(day_options[0], day_options[-1], freq='D').tolist()
    day_options_disabled = [date.date() for date in day_options_disabled if date.date() or date.date() != datetime.date(2022,9,22)]

    print("creating layout")
    # calendar
    calendar_picker_dcc = dcc.DatePickerSingle(
        id='my-date-picker-single',
        date=default_visible_date,
        min_date_allowed=day_options[0],
        max_date_allowed=day_options[-1],
        initial_visible_month=default_visible_date,
        disabled_days=day_options_disabled,
        calendar_orientation='horizontal',
        style={"margin-left": MARGIN_SIZE[SEL_SIZE]},
        disabled = True,  # open source code has no databse except for 9/1/22
    )

    sidebar_style = {
        "min-height": "95vh",
        # "background-color": "#f8f9fa",
        "box-shadow": "0.3rem 0.5rem 0.5rem gray"
        # "box-shadow": "inset 0 -3em 3em rgba(0, 0, 0, 0.1), 0 0 0 1px rgb(255, 255, 255), "
        #              "0.3em 0.3em 1em rgba(0, 0, 0, 0.3)",
    }

    chart_style = {"min-height": "95vh",
                   "box-shadow": "0.3rem 0.5rem 0.5rem gray"
                   }

    # fast forward button icon
    btn1_content = html.Span([html.Div('100x', style=dict(paddingRight='0.3vw', display='inline-block')),
                              html.I(className='fa-solid fa-forward')])
    ff_button = dbc.Button(children=btn1_content, id="ff_button", disabled=False, n_clicks=0, className="btn btn-secondary",
                           style=dict(textAlign='center'))

    # save button
    btn2_content = html.Span([html.I(className='fa-solid fa-file-waveform'),
                              html.Div('Save trades', style=dict(paddingLeft='0.3vw', display='inline-block')),
                              ])
    save_button = dbc.Button(children=btn2_content, id="save-val", n_clicks=0, className="btn btn-secondary",
                             style=dict(textAlign='center'))
    # export button
    btn2_content = html.Span([dcc.Download(id="download-trades-csv"),
                              html.I(className='fa-solid fa-download'),
                              html.Div('Export trades', style=dict(paddingLeft='0.3vw', display='inline-block')),
                              ])
    export_button = dbc.Button(children=btn2_content, id="export-val", n_clicks=0, className="btn btn-secondary",
                               style=dict(textAlign='center'))

    # buttons
    trade_button_rows = dbc.ButtonGroup([
        dbc.Button("Buy to open", id='b2o-val', class_name="btn btn-primary", n_clicks=0),
        dbc.Button("Sell to open", id='s2o-val', class_name="btn btn-primary", n_clicks=0),
        dbc.Button("Buy to cover", id='b2c-val', class_name="btn btn-primary", n_clicks=0),
        dbc.Button("Sell to close", id='s2c-val', class_name="btn btn-primary", n_clicks=0),
    ], className="btn-group btn-group-" + SCREEN_SIZE[SEL_SIZE], vertical=True,
        style={"margin-left": MARGIN_SIZE[SEL_SIZE], "margin-right": MARGIN_SIZE[SEL_SIZE]})
    misc_button_rows = dbc.ButtonGroup([
        save_button,
        export_button,
        ff_button,
    ], style={"margin-top": MARGIN_SIZE[SEL_SIZE], "margin-left": MARGIN_SIZE[SEL_SIZE],
              "margin-right": MARGIN_SIZE[SEL_SIZE]},
        className="btn-group btn-group-" + SCREEN_SIZE[SEL_SIZE], vertical=True)

    # range slider for price chart
    chart_range_slider = html.Div([
        html.Label("Chart range",
                   style={"padding-left": MARGIN_SIZE[SEL_SIZE], "padding-top": MARGIN_SIZE[SEL_SIZE]}
                   ),
        dcc.Slider(5, 480, 1,
                   value=CHART_SPAN,
                   marks={5: '5min',
                          60: '1hr',
                          120: '2hr',
                          240: '4hr',
                          480: '8hr',
                          1440: '24hr'
                          },
                   id='chart-range-slider',
                   ),

        html.Div(id='slider-output-container')
    ], style={"padding-left": MARGIN_SIZE[SEL_SIZE], "padding-top": MARGIN_SIZE[SEL_SIZE]}
    )

    # sampling period
    dropdown_sampling_rate = dbc.DropdownMenu(
        id='sampling-rate-dd',
        label="Candle duration",
        children=[
            html.Label('Seconds'),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem("1s", id='sel_1s', style={"text-align": "center"}),
            dbc.DropdownMenuItem("5s", id='sel_5s', style={"text-align": "center"}),
            dbc.DropdownMenuItem("10s", id='sel_10s', style={"text-align": "center"}),
            html.Label('Minutes'),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem("1m", id='sel_1m', style={"text-align": "center"}),
            dbc.DropdownMenuItem("5m", id='sel_5m', style={"text-align": "center"}),
            dbc.DropdownMenuItem("15m", id='sel_15m', style={"text-align": "center"}),
            dbc.DropdownMenuItem("30m", id='sel_30m', style={"text-align": "center"}),
            html.Label('Hours'),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem("1h", style={"text-align": "center"}),
            dbc.DropdownMenuItem("4h", style={"text-align": "center"}),
        ], className="btn-group dropright",
        style={"display": "none",  # hide it until its ready for production
               "margin-top": MARGIN_SIZE[SEL_SIZE], "margin-left": MARGIN_SIZE[SEL_SIZE],
               "margin-right": MARGIN_SIZE[SEL_SIZE]},
    )

    # info card (collapsable)
    alert_card = dbc.Alert(
        children="Layout loaded.", id='left-alert', duration=10000, is_open=True, color="primary",
        style={"padding-left": MARGIN_SIZE[SEL_SIZE], "padding-top": MARGIN_SIZE[SEL_SIZE]}
    )

    sidebar_div = html.Div([
        html.H2("Action bar",
                style={"font-size": TEXT_SIZE[SEL_SIZE], "padding-left": MARGIN_SIZE[SEL_SIZE],
                       "padding-top": MARGIN_SIZE[SEL_SIZE]}),
        html.Label("Trade",
                   style={"padding-left": MARGIN_SIZE[SEL_SIZE], "padding-top": MARGIN_SIZE[SEL_SIZE]}),
        dbc.Nav([trade_button_rows,
                 misc_button_rows,
                 html.Label("Choose date",
                            style={"padding-top": MARGIN_SIZE[SEL_SIZE], "padding-left": MARGIN_SIZE[SEL_SIZE]}),
                 calendar_picker_dcc,
                 dbc.Button(disabled=True, children="Submit", id="submit-date-button", type="submit",
                            style={"margin-left": MARGIN_SIZE[SEL_SIZE], "margin-right": MARGIN_SIZE[SEL_SIZE]},
                            className="btn btn-secondary btn-" + SCREEN_SIZE[SEL_SIZE], n_clicks=0),

                 dbc.Spinner(html.Div(id="loading-new-date")),
                 html.Br(),
                 chart_range_slider,
                 dropdown_sampling_rate,

                 ], vertical=True, pills=True),
        dbc.Col(
            [html.Label("Alerts"),
             alert_card], className="col",
            style={"margin-left": MARGIN_SIZE[SEL_SIZE], "margin-top": MARGIN_SIZE[SEL_SIZE]}),
    ], style=sidebar_style)

    return dbc.Container([dbc.Row([
        dcc.Store(id="trading-history-memory", data={}),
        dcc.Store(id="my-date-picker-single-mem", data=default_visible_date),
        dcc.Store(
            id="loading-replay",
           ),
        dcc.Interval(
            id='interval-component',
            interval=SPEED * 1000,
            n_intervals=0),
        dcc.Interval(
            id='interval-component2',
            interval=60 * 1000,
            n_intervals=0),

    ]),
        dbc.Row([
            dbc.Col([dbc.Card(sidebar_div, style={"height": "95vh"})], class_name='toggled',
                    width=WIDTH_SIDEBAR[SEL_SIZE]),
            dbc.Col([dbc.Card(deg.ExtendableGraph(
                id='price-chart',
                figure=dict(
                    data=data,
                    layout=layout_price_chart
                ),
                style=chart_style
            ), style={"min-height": "95vh", "height": "95vh"}),
            ], class_name='col', width=WIDTH_PRICE_CHART[SEL_SIZE]
            ),
            dbc.Col([dbc.Card(deg.ExtendableGraph(
                id='volume-profile-chart',
                figure=vp_figure,
                style=chart_style, responsive=True,
            ), style={"min-height": "95vh", "height": "95vh"}, ), ], class_name='col',
                width=WIDTH_VPROF_CHART[SEL_SIZE],
            )
        ],
        ),

    ], fluid=True, )


@dash.callback(Output('price-chart', 'extendData'),
               Output('volume-profile-chart', 'figure'),
               Input('interval-component', 'n_intervals'),
               Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
               State('my-date-picker-single-mem', 'data'),
               State('ff_button', 'n_clicks'),
               State('chart-range-slider', 'value'),
               prevent_initial_call=True,
               )
def update_chart_figures(n_intervals: int,
                         theme_bool: bool,
                         date_str: str,
                         ff_clicks: int,
                         chart_range: int) -> tuple:
    """
    Updates price chart and volume profile chart figures.
    interval for price-chart output is 1s. While volume profile chart updates every 1 minute.
    @param n_intervals: interval component runs indefinitely every 1s
    @param date_str: date format 'YYYY/MM/DD'
    @param ff_clicks: fastforward button clicks
    @param theme_bool: toggle theme, if True then light else dark
    @param chart_range: output of slider from 5min-4hour (in minutes)
    @return: list of extensions for price-chart figure and update of volume profile figure
    """
    # add 1 s to figure
    theme_name = "bootstrap" if theme_bool else "cyborg"
    if n_intervals is None:
        raise PreventUpdate
    print("Extending figure via Dash Output extendData")
    if n_intervals is not None:
        x_new = datetime.time(hour=ending_times[n_intervals + 100 * ff_clicks][0],
                              minute=ending_times[n_intervals + 100 * ff_clicks][1],
                              second=ending_times[n_intervals + 100 * ff_clicks][2])
    print("n_intervals ", n_intervals)
    print("increment time to ", x_new)
    # generate Y-value
    print("grabbing new datapoint")
    date_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    print("Start update price chart")
    input_data = read_indicators_from_db(date_dt, starting_time=premark_open_time, ending_time=x_new)
    print("End update price chart")
    open_new = input_data[1].values[-1]
    high_new = input_data[2].values[-1]
    low_new = input_data[3].values[-1]
    close_new = input_data[4].values[-1]
    price_sma1_new = input_data[5].values[-1]
    price_sma2_new = input_data[6].values[-1]
    volume_new = input_data[7].values[-1]
    volume_sma1_new = input_data[8].values[-1]
    volume_sma2_new = input_data[8].values[-1]
    on_balance_volume_new = input_data[10].values[-1]
    vwap_new = input_data[11].values[-1]
    vpoc_new = input_data[12].values[-1]

    # volume bar colors
    vol_sign = -1 if close_new - open_new < 0 else 1 if close_new - open_new > 0 else 0
    marker_color_new = 'red' if vol_sign == -1 else 'green' if vol_sign == 1 else 'grey'

    # volume profile
    #  file name and path
    base_dir = 'database/indicators/'
    file_path = base_dir + get_contract_location(date_dt)

    # current time is every 1mins
    start_vprof = time.time()
    curr_time_str = x_new.strftime("%H-%M")
    file = open(file_path + "volume_profile_{}.pkl".format(curr_time_str), 'rb')
    volume_profile_new = pickle.load(file)
    vp_data, vp_layout = MySubplots.volume_profile_plot(volume_profile_new, theme_name)
    vp_figure = go.Figure(data=vp_data, layout=vp_layout)
    end_vprof = time.time()
    print("Volume profile update ", end_vprof - start_vprof)
    x_new = list(input_data[0])[-1]
    print("update figure for time ", x_new)
    return [[dict(x=[x_new], close=[close_new], high=[high_new], low=[low_new], open=[open_new]), \
             dict(x=[x_new], y=[price_sma1_new]), \
             dict(x=[x_new], y=[price_sma2_new]), \
             {'x': [x_new], 'y': [volume_new], 'marker.color': [marker_color_new]}, \
             dict(x=[x_new], y=[volume_sma2_new]), \
             dict(x=[x_new], y=[volume_sma1_new]), \
             dict(x=[x_new], y=[on_balance_volume_new]), \
             dict(x=[x_new], y=[vwap_new]), \
             dict(x=[x_new], y=[vpoc_new]), \
             ], [0, 1, 2, 3, 4, 5, 6, 7, 8], chart_range * 6], vp_figure


@callback(Output('interval-component', 'n_intervals'),
          Output('ff_button', 'n_clicks'),
          Output('loading-new-date', 'children'),
          Input('submit-date-button', 'n_clicks'),
          State('interval-component', 'n_intervals'),
          prevent_initial_call=True,
          )
def pause_updates(n, n_int):
    """
    This callback function ensures interval component and ff buttons are reset after submit date is clicked
    """
    if n:
        sleep(1)
        return 0, 0, ''


@dash.callback(Output('price-chart', 'figure'),
               Output('loading-replay', 'data'),
               Output('my-date-picker-single-mem', 'data'),
               Input('submit-date-button', 'n_clicks'),
               Input('ff_button', 'n_clicks'),
               Input(ThemeSwitchAIO.ids.switch("theme"), "value"),
               Input('sel_1s', 'n_clicks'),
               Input('sel_5s', 'n_clicks'),
               Input('sel_10s', 'n_clicks'),
               Input('sel_1m', 'n_clicks'),
               Input('sel_5m', 'n_clicks'),
               Input('sel_15m', 'n_clicks'),
               Input('sel_30m', 'n_clicks'),
               Input('chart-range-slider', 'value'),
               State('my-date-picker-single', 'date'),
               State('my-date-picker-single-mem', 'data'),
               State('interval-component', 'n_intervals'),
               running=[
                   (Output('interval-component', 'disabled'), True, False),
                   (Output('ff_button', 'disabled'), True, False),
                   (Output('ff_button', 'disabled'), True, False),
                   (Output('submit-date-button', 'disabled'), True, False),
                   (Output('loading-new-date', 'children'), 'loading...', '')
               ],
               prevent_initial_call=True,
               background=True,
               cache_by=True
               )
def update_all_figures(submit_clicks: int,
                       ff_clicks: int,
                       theme_bool: bool,
                       dd_sel1: int, dd_sel2: int, dd_sel3: int, dd_sel4: int, dd_sel5: int, dd_sel6: int, dd_sel7: int,
                       chart_range: int,
                       date_choice: str,
                       current_date: str,
                       n_intervals: int) -> tuple:  # add other args for additional inputs
    """

    @param submit_clicks:
    @param ff_clicks:
    @param theme_bool:
    @param dd_sel1: candle duration 1s
    @param dd_sel2: candle duration 5s
    @param dd_sel3: candle duration 10s
    @param dd_sel4: candle duration 1m
    @param dd_sel5: candle duration 5m
    @param dd_sel6: candle duration 15m
    @param dd_sel7: candle duration 30m
    @param chart_range: x-axis range for price-chart
    @param date_choice: 'YYYY/MM/DD'
    @param n_intervals: intervals in 1s increments
    @return: new figure and loading
    """
    # read parquet DB for new selected date
    global market_data
    # toggle theme
    theme_name = "bootstrap" if theme_bool else "cyborg"
    if ctx.triggered_id == 'submit-date-button':
        new_date = datetime.datetime.strptime(date_choice, "%Y-%m-%d").date()
        # smart select contract month based on nearest expiration
        input_data = read_indicators_from_db(input_date=new_date, starting_time=premark_open_time,
                                             ending_time=RTH_open_time)
        data, layout_price_chart = MySubplots.plotly_subplots_realtime(*input_data, visible_traces, theme_name)
        new_figure = go.Figure(data=data, layout=layout_price_chart)
        # volume profile
        precompute_vprof(new_date, min_intervals=1)
        sleep(5)
        return new_figure, 'loading chart', date_choice

    else: #ctx.triggered_id == 'chart-range-slider' or ctx.triggered_id=='ff_button' or ctx.triggered_id=='theme':
        x_new = datetime.datetime(
            year=1,
            month=1,
            day=1,
            hour=ending_times[n_intervals + 100 * ff_clicks][0],
            minute=ending_times[n_intervals + 100 * ff_clicks][1],
            second=ending_times[n_intervals + 100 * ff_clicks][2])
        chart_range_hours = 0
        chart_range_mins = chart_range
        if RESAMPLE_PERIOD == '1s':
            while chart_range_mins > 59:
                chart_range_mins %= 60
                chart_range_hours += 1
        x_prev = x_new + datetime.timedelta(minutes=-chart_range_mins, hours=-chart_range_hours)
        x_new = x_new.time()
        x_prev = x_prev.time()

        new_date = datetime.datetime.strptime(current_date, "%Y-%m-%d").date()
        # smart select contract month based on nearest expiration
        input_data = read_indicators_from_db(input_date=new_date, starting_time=x_prev,
                                             ending_time=x_new)
        data, layout_price_chart = MySubplots.plotly_subplots_realtime(*input_data, visible_traces, theme_name)
        new_figure = go.Figure(data=data, layout=layout_price_chart)
        return new_figure, 'loading chart', current_date

    # to do: implement different sampling here
    # use sample values for indicators
    # change candlestick, volume, and OBV sampling, specificially, open, close, high low price data
"""
    if ctx.triggered_id == 'sel_1s':
        pass
    elif ctx.triggered_id == 'sel_5s':
        pass
    elif ctx.triggered_id == 'sel_10s':
        pass
    elif ctx.triggered_id == 'sel_1m':
        pass
    elif ctx.triggered_id == 'sel_5m':
        pass
    elif ctx.triggered_id == 'sel_15m':
        pass
    elif ctx.triggered_id == 'sel_30m':
        pass
"""

@callback(Output('left-alert', 'children'),
          Output('left-alert', 'is_open'),
          Output('trading-history-memory', 'data'),
          [Input("b2o-val", "n_clicks"),
           Input("s2o-val", "n_clicks"),
           Input("s2c-val", "n_clicks"),
           Input("b2c-val", "n_clicks"),
           Input("save-val", "n_clicks"),
           State('my-date-picker-single-mem', 'data'),
           State('price-chart', "figure"),
           State('trading-history-memory', 'data'),
           ],
          prevent_initial_call=True
          )
def write_trade_history(b2o_click: int, s2o_click: int, s2c_click: int, b2c_click: int, save_click: int,
                        date_choice: str, chart: plotly.graph_objects.Figure, trading_history_json: dict) -> tuple:
    """
    Callback function for storing, and writing user's trade history to disk.
    @param b2o_click: buy to open clicks
    @param s2o_click: sell to open (short) clicks
    @param s2c_click: sell to close clicks
    @param b2c_click: buy to close (cover) clicks
    @param save_click: saves trades
    @param date_choice: date state
    @param chart: price-chart figure state
    @param trading_history_json: trading history state
    @return: alert (str type), activate alert (bool type), store trading history (json type)
    """
    msg = "no trading history"
    if b2o_click or s2o_click or s2c_click or b2c_click:
        order_price = chart['data'][0]['close'][-1]
        order_time = chart['data'][0]['x'][-1].split('T')[1]
        num_indicators = len(chart['data'])
        indicators = dict()
        for num in range(1, num_indicators):
            indicators[chart['data'][num]['name']] = chart['data'][num]['y'][-1]
        if trading_history_json == {}:
            trading_history_df = pd.DataFrame(columns=["date", "order_time", "order_price", "order_type"] + list(indicators.keys()),
            )
        else:
            trading_history_df = pd.DataFrame(trading_history_json,
                                columns=["date", "order_time", "order_price", "order_type"] + list(indicators.keys()),
                                )
    if "b2o-val" == ctx.triggered_id:
        msg = "Buy to open 1 contract @ {}".format(order_price)
        hist_new = pd.DataFrame(np.array([[date_choice, order_time, order_price, order_types["b2o"]] + list(indicators.values())]),
                                columns=["date", "order_time", "order_price", "order_type"] + list(indicators.keys()),
                                )
        trading_history_df = pd.concat([trading_history_df, hist_new], ignore_index=True, axis=0)
    elif "s2o-val" == ctx.triggered_id:
        msg = "Sold to open (short) 1 contract @ {}".format(order_price)
        hist_new = pd.DataFrame(np.array([[date_choice, order_time, order_price, order_types["s2o"]] + list(indicators.values())]),
                                columns=["date", "order_time", "order_price", "order_type"] + list(indicators.keys()),
                                )
        trading_history_df = pd.concat([trading_history_df, hist_new], ignore_index=True, axis=0)
    elif "s2c-val" == ctx.triggered_id:
        msg = "Sold to close 1 contract @ {}".format(order_price)
        hist_new = pd.DataFrame(np.array([[date_choice, order_time, order_price, order_types["s2c"]] + list(indicators.values())]),
                                columns=["date", "order_time", "order_price", "order_type"] + list(indicators.keys()),
                                )
        trading_history_df = pd.concat([trading_history_df, hist_new], ignore_index=True, axis=0)
    elif "b2c-val" == ctx.triggered_id:
        msg = "Bought to cover 1 contract @ {}".format(order_price)
        hist_new = pd.DataFrame(np.array([[date_choice, order_time, order_price, order_types["b2c"]] + list(indicators.values())]),
                                columns=["date", "order_time", "order_price", "order_type"] + list(indicators.keys()),
                                )
        trading_history_df = pd.concat([trading_history_df, hist_new], ignore_index=True, axis=0)
    if "save-val" == ctx.triggered_id:
        trading_filename = "trading_hist.csv"
        trading_history_df.to_csv('trade_history/' + trading_filename, index=False, mode='a')
        msg = "Saved trading activity in trade_history/{}".format(trading_filename)

    return msg, True, trading_history_df.to_dict()


@callback(
    Output("download-trades-csv", "data"),
    Input("export-val", "n_clicks"),
    State('trading-history-memory', 'data'),
    prevent_initial_call=True,
)
def download_file(n_clicks, trading_hist_json):
    """
    download csv file of trade history
    @param n_clicks:
    @return:
    """
    trading_history_df = pd.DataFrame(trading_hist_json)
    return dcc.send_data_frame(trading_history_df.to_csv, "my_trades.csv")
