import scrapy, time, os, random
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as OptionsChrome
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException


class HotforexUsersSpider(scrapy.Spider):
    name = 'hotforex_users'
    allowed_domains = ['www.hfm.com']
    start_urls = ['https://www.hfm.com/int/en/']


    def __init__(self, input_spider, delay=15):
        """
        Scraping statistics for copy trading strategies on Hotforex.
        """

        # Parameters
        self.delay = delay
        self.credentials = input_spider

        # Do not open a web browser and private mode. I have Selenium 4
        # https://learn.microsoft.com/en-us/answers/questions/839496/how-to-set-edge-capabilities-for-edge-browser-in-p
        options = OptionsChrome()
        options.add_argument('--disable-popup-blocking')

        # Move back one folder in order to reach "drivers". Number "1" set it.
        # https://softhints.com/python-change-directory-parent/
        drivers_dir = os.path.normpath(os.getcwd() + (os.sep + os.pardir) * 1) + '/drivers/chromedriver.exe'

        # "executable_path" has been deprecated selenium python. Here is the solution
        # https://stackoverflow.com/questions/64717302/deprecationwarning-executable-path-has-been-deprecated-selenium-python
        # https://stackoverflow.com/questions/18707338/print-raw-string-from-variable-not-getting-the-answers
        drivers_dir = r'%s' %drivers_dir

        # Testing version directory
        testing_dir = os.path.normpath(os.getcwd() + (os.sep + os.pardir) * 1) + '/drivers/chrome-win64_113/chrome.exe'

        # Use undetected webdriver
        self.driver = uc.Chrome(driver_executable_path=drivers_dir, options=options, browser_executable_path=testing_dir)

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

        time.sleep( round(random.uniform(2.1, 2.9), 4) )


    def login(self):
        # Open website
        self.driver.get(self.start_urls[0])

        # Wait until "Home" icon is clickable.
        self.pause_spider(self.driver, "//div[@class='container position-relative pe-lg-0']/a")
        
        # Accept cookies
        self.accept_cookies()

        # Click Login button
        login_button = "(//div[@class='container position-relative pe-lg-0'])[2]/div[3]/div[1]/a"
        self.driver.find_element(By.XPATH, login_button).click()

        # Wait until "Home" icon is clickable.
        self.pause_spider(self.driver, "//a[@class='brand-logo']")

        # Write email and password
        # https://www.selenium.dev/documentation/webdriver/elements/finders/
        self.driver.find_element(By.ID, 'username').send_keys(self.credentials[0])
        time.sleep(random.uniform(2.1, 3.0))
        self.driver.find_element(By.ID, 'password').send_keys(self.credentials[1])

        # Wait
        time.sleep(random.uniform(2.1, 3.0))

        # Press "Enter" after write. "Keys.RETURN" do the same
        # https://www.geeksforgeeks.org/special-keys-in-selenium-python/
        self.driver.find_element(By.ID, 'password').send_keys(Keys.ENTER)
        
        # Time sleep to write Google Auth and press Enter
        time.sleep(random.uniform(21, 30))

        # Wait until "Home" icon is clickable.
        self.pause_spider(self.driver, "//div[@class='brand flex-column-auto']/a")


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

        # Click on "Follow A Strategy" button
        strategies_list_path = "(//ul[@class='menu-subnav'])[2]/li[3]/a"
        self.driver.find_element(By.XPATH, strategies_list_path).click()

        # Wait until the first result is clickable
        self.pause_spider(self.driver, "(//div[@id='card-body']/div/div/a)[1]")


    def try_to_click(self, driver, button_path, path_wait):
        """
        Function to click
        """
        condition_click = False
        exceptions = (StaleElementReferenceException, ElementClickInterceptedException)

        element = driver.find_element(By.XPATH, button_path)

        while not condition_click:
            try:
                # Click button and wait until subtitle is clickable.
                element.click()
                self.pause_spider(driver, path_wait)

                condition_click = True

            except exceptions as error_msg:
                print('Error clicking on tab: {}. Trying again'.format(error_msg))
                driver.execute_script("arguments[0].scrollIntoView();", element)

                time.sleep( round(random.uniform(1.5, 3.3), 4) )
            
            except NoSuchElementException as error_msg:
                # "Next" button doesn't exist
                condition_click = False
        
        return condition_click


    def parse(self, response):
        next_page= True

        while next_page:
            
            for profile in self.driver.find_elements(By.XPATH, "//div[@id='card-body']/div/div/a"):
                # Get name and website
                try:
                    provider_name = profile.find_element(By.XPATH, ".//div/h3").text
                except:
                    provider_name = "NA"
                
                try:
                    website = profile.get_attribute("href")
                except:
                    website = "NA"

                yield {'Provider name': provider_name,
                       'Provider profile': website}
            
            # Click navigation button and wait
            button = "//div[@class='paginationjs-pages']/ul/li[contains(@title, 'Next page')]"
            wait = "(//div[@id='card-body']/div/div/a)[1]"

            next_page = self.try_to_click(self.driver, button, wait)

        self.driver.close()
