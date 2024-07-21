import time
import random
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from scrapers.Scraper import Scraper
import traceback
import os


class BuiltInScraper(Scraper):
    def __init__(self, **kwargs):
        super().__init__('BuiltIn', 'https://builtin.com/', **kwargs)
        self.logger.info(f"Success: {self.__class__.__name__} initialized")

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
        total_terms = len(search_terms['BuiltIn_Search_Terms'])
        for index, term in enumerate(search_terms['BuiltIn_Search_Terms']):
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
                self.driver.get("https://builtin.com")
                time.sleep(10)  # Allow some time to load the main page again

    def input_search_keywords(self, keyword, location):
        keyword_box = self.wait.until(
            ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'searchJobsInput')]")))
        keyword_box.send_keys(keyword)
        location_box = self.wait.until(
            ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'locationDropdownInput')]")))
        location_box.click()
        location_box.send_keys(Keys.CONTROL + "a")
        location_box.send_keys(Keys.BACKSPACE)
        # BuiltIn has a separate box for specifying remote/hybrid/in office. In addition to this, the location box can't
        # take Remote as a location. For this site, we apply the remote filter later and use USA for a broad search.
        if location == 'Remote':
            location_box.send_keys("United States")
        else:
            location_box.send_keys(location)
        time.sleep(3)
        # Once the location is put in, you need to send down arrow & enter key to lock it in. Otherwise, switching
        # context wipes out the entry and a default location is used (for example, United States).
        location_box.send_keys(Keys.DOWN)
        location_box.send_keys(Keys.ENTER)
        search_button = self.wait.until(ec.element_to_be_clickable((
            By.XPATH, "//button[.//span[contains(text(), 'See Job Matches') or contains(text(), 'See Jobs')]]")))
        time.sleep(3)
        search_button.click()

    def apply_job_filters(self, location):
        time.sleep(3)
        date_posted_button = self.wait.until(ec.element_to_be_clickable((By.ID, "postedDateDropdownButton")))
        date_posted_button.click()  # Open menu
        time.sleep(3)
        time_filter = self.wait.until(
            ec.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Past 24 hours')]")))
        time_filter.click()
        date_posted_button.click()  # Close menu
        # There's an apply button, however it is pointless to use currently as filters apply instantly without it.
        time.sleep(3)
        # id="remotePreference-2" is for the option Remote.
        # id="remotePreference-3" is for the option Hybrid.
        # id="remotePreference-1" is for the option In Office.
        # All 3 options are selected by default when you get to the site. So for example, if you want to select remote
        # as your only option you have to deselect hybrid & in office.
        if location == 'Remote':
            remote_filter_button = self.wait.until(
                ec.element_to_be_clickable((By.ID, "remotePreferenceDropdownButton")))
            remote_filter_button.click()  # Open menu
            time.sleep(3)
            hybrid_filter = self.wait.until(ec.element_to_be_clickable((By.ID, "remotePreference-3")))
            hybrid_filter.click()
            time.sleep(1)
            onsite_filter = self.wait.until(ec.element_to_be_clickable((By.ID, "remotePreference-1")))
            onsite_filter.click()
            time.sleep(1)
            remote_filter_button.click()  # Close menu
            time.sleep(3)
        else:
            remote_filter_button = self.wait.until(
                ec.element_to_be_clickable((By.ID, "remotePreferenceDropdownButton")))
            remote_filter_button.click()  # Open menu
            time.sleep(3)
            remote_filter = self.wait.until(ec.element_to_be_clickable((By.ID, "remotePreference-2")))
            remote_filter.click()
            time.sleep(1)
            remote_filter_button.click()  # Close menu
            distance_filter_button = self.wait.until(ec.element_to_be_clickable((By.ID, "searchAreaDropdownButton")))
            distance_filter_button.click()  # Open menu
            time.sleep(3)
            distance_filter = self.wait.until(ec.element_to_be_clickable((By.ID, "searchArea-100")))
            distance_filter.click()
            time.sleep(1)
            distance_filter_button.click()  # Close menu
            time.sleep(3)

    def scrape_job_pages(self):
        while True:
            time.sleep(random.uniform(3, 6))
            self.scrape_job_cards(self.driver.find_elements(By.CSS_SELECTOR, "div[data-id='job-card']"))
            next_page = self.get_next_page()
            if next_page is None:
                break
            next_page.click()

    def scrape_job_cards(self, list_of_elements):
        for element in list_of_elements:
            company_title_element = element.find_element(By.CSS_SELECTOR, "div[data-id='company-title']")
            listing_id = company_title_element.get_attribute("data-builtin-track-job-id")
            # The title element contains the title, but also has a href for the link:
            title_element = element.find_element(By.CSS_SELECTOR, "h2 > a")
            link = title_element.get_attribute('href')
            title = title_element.text
            company = company_title_element.text
            # Unfortunately, the site has a lot of nested divs without any unique identifiers. This makes grabbing some
            # data a brittle process requiring a very specific path. It's likely to break with minor site updates.
            location = element.find_element(
                By.CSS_SELECTOR, "div.bounded-attribute-section > div > div > div:nth-child(2)"
            ).text
            compensation = None
            try:
                compensation = element.find_element(
                    By.CSS_SELECTOR, "div.bounded-attribute-section > div > div:nth-child(2) > div:nth-child(2)").text
                # Due to brittle pathing and compensation not being always present, we need to be sure that
                # what we just scraped is actually the compensation. From sampling some listings it seems
                # the most reliable way is to check if it contains the word 'annually' as there are no hourly rates.
                if 'Annually' not in compensation:
                    compensation = None
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
                element = self.driver.find_element(By.XPATH, "//a[@aria-label='Go to Next Page']")
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
    scraper = BuiltInScraper(headless=False)
    scraper.run()
