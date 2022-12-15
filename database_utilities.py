import os
import tarfile
import datetime
from pprint import pprint
import pandas as pd
import pandas
from os.path import exists


def archive_database_directories(names: list):
    """
    This function is unused because it's very slow relative to terminal command tar
    @param names:
    @return:
    """
    for name in names:
        print(name)
        archive = tarfile.open(name=name+'.xz', mode='w:xz', preset=2)
        archive.add(name, recursive=True)
    return archive


def extract_files_from_archive(name: str, member: str, extract_to_path='.'):
    """
    Extract member file 'member' from tarfile 'name' and put in path 'extract_to_path'.
    Input 'member' could be a directory or a single file.
    @param name: tarfile name
    @param member: member inside tarfile to extract
    @param extract_to_path: path to extract member file to
    @return: none
    """
    from pprint import pprint
    tarinfo_list = []
    with tarfile.open(name) as tar:
        tarmembers = tar.getmembers()
        print("searching for "+member+" in "+name)
        for i, tarmember in enumerate(tarmembers):
            if tarmember.name.startswith(member):
                tarinfo_list.append(tarmember)
        print("extracting ")
        pprint(tarinfo_list)
        for m in tarinfo_list:
            tar.extract(member=m, path=extract_to_path)


def get_contract_location(input_date: datetime.date) -> str:
    """
    Selects proper futures contract code based on the input_date parameter.
    Outputs file_path to read from in Database
    @return: file_path
    @rtype: str
    @type input_date: datetime.date
    @param input_date: datetime.date object to locate contract path in DB
    """
    nearest_month_code = "H" if (input_date.month <= 3) & (input_date.day <= 15) | (input_date.month < 3) \
        else "M" if (input_date.month <= 6) & (input_date.day <= 15) | (input_date.month < 6) \
        else "U" if (input_date.month <= 9) & (input_date.day <= 15) | (input_date.month < 9) \
        else "Z"
    contract_name = "ES" + nearest_month_code + input_date.strftime("%y")
    file_path = contract_name + "/" + str(input_date.strftime("%Y")) + "/" + str(
        input_date.month) + "/" + str(input_date.day) + "/"
    return file_path


def read_date_from_db(input_date: datetime.date) -> pandas.DataFrame:
    """
    Function reads from Parquet database futures contract data containing time (millisecond), price and volume columns.
    @rtype: pandas.DataFrame
    @param input_date: datetime.date object specifying date to read price data for:
    @return df: Object containing order milisecond price/volume orders
    """
    base_dir = 'database/'
    file_path = base_dir + 'market_data/tick_data/2022166b/' + get_contract_location(input_date)
    if exists(base_dir+file_path):
        print("file exists, speed up without decompression")
    else:
        extract_files_from_archive(name='database/tickdata_small.tar.lzma',
                                   member=file_path + "data.parquet",
                                   extract_to_path='database/')
    df = pd.read_parquet(base_dir + file_path + "data.parquet")
    # clean up dataframe
    df = df.drop(columns=['year', 'month', 'day', 'date'])
    df.set_index("time", inplace=True)
    return df


def read_indicators_from_db(input_date: datetime.date, starting_time, ending_time):
    """
    Function reads from Pickle database pre-computed 1-second aggregated order data into pandas DataFrame object.
    Also, selects proper futures contract code based on the input_date parameter and filters object by
    starting_time and ending_time parameters.
    @param input_date: datetime.date object specifying date to read price data for:
    @param starting_time:
    @param ending_time:
    @rtype: list of pandas.Series objects
    @return list of pandas.Series objects: Each series in the list is Timestamp indexed and is spaced by 1s intervals
    """
    base_dir = 'database/'
    file_path = 'indicators/' + get_contract_location(input_date)
    if exists(base_dir+file_path):
        print("file exists, speed up without decompression")
    else:
        extract_files_from_archive(name='database/indicators_small.tar.lzma',
                               member=file_path,
                               extract_to_path='database/')

    members = ['intraday_prices_obj;open_price.pkl',
                         "intraday_prices_obj;close_price.pkl",
                         "intraday_prices_obj;low_price.pkl",
                         "intraday_prices_obj;high_price.pkl",
                         "intraday_prices_obj;price_ma0.pkl",
                         "intraday_prices_obj;price_ma1.pkl",
                         "intraday_prices_obj;volume.pkl",
                         "intraday_prices_obj;vol_ma0.pkl",
                         "intraday_prices_obj;vol_ma1.pkl",
                         "market_prof_obj;on_balance_volume.pkl",
                         "market_prof_obj;vwap.pkl",
                         "market_prof_obj;vpoc.pkl",
                         ]
    # read parquet DB for default visible date
    open_price_ser = pd.read_pickle(base_dir + file_path + "intraday_prices_obj;open_price.pkl")
    close_price_ser = pd.read_pickle(base_dir + file_path + "intraday_prices_obj;close_price.pkl")
    low_price_ser = pd.read_pickle(base_dir + file_path + "intraday_prices_obj;low_price.pkl")
    high_price_ser = pd.read_pickle(base_dir + file_path + "intraday_prices_obj;high_price.pkl")
    price_ma0_ser = pd.read_pickle(base_dir + file_path + "intraday_prices_obj;price_ma0.pkl")
    price_ma1_ser = pd.read_pickle(base_dir + file_path + "intraday_prices_obj;price_ma1.pkl")
    volume_ser = pd.read_pickle(base_dir + file_path + "intraday_prices_obj;volume.pkl")
    vol_ma0_ser = pd.read_pickle(base_dir + file_path + "intraday_prices_obj;vol_ma0.pkl")
    vol_ma1_ser = pd.read_pickle(base_dir + file_path + "intraday_prices_obj;vol_ma1.pkl")
    on_balance_vol_ser = pd.read_pickle(base_dir + file_path + "market_prof_obj;on_balance_volume.pkl")
    vwap_ser = pd.read_pickle(base_dir + file_path + "market_prof_obj;vwap.pkl")
    vpoc_ser = pd.read_pickle(base_dir + file_path + "market_prof_obj;vpoc.pkl")

    # filter by starting time
    open_price_ser = open_price_ser[
        (open_price_ser.index.time >= starting_time) & (open_price_ser.index.time <= ending_time)]
    close_price_ser = close_price_ser[
        (close_price_ser.index.time >= starting_time) & (close_price_ser.index.time <= ending_time)]
    high_price_ser = high_price_ser[
        (high_price_ser.index.time >= starting_time) & (high_price_ser.index.time <= ending_time)]
    low_price_ser = low_price_ser[
        (low_price_ser.index.time >= starting_time) & (low_price_ser.index.time <= ending_time)]
    price_ma0_ser = price_ma0_ser[
        (price_ma0_ser.index.time >= starting_time) & (price_ma0_ser.index.time <= ending_time)]
    price_ma1_ser = price_ma1_ser[
        (price_ma1_ser.index.time >= starting_time) & (price_ma1_ser.index.time <= ending_time)]
    volume_ser = volume_ser[(volume_ser.index.time >= starting_time) & (volume_ser.index.time <= ending_time)]
    vol_ma0_ser = vol_ma0_ser[(vol_ma0_ser.index.time >= starting_time) & (vol_ma0_ser.index.time <= ending_time)]
    vol_ma1_ser = vol_ma1_ser[(vol_ma1_ser.index.time >= starting_time) & (vol_ma1_ser.index.time <= ending_time)]
    on_balance_vol_ser = on_balance_vol_ser[
        (on_balance_vol_ser.index.time >= starting_time) & (on_balance_vol_ser.index.time <= ending_time)]
    vwap_ser = vwap_ser[(vwap_ser.index.time >= starting_time) & (vwap_ser.index.time <= ending_time)]
    vpoc_ser = vpoc_ser[(vpoc_ser.index.time >= starting_time) & (vpoc_ser.index.time <= ending_time)]

    return open_price_ser.index, open_price_ser, high_price_ser, low_price_ser, close_price_ser, \
           price_ma0_ser, price_ma1_ser, volume_ser, vol_ma0_ser, vol_ma1_ser, on_balance_vol_ser, vwap_ser, vpoc_ser


if __name__ == "__main__":
    import time
    import os
    # test 1
    start=time.time()
    #extract_files_from_archive(name='database/indicators.tar.lzma',
    #                           member='indicators/ESH22/2021/8/31/',
    #                           extract_to_path='database/dummy/')
    end=time.time()
    print('done after ', end-start)
    # test 2
    start=time.time()
    extract_files_from_archive(name='database/tickdata_small.tar.lzma',
                               member='database/market_data/tick_data/2022166b/ESU21/2021/9/9/',
                               extract_to_path='database/dummy/')
    end=time.time()
    print('done after ', end-start)
    start=time.time()
    extract_files_from_archive(name='database/tickdata_small.tar.lzma',
                               member='database/market_data/tick_data/2022166b/dates_arr.pkl',
                               extract_to_path='database/dummy/')
    end=time.time()
    print('done after ', end-start)


