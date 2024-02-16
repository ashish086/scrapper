import json
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire import webdriver as sw_webdriver
from seleniumwire.utils import decode as sw_decode
from selenium.webdriver.chrome.service import Service


class Driver:
    def __init__(self,) -> None:
        #self.driver_path = driver_path
        self.browser = None
        self.setup()

    def setup(self):
        #service =Service(driver_path)
        chrome_opts = webdriver.ChromeOptions()
        chrome_opts.headless = True
        chrome_opts.add_argument('--no-sandbox')
        chrome_opts.add_argument('--disable-extensions')
        chrome_opts.add_argument('--disable-dev-shm-usage')

        # self.browser = webdriver.Chrome(executable_path=self.driver_path, options=chrome_opts)
        # self.browser = webdriver.Chrome(self.driver_path, options=chrome_opts)
        # self.browser = webdriver.Chrome(executable_path=self.driver_path, chrome_options=chrome_opts)
        # self.browser = webdriver.Chrome(self.driver_path, chrome_options=chrome_opts)
        self.browser = webdriver.Chrome()
        #, options=options

    def tear_down(self):
        self.browser.quit()


class Scraper:
    def __init__(self, driver: Driver, base_url: str = "https://food.grab.com/sg/en/restaurants") -> None:
        self.driver = driver
        self.base_url = base_url
        self.grab_internal_post_api = "https://portal.grab.com/foodweb/v2/search"
        self._init_request()

    def _init_request(self):
        self.driver.browser.get(self.base_url)
        sleep(10)

    def load_more(self):
        condition = EC.presence_of_element_located((By.XPATH, '//*[@id="page-content"]'))

        more_results_button = WebDriverWait(self.driver.browser, 10).until(condition)
        print('more_results_button: ', more_results_button, '\n')
        more_results_button.click()
        sleep(10)

        page_num = 1
        while more_results_button:
            try:
                print('page_num: ', page_num)
                more_results_button.click()
                more_results_button = WebDriverWait(self.driver.browser, 10).until(condition)
                page_num += 1
                sleep(10)
            except TimeoutException:
                print("No more LOAD MORE RESULTS button to be clicked!!!\n")
                break

    def capture_post_response(self):
        post_data = []
        for r in self.driver.browser.requests:
            if r.method == 'POST' and r.url == self.grab_internal_post_api:
                data_1 = sw_decode(r.response.body, r.response.headers.get('Content-Encoding', 'identity'))
                data_1 = data_1.decode("utf8")
                data = json.loads(data_1)
                post_data.append(data)
                print(post_data)
        return post_data

    def get_restaurant_latlng(self, post_data):
        d = {}
        for p in post_data:
            l = p['searchResult']['searchMerchants']
            for rst in l:
                try:
                    d[rst['chainID']] = {'chainName': rst['chainName'], 'latlng': rst['latlng']}
                except Exception as err:
                    d[rst['address']['name']] = {'chainName': rst['address']['name'], 'latlng': rst['latlng']}
        return d

    def scrape(self):
        self.load_more()
        post_data = self.capture_post_response()
        restaurants_latlng = self.get_restaurant_latlng(post_data)
        return restaurants_latlng

    def save(self, restaurants_latlng, file: str = 'grab_restaurants_latlng.json'):
        with open(file, 'w') as f:
            json.dump(restaurants_latlng, f, indent=4)


if __name__ == "__main__":
    #driver_path = "C:\\Users\\SUBHAM\\Music\\Downloads\\chromedriver-win64.exe"
    base_url = "https://food.grab.com/sg/en/restaurants"
    #driver = Driver(driver_path)
    scraper = Scraper(driver, base_url)
    restaurants_latlng = scraper.scrape()
    scraper.save(restaurants_latlng)
    driver.tear_down()
