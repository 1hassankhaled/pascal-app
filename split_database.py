import pandas as pd

print("reading market_data/ES_continuous_adjusted_1min.txt")
db_df = pd.read_csv("market_data/ES_continuous_adjusted_1min.txt")
print("configuring dataframe")
db_df.index = pd.to_datetime(db_df['time'], format='%Y-%m-%d %H:%M:%S')
# fill ES dataframe
db_df = db_df.resample("1min").mean()
db_df.reset_index(inplace=True)
db_df.index = pd.to_datetime(db_df['time'], format='%Y-%m-%d %H:%M:%S')

print("splitting dataframe")
db_df['year'] = [x.year for x in db_df['time']]
by_year = [db_df[db_df['year'] == year] for year in db_df['year'].unique()]
for i, year in enumerate(db_df['year'].unique()):
    by_year[i].to_parquet('market_data/split_data/{}.parquet'.format(year), engine='auto', compression='brotli')
    print("writing to Parquet sheet name ", year)

print('Finished splitting DB')
