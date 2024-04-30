import pandas as pd
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess


def run_spider(spider_name, filename, column_name, *args):

    # Get project settings
    project_settings = get_project_settings()

    # Rename filename
    feed_name = project_settings.attributes['FEEDS'].value.attributes
    feed_name[filename] = feed_name.pop('Name.csv')

    # Set settings and start
    process = CrawlerProcess(settings=project_settings)

    # Check if there are additional arguments.
    if len(args[0]) > 0:
        # Tuple unpacking
        args = args[0]

        # Run spider
        process.crawl(spider_name, args)
    else:
        # Run spider
        process.crawl(spider_name)

    process.start()

    # After the process, read the file and drop titles just in case you have lines equals to the title.
    # Read file
    temp = pd.read_csv(filename, encoding='utf-8')

    # Drop titles
    temp.drop(temp[temp[column_name] == column_name].index, inplace=True)

    # Save .csv file
    temp.to_csv(filename, index=False, encoding='utf-8')    