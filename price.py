#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from pandas import Series
from config import RESAMPLE_PERIOD

"""
Created on Mon Jun 27 16:49:02 2022

@author: tradineer
"""


class DailyMarketLevels:
    """DailyMarketLevels class wraps key price levels intraday."""

    def __init__(self):
        self.day_of_week = None
        self.HoD_timestamp = 0
        self.HoD = 0
        self.LoD_timestamp = 0
        self.LoD = 1E12
        self.open = 0
        self.close = 0
        self.closing_vwap = 0
        self.ATR = 0
        self.vx_high = 0
        self.vx_low = 1000

    def update_day_of_week(self, last_timestamp):
        self.day_of_week = last_timestamp.day_name()

    def update_levels(self, last_price, timestamp):
        """Update high of day (HoD) and low of Day (LoD)."""
        if last_price > self.HoD:
            self.HoD = last_price
            self.HoD_timestamp = timestamp
        if last_price < self.LoD:
            self.LoD = last_price
            self.LoD_timestamp = timestamp

    def update_open_price(self, last_price):
        """Update open price."""
        self.open = last_price

    def update_close_price(self, last_price):
        """Update close price."""
        self.close = last_price

    def update_average_true_range(self):
        pass
        # self.

    def update_vx(self, last_vx):
        # update vx high and low of day
        if last_vx > self.vx_high:
            self.vx_high = last_vx
        if last_vx < self.vx_low:
            self.LoD = last_vx

    def to_dict(self):
        """Convert DailyMarketLevels values to dictionary."""
        return {
            "day_of_week": self.day_of_week,
            "open": self.open,
            "high": self.HoD,
            "low": self.LoD,
            "close": self.close,
            "HoD timestamp": self.HoD_timestamp,
            "LoD timestamp": self.LoD_timestamp,
            "VX high": self.vx_high,
            "VX low": self.vx_low
        }


class IntradayPriceAction:
    """container class for intraday price action"""

    def __init__(self, realtime, market_df, sampling_period):
        self.realtime = realtime
        self.sampling_period = sampling_period
        self.open_price = self.__init_open(market_df)
        self.high_price = self.__init_high(market_df)
        self.low_price = self.__init_low(market_df)
        self.close_price = self.__init_close(market_df)
        self.typical_price = self.__init_typical_price()
        self.volume, self.volume_signed = self.__init_volume(market_df)
        self.timestamp = self.__init_timestamps()
        # averages
        self.vol_ma = self.__init_volume_sma()
        self.price_ma = self.__init_typ_price_sma()
        self.vx = []


    def __init_open(self, market_df):
        open_price = market_df['price'].resample(self.sampling_period).first()
        open_price = open_price.fillna(method='ffill')
        return open_price.round(2)


    def __init_close(self, market_df):
        close_price = market_df['price'].resample(self.sampling_period).last()
        close_price = close_price.fillna(method='ffill')
        return close_price.round(2)


    def __init_high(self, market_df):
        high_price = market_df['price'].resample(self.sampling_period).max()
        high_price = high_price.fillna(method='ffill')
        return high_price.round(2)


    def __init_low(self, market_df):
        low_price = market_df['price'].resample(self.sampling_period).min()
        low_price = low_price.fillna(method='ffill')
        return low_price.round(2)

    def __init_typical_price(self):
        return pd.Series((self.open_price + self.close_price + self.high_price + self.low_price) / 4).round(2)

    def __init_volume(self, market_df):
        volume = market_df['volume'].resample(self.sampling_period).sum()
        volume = volume.fillna(method='ffill')
        sign = np.sign(self.close_price - self.open_price)
        return volume.astype(int), volume * sign.astype(int)

    def __init_timestamps(self):
        timestamps = self.open_price.index
        return timestamps

    def __init_volume_sma(self):
        volume_bars_ser = pd.Series(self.volume)
        vol_60_moving_avg_ser = volume_bars_ser.rolling(30*60, min_periods=1).mean()
        vol_30_moving_avg_ser = volume_bars_ser.rolling(15*60, min_periods=1).mean()
        return vol_60_moving_avg_ser.astype(int), vol_30_moving_avg_ser.astype(int)

    def __init_typ_price_sma(self):
        price_ma_60 = self.typical_price.rolling(30*60, min_periods=1).mean()
        price_ma_30 = self.typical_price.rolling(15*60, min_periods=1).mean()
        return price_ma_60.round(2), price_ma_30.round(2)

    def append_open_price_list(self, new_open_price):
        if self.realtime:
            self.open_price = new_open_price
        else:
            self.open_price.append(new_open_price)

    def append_close_price_list(self, new_close_price):
        self.close_price.append(new_close_price)

    def append_high_price_list(self, new_high_price):
        self.high_price.append(new_high_price)

    def append_low_price_list(self, new_low_price):
        self.low_price.append(new_low_price)

    def append_volume_list(self, new_volume):
        self.volume.append(new_volume)

    def append_timestamp(self, new_timestamp):
        if self.realtime:
            self.timestamp = new_timestamp
        else:
            self.timestamp.append(new_timestamp)

    def append_vx(self, new_vx_value):
        self.vx.append(new_vx_value)
