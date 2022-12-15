#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 14:23:18 2022

@author: tradineer
"""
import datetime

TOLERANCE = 10**-2

# debug flags
DEBUG_MODE = 0
DEBUG_DATE = datetime.date(2005, 9, 5)
DEBUG_TIME = datetime.time(8, 30)


# RTH Eeastern standard time
offset_time = False
# timezone per data from https://firstratedata.com/c/main/Gn4T1uV8_E26-cSYTEMfYA
# note ES seems to be CST and VX is EST
premark_open_time = datetime.time(6, 30, 00)
RTH_open_time = datetime.time(8, 30, 00)
RTH_close_time = datetime.time(16, 00, 00)
RTH_IB_time = datetime.time(10)
premarket_open_time = '6:30:00'
market_open_time = '8:30:00'
market_close_time = '16:00:00'  # change closing time because 17:00 is problematic
# calculate how many minutes between IB close and RTH close
dateTimeA = datetime.datetime.combine(datetime.date.today(), RTH_close_time)
dateTimeB = datetime.datetime.combine(datetime.date.today(), RTH_IB_time)
IB_RTH_close_delta = int( (dateTimeA-dateTimeB).total_seconds() / 60 )
# analysis dates
ana_start_date = '2021-09-06'
ana_end_date = '2022-09-05'
# choose filtering
VX_filter = False
VX_range = [20, 30]  # e.g., between 15 and 25 all inclusive

# for stats
percent_incr = [0.0, 0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009, 0.01, 0.011, 0.012, 0.013, 0.014, 0.015, 0.016, 0.017, 0.018, 0.019, 0.02, 0.021, 0.022, 0.023, 0.024, 0.025, 0.026, 0.027, 0.028, 0.029, 0.03, 0.031, 0.032, 0.033, 0.034, 0.035, 0.036, 0.037, 0.038, 0.039, 0.04, 0.041, 0.042, 0.043, 0.044, 0.045, 0.046, 0.047,
                0.048, 0.049, 0.05, 0.051, 0.052, 0.053, 0.054, 0.055, 0.056, 0.057, 0.058, 0.059, 0.06, 0.061, 0.062, 0.063, 0.064, 0.065, 0.066, 0.067, 0.068, 0.069, 0.07, 0.071, 0.072, 0.073, 0.074, 0.075, 0.076, 0.077, 0.078, 0.079, 0.08, 0.081, 0.082, 0.083, 0.084, 0.085, 0.086, 0.087, 0.088, 0.089, 0.09, 0.091, 0.092, 0.093, 0.094, 0.095, 0.096, 0.097, 0.098, 0.099]

# mid price var
percent_ch = [-10.   ,  -9.375,  -8.75 ,  -8.125,  -7.5  ,  -6.875,  -6.25 ,
        -5.625,  -5.   ,  -4.375,  -3.75 ,  -3.125,  -2.5  ,  -1.875,
        -1.25 ,  -0.625,   0.   ,   0.625,   1.25 ,   1.875,   2.5  ,
         3.125,   3.75 ,   4.375,   5.   ,   5.625,   6.25 ,   6.875,
         7.5  ,   8.125,   8.75 ,   9.375,  10.   ]

hist_bins_count = 33


# select Parquet DB LUT
parquet_db_filename_2021 = {"ESU22_2021_{}.parquet".format(i) for i in range(1, 13)}
parquet_db_filename_2022 = ["ESU22_2022_{}.parquet".format(i) for i in range(1, 13)]
parquet_db_dict_2021 = {}
for i, filename in enumerate(parquet_db_filename_2021):
    parquet_db_dict_2021[i+1] = filename
parquet_db_dict_2022 = {}
for i, filename in enumerate(parquet_db_filename_2022):
    parquet_db_dict_2022[i+1] = filename

# for dash app

print("generate time intervals in seconds")
# global vars
CHART_SIZE_DICT = dict(DesktopUHD='2100px',
                  DesktopHD='1100px',
                  Desktop='900px',
                  Tablet='700px',
                  Phablet='500px',
                  Mobile='350px',)

CHART_SIZE = CHART_SIZE_DICT['DesktopUHD']

CHART_SPAN = 30  # minutes
RESAMPLE_PERIOD = '10s'  # seconds (actual replay data agg)
SPEED = 30  # interval callback component in seconds
RESAMPLE_PERIOD_STR = {'1s': '00:00:01', '5s': '00:00:05', '10s': '00:00:10', '30s': '00:00:30',
                       '1min': '00:01:00', '5min': '00:05:00',}[RESAMPLE_PERIOD]
if RESAMPLE_PERIOD == '1min' or RESAMPLE_PERIOD == '5min':
    ending_times = []
    starting_times = []
    for h in range(RTH_open_time.hour, 16):
        for m in range(0, 60):
            ending_times.append([h, m, 0])
    for h in range(RTH_open_time.hour, 16):
        for m in range(0, 60):
            for s in range(0, 60):
                starting_times.append([h, m, 0])
    ending_times = ending_times[30:]
elif RESAMPLE_PERIOD == '1s':
    ending_times = []
    starting_times = []
    for h in range(RTH_open_time.hour, 16):
        for m in range(0, 60):
            for s in range(0, 60):
                ending_times.append([h, m, s])
    ending_times = ending_times[60*30:]
    for h in range(RTH_open_time.hour, 16):
        for m in range(0, 60):
            for s in range(0, 60):
                starting_times.append([h, m, s])
    starting_times = starting_times[60*15:]
elif RESAMPLE_PERIOD == '10s':
    ending_times = []
    for h in range(RTH_open_time.hour, 16):
        for m in range(0, 60):
            for s in range(0, 60, 10):
                ending_times.append([h, m, s])
    ending_times = ending_times[6*30:]


order_types = {"b2o": "buy to open",
               "s2c": "sell to close",
               "s2o": "short to open",
               "b2c": "buy to cover"}

# for dash app
SEL_SIZE = "S"
SCREEN_SIZE = {"S": "sm", "M": "md", "L": "lg"}
MARGIN_SIZE = {"S": "1rem", "M": "1.5rem", "L": "2rem"}
TEXT_SIZE = {"S": "1em", "M": "1.5em", "L": "2em"}
WIDTH_SIDEBAR = {"S": 2, "L": 1}
WIDTH_PRICE_CHART = {"S": 8, "L": 10}
WIDTH_VPROF_CHART = {"S": 2, "L": 1}

default_visible_date = datetime.date(2022, 9, 1)

visible_traces = dict(
    candlestick=True,
    price_ma1=True,
    price_ma2=True,
    volume_bars=True,
    volume_ma1=False,
    volume_ma2=False,
    on_balance_volume=True,
    vwap=True,
    vpoc=True,
    volume_profile=False,
)

vwap_vis_traces = dict(
    candlestick=False,
    price_ma1=False,
    price_ma2=False,
    volume_bars=False,
    volume_ma1=False,
    volume_ma2=False,
    on_balance_volume=False,
    vwap=False,
    vpoc=False,
    volume_profile=True,
)

# plotly template
PY_TEMPLATE = "bootstrap"
GLOBAL_THEME = "bootstrap"

#PY_TEMPLATE = "darkly"
#GLOBAL_THEME = "darkly"


# contract selection
CONTRACT_MONTH_DICT = dict(
    march="H",
    june="M",
    september="U",
    december="Z",
)
