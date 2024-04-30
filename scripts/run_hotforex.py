import pandas as pd
from custom_functions import run_spider


# ------------------------------ Input data ------------------------------ #
# - "hotforex_users" to scrape users data.
# - "hotforex_stats" to scrape user statistics
spider_name = 'hotforex_stats'
drop_rows = True


# ------------------------------ Settings ------------------------------ #
# Credentials
credentials = pd.read_csv('Data/0 Credentials/credentials.csv', dtype=str)
credentials = credentials.values[0]

# The keys of "filenames" must be equal to names of ".py" files
filenames = {'hotforex_users': 'Data/2 April_2024/Users.csv', 'hotforex_stats': 'Data/2 April_2024/Statistics.csv'}

if spider_name == 'hotforex_stats':
    df = pd.read_csv(filenames['hotforex_users'])

    if drop_rows:
        # Drop rows. Only for continue running the script. "last_valid_row" from .csv file
        temp = pd.read_csv(filenames['hotforex_stats'], encoding='utf-8')
        temp.drop(temp[temp['Provider name'] == 'Provider name'].index, inplace=True)
        temp.to_csv(filenames['hotforex_stats'], index=False, encoding='utf-8')
        
        df.drop(range(temp.shape[0]), axis=0, inplace=True)

arguments = {'hotforex_users': (credentials) if spider_name == 'hotforex_users' else "",
             'hotforex_stats': (credentials, df['Provider profile']) if spider_name == 'hotforex_stats' else ""}


# ------------------------------ Run spider ------------------------------ #
run_spider(spider_name, filenames[spider_name], 'Provider name', arguments[spider_name])
