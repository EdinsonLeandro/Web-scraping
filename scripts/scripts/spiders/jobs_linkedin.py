import scrapy
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as OptionsChrome
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import os, pickle, time, random
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from math import ceil
from datetime import datetime


class JobsLinkedinSpider(scrapy.Spider):
    name = 'jobs_linkedin'
    allowed_domains = ['www.linkedin.com']
    start_urls = ['https://www.linkedin.com', 'https://www.linkedin.com/jobs/']

    handle_httpstatus_list = [403, 429]

    def __init__(self, input_spider, delay=10):

        # Parameters
        self.delay = delay
        self.credentials = input_spider[0]      # List of LinkedIn Credentials
        self.keywords = input_spider[1]         # Keyword and Location
        self.num_windows = input_spider[2]      # Number of windows to run in parallel

        # Current date
        self.current_date = datetime.now().strftime('%Y-%m-%d')        

        # Move back one folder in order to reach "drivers". Number "1" set it.
        # https://softhints.com/python-change-directory-parent/
        drivers_dir = os.path.normpath(os.getcwd() + (os.sep + os.pardir) * 1) + '/drivers/chromedriver.exe'

        # "executable_path" has been deprecated selenium python. Here is the solution
        # https://stackoverflow.com/questions/64717302/deprecationwarning-executable-path-has-been-deprecated-selenium-python
        # https://stackoverflow.com/questions/18707338/print-raw-string-from-variable-not-getting-the-answers
        self.drivers_dir = r'%s' %drivers_dir

        # Testing version directory
        self.testing_dir = os.path.normpath(os.getcwd() + (os.sep + os.pardir) * 1) + '/drivers/chrome-win64_113/chrome.exe'

        option = OptionsChrome()
        option.add_argument('--disable-popup-blocking')

        browser = uc.Chrome(driver_executable_path=self.drivers_dir, options=option, browser_executable_path=self.testing_dir)
        browser.maximize_window()

        self.browser_list = []
        self.browser_list.append(browser)

        # Login to LinkedIn. Browser, email and password
        self.login(self.browser_list[0], self.credentials[0], self.credentials[1], 0)

        # Search keywords
        self.search_keywords(self.browser_list[0])

        # Apply filters
        self.apply_filters(self.browser_list[0])

        # Max number of results. There are 25 results by page
        path_results = "//div[@class='scaffold-layout__list ']/header/div/small/div/span"

        max_results = self.browser_list[0].find_element(By.XPATH, path_results).text
        max_results = int(max_results.replace(",", "").split(" ")[0])
        self.max_results = 1000 if max_results >= 1000 else ceil(max_results/25)*25


    # https://www.selenium.dev/documentation/webdriver/waits/
    # https://www.selenium.dev/selenium/docs/api/py/webdriver_support/selenium.webdriver.support.expected_conditions.html
    def pause_spider(self, driver, path):
        WebDriverWait(driver, timeout=self.delay).\
            until(EC.element_to_be_clickable((By.XPATH, path)))

        time.sleep( round(random.uniform(2.1, 2.9), 4) )


    def load_cookie(self, driver, path):
        """
        Function to load cookie from browser.
        """
        with open(path, 'rb') as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for item in cookies:
                driver.add_cookie(item)


    def save_cookie(self, driver, path):
        """
        Function to save cookies.
        """        
        with open(path, 'wb') as filehandler:
            pickle.dump(driver.get_cookies(), filehandler)


    def login(self, driver, email, password, index):
        """Function to go to linkedin and login"""
        path_file = f"Data/Cookies/linkedin_cookies_{index}.txt"

        # If there is a cookie, the web page goes directly to feed
        if os.path.exists(path_file):
            driver.get(self.start_urls[0])
            self.load_cookie(driver, path_file)
            driver.get(self.start_urls[0])

            # Wait until "Home" icon is clickable.
            self.pause_spider(driver, "//nav[@class='global-nav__nav']/ul/li[1]")

        else:
            # Open linkedIn in web browser
            driver.get('https://www.linkedin.com/login')

            # Wait until "Sign in" icon is clickable.
            self.pause_spider(driver, "//button[@class='btn__primary--large from__button--floating']")

            # Write email and password
            # https://www.selenium.dev/documentation/webdriver/elements/finders/
            driver.find_element(By.ID, 'username').send_keys(email)
            driver.find_element(By.ID, 'password').send_keys(password)

            # Wait
            time.sleep(round(random.uniform(3.0, 5.0), 4))

            # Press "Enter" after write. "Keys.RETURN" do the same
            # https://www.geeksforgeeks.org/special-keys-in-selenium-python/
            driver.find_element(By.ID, 'password').send_keys(Keys.ENTER)
            
            # Wait until "Home" icon is clickable.
            self.pause_spider(driver, "//nav[@class='global-nav__nav']/ul/li[1]")

            # Wait
            time.sleep(round(random.uniform(2.0, 4.0), 4))

            self.save_cookie(driver, path_file)


    def search_keywords(self, driver):
        # Get jobs website.
        driver.get(self.start_urls[1])
        self.pause_spider(driver, "//nav[@class='global-nav__nav']/ul/li[1]")

        # Identify element by class name to write input.
        # Write keywords.
        input_title = driver.find_element(By.XPATH, "(//input[@aria-label='Search by title, skill, or company'])[1]")
        input_location = driver.find_element(By.XPATH, "(//input[@aria-label='City, state, or zip code'])[1]")

        # Clear space
        input_location.clear()

        # Send keys
        ActionChains(driver).send_keys_to_element(input_title, self.keywords[0])\
                            .pause(random.uniform(1.9, 2.9))\
                            .send_keys_to_element(input_location, self.keywords[1])\
                            .pause(random.uniform(1.9, 2.9))\
                            .send_keys(Keys.ENTER)\
                            .pause(random.uniform(1.9, 2.9))\
                            .perform()

        # Wait for the first element
        self.pause_spider(driver, "(//div[@data-view-name='job-card'])[1]")


    def apply_filters(self, driver):
        filter_path = "//li[@class='search-reusables__secondary-filters-filter'][{}]/fieldset/div/ul/li[{}]/label/p"

        # Reset filter just in case
        try:
            driver.find_element(By.XPATH, "//button[@aria-label='Reset applied filters']").click()
            time.sleep(random.uniform(2.1, 3.1))
        except:
            pass

        # Click on "All filters" button. Wait for wait button.
        driver.find_element(By.XPATH, "//div[@id='search-reusables__filters-bar']/div/div/button").click()
        self.pause_spider(driver, "//div[@role='dialog']/div[3]/div/button[2]")

        # Object with the elements to filter job openings
        filter_only_by = driver.find_elements(By.XPATH, "//li[@class='search-reusables__secondary-filters-filter']")

        # Find de location of: sort by, data posted, experience level, job type, remote
        # Get subtitles
        filter_subtitles = [item.find_element(By.XPATH, ".//fieldset/h3").text.lower() for item in filter_only_by]
        
        # Find the location of our target section
        target_section = ["sort by", "date posted", "experience level", "job type", "remote"]
        loc_target_section = list(filter(lambda x: filter_subtitles[x] in target_section, range(len(filter_subtitles))))

        # List of targets to filter job openings
        target_items = [['most recent'],
                        ['past month'],
                        ['entry level', 'associate', 'mid-senior level'],
                        ['full-time', 'part-time', 'contract'],
                        ['remote']]

        # For each location of target section, obtain the location of target items
        position_to_click = []
        for loc, target in zip(loc_target_section, target_items):
            # Find all elements inside the filter
            element = filter_only_by[loc].find_elements(By.XPATH, ".//fieldset/div/ul/li/label/p/span[1]")

            # Get all items in the target section
            filter_items = [item.text.lower() for item in element]

            for item in target:
                # Just in case there is no available one of the targets
                try:
                    position_to_click.append((loc, filter_items.index(item)))
                except:
                    pass

        # Click on each item
        for item in position_to_click:
            driver.find_element( By.XPATH, filter_path.format(item[0]+1, item[1]+1) ).click()
            time.sleep( round(random.uniform(1.5, 1.9), 4) )

        # Click on "Show results". Wait for the first element
        driver.find_element(By.XPATH, "//div[@role='dialog']/div[3]/div/button[2]").click()
        self.pause_spider(driver, "(//div[@data-view-name='job-card'])[1]")


    def search_job_opening_links(self, driver):
        # Get first url
        first_url = driver.current_url

        # Save data
        job_links = []

        links_path = "//div[@class='full-width artdeco-entity-lockup__title ember-view']/a"

        # For each page. Linkedin offers at maximum 40 pages, 25 result per pages.
        for num_page in range(0, self.max_results, 25):
            driver.get(first_url + f"&start={num_page}")
            self.pause_spider(driver, "(//div[@data-view-name='job-card'])[1]")
            time.sleep(random.uniform(2.1, 2.9))

            # "temp < 19" in order to make sure to scroll the window until the end. We need all objects
            # temp = 19 -> min 23, max 25
            # temp = 18 -> min 22, max 24
            # temp = 17 -> min 21, max 23
            # temp = 16 -> min 20, max 22

            temp = 0
            while temp < 20:
                temp += random.randint(4, 6)
                # If there is an error, it means that the last page does not have 25 elements. Interrupt scrolling
                try:
                    element = driver.find_element(By.XPATH, f"(//div[@data-view-name='job-card'])[{temp}]")
                    driver.execute_script("arguments[0].scrollIntoView();", element)
                except:
                    break

                # scroll_size = random.randint(1500, 2000)
                # driver.execute_script(f"window.scrollBy(0,{scroll_size})","")

                # Wait 2 seconds to allow time for the elements appear
                time.sleep(random.uniform(2.9, 3.5))

            # Read data
            job_items = driver.find_elements(By.XPATH, links_path)
            urls = [item.get_attribute("href") for item in job_items]

            # Append to list
            job_links.extend(urls)

        return job_links


    def open_web_browsers(self):
        # Open more web browsers
        if self.num_windows > 1:
            for _ in range(self.num_windows-1):
                option = OptionsChrome()
                option.add_argument('--disable-popup-blocking')

                browser = uc.Chrome(driver_executable_path=self.drivers_dir, options=option, browser_executable_path=self.testing_dir)
                browser.maximize_window()

                self.browser_list.append(browser)


    def clean_html(self, html_string):
        """Cleans HTML content from a string, removing tags, comments, and extra whitespace.

        Args:
            html_string: The HTML string to clean.

        Returns:
            The cleaned text string.
        """

        # Use BeautifulSoup to parse the HTML (more robust than regex for complex HTML).
        soup = BeautifulSoup(html_string, "html.parser")  # Use html.parser for regular HTML

        # Extract all text from the soup.
        text = soup.get_text()

        # Clean up whitespace (leading/trailing, extra spaces, newlines).
        cleaned_text = text.strip().replace("\n", " ").replace("\r", " ")
        
        # Remove extra spaces between words
        cleaned_text = " ".join(cleaned_text.split())

        return cleaned_text


    def remove_contained_items(self, input_list):
        """
        Removes items from a list if they are completely contained within another item in the list.

        Args:
            lst: The input list.

        Returns:
            A new list with the contained items removed.
        """
        new_list = []

        for item in input_list:
            contained = False
            for other_item in input_list:
                if (item != other_item) and (item in other_item):
                    contained = True
                    break
            if not contained:
                new_list.append(item)

        return new_list


    def clean_job_description(self, raw_description):
        # Clean HTML data
        clean_description = list(map(lambda x: self.clean_html(x), raw_description))

        # Clean empty strings
        clean_description = list(filter(lambda x: x!="", clean_description))

        # Remove duplicates
        clean_description = list(dict.fromkeys(clean_description))

        # Removes items from a list if they are completely contained within another item in the list.
        clean_description = self.remove_contained_items(clean_description)

        # Join all items in only one string
        return "\n".join(clean_description)
    

    def read_job_info(self, urls):

        def run_request(input_request):

            index , url = input_request

            # Create a new WebDriver instance for each thread
            browser = self.browser_list[index]

            # Save data into dictionary
            data = {}

            path_title = "//div[@class='t-24 job-details-jobs-unified-top-card__job-title']/h1"
            path_company = "//div[@class='job-details-jobs-unified-top-card__company-name']/a"
            path_details = "//div[@class='job-details-jobs-unified-top-card__primary-description-container']/div/span[{}]"

            # Request LinkedIn url. Wait until "Home" icon is clickable.
            browser.get(url)
            self.pause_spider(browser, "//nav[@class='global-nav__nav']/ul/li[1]")
            
            # Job Title
            try:
                data['JobTitle'] = browser.find_element(By.XPATH, path_title).text
            except:
                data['JobTitle'] = ""

            # Company name
            try:
                data['CompanyName'] = browser.find_element(By.XPATH, path_company).text
            except:
                data['CompanyName'] = ""

            # Company LinkedIn url
            try:
                data['CompanyLinkedinUrl'] = browser.find_element(By.XPATH, path_company).get_attribute("href")
            except:
                data['CompanyLinkedinUrl'] = ""

            # Job Location
            try:
                data['Location'] = browser.find_element(By.XPATH, path_details.format(1)).text
            except:
                data['Location'] = ""

            # Publication date
            for item in ['/strong/span[1]', '/strong/span[2]', '/span']:
                try:
                    data['Date'] = browser.find_element(By.XPATH, path_details.format(3) + item).text
                    break
                except:
                    data['Date'] = None

            # Salary, Remote and job type
            preferences = browser.find_elements(By.XPATH, "//button[@class='job-details-preferences-and-skills']/div/span")

            data['Salary'], data['Remote'], data['Type'] = "", "", ""

            if preferences:
                # Get the text for each element
                preferences = [item.text for item in preferences]

                # Remove "\n" strings
                preferences = list(filter(lambda x: x.strip(), preferences))

                for item in preferences:
                    if ("$" in item) or ("€" in item) or ("£" in item):
                        data['Salary'] = item
                    elif ("On-site" == item) or ("Hybrid" == item) or ("Remote" == item):
                        data['Remote'] = item
                    else:
                        data['Type'] = item

            # Click in "Show more" to make all job description visible
            try:
                show_more_button = browser.find_element(By.XPATH, "//button[@aria-label='Click to see more description']")
                
                # Scroll to "Show more" button before click 
                browser.execute_script("arguments[0].scrollIntoView();", show_more_button)
                browser.execute_script(f"window.scrollBy(0,-{random.randint(200,400)})","")
                time.sleep( round(random.uniform(1.1, 1.5), 4) )

                show_more_button.click()
                time.sleep(random.uniform(1.9, 2.5))
            except:
                pass

            # Get Raw Job Description
            try:
                data['JobDescription'] = browser.find_element(By.XPATH, "//div[@id='job-details']/div/p").text
            except:
                data['JobDescription'] = ""

            return data

        # Initialize empty dictionary.
        raw = defaultdict(list)

        # Create a ThreadPoolExecutor with the desired number of threads
        with ThreadPoolExecutor(max_workers=self.num_windows) as executor:
            # Submit each URL request as a separate task to the executor
            futures = [executor.submit(run_request, index_url) for index_url in enumerate(urls)]

            # Wait for all tasks to complete
            results = [future.result() for future in futures]

        # "results" contain a list of dictionaries. Append all data in "raw_data" dictionary
        for sample in range(len(results)):
            raw['JobTitle'].append(results[sample]['JobTitle'])
            raw['CompanyName'].append(results[sample]['CompanyName'])
            raw['CompanyLinkedinUrl'].append(results[sample]['CompanyLinkedinUrl'])
            raw['Location'].append(results[sample]['Location'])
            raw['Date'].append(results[sample]['Date'])
            raw['Salary'].append(results[sample]['Salary'])
            raw['Remote'].append(results[sample]['Remote'])
            raw['Type'].append(results[sample]['Type'])
            raw['JobDescription'].append(results[sample]['JobDescription'])

        return raw


    def parse(self, response):
        # Search all job opening links
        job_opening_links = self.search_job_opening_links(self.browser_list[0])

        # Open more windows to run in parallel.
        self.open_web_browsers()

        # Get information from job openings
        for num in range(0, len(job_opening_links), self.num_windows):
            item_links = job_opening_links[num: num + self.num_windows]

            raw_data = self.read_job_info(item_links)

            # Yield
            for num in range(len(item_links)):
                yield {'Job title': raw_data['JobTitle'][num],
                       'Job opening link': item_links[num],
                       'Salary': raw_data['Salary'][num],
                       'Job location': raw_data['Location'][num],
                       'Publication date': raw_data['Date'][num],
                       'Remote': raw_data['Remote'][num],
                       'Job type': raw_data['Type'][num],
                       'Job description': raw_data['JobDescription'][num],
                       'Company name': raw_data['CompanyName'][num],
                       'Company website': "",
                       'Company linkedin url': raw_data['CompanyLinkedinUrl'][num],
                       'Input_Keyword':self.keywords[0],
                       'Input_Location': self.keywords[1],
                       'Search date': self.current_date,
                       'Source': 'Linkedin'}
        
        for item in self.browser_list:
            item.close()
