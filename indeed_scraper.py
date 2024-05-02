import csv
import os
import time
import random
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains


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


def read_json_file():
    with open('search_terms.json', 'r') as json_file:
        return json.load(json_file)


def scrape_search_terms():
    search_terms = read_json_file()
    for term in search_terms['Indeed_Search_Terms']:
        global scraped_job_listings
        scraped_job_listings = {}
        keyword = term['keyword']
        location = term['location']
        input_search_keywords(keyword, location)
        try:
            apply_job_filters(location)
            scrape_job_pages()
            csv_filepath = generate_filepath()
            write_to_csv(scraped_job_listings, csv_filepath)
        except TimeoutException:
            print("Unable to apply filters. This can be caused by no search results, in addition to a missing element.")
            continue


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


def write_to_csv(job_listings, filepath):
    with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['listing_id', 'source', 'title', 'company', 'link', 'time_when_scraped', 'time_since_post',
                      'location', 'compensation']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for listing_id, listing in job_listings.items():
            writer.writerow({
                'listing_id': listing_id,
                'source': listing['source'],
                'title': listing['title'],
                'company': listing['company'],
                'link': listing['link'],
                'time_when_scraped': listing['time_when_scraped'],
                'time_since_post': listing['time_since_post'],
                'location': listing['location'],
                'compensation': listing['compensation']
            })


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
        time_since_post = element.find_element(By.CSS_SELECTOR, "span[data-testid='myJobsStateDate']").text
        scraped_job_listings[listing_id] = {
            'link': link,
            'source': "Indeed",
            'title': title,
            'company': company,
            'time_when_scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'time_since_post': time_since_post,
            'location': location,
            'compensation': compensation
        }


def generate_filepath():
    output_dir = os.path.join(os.path.join(os.environ['USERPROFILE'], 'Desktop'), 'JobScraper')
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f'Indeed_{timestamp}.csv'
    filepath = os.path.join(output_dir, filename)
    return filepath


def input_search_keywords(keyword, location):
    # FIXME: why does this break in headless mode but not in non-headless?
    # FIXME: you can take screenshots in headless mode, would be a great insight
    # FIXME: seems to have the same issue running minimized, maybe needs actions to move to the element?
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


options = Options()
# options.add_argument('--headless')  # Disable headless mode if you are watching it run for troubleshooting/demo
driver = webdriver.Chrome(options=options)
driver.maximize_window()
driver.get('https://www.indeed.com')
wait = WebDriverWait(driver, 15)
actions = ActionChains(driver)
scraped_job_listings = {}
scrape_search_terms()
driver.quit()
