import scrapy, time, os, random, pickle, re
from scrapy import Selector
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options as OptionsEdge
from selenium.webdriver.edge.service import Service as ServiceEdge
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class HotforexSpider(scrapy.Spider):
    name = 'hotforex'
    allowed_domains = ['www.hfm.com']
    start_urls = ['https://www.hfm.com/sv/en']


    def __init__(self, id, password, delay=30):
        """
        Scraping statistics for copy trading strategies on Hotforex.
        """

        # Parameters
        self.delay = delay
        self.id = id
        self.password = password

        # Do not open a web browser and private mode. I have Selenium 4
        # https://learn.microsoft.com/en-us/answers/questions/839496/how-to-set-edge-capabilities-for-edge-browser-in-p
        self.options = OptionsEdge()
        # self.options.add_argument("headless")
        # self.options.add_argument("inprivate")

        # Move back one folder in order to reach "drivers". Number "1" set it.
        # https://softhints.com/python-change-directory-parent/
        drivers_dir = os.path.normpath(os.getcwd() + (os.sep + os.pardir) * 1) + '/drivers/msedgedriver.exe'

        # "executable_path" has been deprecated selenium python. Here is the solution
        # https://stackoverflow.com/questions/64717302/deprecationwarning-executable-path-has-been-deprecated-selenium-python
        # https://stackoverflow.com/questions/18707338/print-raw-string-from-variable-not-getting-the-answers
        self.drivers_dir = r'%s' %drivers_dir

        # Use Edge browser.
        self.driver = webdriver.Edge(service=ServiceEdge(self.drivers_dir), options=self.options)

        # View full web page
        self.driver.maximize_window()

        # Login
        self.login()

        # Click HFcopy
        self.click_hfcopy()


    # https://www.selenium.dev/documentation/webdriver/waits/
    # https://www.selenium.dev/selenium/docs/api/py/webdriver_support/selenium.webdriver.support.expected_conditions.html
    def pause_spider(self, driver, path):
        WebDriverWait(driver, timeout=self.delay).\
            until(EC.element_to_be_clickable((By.XPATH, path)))

        time.sleep( round(random.uniform(2.0, 6.0), 4) )


    def login(self):
        # Open website
        self.driver.get(self.start_urls[0])

        # Wait until "Home" icon is clickable.
        self.pause_spider(self.driver, "//ul[@class='orejime-Notice-actions']/li[1]/button")
        
        # Accept cookies
        self.accept_cookies()

        # Click Login button
        # login_button = "(//div[@class='container'])[1]/div[3]/div[1]/a"
        login_button = "(//div[@class='container position-relative pe-lg-0'])[2]/div[3]/div[1]/a"
        self.driver.find_element(By.XPATH, login_button).click()

        # Wait until "Home" icon is clickable.
        self.pause_spider(self.driver, "//a[@class='brand-logo']")

        # Write email and password
        # https://www.selenium.dev/documentation/webdriver/elements/finders/
        self.driver.find_element(By.ID, 'username').send_keys(self.id)
        self.driver.find_element(By.ID, 'password').send_keys(self.password)

        # Wait
        time.sleep(round(random.uniform(3.0, 5.0), 4))

        # Press "Enter" after write. "Keys.RETURN" do the same
        # https://www.geeksforgeeks.org/special-keys-in-selenium-python/
        self.driver.find_element(By.ID, 'password').send_keys(Keys.ENTER)
        
        # Wait until "Home" icon is clickable.
        self.pause_spider(self.driver, "//div[@class='brand flex-column-auto']/a")

        # Wait
        time.sleep(round(random.uniform(2.0, 4.0), 4))


    def accept_cookies(self):
        accept_cookies = "//ul[@class='orejime-Notice-actions']/li[1]/button"
        try:
            # Click pop-up window "HOW WE USE COOKIES"
            self.driver.find_element(By.XPATH, accept_cookies).click()
            
            # Wait
            time.sleep(round(random.uniform(2.0, 4.0), 4))
        except:
            pass        


    def click_hfcopy(self):
        # Click HFcopy menu
        self.driver.find_element(By.ID, 'menu_item_hf_copy').click()

        # Wait
        time.sleep(round(random.uniform(2.0, 4.0), 4))

        # Click on "Strategies List" button
        strategies_list = "//ul[@class='menu-nav']/li[13]/div/ul/li[3]/a"
        self.driver.find_element(By.XPATH, strategies_list).click()

        # Wait until "Show Filters" button is clickeable.
        self.pause_spider(self.driver, "//button[@class='btn btn-outline-secondary']")


    def use_regex(self, pattern, data):
        try:
            result = re.findall(pattern, data)[0]
        except:
            result = None

        return result


    def read_data(self, url):
        # Paths
        user_settings_path = ".//div[@id='user-settings-text']"
        account_path = ".//div[@class='card-body']/div[2]"
        stats_path_1 = "(.//div[@class='userBoxInfo'])[2]/div/div[1]/div/table/tbody"
        stats_path_2 = "(.//div[@class='userBoxInfo'])[2]/div/div[2]/table/tbody"
        trading_path = "(.//div[@class='userBoxInfo'])[3]/div/div[2]/div/table/tbody"

        # Patterns to do regex.
        pattern_float = r"\-?\d+\.?\d+"
        pattern_int = r"\d+"
        pattern_date = r"[\d/:]+"

        # Open new tab
        self.driver.execute_script("window.open('');")

        # Switch driver to new tab window
        self.driver.switch_to.window(self.driver.window_handles[1])

        # Get url
        self.driver.get(url)
        self.pause_spider(self.driver, "//li[@class='breadcrumb-item']/a")

        # Read HTML data
        html_user =  Selector(text=self.driver.page_source)

        # ---------- USER
        user = {}
        user['Name'] = html_user.xpath(user_settings_path + "/span/b/text()").get()
        user['Id'] = html_user.xpath(user_settings_path + "/span[2]/text()").get()
        user['Url'] = url
        user['Country'] = html_user.xpath(user_settings_path + "/span[4]/text()").get()
        
        # Last updated date. Clean data with regular expression
        last_updated = html_user.xpath(user_settings_path + "/span[5]/text()").get()
        last_updated = " ".join(re.findall(pattern_date, str(last_updated))[1:3])

        user['Last updated'] = last_updated
        user['Message'] = html_user.xpath(".//div[@class='col-md-5 col-sm-12']/center/p/i/text()").get()

        # ---------- ACCOUNT
        account = {}
        since = html_user.xpath(account_path + "/div[1]/div/span[2]/i/following::node()").get()
        gain = html_user.xpath(account_path + "/div[2]/div/span[2]/i/following::node()").get()
        dd = html_user.xpath(account_path + "/div[3]/div/br/following::node()").get()
        followers = html_user.xpath(account_path + "/div[4]/div/i/following::node()").get()
        fee = html_user.xpath(account_path + "/div[5]/div/span[2]/text()").get()
        score = html_user.xpath(account_path + "/div[6]/div/span[2]/text()").get()

        # Use regex to clean data
        account['Since'] = str(since).strip()
        account['Gain'] = self.use_regex(pattern_float, gain)
        account['Max Drawdown'] = self.use_regex(pattern_float, dd)
        account['Followers'] = self.use_regex(pattern_int, followers)
        account['Fee'] = self.use_regex(pattern_int, fee)
        account['Score'] = str(score).strip()

        # ---------- PERFORMANCE
        performance = {}
        
        # Select onl rows with years data
        years_data = html_user.xpath("//div[@class='userBoxInfo mb-7']/div")
        years_data = years_data[2 : len(years_data) - 1]

        for row in years_data:
            # Get year
            year = row.xpath(".//div[1]/span/b/text()").get()
            performance[year] = []

            for item in row.xpath(".//div[2]/div/div"):
                num = item.xpath(".//a/text()").get()
                # If raise an error, there is no data for this month.
                num = self.use_regex(pattern_float, num)

                # Append performance data for each month
                performance[year].append(num)
            
            # Total
            total = row.xpath(".//div[3]/a[2]/text()").get()
            total = self.use_regex(pattern_float, total)

            performance[year].append(total)
        
        # ---------- Financial Statistics.
        financial = {}
        balance = html_user.xpath(stats_path_1 + "/tr[1]/td/text()").get()
        equity = html_user.xpath(stats_path_1 + "/tr[2]/td/text()").get()
        initial_deposit = html_user.xpath(stats_path_1 + "/tr[3]/td/text()").get()
        total_deposit = html_user.xpath(stats_path_2 + "/tr[1]/td/text()").get()
        total_withdrawals = html_user.xpath(stats_path_2 + "/tr[2]/td/text()").get()
        profit = html_user.xpath(stats_path_2 + "/tr[3]/td/text()").get()

        stats = [balance, equity, initial_deposit, total_deposit, total_withdrawals, profit]
        stats = list(map( lambda x: "".join(re.findall(pattern_float, str(x))), stats ))

        financial['Balance'] = stats[0]
        financial['Equity'] = stats[1]
        financial['Initial Deposit'] = stats[2]
        financial['Total Deposits'] = stats[3]
        financial['Total Withdrawals'] = stats[4]
        financial['Profit'] = stats[5]

        # ---------- Trading.
        trading = {}
        trading['N Closed'] = html_user.xpath(trading_path + "/tr[1]/td/text()").get()
        trading['N Open'] = html_user.xpath(trading_path + "/tr[2]/td/text()").get()
        trading['Positive Closed'] = html_user.xpath(trading_path + "/tr[3]/td/span/text()").get()
        trading['Negative Closed'] = html_user.xpath(trading_path + "/tr[4]/td/span/text()").get()

        profitability = html_user.xpath(trading_path + "/tr[5]/td/text()").get()
        trading['Profitability'] = self.use_regex(pattern_float, profitability)

        avg_profit = html_user.xpath(trading_path + "/tr[6]/td/span/text()").get()
        trading['Avg Profit'] = self.use_regex(pattern_float, avg_profit)

        avg_loss = html_user.xpath(trading_path + "/tr[7]/td/span/text()").get()
        trading['Avg Loss'] = self.use_regex(pattern_float, avg_loss)

        trading['Avg size'] = html_user.xpath(trading_path + "/tr[8]/td/text()").get()
        trading['Avg length'] = html_user.xpath(trading_path + "/tr[9]/td/text()").get()

         # ---------- Activity.
        activity = {}
        activity['Symbol'], activity['Action'], activity['Size'] = [], [], []
        activity['Open'], activity['Close'], activity['Profit'] = [], [], []

        for item in html_user.xpath("(//div[@class='userBoxInfo'])[4]/table/tbody/tr"):
            activity['Symbol'].append(item.xpath(".//td[1]/text()").get())
            activity['Action'].append(item.xpath(".//td[2]/span/text()").get())
            activity['Size'].append(item.xpath(".//td[3]/text()").get())
            activity['Open'].append(item.xpath(".//td[4]/text()").get())
            activity['Close'].append(item.xpath(".//td[5]/text()").get())
            activity['Profit'].append(item.xpath(".//td[6]/text()").get())

        self.driver.close()

        # Switch back to the first tab
        self.driver.switch_to.window(self.driver.window_handles[0])

        raw_data = {'User': user, 'Account': account, 'Performance': performance,
                    'Financial': financial, 'Trading': trading, 'Activity': activity}

        return raw_data


    def parse(self, response):
        # Read HTML data
        html_data =  Selector(text=self.driver.page_source)

        for profile in html_data.xpath("//div[@id='user-settings-text']"):
            # Get website
            website = profile.xpath(".//a/@href").get()
            website = f"https://my.hfm.com{website}"

            data = self.read_data(website)

            yield {'Name': data['User']['Name'],
                   'ID': data['User']['Id'],
                   'Hotforex url': data['User']['Url'],
                   'Location': data['User']['Country'],
                   'Last updated': data['User']['Last updated'],
                   'Message': data['User']['Message'],

                   'Active since': data['Account']['Since'],
                   'Gain': data['Account']['Gain'],
                   'Max Drawdown': data['Account']['Max Drawdown'],
                   'Followers': data['Account']['Followers'],
                   'Performance Fee': data['Account']['Fee'],
                   'Stability Score': data['Account']['Score'],
                   
                   'Performance': data['Performance'],
                   
                   'Balance': data['Financial']['Balance'],
                   'Equity': data['Financial']['Equity'],
                   'Initial Deposit': data['Financial']['Initial Deposit'],
                   'Total Deposits': data['Financial']['Total Deposits'],
                   'Total Withdrawals': data['Financial']['Total Withdrawals'],
                   'Profit': data['Financial']['Profit'],
                   
                   'Number of Closed Trades': data['Trading']['N Closed'],
                   'Number of Open Trades': data['Trading']['N Open'],
                   'Positive Closed Trades': data['Trading']['Positive Closed'],
                   'Negative Closed Trades': data['Trading']['Negative Closed'],
                   'Profitability': data['Trading']['Profitability'],
                   'Average Profit': data['Trading']['Avg Profit'],
                   'Average Loss': data['Trading']['Avg Loss'],
                   'Average Lot Size': data['Trading']['Avg size'],
                   'Average Trade Length': data['Trading']['Avg length'],

                   'Activity': data['Activity']}

            time.sleep( round(random.uniform(5.0, 8.0), 4) )

        self.driver.close()
        
        # Sometimes, the script open again the same link. Scrape all the users, but repeat again
        # some of them. It does not deal with pagination.