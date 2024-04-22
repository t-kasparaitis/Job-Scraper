import configparser
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
        # navigate_to_jobs()  # not sure that navigating to a job page will be needed on indeed
        input_search_keywords(keyword, location)
        scrape_job_pages(location)  # TODO update from here
        csv_filepath = generate_filepath()
        write_to_csv(scraped_job_listings, csv_filepath)


def write_to_csv(job_listings, filepath):
    with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['listing_id', 'source', 'title', 'company', 'link', 'time_when_scraped', 'time_since_post']
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
                'time_since_post': listing['time_since_post']
            })


def scrape_job_pages(location):
    # Indeed resets job search filters automatically between search terms
    # apply_job_filters(location)
    while True:
        time.sleep(random.uniform(3, 6))
        # scroll_to_end(driver.find_element(By.CLASS_NAME, "jobs-search-results-list"))
        # TODO: div data-testid = slider_item
        scrape_job_cards(driver.find_elements(By.CSS_SELECTOR, "[data-job-id]"))
        time.sleep(random.uniform(3, 6))
        # if get_next_page() is None:
        #     break
        # get_next_page().click()
        time.sleep(random.uniform(7, 12))  # Introduced higher floor for "things aren't loading" (rate-limiting?)
        # scroll_to_end(driver.find_element(By.CLASS_NAME, "jobs-search-results-list"))
        # scrape_job_cards(driver.find_elements(By.CSS_SELECTOR, "[data-job-id]"))


def scrape_job_cards(list_of_elements):
    for element in list_of_elements:
        try:
            listing_id = element.get_attribute("data-job-id")
            link = "https://www.linkedin.com/jobs/view/" + listing_id
            # FIXME: getting some empty grabs that are currently caused by exception handler
            aria_label = element.find_element(By.CSS_SELECTOR, 'a.job-card-container__link[aria-label][tabindex="0"]')
            title = aria_label.get_attribute("aria-label")
            company = element.find_element(
                By.XPATH, ".//span[contains(@class, 'job-card-container__primary-description')]").text
            scraped_job_listings[listing_id] = {
                'link': link,
                'title': title,
                'company': company,
                'time_when_scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'time_since_post': element.find_element(By.CSS_SELECTOR, 'time').text
            }
        except NoSuchElementException:
            continue


def generate_filepath():
    output_dir = os.path.join(os.path.join(os.environ['USERPROFILE'], 'Desktop'), 'JobScraper')
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f'LinkedIn_{timestamp}.csv'
    filepath = os.path.join(output_dir, filename)
    return filepath


def input_search_keywords(keyword, location):
    keyword_box = wait.until(
        ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'text-input-what')]")))
    keyword_box.send_keys(keyword)
    time.sleep(random.uniform(1, 2))
    location_box = wait.until(
        ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'text-input-where')]")))
    location_box.send_keys(location)
    time.sleep(random.uniform(1, 2))
    keyword_box.send_keys(Keys.ENTER)
    time.sleep(random.uniform(1, 2))
    search_button = wait.until(ec.element_to_be_clickable((By.XPATH, "//button[contains(@text, 'Search')]")))
    search_button.click()
    time.sleep(random.uniform(1, 2))


options = Options()
# options.add_argument('--headless')  # Disable headless mode if you are watching it run for troubleshooting/demo
driver = webdriver.Chrome(options=options)
driver.maximize_window()
driver.get('https://www.indeed.com')
wait = WebDriverWait(driver, 10)
scraped_job_listings = {}
scrape_search_terms()
