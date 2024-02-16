import json
from time import sleep
import pandas as pd
#from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire import webdriver
from seleniumwire.utils import decode as sw_decode


class Driver:
    def __init__(self) -> None:
        self.browser = None
        self.setup()

    def setup(self):
        self.browser = webdriver.Chrome()

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

    # def load_more(self):
    #     condition = EC.presence_of_element_located((By.XPATH, '//*[@id="page-content"]'))

    #     more_results_button = WebDriverWait(self.driver.browser, 10).until(condition)
    #     print('more_results_button: ', more_results_button, '\n')
    #     more_results_button.click()
    #     sleep(10)

    #     page_num = 1
    #     while more_results_button:
    #         try:
    #             print('page_num: ', page_num)
    #             more_results_button.click()
    #             more_results_button = WebDriverWait(self.driver.browser, 10).until(condition)
    #             page_num += 1
    #             sleep(10)
    #         except TimeoutException:
    #             print("No more LOAD MORE RESULTS button to be clicked!!!\n")
    #             break
    def load_more(self):
        condition = EC.presence_of_element_located((By.XPATH, '//*[@id="page-content"]'))

        try:
            page_num = 1
            while page_num <= 10:
                more_results_button = WebDriverWait(self.driver.browser, 10).until(condition)
                print('page_num: ', page_num)
                more_results_button.click()
                sleep(10)
                page_num += 1
        except TimeoutException:
            print("No more LOAD MORE RESULTS button to be clicked!!!\n")
            print("Window closed. Unable to load more results.")
        

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

    # def scrape(self):
    #     self.load_more()
    #     post_data = self.capture_post_response()
    #     restaurants_latlng = self.get_restaurant_latlng(post_data)
    #     return restaurants_latlng

    # def save(self, restaurants_latlng, file: str = 'grab_restaurants.json'):
    #     with open(file, 'w') as f:
    #         json.dump(restaurants_latlng, f, indent=4)
    # def scrape(self):
    #     self.load_more()
    #     post_data = self.capture_post_response()
    #     restaurants_latlng = self.get_restaurant_latlng(post_data)
        
    #     print("Data scraped successfully:", restaurants_latlng)  # Debug statement
        
    #     return restaurants_latlng

    # def save(self, restaurants_latlng, file: str = 'grab_restaurants.json'):
    #     try:
    #         with open(file, 'w') as f:
    #             json.dump(restaurants_latlng, f, indent=4)
    #             print("Data saved successfully to:", file)  # Debug statement
    #     except Exception as e:
    #         print("Error saving data:", e)  # Debug statement


    def scrape(self):
        self.load_more()
        post_data = self.capture_post_response()
        restaurants_latlng = self.get_restaurant_latlng(post_data)
        
        print("Data scraped successfully:", restaurants_latlng)  # Debug statement
        
        return restaurants_latlng

    def save(self, restaurants_latlng, file: str = 'grab_restaurants.csv'):
        try:
            df = pd.DataFrame.from_dict(restaurants_latlng, orient='index')
            df.to_csv(file, index_label='chainID')
            print("Data saved successfully to:", file)  # Debug statement
        except Exception as e:
            print("Error saving data:", e)  # Debug stateme

if __name__ == "__main__":
    driver = Driver()
    base_url = "https://food.grab.com/sg/en/restaurants"
    scraper = Scraper(driver, base_url)
    restaurants_latlng = scraper.scrape()
    scraper.save(restaurants_latlng)
    driver.tear_down()
    driver.quit()