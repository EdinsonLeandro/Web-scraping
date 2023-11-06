import scrapy, time, os, random
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as OptionsChrome
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class HotforexUsersSpider(scrapy.Spider):
    name = 'hotforex_users'
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
        self.options = OptionsChrome()
        self.options.add_argument('--disable-popup-blocking')

        # Move back one folder in order to reach "drivers". Number "1" set it.
        # https://softhints.com/python-change-directory-parent/
        drivers_dir = os.path.normpath(os.getcwd() + (os.sep + os.pardir) * 1) + '/drivers/chromedriver.exe'

        # "executable_path" has been deprecated selenium python. Here is the solution
        # https://stackoverflow.com/questions/64717302/deprecationwarning-executable-path-has-been-deprecated-selenium-python
        # https://stackoverflow.com/questions/18707338/print-raw-string-from-variable-not-getting-the-answers
        self.drivers_dir = r'%s' %drivers_dir

        # Use undetected webdriver
        self.driver = uc.Chrome(driver_executable_path=drivers_dir, options=self.options)

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

        time.sleep( round(random.uniform(2.1, 3.3), 4) )


    def login(self):
        # Open website
        self.driver.get(self.start_urls[0])

        # Wait until "Home" icon is clickable.
        self.pause_spider(self.driver, "//ul[@class='orejime-Notice-actions']/li[1]/button")
        
        # Accept cookies
        self.accept_cookies()

        # Click Login button
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
        strategies_list_path = "(//ul[@class='menu-subnav'])[2]/li[3]/a"
        self.driver.find_element(By.XPATH, strategies_list_path).click()

        # Wait until "Show Filters" button is clickeable.
        self.pause_spider(self.driver, "//button[@class='btn btn-outline-secondary']")
    

    def parse(self, response):
        # Get maximum number of pages
        last_page = self.driver.find_element(By.XPATH, ".//ul[@class='pagination']/li[8]/a").text
        last_page = int(last_page)
        
        for _ in range(last_page):
            
            for profile in self.driver.find_elements(By.XPATH, ".//div[@id='user-settings-text']"):
                # Get website
                website = profile.find_element(By.XPATH, ".//a").get_attribute("href")

                yield {'Provider Profile': website}
            
            # Click navigation button
            self.driver.find_element(By.XPATH, "//ul[@class='pagination']/li[9]/a").click()

            # Wait until first element is clickable
            self.pause_spider(self.driver, "(//td[@data-title='Strategy Provider']/div/div/a)[1]")


        self.driver.close()
