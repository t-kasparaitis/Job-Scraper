import time
import random
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from Scraper import Scraper


class BuiltInScraper(Scraper):
    def __init__(self, **kwargs):
        super().__init__('BuiltIn', 'https://builtin.com/', **kwargs)
        self.logger.info(f"{self.__class__.__name__} initialized")


# def get_next_page():
#     for _ in range(20):
#         try:
#             time.sleep(.5)
#             element = driver.find_element(By.XPATH, "//a[@aria-label='Next Page']")
#             # Check if element's top & bottom are within the viewport:
#             is_visible = driver.execute_script(
#                 "var rect = arguments[0].getBoundingClientRect();"
#                 "return (rect.top >= 0 && rect.bottom <= window.innerHeight);",
#                 element
#             )
#             if is_visible:
#                 return element
#             driver.execute_script("window.scrollBy(0, 500);")
#         except (NoSuchElementException, StaleElementReferenceException):
#             driver.execute_script("window.scrollBy(0, 500);")
#             continue
#     return None


def scrape_search_terms():
    search_terms = scraper.read_json_file()
    for term in search_terms['BuiltIn_Search_Terms']:
        scraper.scraped_job_listings = {}
        keyword = term['keyword']
        location = term['location']
        input_search_keywords(keyword, location)
        try:
            apply_job_filters(location)
            scrape_job_pages()
            csv_filepath = scraper.generate_filepath()
            scraper.write_to_csv(scraper.scraped_job_listings, csv_filepath)
        except TimeoutException:
            print("Unable to apply filters. This can be caused by no search results, in addition to a missing element.")
            continue


def apply_job_filters(location):
    time.sleep(3)
    date_posted_button = wait.until(ec.element_to_be_clickable((By.ID, "postedDateDropdownButton")))
    date_posted_button.click()  # Open menu
    time.sleep(3)
    time_filter = wait.until(ec.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Past 24 hours')]")))
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
        remote_filter_button = wait.until(ec.element_to_be_clickable((By.ID, "remotePreferenceDropdownButton")))
        remote_filter_button.click()  # Open menu
        time.sleep(3)
        hybrid_filter = wait.until(ec.element_to_be_clickable((By.ID, "remotePreference-3")))
        hybrid_filter.click()
        onsite_filter = wait.until(ec.element_to_be_clickable((By.ID, "remotePreference-1")))
        onsite_filter.click()
        remote_filter_button.click()  # Close menu
        time.sleep(3)
    else:
        remote_filter_button = wait.until(ec.element_to_be_clickable((By.ID, "remotePreferenceDropdownButton")))
        remote_filter_button.click()  # Open menu
        time.sleep(3)
        remote_filter = wait.until(ec.element_to_be_clickable((By.ID, "remotePreference-2")))
        remote_filter.click()
        remote_filter_button.click()  # Close menu
        distance_filter_button = wait.until(ec.element_to_be_clickable((By.ID, "searchAreaDropdownButton")))
        distance_filter_button.click()  # Open menu
        time.sleep(3)
        distance_filter = wait.until(ec.element_to_be_clickable((By.ID, "searchArea-100")))
        distance_filter.click()
        distance_filter_button.click()  # Close menu
        time.sleep(3)


def scrape_job_pages():
    while True:
        time.sleep(random.uniform(3, 6))
        scrape_job_cards(driver.find_elements(By.CSS_SELECTOR, "a[data-jk]"))
        next_page = get_next_page()
        if next_page is None:
            break
        next_page.click()


# def scrape_job_cards(list_of_elements):
#     for element in list_of_elements:
#         listing_id = element.get_attribute("data-jk")
#         link = "https://www.indeed.com/viewjob?jk=" + listing_id
#         title = element.find_element(By.ID, f"jobTitle-{listing_id}").get_attribute("title")
#         element = driver.find_element(By.XPATH, f".//div[contains(@class, 'job_{listing_id}')]")
#         company = element.find_element(By.CSS_SELECTOR, "span[data-testid='company-name']").text
#         location = element.find_element(By.CSS_SELECTOR, "div[data-testid='text-location']").text
#         compensation = None
#         # Compensation isn't always shown & the message that it's not there is under a different & dynamic class:
#         try:
#             compensation = element.find_element(
#                 By.XPATH, ".//div[contains(@class, 'salary-snippet-container')]").text
#         except NoSuchElementException:
#             pass
#         time_since_post = element.find_element(By.CSS_SELECTOR, "span[data-testid='myJobsStateDate']").text
#         scraper.scraped_job_listings[listing_id] = {
#             'link': link,
#             'source': scraper.source,
#             'title': title,
#             'company': company,
#             'time_when_scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#             'time_since_post': time_since_post,
#             'location': location,
#             'compensation': compensation
#         }


def input_search_keywords(keyword, location):
    keyword_box = wait.until(
        ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'searchJobsInput')]")))
    # # The timers after an element has been found are necessary as otherwise the search boxes are cleared out somehow:
    # time.sleep(random.uniform(1, 2))
    # keyword_box.click()
    # keyword_box.send_keys(Keys.CONTROL + "a")
    # keyword_box.send_keys(Keys.BACKSPACE)
    keyword_box.send_keys(keyword)
    # time.sleep(random.uniform(1, 2))
    location_box = wait.until(
        ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'locationDropdownInput')]")))
    # time.sleep(random.uniform(1, 2))
    location_box.click()
    location_box.send_keys(Keys.CONTROL + "a")
    location_box.send_keys(Keys.BACKSPACE)
    # BuiltIn has a separate box for specifying remote/hybrid/in office. In addition to this, the location box can't
    # take Remote as a location. For this site, we apply the remote filter later and use USA for a broad search.
    if location == 'Remote':
        location_box.send_keys("United States")
    else:
        location_box.send_keys(location)
    # time.sleep(random.uniform(1, 2))
    search_button = wait.until(ec.element_to_be_clickable((
        By.XPATH, "//button[normalize-space()='See Jobs']")))
    # time.sleep(random.uniform(1, 2))
    search_button.click()
    # time.sleep(random.uniform(1, 2))


if __name__ == "__main__":
    scraper = BuiltInScraper(headless=False)
    wait = scraper.wait
    driver = scraper.driver
    try:
        scrape_search_terms()
    except Exception as e:
        scraper.logger.error(f"An error occurred: {e}")
    finally:
        scraper.close()
