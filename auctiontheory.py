#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 29 17:10:14 2022

@author: tradineer
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats
import scipy.signal
from scipy import stats as st
from pandas import Series


class MarketProfileHighFreq:
    def __init__(self, timestamp: Series, typical_price: Series, candle_volume: Series):
        """
        @type timestamp: Series
        @type candle_volume: Series
        @type typical_price: Series
        @param timestamp: timestamps list
        @param typical_price: typical prices list
        @param candle_volume: candle volume list (signed)
        """
        self.candle_duration = 1  # in seconds
        self.num_bins = 33
        self.volume_profile = 0
        self.bins = 0
        self.bins_pos = 0
        self.bins_neg = 0
        self.vpoc = [0]
        self.POC = [0]
        self.VAH = 0  # unused
        self.VAL = 0  # unused
        self.typical_price = typical_price
        self.ONVPOC = 0
        self.vwap = []
        self.VWAP_offset = []
        self.intraday_price_variation_from_mid = []
        self.price_volume = []
        self.timestamp = timestamp
        self.on_balance_volume = [0]
        self.obv_gradient = []
        self.price2VWAP_stdev = []
        self.price_var_from_mid_std_mean = 0
        self.price_var_from_mid_std_max = 0
        self.price_var_from_mid_kurtosis = 0
        self.price_var_from_mid_skew = 0
        self.price_var_from_mid_mean = 0
        self.price_var_from_mid_mode = 0
        self.price_var_from_mid_median = 0
        self.price_var_from_mid_max = 0
        self.price_var_from_mid_min = 0
        self.num_below_vwap = 0
        self.num_above_vwap = 0
        self.num_at_vwap = 0
        self.delta_tp_delta_v = []  # store d(typical price)/d(volume)
        self.candle_volume = candle_volume
        self.volume_profile_pos = 0
        self.volume_profile_neg = 0
        self.day_of_week = None
        self.__profile_dist = 0
        self.__average_price = 0
        self.__TPV = [0]
        self.__cum_TPV = [0]
        self.__cum_volume = [0]

    # to do list:
    ## std deviation of typical price per day relative to VWAP
    ## average, median, mode, max, min stdev of tp relative to VWAP

    def update_price2vwap_counts(self):
        # at vwap (within tolerance of 0.000001)
        at = np.isclose(self.intraday_price_variation_from_mid, 0, atol=1e-6)
        self.num_at_vwap = np.sum(at)
        above = np.array(self.intraday_price_variation_from_mid) > 1e-6
        self.num_above_vwap = np.sum(above)
        below = np.array(self.intraday_price_variation_from_mid) < -1e-6
        self.num_below_vwap = np.sum(below)

    def update_timestamp(self, last_timestamp):
        self.timestamp.append(last_timestamp)

    def update_on_balance_volume(self):
        for i in range(1, len(self.candle_volume)):
            self.on_balance_volume.append(self.on_balance_volume[i - 1] + self.candle_volume[i])
        self.on_balance_volume = pd.Series(data=self.on_balance_volume, index=self.timestamp).astype(int)

    def update_vwap(self):
        tpv = self.typical_price * self.candle_volume.abs()
        cum_tpv = tpv.cumsum()
        cum_tpv = pd.Series(data=cum_tpv)
        cum_vol = self.candle_volume.abs().cumsum()
        vwap = pd.Series(data=cum_tpv / cum_vol, index=self.timestamp)
        vwap = vwap.fillna(method="backfill")
        self.vwap = vwap.round(2)

    def update_volume_profile(self, normalize=False):
        # volume profile calculation.
        # negative/positive splitting is unreliable at all bc bin edges would need to be super large in number
        # otherwise we run into a problem of undersampling
        [self.volume_profile, self.bins] = np.histogram(
            self.typical_price, bins=self.num_bins, weights=self.candle_volume.abs())
        if normalize:
            self.volume_profile = self.volume_profile / np.max(self.volume_profile)
        self.volume_profile = pd.Series(data=self.volume_profile, index=np.round(self.bins[1:], 2)).round(2)

    def update_volume_profile_fast(self, normalize=False):
        # to be completed later
        pass

    def update_vpoc(self, steps=60 * 10):
        # get max volume node
        numel = len(self.candle_volume)
        self.vpoc = [0] * numel
        for i in range(1, numel, steps):
            [self.volume_profile, self.bins] = np.histogram(
                self.typical_price[:i], bins=self.num_bins, weights=self.candle_volume[:i].abs())
            max_ind = np.argmax(self.volume_profile)
            self.vpoc[i] = self.bins[max_ind]
        try:
            self.vpoc[0] = self.vpoc[1]
        except:
            pass
        # fill zeros
        self.vpoc = pd.Series(data=self.vpoc, index=self.timestamp).round(2)
        self.vpoc = self.vpoc.replace(to_replace=0, method='ffill')

    def update_POC(self):
        pass

    def smoothen_VPOC(self, ks=33):
        # make VPOC smoothe
        self.VPOC = list(scipy.signal.medfilt(self.VPOC, kernel_size=ks))

    def update_price_volume(self, high, low, close):
        # unused method
        self.__average_price = (high + low + close) / 3

    def __estimator(self, percent, tol=0.01, plot=True):  # unused
        hist = (self.volume_profile, self.bins)
        hist_dist = scipy.stats.rv_histogram(hist)
        # find values that are close to 30% volume
        dist_cdf = hist_dist.cdf(self.bins)
        value = np.isclose(dist_cdf, [percent], rtol=tol)
        if plot:
            plt.plot(self.bins, dist_cdf)
            plt.show()
        return value

    def update_VAL(self):
        self.VAL = self.__estimator(0.8)
        print("line 42: ", self.bins[self.VAL])

    def update_intraday_price_variation_from_mid(self, last_price, mid_price, volume, timestamp):
        # this creates a histogram around mid_price (which could be simply IBH-IBL/2 +IBL or VPOC, POC, VWAP, etc
        # calculate percent diff last price and mid
        last_percent_diff = (last_price - mid_price) / mid_price
        self.intraday_price_variation_from_mid.append(last_percent_diff)

    def update_price_stats(self):
        # calculate mean, mode, median, min, and max standard deviations of price per day rel. to VWAP
        self.price_var_from_mid_std_mean = np.mean(self.VWAP_offset)
        self.price_var_from_mid_std_max = np.max(self.VWAP_offset)
        self.price_var_from_mid_kurtosis = st.kurtosis(self.intraday_price_variation_from_mid)
        self.price_var_from_mid_skew = st.skew(self.intraday_price_variation_from_mid)
        self.price_var_from_mid_median = np.median(self.intraday_price_variation_from_mid)
        # st.mode doesn't work well bc values don't repeat much
        if not np.any(np.isnan(self.intraday_price_variation_from_mid)):
            hist, bins = np.histogram(self.intraday_price_variation_from_mid)
            self.price_var_from_mid_mode = bins[np.argmax(hist)]
        else:
            self.price_var_from_mid_mode = None
        # self.price_var_from_mid_mode = st.mode(self.intraday_price_variation_from_mid)[0][0]
        self.price_var_from_mid_max = np.max(self.intraday_price_variation_from_mid)
        self.price_var_from_mid_min = np.min(self.intraday_price_variation_from_mid)

    def update_day_of_week(self, last_timestamp):
        self.day_of_week = last_timestamp.day_name()

    def to_dict(self):
        return {
            "counts_at_vwap": self.num_at_vwap,
            "counts_below_vwap": self.num_below_vwap,
            "counts_above_vwap": self.num_above_vwap,
            "price_var_from_mid_std_mean": self.price_var_from_mid_std_mean,
            "price_var_from_mid_std_max": self.price_var_from_mid_std_max,
            "price_var_from_mid_kurtosis": self.price_var_from_mid_kurtosis,
            "price_var_from_mid_skew": self.price_var_from_mid_skew,
            "price_var_from_mid_median": self.price_var_from_mid_median,
            "price_var_from_mid_mode": self.price_var_from_mid_mode,
            "price_var_from_mid_max": self.price_var_from_mid_max,
            "price_var_from_mid_min": self.price_var_from_mid_min,
            "VWAP_close": self.VWAP[-1]
        }


if __name__ == "__main__":
    import os
    from price import IntradayPriceAction
    import datetime
    import time
    from pathlib import Path
    #from playsound import playsound
    from natsort import natsorted
    import matplotlib.pyplot as plt

    #playsound('/Users/Tradineer/opt/star wars sounds/Jump to lightspeed.mp3')

    begin = time.time()

    # get all database subidrs
    print("Start read parquet DB")
    start = time.time()
    base_dir = "database/database/market_data/tick_data/2022166b/"
    dirs = natsorted(Path(base_dir).glob('**/*.parquet'))
    list_of_df = [pd.read_parquet(d) for d in dirs]
    end = time.time()
    print("Elapsed time {:06.2f}".format(end - start))

    for n, df in enumerate(list_of_df):
        start = time.time()
        df['datetime'] = df.apply(lambda x: datetime.datetime.combine(x.date, x.time), axis=1)
        df.rename({"datetime": "time"})
        end = time.time()
        print("Elapsed time {:06.2f}".format(end - start))

        start = time.time()
        print("Set time col to index ")
        df.set_index('datetime', drop=True, inplace=True)
        end = time.time()
        print("Elapsed time {:06.2f}".format(end - start))

        print("Drop redundant cols from DF")
        start = time.time()
        df = df.drop(columns=["year", "month", "day"])

        start = time.time()
        print("instantiate intradaypriceaction class object ")
        intraday_prices_obj = IntradayPriceAction(realtime=True, market_df=df, sampling_period='10s')
        typ_price = 0.25 * (intraday_prices_obj.open_price + intraday_prices_obj.high_price +
                            intraday_prices_obj.low_price + intraday_prices_obj.close_price)
        end = time.time()
        print("Elapsed time {:06.2f}".format(end - start))

        start = time.time()
        print("instantiate marketprofile class object ")
        market_prof_obj = MarketProfileHighFreq(intraday_prices_obj.timestamp, typ_price,
                                                intraday_prices_obj.volume_signed)
        end = time.time()
        print("Elapsed time {:06.2f}".format(end - start))

        start = time.time()
        print("Compute OBV ")
        market_prof_obj.update_on_balance_volume()
        end = time.time()
        print("Elapsed time {:06.2f}".format(end - start))

        start = time.time()
        print("Compute VWAP ")
        market_prof_obj.update_vwap()
        end = time.time()
        print("Elapsed time {:06.2f}".format(end - start))

        start = time.time()
        print("Compute vpoc ")
        market_prof_obj.update_vpoc()
        end = time.time()
        print("Elapsed time {:06.2f}".format(end - start))

        start = time.time()
        print("Compute volume profile ")
        market_prof_obj.update_volume_profile()
        end = time.time()
        print("Elapsed time {:06.2f}".format(end - start))

        start = time.time()
        print("Generate plot")

        write_dir = "indicators/" + "{0}/{1}/{2}/{3}/".format(dirs[n].parts[-5], dirs[n].parts[-4], dirs[n].parts[-3],
                                                              dirs[n].parts[-2])
        # store indicators
        try:
            os.makedirs(write_dir)
        except FileExistsError:
            pass
        finally:
            intraday_prices_obj.close_price.to_pickle(write_dir + "intraday_prices_obj;close_price.pkl")
            intraday_prices_obj.open_price.to_pickle(write_dir + "intraday_prices_obj;open_price.pkl")
            intraday_prices_obj.high_price.to_pickle(write_dir + "intraday_prices_obj;high_price.pkl")
            intraday_prices_obj.low_price.to_pickle(write_dir + "intraday_prices_obj;low_price.pkl")
            intraday_prices_obj.price_ma[0].to_pickle(write_dir + "intraday_prices_obj;price_ma0.pkl")
            intraday_prices_obj.price_ma[1].to_pickle(write_dir + "intraday_prices_obj;price_ma1.pkl")
            intraday_prices_obj.volume.to_pickle(write_dir + "intraday_prices_obj;volume.pkl")
            intraday_prices_obj.vol_ma[0].to_pickle(write_dir + "intraday_prices_obj;vol_ma0.pkl")
            intraday_prices_obj.vol_ma[1].to_pickle(write_dir + "intraday_prices_obj;vol_ma1.pkl")
            market_prof_obj.on_balance_volume.to_pickle(write_dir + "market_prof_obj;on_balance_volume.pkl")
            market_prof_obj.vwap.to_pickle(write_dir + "market_prof_obj;vwap.pkl")
            market_prof_obj.vpoc.to_pickle(write_dir + "market_prof_obj;vpoc.pkl")

    end = time.time()
    print("Total time {:06.2f}".format(end - begin))
    #playsound('/Users/Tradineer/opt/star wars sounds/Falcon landing.mp3')

    # partial validation
    close_price = pd.read_pickle(write_dir + "intraday_prices_obj;close_price.pkl")
    price_ma0 = pd.read_pickle(write_dir + "intraday_prices_obj;price_ma0.pkl")
    assert all(close_price == intraday_prices_obj.close_price)
    assert all(price_ma0 == intraday_prices_obj.price_ma[0])

    print("end program ")
