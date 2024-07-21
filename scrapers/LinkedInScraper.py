import time
import random
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from scrapers.Scraper import Scraper
import traceback
import os


class LinkedInScraper(Scraper):
    def __init__(self, **kwargs):
        super().__init__('LinkedIn', 'https://www.linkedin.com/login', **kwargs)
        self.logger.info(f"Success: {self.__class__.__name__} initialized")

    def run(self):
        try:
            self.sign_in()
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

    def is_scroll_at_bottom(self, scrollable_element):
        return self.driver.execute_script("return arguments[0].scrollTop == (arguments[0].scrollHeight - "
                                          "arguments[0].offsetHeight);", scrollable_element)

    def scroll_to_end(self, scrollable_element):
        while not self.is_scroll_at_bottom(scrollable_element):
            self.driver.execute_script("arguments[0].scrollBy(0, arguments[0].offsetHeight);", scrollable_element)
            time.sleep(random.uniform(1, 2))

    def scrape_job_cards(self, list_of_elements):
        for element in list_of_elements:
            try:
                listing_id = element.get_attribute("data-job-id")
                link = "https://www.linkedin.com/jobs/view/" + listing_id
                aria_label = element.find_element(By.CSS_SELECTOR,
                                                  'a.job-card-container__link[aria-label][tabindex="0"]')
                title = aria_label.get_attribute("aria-label")
                company = element.find_element(
                    By.XPATH, ".//span[contains(@class, 'job-card-container__primary-description')]").text
                location = element.find_element(
                    By.XPATH, ".//div[contains(@class, 'artdeco-entity-lockup__caption')]").text
                compensation = element.find_element(
                    By.XPATH, ".//div[contains(@class, 'artdeco-entity-lockup__metadata')]").text
                self.scraped_job_listings[listing_id] = {
                    'link': link,
                    'source': self.source,
                    'title': title,
                    'company': company,
                    'time_when_scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'location': location,
                    'compensation': compensation
                }
            except NoSuchElementException:
                continue

    def get_next_page(self):
        # When there is only 1 page of results, LinkedIn does not display a number at the bottom of the page
        try:
            current_page_button = self.driver.find_element(By.XPATH, "//button[@aria-current='true']")
        except NoSuchElementException:
            return None
        current_page_label = current_page_button.get_attribute("aria-label")
        # Though LinkedIn can show "..." instead of a page number, the aria-label will always have the Page # due to ADA
        next_page_number = int(current_page_label.split()[1]) + 1
        try:
            next_page_button = self.driver.find_element(By.XPATH, f"//button[@aria-label='Page {next_page_number}']")
            return next_page_button
        except NoSuchElementException:
            return None

    def scrape_job_pages(self, location):
        self.apply_job_filters(location)
        time.sleep(random.uniform(3, 6))
        while True:
            self.scroll_to_end(self.driver.find_element(By.CLASS_NAME, "jobs-search-results-list"))
            self.scrape_job_cards(self.driver.find_elements(By.CSS_SELECTOR, "[data-job-id]"))
            time.sleep(random.uniform(3, 6))
            if self.get_next_page() is None:
                break
            self.get_next_page().click()
            # Increased the low-end of the range to counter occasional rate-limiting (message: "things aren't loading"?)
            time.sleep(random.uniform(7, 12))

    def apply_job_filters(self, location):
        # aria-label="Show all filters. Clicking this button displays all available filter options."
        all_filters_button = self.wait.until(ec.element_to_be_clickable((
            By.CSS_SELECTOR, "button.search-reusables__all-filters-pill-button")))
        all_filters_button.click()
        time.sleep(2)
        # reset filters between runs to exclude behavior such as getting hybrid/on-site along with remote roles:
        reset_applied_filters = self.wait.until(ec.element_to_be_clickable((
            By.XPATH, "//button[contains(@class, 'artdeco-button') and contains(., 'Reset')]")))
        reset_applied_filters.click()
        # Job cards don't show how long ago something was posted on the card, unless sorted by most recent:
        most_recent_filter = self.wait.until(ec.element_to_be_clickable((By.XPATH, "//span[text()='Most recent']")))
        most_recent_filter.click()
        time.sleep(2)
        previous_day_filter = self.wait.until(ec.element_to_be_clickable((By.XPATH, "//span[text()='Past 24 hours']")))
        previous_day_filter.click()
        time.sleep(2)
        # Putting remote in the search box is not enough for remote jobs,
        # on-site/hybrid roles still show up without this:
        if location == 'Remote':
            first_element_found = False
            scroll_increment = 500
            for _ in range(10):
                try:
                    if not first_element_found:
                        time.sleep(.5)
                        target = self.driver.find_element(By.XPATH, "//span[text()='Remote']")
                        target.click()
                        first_element_found = True
                    if first_element_found:
                        break
                except (NoSuchElementException, StaleElementReferenceException):
                    self.driver.execute_script(f"arguments[0].scrollBy(0, {scroll_increment});",
                                               self.driver.find_element(By.CLASS_NAME, "artdeco-modal__content"))
        # Similarly, if you are looking for local hybrid, remote will show up unless you checkmark on-site/hybrid:
        else:
            scroll_increment = 500
            first_element_found = False
            second_element_found = False
            for _ in range(10):
                try:
                    time.sleep(.5)
                    if not first_element_found:
                        target = self.driver.find_element(By.XPATH, "//span[text()='On-site']")
                        target.click()
                        first_element_found = True
                    if not second_element_found:
                        target = self.driver.find_element(By.XPATH, "//span[text()='Hybrid']")
                        target.click()
                        second_element_found = True
                    if first_element_found and second_element_found:
                        break
                except (NoSuchElementException, StaleElementReferenceException):
                    self.driver.execute_script(f"arguments[0].scrollBy(0, {scroll_increment});",
                                               self.driver.find_element(By.CLASS_NAME, "artdeco-modal__content"))
        time.sleep(5)  # Give time to process search results to let the button grab be reliable
        show_results = self.wait.until(
            ec.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.search-reusables__secondary-filters-show-results-button")))
        show_results.click()
        time.sleep(5)

    def sign_in(self):
        config = self.read_config_file()
        username = config['linkedin_credentials']['username']
        password = config['linkedin_credentials']['password']
        username_box = self.wait.until(ec.element_to_be_clickable((By.ID, "username")))
        username_box.send_keys(username)
        username_box = self.wait.until(ec.element_to_be_clickable((By.ID, "password")))
        username_box.send_keys(password)
        sign_in_button = self.wait.until(ec.element_to_be_clickable((By.XPATH, "//button[@aria-label='Sign in']")))
        sign_in_button.click()
        try:
            # Wait to check that we are on the homepage:
            self.wait.until(ec.title_contains("Feed | LinkedIn"))
        except TimeoutException:
            current_page_title = self.driver.title
            # When LinkedIn bot detection catches us due to login attempts the title contains Security Verification:
            if "Security Verification" in current_page_title:
                self.logger.critical("Caught by LinkedIn's bot detection during sign in")
                self.security_verification()
            # If we are not caught due to bot detection, then we have a different sort of problem:
            else:
                self.logger.critical("Failed to sign in within the allotted amount of time")
                raise

    def minimize_message_window(self):
        # Minimize messaging for better view when testing:
        minimize_chevron = self.wait.until(ec.element_to_be_clickable(
            (By.XPATH,
             "//div[contains(@class, 'msg-overlay-bubble-header__controls')]//use[@href='#chevron-down-small']"))
        )
        minimize_chevron.click()

    def navigate_to_jobs(self):
        jobs_page = self.wait.until(ec.element_to_be_clickable(
            (By.XPATH, "//a[contains(@class, 'app-aware-link') and @href='https://www.linkedin.com/jobs/?']"))
        )
        jobs_page.click()
        self.wait.until(ec.title_contains("Jobs | LinkedIn"))

    def input_search_keywords(self, keyword, location):
        keyword_box = self.wait.until(
            ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'jobs-search-box-keyword')]")))
        keyword_box.click()
        keyword_box.send_keys(Keys.CONTROL + "a")
        keyword_box.send_keys(Keys.BACKSPACE)
        keyword_box.send_keys(keyword)
        time.sleep(random.uniform(1, 2))
        location_box = self.wait.until(
            ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'jobs-search-box-location')]")))
        location_box.click()
        location_box.send_keys(Keys.CONTROL + "a")
        location_box.send_keys(Keys.BACKSPACE)
        location_box.send_keys(location)
        time.sleep(random.uniform(1, 2))
        location_box.send_keys(Keys.ENTER)
        time.sleep(random.uniform(1, 2))

    def scrape_search_terms(self):
        search_terms = self.read_json_file()
        for term in search_terms['LinkedIn_Search_Terms']:
            self.scraped_job_listings = {}
            keyword = term['keyword']
            location = term['location']
            self.navigate_to_jobs()
            self.logger.info(f"Start: Searching for {keyword} in {location}")
            self.input_search_keywords(keyword, location)
            self.scrape_job_pages(location)
            csv_filepath = self.generate_filepath()
            self.write_to_csv(self.scraped_job_listings, csv_filepath)


if __name__ == "__main__":
    # This runs the scraper as a script rather than a module on Windows. It allows watching the scraper in action
    # for debugging or demo purposes. Otherwise, this isn't possible as our Airflow & WSL combo is command line only.
    scraper = LinkedInScraper(headless=False)
    scraper.run()
