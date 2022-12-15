from plotly.subplots import make_subplots
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from plotly.graph_objs.layout import YAxis, XAxis, Margin
from numpy import abs
import time
from dash_bootstrap_templates import load_figure_template
from config import PY_TEMPLATE
import numpy as np


# Makes the Bootstrap Themed Plotly templates available
templates = [
    "bootstrap",
    "minty",
    "pulse",
    "flatly",
    "quartz",
    "cyborg",
    "darkly",
    "vapor",
    "materia"
]
load_figure_template(templates)


def plotly_subplots_realtime(time_data, open_data, high_data, low_data, close_data, price_ma1, price_ma2,
                             volume_data, vol_ma1, vol_ma2, on_balance_volume, vwap, vpoc,
                             visible, theme_name):

    # candlestick chart

    candlestick_trace = go.Candlestick(x=time_data,
                                       name="candlesticks",
                                       close=close_data,
                                       high=high_data,
                                       low=low_data,
                                       open=open_data,
                                       xaxis='x1',
                                       yaxis='y1',
                                       visible=visible['candlestick']
                                       )

    price_ma1_trace = go.Scattergl(x=time_data,
                                 y=price_ma1,
                                 xaxis="x1",
                                 yaxis="y1",
                                 name="price sma (slow)",
                                 line=dict(dash='dashdot', color='rgb(10,150,230)'),
                                 #marker=dict(autocolorscale=True),
                                 opacity=0.7,
                                 visible=visible['price_ma1']
                                 )

    price_ma2_trace = go.Scattergl(x=time_data,
                                 y=price_ma2,
                                 xaxis="x1",
                                 yaxis="y1",
                                 name="price sma (fast)",
                                 line=dict(dash='dashdot', color='rgb(100,150,150)'),
                                 #marker=dict(autocolorscale=True),
                                 opacity=0.7,
                                 visible=visible['price_ma2']
                                 )

    vol_sign = np.sign(close_data - open_data).values
    volume_colors = ['red' if p==-1 else 'green' if p==1 else 'grey' for p in vol_sign]
    volume_bars = go.Bar(x=time_data,
                         y=volume_data,
                         name="volume",
                         xaxis='x1',
                         yaxis='y2',
                         opacity=1.,
                         visible=visible['volume_bars'],
                         marker_color=volume_colors

                         )

    vol_ma1_trace = go.Scattergl(x=time_data,
                               y=vol_ma1,
                               xaxis="x1",
                               yaxis="y2",
                               name="volume sma1",
                               line=dict(dash='dashdot', color='rgb(10,150,230)'),
                               #marker=dict(autocolorscale=True),
                               opacity=1.,
                               visible=visible['volume_ma1']
                               )

    vol_ma2_trace = go.Scattergl(x=time_data,
                               y=vol_ma2,
                               xaxis="x1",
                               yaxis="y2",
                               name="volume sma2",
                               line=dict(dash='dashdot', color='rgb(150,150,10)'),
                               #marker=dict(autocolorscale=True),
                               opacity=1.,
                               visible=visible['volume_ma2']

                               )

    obv_bars = go.Bar(x=time_data,
                      y=on_balance_volume,
                      name="obv",
                      xaxis='x1',
                      yaxis='y3',
                      opacity=1.,
                      text=on_balance_volume,
                      visible=visible['on_balance_volume'],
                      #marker=dict(color="white")
                      )

    vwap_trace = go.Scattergl(x=time_data,
                            y=vwap,
                            name='VWAP',
                            xaxis='x1',
                            yaxis='y1',
                            line=dict(color='turquoise', width=3),
                            visible=visible['vwap']
                            )

    vpoc_trace = go.Scattergl(x=time_data,
                            y=vpoc,
                            name='VPOC',
                            xaxis='x1',
                            yaxis='y1',
                            line=dict(color='orange', width=1.5),
                            visible=visible['vpoc']
                            )



    data = [candlestick_trace, price_ma1_trace, price_ma2_trace, volume_bars, vol_ma1_trace, vol_ma2_trace, obv_bars,
            vwap_trace, vpoc_trace,]

    layout = go.Layout(
        template=theme_name,
        autosize=True,
        xaxis_rangeslider_visible=False,
        hovermode='closest',
        #paper_bgcolor="rgba(255,255,255,0.1)",
        #paper_bgcolor="rgba(200,200,200,0.0)",
        #plot_bgcolor="rgba(205,205,200,0.9)",
        xaxis=XAxis(
            title="Time",
            showgrid=True,
            visible=False
        ),
        yaxis=dict(
            domain=[0.3, 1],
            title="Index"
        ),
        yaxis2=dict(
            range=[0, np.max(volume_data)],
            domain=[0.15, 0.29],
            title="Volume",
            side="left",
        ),
        yaxis3=dict(
            domain=[0.0, 0.14],
            title="OBV",
            side="left",

        ),
    )
    return data, layout


def volume_profile_plot(volume_prof_ser, theme_name):

    volume_profile_trace = go.Bar(
                                  x=volume_prof_ser.values,
                                  y=volume_prof_ser.index,
                                  name="Volume profile",
                                  orientation='h',
                                  xaxis='x1',
                                  yaxis='y1',
                                  opacity=0.9,
                                  marker_color='gold',
                                  )

    data = [volume_profile_trace]

    layout = go.Layout(
        title='Overnight Volume Profile',
        template=theme_name,
        xaxis_rangeslider_visible=False,
        hovermode='closest',
        #paper_bgcolor="rgba(250,250,250,0.1)",
        #plot_bgcolor="rgba(205,205,200,1.)",
        xaxis=XAxis(
            range=[0, 1.1*volume_prof_ser.values.max()],
            tickmode='linear',
            tick0=0.1,
            dtick=0.1,
            showgrid=False,
            visible=False
        ),
        yaxis=YAxis(
            domain=[0.3, 1],
            visible=True,
            showgrid=True

        )
    )

    return data, layout
