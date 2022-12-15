#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 14:10:46 2022

@author: tradineer
"""
from dateutil import parser
import datetime


class LiveMarketSimulator:
    def __init__(self, market_data):
        self.__market_data = market_data
        self.price = market_data['close']
        self.closing_price_column = None  # legacy
        self.timestamp_column = market_data['time']
        self.last_price = None
        self.high_price = None
        self.low_price = None
        self.last_timestamp = None
        self.last_volume = None
        self.max_iter = len(market_data)
        self.time_elapsed = 0
        self.iterable = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.iterable > self.max_iter - 1:
            raise StopIteration
        self.high_price = self.__market_data.high[self.iterable]
        self.low_price = self.__market_data.low[self.iterable]
        self.open_price = self.__market_data.open[self.iterable]
        self.last_price = self.__market_data.close[self.iterable]
        if self.last_price > self.open_price:  # green candle
            self.last_volume = 1 * (self.__market_data.volume[self.iterable])
        elif self.last_price < self.open_price:  # red candle
            self.last_volume = -1 * (self.__market_data.volume[self.iterable])
        elif self.last_price == self.open_price:  # neutral candle
            self.last_volume = 1 * (self.__market_data.volume[self.iterable])
        if self.__market_data.volume[self.iterable] == 0:
            self.last_volume = 1

        timestamp = self.timestamp_column[self.iterable]  # this should be datetime obj if not..
        if isinstance(timestamp, str):  # condition that it's not datetime (is string) parse it
            self.last_timestamp = parser.parse(timestamp)
        else:
            self.last_timestamp = timestamp
        self.iterable += 1
        self.time_elapsed += 1

        return self.last_timestamp, self.last_price, self.last_volume


class LiveMarketSimulatorHF:  # high frequency version
    def __init__(self, market_data):
        self.__market_data = market_data
        self.last_price = None
        self.last_timestamp = None
        self.last_volume = None
        self.max_iter = len(market_data)
        self.time_elapsed = 0
        self.iterable = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.iterable > self.max_iter - 1:
            raise StopIteration
        self.last_price = self.__market_data.price[self.iterable]
        self.last_volume = self.__market_data.volume[self.iterable]
        self.last_timestamp = self.__market_data.time[self.iterable]

        return self.last_timestamp, self.last_price, self.last_volume
