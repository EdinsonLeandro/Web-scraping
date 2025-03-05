import os
import subprocess
from utility_functions import run_spider, send_output_file, get_credentials


def search_jobs_openings(num_windows:int, keyword:str, location:str, spider_name:str, file_path:str):
    
    # Define the file name where the downloaded information will be saved
    filename = os.path.join('Data', 'Openings', 'Jobs_openings.csv')
    
    # Delete the file if this exist
    if os.path.exists(filename):
        os.remove(filename)

    # Define arguments
    arguments = [(keyword, location), num_windows]

    if spider_name == 'linkedin':
        # Obtain credentials to log in to LinkedIn
        credentials = get_credentials('Linkedin')

        # Insert credentials into the argument list
        arguments.insert(0, credentials)

    # Search job openings
    try:
        run_spider(f"jobs_{spider_name}", filename, arguments)
    except:
        for _ in range(num_windows):
            subprocess.call(["taskkill","/F","/IM","chrome.exe"])

    # Send output to google sheet
    send_output_file(filename, file_path, 'Data')


if __name__ == '__main__':
    # --------------------- Input data --------------------- #
    # Number of windows to run in parallel
    num_windows = 1
    
    # Keyword and Location
    keyword = '"Data Scientist"'
    location = 'Venezuela'

    # Process: linkedin, indeed. The next target is GLASSDOOR
    spider_name = 'linkedin'

    # File location to save data. It can be an google sheet file or Excel file
    file_path = "https://docs.google.com/spreadsheets/d/1Afed3KMazqvo4Q-9R0Wc5CWb3bzHR4DCyWiBGOSsMm8/edit?gid=0#gid=0"

    # --------------------- Run spider --------------------- #
    search_jobs_openings(num_windows, keyword, location, spider_name, file_path)
