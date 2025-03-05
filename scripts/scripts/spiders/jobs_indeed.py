import scrapy, os, time, random, re, shlex
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options as OptionsChrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from datetime import datetime


class JobsIndeedSpider(scrapy.Spider):
    name = 'jobs_indeed'
    allowed_domains = ['www.indeed.com']
    start_urls = ['http://www.indeed.com']

    handle_httpstatus_list = [403]

    def __init__(self, input_spider, delay=20):
        # Parameters
        self.delay = delay
        self.keywords = input_spider[0]          # Keyword and Location, in this order
        self.num_windows = input_spider[1]       # Number of windows to run in parallel

        # Current date
        self.current_date = datetime.now().strftime('%Y-%m-%d')

        # Move back one folder in order to reach "drivers". Number "1" set it.
        drivers_dir = os.path.normpath(os.getcwd() + (os.sep + os.pardir) * 1) + '/drivers/chromedriver.exe'

        # "executable_path" has been deprecated selenium python. Here is the solution
        drivers_dir = r'%s' %drivers_dir

        # Testing version directory
        self.testing_dir = os.path.normpath(os.getcwd() + (os.sep + os.pardir) * 1) + '/drivers/chrome-win64_113/chrome.exe'

        # Open three new windows
        self.browser_list = []

        # User agents: Edge, Chrome, Firefox, Opera, Vivaldi. Internet Explorer doesn't work.
        user_agents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.2739.63",
                       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                       "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
                       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 OPR/112.0.0.0",
                       "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Vivaldi/6.9.3447.37"]

        for _ in range(self.num_windows):
            option = OptionsChrome()
            option.add_argument('--disable-popup-blocking')
            # option.add_argument(f'--user-agent={random.choice(user_agents)}')

            new_browser = uc.Chrome(driver_executable_path=drivers_dir, options=option, browser_executable_path=self.testing_dir)
            new_browser.maximize_window()
 
            # In order to overcome Cloudfare captcha, the trick is the following:
            # 1. Open a second tab.
            # 2. In this new tab, send a request to "http://www.indeed.com/"
            # 3. Manually click in order to overcome the captcha.
            # 4. Refresh the previous tab

            # I found this trick here: https://github.com/ultrafunkamsterdam/undetected-chromedriver/issues/1388
            new_browser.get(self.start_urls[0])
            time.sleep(random.uniform(15.5, 20.9))

            self.browser_list.append(new_browser)


    def pause_spider(self, driver, path):
        WebDriverWait(driver, timeout=self.delay).\
            until(EC.element_to_be_clickable((By.XPATH, path)))
        
        time.sleep( random.uniform(2.1, 2.9) )


    def search_keywords(self, driver):
        """
        Search keywords and location using request to web browser
        """
        # We need to add to this url the keywords and location
        url = f"{self.start_urls[0]}/jobs?q="

        # Tuple unpacking
        keyword, location = self.keywords

        # Get a list of Keywords. Assumption: the keywords are in this way: "key1", "key2", etc.
        keyword_list = shlex.split(keyword, posix=False)

        # Add keywords to url
        for item in keyword_list:
            url += item + "+"

        # Discard the last "+"
        url = url[:-1]

        # Add location
        url = url + "&l=" + location.replace(" ", "+")

        # Request url with keywords and location
        driver.get(url)
        self.pause_spider(driver, "//div[@class='gnav-Logo-icon']")

        button_path = "(//div[@class='yosegi-FilterPill-dropdownPillContainer']/button)[1]"

        while True:
            try:
                # Wait until first button is clickable
                self.pause_spider(driver, button_path)
                break
            except TimeoutException as error_msg:
                print("Trying again")

        return url


    def get_item_data(self, driver, path, text):
        """
        text: Boolean. True if we want text. Otherwise, get "href" attribute
        """
        try:
            if text:
                item_data = driver.find_element(By.XPATH, path).text
            else:
                item_data = driver.find_element(By.XPATH, path).get_attribute('href')
        except:
            item_data = ""

        return item_data


    def read_job_info(self, urls):

        def run_request(input_request):
            # Paths
            title_path = ["//h2[@data-testid='simpler-jobTitle']",
                          "//h1[@data-testid='jobsearch-JobInfoHeader-title']"]
            
            company_path = ["//div[@data-testid='simpler-simplified-header']/div/div/span/a",
                            "//div[@data-testid='inlineHeader-companyName']/span/a"]
            
            location_remote_path = ["//div[@data-testid='jobsearch-JobInfoHeader-companyLocation']/div",
                                    "//div[@data-testid='jobsearch-CompanyInfoContainer']/div/div/div/div"]

            index , url = input_request

            # Create a new WebDriver instance for each thread
            browser = self.browser_list[index]
            
            # Get url
            while True:
                try:
                    # Time sleep in order to avoid sending  all request at the same time
                    time.sleep(random.uniform(0.5, 1.9))

                    browser.get(url)
                    self.pause_spider(browser, "//div[@class='gnav-Logo-icon']")
                    break
                except TimeoutException as error_msg:
                    print('Timeout exception raised. Trying again')
                    # WE CAN SEND A MESSAGE BY TELEGRAM TO LET KNOW THE ISSUE WITH THE CAPTCHA
                    break

            data = {}

            # ----- Job title
            for path in title_path:
                data['JobTitle'] = self.get_item_data(browser, path, True)

                # Break if there is information
                if data['JobTitle']:
                    break

            # ----- Company name
            for path in company_path:
                data['CompanyName'] = self.get_item_data(browser, path, True)
                
                # Break if there is information
                if data['CompanyName']:
                    break

            # ----- Indeed profile
            for path in company_path:
                data['CompanyIndeed'] = self.get_item_data(browser, path, False)

                if data['CompanyIndeed']:
                    break

            # ----- Location and Remote
            for path in location_remote_path:
                header = browser.find_elements(By.XPATH, path)

                if header:
                    break

            header = [item.text for item in header]
            data['Location'], data['Remote'] = "", ""

            if header:
                # Sometimes, the path include the company name. Delete this item
                check_name = [data['CompanyName'] in item for item in header]
                if any(check_name):
                    header.pop(check_name.index(True))

                if header:
                    for item in ['Remote', 'Hybrid work']:
                        try:
                            # Find the index of "Remote" or 'Hybrid work'
                            position_remote = header.index(item)
                            data['Remote'] = header[position_remote]

                            # Remove the item from the list
                            header.pop(position_remote)                        
                            break
                        except:
                            pass

                    if header:
                        # If there is one more element, the Location will be the last one
                        data['Location'] = header[-1]

            # ----- Salary and Job type
            try:
                salary_job_type = browser.find_elements(By.XPATH, "//div[@id='salaryInfoAndJobType']/span")
            except:
                salary_job_type = ""

            # Sometimes, this line have salary and job type, other times only have only one
            if salary_job_type:
                if len(salary_job_type) == 2:
                    # Extract salary and job opening
                    salary_job_type = [x.text for x in salary_job_type]
                    salary, data['Type'] = salary_job_type[0], salary_job_type[1][2:]
                else:
                    # Check if one of ['$', '€', '£'] are in salary_job_type[0]
                    if any(list(map(lambda x: x in salary_job_type[0].text, ["$", "\u20AC", "\u00A3"]))):
                        # The first item is the salary
                        salary, data['Type'] = salary_job_type[0].text, None
                    else:
                        salary, data['Type'] = None, salary_job_type[0].text
            else:
                salary, data['Type'] = None, None
            
            # Use regex to clean salary data. This regex is the same that we are using in linkedin script.
            if salary:
                # Match Dollar, Euro or British pound
                salary = re.findall(r"[\$\u20AC\u00A3]{1}\d*\,?\.?\d*", salary, re.UNICODE)

                # Sometimes, salary is range per year. Other times is one number per hour
                data['Salary'] = " - ".join(salary) if len(salary)==2 else salary[0]
            else:
                data['Salary'] = None

            try:
                # Job description
                job_description = browser.find_element(By.XPATH, "//div[@id='jobDescriptionText']").text
                
                # Remove duplicate sentences
                job_description = job_description.split("\n")
                job_description = list(dict.fromkeys(job_description))

                data['JobDescription'] = job_description = "\n".join(job_description)
            except:
                data['JobDescription'] = ""

            return data

        # Initialize empty dictionary.
        raw = defaultdict(list)

        # Create a ThreadPoolExecutor with the desired number of threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit each URL request as a separate task to the executor
            futures = [executor.submit(run_request, index_url) for index_url in enumerate(urls)]

            # Wait for all tasks to complete
            results = [future.result() for future in futures]

        # "results" contain a list of dictionaries. Append all data in "raw_data" dictionary
        for sample in range(len(results)):
            raw['JobTitle'].append(results[sample]['JobTitle'])
            raw['CompanyName'].append(results[sample]['CompanyName'])
            raw['Location'].append(results[sample]['Location'])
            raw['Remote'].append(results[sample]['Remote'])
            raw['Salary'].append(results[sample]['Salary'])
            raw['Type'].append(results[sample]['Type'])
            raw['CompanyIndeed'].append(results[sample]['CompanyIndeed'])
            raw['JobDescription'].append(results[sample]['JobDescription'])

        return raw


    def read_job_links(self, driver, url):
        """
        Read all Job opening links and Job state dates
        """

        # "next_button = True" in order to enter to first page.
        num_jobs_path = "//div[@class='jobsearch-JobCountAndSortPane-jobCount css-1xv49jx eu4oa1w0']/span"
        
        # Initialize empty list to save all job opening links and Job state date
        job_openings_links = []

        # Read number of job openings. If the value is lower than or equal to 15, it means that there is only one page
        num_jobs = driver.find_element(By.XPATH, num_jobs_path).text
        num_jobs = re.search(r"\d*,?\d+", num_jobs)[0].replace(",", "")  #type: ignore
        num_jobs = int(num_jobs)

        # There are maximum 67 pages on Indeed (15 * 67 = 1005)
        for page in range(67):
        # for page in range(1):
            driver.get(url + f"&start={page}0")
            self.pause_spider(driver, "//div[@class='gnav-Logo-icon']")

            # Read all openings objects
            openings = driver.find_elements(By.XPATH, "//div[@class='job_seen_beacon']")

            # Read job openings links.
            links = [item.find_element(By.XPATH, ".//table/tbody/tr/td/div/h2/a") for item in openings]
            job_openings_links.extend([item.get_attribute('href') for item in links])

            # If this messahe appears: "We have removed some job postings very similar to those already shown", it means
            # that there is no more results.
            try:
                show_omitted = driver.find_element(By.XPATH, "//a[@data-testid='show-omitted-jobs-negative']")
            except:
                show_omitted = ""

            # If there is only one page or indeed reaches the maximum number of results
            if (num_jobs <= 15) or (show_omitted):
                break
        
        return job_openings_links


    def search_website_data(self, urls):

        def run_request(input_request):
            """
            From indeed profile link, search the the website and then the linkedIn url.
            """
            list_path = ["//li[@data-testid='companyInfo-companyWebsite']/div[2]/a",
                         "//div[@data-testid='simpler-simplified-header']/div/div/span/a"]

            index , url = input_request

            # Create a new WebDriver instance for each thread
            browser = self.browser_list[index]

            # Time sleep in order to avoind sending all request at the same time
            time.sleep(random.uniform(0.5, 1.9))

            website = ""

            # Sometimes, the Company indeed profile is not available
            if url:
                browser.get(url)
                self.pause_spider(browser, "//div[@class='gnav-Logo-icon']")

                # Get company website from indeed profile
                for item in list_path:
                    try:
                        website = browser.find_element(By.XPATH, item).get_attribute('href')
                        break
                    except:
                        website = ""

            return website

        # Initialize empty dictionary.
        raw = []

        # Create a ThreadPoolExecutor with the desired number of threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit each URL request as a separate task to the executor
            futures = [executor.submit(run_request, index_url) for index_url in enumerate(urls)]

            # Wait for all tasks to complete
            results = [future.result() for future in futures]

        # "results" contain a list of list. Append all data in "raw" dictionary
        for sample in range(len(results)):
            raw.append(results[sample])
        
        return raw    


    def parse(self, response):
        # Search keyword
        link = self.search_keywords(self.browser_list[0])

        # 1. Read all job opening links.
        job_openings_links = self.read_job_links(self.browser_list[0], link)

        # 2. Read information from each job opening link
        for num in range(0, len(job_openings_links), self.num_windows):
            links = job_openings_links[num: num + self.num_windows]
            raw_data = self.read_job_info(links)

            # 3. Search company websites from indeed profiles
            websites_data = self.search_website_data(raw_data['CompanyIndeed'])

            # Yield
            for element in range(len(links)):
                # Linkedin profiles after the spider execution
                yield {'Job title' : raw_data['JobTitle'][element],
                       'Job opening link': links[element],
                       'Salary': raw_data['Salary'][element],
                       'Job location': raw_data['Location'][element],
                       'Publication date': "",
                       'Remote': raw_data['Remote'][element],
                       'Job type': raw_data['Type'][element],
                       'Job description': raw_data['JobDescription'][element],
                       'Company name': raw_data['CompanyName'][element],
                       'Company website': websites_data[element],
                       'Company linkedin url': "",
                       'Input_Keyword':self.keywords[0],
                       'Input_Location': self.keywords[1],
                       'Search date': self.current_date,
                       'Source': 'Indeed'}

        # Close all browsers
        for window in self.browser_list:
            window.close()
