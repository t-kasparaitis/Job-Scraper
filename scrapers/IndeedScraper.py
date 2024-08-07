import time
import random
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from scrapers.Scraper import Scraper
from fake_useragent import UserAgent
import traceback
import os


class IndeedScraper(Scraper):
    def __init__(self, **kwargs):
        ua = UserAgent(os='windows', browsers='chrome', platforms='pc')
        super().__init__('Indeed', 'https://www.indeed.com', user_agent=ua.random, **kwargs)
        self.logger.info(f"{self.__class__.__name__} initialized")

    def run(self):
        try:
            self.scrape_search_terms()
        except Exception as e:
            current_page_title = self.driver.title  # Get the page title for crashes to provide more detail
            stack_trace = traceback.format_exc()
            self.logger.error(
                f"Failure: {type(e).__name__}, {e}\nOn page: {current_page_title}\n{stack_trace}")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            screenshot_name = f'{self.source}_{timestamp}_Error_Screenshot.png'
            screenshot_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_filepath = os.path.join(screenshot_dir, screenshot_name)
            self.driver.save_screenshot(screenshot_filepath)
            raise
        finally:
            self.close()

    def scrape_search_terms(self):
        search_terms = self.read_json_file()
        total_terms = len(search_terms['Indeed_Search_Terms'])
        for index, term in enumerate(search_terms['Indeed_Search_Terms']):
            try:
                self.scraped_job_listings = {}
                keyword = term['keyword']
                location = term['location']
                self.logger.info(f"Start: Searching for {keyword} in {location}")
                self.input_search_keywords(keyword, location)
                self.apply_job_filters(location)
                self.scrape_job_pages()
                csv_filepath = self.generate_filepath()
                self.write_to_csv(self.scraped_job_listings, csv_filepath)
                # Go back to the main page to input search terms, unless it's the last term:
                if index < total_terms - 1:
                    self.driver.get('https://www.indeed.com')
                    time.sleep(10)  # Allow some time to load the main page again
            except TimeoutException:
                inner_stack_trace = traceback.format_exc()
                current_page_title = self.driver.title  # Get the page title for crashes to provide more detail
                self.logger.error(f"Failure: {TimeoutException}"
                                  f"\nOn Page: {current_page_title}"
                                  f"\nDetails: {inner_stack_trace}")
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                screenshot_name = f'{self.source}_{timestamp}_Error_Screenshot.png'
                screenshot_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_filepath = os.path.join(screenshot_dir, screenshot_name)
                self.driver.save_screenshot(screenshot_filepath)
                # Cover the edge case of a crash on the very last term:
                if index >= total_terms - 1:
                    return
                else:
                    self.driver.get('https://www.indeed.com')
                    time.sleep(10)  # Allow some time to load the main page again
                    continue

    def input_search_keywords(self, keyword, location):
        time.sleep(
            5)  # Gets around a Stale Element Exception that otherwise occurs when interacting with search box etc.
        keyword_box = self.wait.until(
            ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'text-input-what')]")))
        # The timers after an element are necessary as otherwise the search boxes are cleared out somehow:
        time.sleep(random.uniform(1, 2))
        keyword_box.click()
        keyword_box.send_keys(Keys.CONTROL + "a")
        keyword_box.send_keys(Keys.BACKSPACE)
        keyword_box.send_keys(keyword)
        time.sleep(random.uniform(1, 2))
        location_box = self.wait.until(
            ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'text-input-where')]")))
        time.sleep(random.uniform(1, 2))
        location_box.click()
        location_box.send_keys(Keys.CONTROL + "a")
        location_box.send_keys(Keys.BACKSPACE)
        location_box.send_keys(location)
        time.sleep(random.uniform(1, 2))
        search_button = self.wait.until(ec.element_to_be_clickable((
            By.XPATH, "//button[normalize-space()='Search']")))
        time.sleep(random.uniform(1, 2))
        search_button.click()
        time.sleep(random.uniform(1, 2))
        try:
            self.wait.until(ec.title_contains("Just a moment..."))
            self.security_verification()
        except TimeoutException:
            pass

    def apply_job_filters(self, location):
        time.sleep(3)
        date_posted_button = self.wait.until(ec.element_to_be_clickable((By.ID, "filter-dateposted")))
        date_posted_button.click()
        time.sleep(3)
        time_filter = self.wait.until(ec.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Last 24 hours')]")))
        time_filter.click()
        time.sleep(3)
        if location == 'Remote':
            remote_filter_button = self.wait.until(ec.element_to_be_clickable((By.ID, "filter-remotejob")))
            remote_filter_button.click()
            time.sleep(3)
            remote_filter = self.wait.until(ec.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Remote')]")))
            remote_filter.click()
            time.sleep(3)
        else:
            distance_filter_button = self.wait.until(ec.element_to_be_clickable((By.ID, "filter-radius")))
            distance_filter_button.click()
            time.sleep(3)
            distance_filter = self.wait.until(
                ec.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Within 100 miles')]")))
            distance_filter.click()
            time.sleep(3)

    def scrape_job_pages(self):
        while True:
            time.sleep(random.uniform(3, 6))
            self.scrape_job_cards(self.driver.find_elements(By.CSS_SELECTOR, "a[data-jk]"))
            next_page = self.get_next_page()
            if next_page is None:
                break
            time.sleep(random.uniform(7, 12))
            next_page.click()

    def scrape_job_cards(self, list_of_elements):
        for element in list_of_elements:
            listing_id = element.get_attribute("data-jk")
            link = "https://www.indeed.com/viewjob?jk=" + listing_id
            title = element.find_element(By.ID, f"jobTitle-{listing_id}").get_attribute("title")
            element = self.driver.find_element(By.XPATH, f".//div[contains(@class, 'job_{listing_id}')]")
            company = element.find_element(By.CSS_SELECTOR, "span[data-testid='company-name']").text
            location = element.find_element(By.CSS_SELECTOR, "div[data-testid='text-location']").text
            compensation = None
            # Compensation isn't always shown & the message that it's not there is under a different & dynamic class:
            try:
                compensation = element.find_element(
                    By.XPATH, ".//div[contains(@class, 'salary-snippet-container')]").text
            except NoSuchElementException:
                pass
            self.scraped_job_listings[listing_id] = {
                'link': link,
                'source': self.source,
                'title': title,
                'company': company,
                'time_when_scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'location': location,
                'compensation': compensation
            }

    def get_next_page(self):
        for _ in range(20):
            try:
                time.sleep(.5)
                element = self.driver.find_element(By.XPATH, "//a[@aria-label='Next Page']")
                # Check if element's top & bottom are within the viewport:
                is_visible = self.driver.execute_script(
                    "var rect = arguments[0].getBoundingClientRect();"
                    "return (rect.top >= 0 && rect.bottom <= window.innerHeight);",
                    element
                )
                if is_visible:
                    return element
                self.driver.execute_script("window.scrollBy(0, 500);")
            except (NoSuchElementException, StaleElementReferenceException):
                self.driver.execute_script("window.scrollBy(0, 500);")
                continue
        return None


if __name__ == "__main__":
    # This runs the scraper as a script rather than a module on Windows. It allows watching the scraper in action
    # for debugging or demo purposes. Otherwise, this isn't possible as our Airflow & WSL combo is command line only.
    scraper = IndeedScraper(headless=False)
    scraper.run()
