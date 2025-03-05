import os
from utility_functions import run_spider, get_credentials, prepare_raw_data


# ------------------------------ Input data ------------------------------ #
def get_hotforex_data(spider_name, drop_rows):
    # Check if folder "Data" does not exist.
    if not os.path.exists("Data"):
        # Make directory to save Data.
        os.makedirs("Data")

    # The keys of "filenames" are equals to names of spiders ".py" files
    filenames = {'hotforex_users': 'Data/Users.csv',
                 'hotforex_stats': 'Data/Statistics.csv'}

    # Get credentials and prepare the data
    credentials = get_credentials('Hotforex')

    # Prepare raw data
    if spider_name == 'hotforex_stats':
        raw_data = prepare_raw_data(filenames['hotforex_users'], filenames['hotforex_stats'], drop_rows)

    arguments = [credentials]
    if spider_name == 'hotforex_stats':
        arguments.append(raw_data['Provider profile'])
    
    arguments = tuple(arguments)

    # Run spider
    run_spider(spider_name, filenames[spider_name], 'Provider name', arguments)


if __name__ == '__main__':
    # First step: Run "hotforex_users" to scrape the profile of each trader.
    # Second step: Run "hotforex_stats" to scrape the statistics of each trader.

    spider_name = 'hotforex_stats'
    drop_rows = False

    get_hotforex_data(spider_name, drop_rows)
