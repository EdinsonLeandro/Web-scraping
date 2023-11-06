import pandas as pd
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess

# ------------------------------------------------------ #
# --------------------- Input data --------------------- #
# ------------------------------------------------------ #

# Credentials
creds = pd.read_csv('Credentials/credentials.csv')

# True for scrape users data. False to scrape statistics 
condition_users = False

drop_rows = True

filename = 'Data/Users.csv' if condition_users else 'Data/Statistics.csv'


# ------------------------------------------------------------ #
# ------------------------ Run spider ------------------------ #
# ------------------------------------------------------------ #

# Get project settings
project_settings = get_project_settings()

# Rename filename
feed_name = project_settings.attributes['FEEDS'].value.attributes
feed_name[filename] = feed_name.pop('Name.csv')

# Set settings and start
process = CrawlerProcess(settings=project_settings)

if condition_users:
    process.crawl('hotforex_users', str(creds.loc[0, 'id']), creds.loc[0, 'password'])
else:
    df = pd.read_csv('Data/Users.csv')

    if drop_rows:
        # Drop rows. Only for continue running the script. "last_valid_row" from .csv file
        temp = pd.read_csv(f"Data/Statistics.csv", encoding='utf-8')
        temp.drop(temp[temp['Name'] == 'Name'].index, inplace=True)
        temp.to_csv(f"Data/Statistics.csv", index=False, encoding='utf-8')
        
        df.drop(range(temp.shape[0]), axis=0, inplace=True)

    process.crawl('hotforex_stats', str(creds.loc[0, 'id']), creds.loc[0, 'password'], df['Provider Profile'])

process.start()