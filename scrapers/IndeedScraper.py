import time
import random
import traceback
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from Scraper import Scraper
from fake_useragent import UserAgent


class IndeedScraper(Scraper):
    def __init__(self, **kwargs):
        super().__init__('Indeed', 'https://www.indeed.com', **kwargs)
        self.logger.info(f"{self.__class__.__name__} initialized")

    @staticmethod
    def security_verification():
        time.sleep(90)  # Cloudflare keeps looping asking for a box to be checked, upping time for testing
        # Verifying you are human. This may take a few seconds.
        # <input type="checkbox">


def scrape_search_terms():
    search_terms = scraper.read_json_file()
    for term in search_terms['Indeed_Search_Terms']:
        scraper.scraped_job_listings = {}
        keyword = term['keyword']
        location = term['location']
        scraper.logger.info(f"Starting search for {keyword} in {location}")
        input_search_keywords(keyword, location)
        try:
            apply_job_filters(location)
            scrape_job_pages()
            csv_filepath = scraper.generate_filepath()
            scraper.write_to_csv(scraper.scraped_job_listings, csv_filepath)
        except TimeoutException:
            print("Unable to apply filters. This can be caused by no search results, in addition to a missing element.")
            continue


def input_search_keywords(keyword, location):
    time.sleep(5)  # Gets around a Stale Element Exception that otherwise occurs when interacting with search box etc.
    keyword_box = wait.until(
        ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'text-input-what')]")))
    # The timers after an element has been found are necessary as otherwise the search boxes are cleared out somehow:
    time.sleep(random.uniform(1, 2))
    keyword_box.click()
    keyword_box.send_keys(Keys.CONTROL + "a")
    keyword_box.send_keys(Keys.BACKSPACE)
    keyword_box.send_keys(keyword)
    time.sleep(random.uniform(1, 2))
    location_box = wait.until(
        ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'text-input-where')]")))
    time.sleep(random.uniform(1, 2))
    location_box.click()
    location_box.send_keys(Keys.CONTROL + "a")
    location_box.send_keys(Keys.BACKSPACE)
    location_box.send_keys(location)
    time.sleep(random.uniform(1, 2))
    search_button = wait.until(ec.element_to_be_clickable((
        By.XPATH, "//button[normalize-space()='Search']")))
    time.sleep(random.uniform(1, 2))
    search_button.click()
    time.sleep(random.uniform(1, 2))
    try:
        wait.until(ec.title_contains("Just a moment..."))
        scraper.security_verification()  # TODO: Just a wait time to get past verification, need logic for it later
    except TimeoutException:
        pass


def apply_job_filters(location):
    time.sleep(3)
    date_posted_button = wait.until(ec.element_to_be_clickable((By.ID, "filter-dateposted")))
    date_posted_button.click()
    time.sleep(3)
    time_filter = wait.until(ec.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Last 24 hours')]")))
    time_filter.click()
    time.sleep(3)
    if location == 'Remote':
        remote_filter_button = wait.until(ec.element_to_be_clickable((By.ID, "filter-remotejob")))
        remote_filter_button.click()
        time.sleep(3)
        remote_filter = wait.until(ec.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Remote')]")))
        remote_filter.click()
        time.sleep(3)
    else:
        distance_filter_button = wait.until(ec.element_to_be_clickable((By.ID, "filter-radius")))
        distance_filter_button.click()
        time.sleep(3)
        distance_filter = wait.until(
            ec.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Within 100 miles')]")))
        distance_filter.click()
        time.sleep(3)


def scrape_job_pages():
    while True:
        time.sleep(random.uniform(3, 6))
        scrape_job_cards(driver.find_elements(By.CSS_SELECTOR, "a[data-jk]"))
        next_page = get_next_page()
        if next_page is None:
            break
        next_page.click()


def scrape_job_cards(list_of_elements):
    for element in list_of_elements:
        listing_id = element.get_attribute("data-jk")
        link = "https://www.indeed.com/viewjob?jk=" + listing_id
        title = element.find_element(By.ID, f"jobTitle-{listing_id}").get_attribute("title")
        element = driver.find_element(By.XPATH, f".//div[contains(@class, 'job_{listing_id}')]")
        company = element.find_element(By.CSS_SELECTOR, "span[data-testid='company-name']").text
        location = element.find_element(By.CSS_SELECTOR, "div[data-testid='text-location']").text
        compensation = None
        # Compensation isn't always shown & the message that it's not there is under a different & dynamic class:
        try:
            compensation = element.find_element(
                By.XPATH, ".//div[contains(@class, 'salary-snippet-container')]").text
        except NoSuchElementException:
            pass
        scraper.scraped_job_listings[listing_id] = {
            'link': link,
            'source': scraper.source,
            'title': title,
            'company': company,
            'time_when_scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'location': location,
            'compensation': compensation
        }


def get_next_page():
    for _ in range(20):
        try:
            time.sleep(.5)
            element = driver.find_element(By.XPATH, "//a[@aria-label='Next Page']")
            # Check if element's top & bottom are within the viewport:
            is_visible = driver.execute_script(
                "var rect = arguments[0].getBoundingClientRect();"
                "return (rect.top >= 0 && rect.bottom <= window.innerHeight);",
                element
            )
            if is_visible:
                return element
            driver.execute_script("window.scrollBy(0, 500);")
        except (NoSuchElementException, StaleElementReferenceException):
            driver.execute_script("window.scrollBy(0, 500);")
            continue
    return None


if __name__ == "__main__":
    ua = UserAgent(os='windows', browsers='chrome', platforms='pc')
    scraper = IndeedScraper(headless=False, user_agent=ua.random)
    wait = scraper.wait  # TODO: start from here; this is how you can initialize things
    driver = scraper.driver
    try:
        scrape_search_terms()
    except Exception as e:
        traceback_details = traceback.format_exc()
        scraper.logger.error(f"An error occurred: {e}\nDetails: {traceback_details}")
    finally:
        scraper.close()
