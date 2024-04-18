import configparser
import csv
import os
import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys


def is_scroll_at_bottom(scrollable_element):
    return driver.execute_script("return arguments[0].scrollTop == "
                                 "(arguments[0].scrollHeight - arguments[0].offsetHeight);", scrollable_element)


def scroll_to_end(scrollable_element):
    while not is_scroll_at_bottom(scrollable_element):
        driver.execute_script("arguments[0].scrollBy(0, arguments[0].offsetHeight);", scrollable_element)
        time.sleep(random.uniform(1, 2))


def scrape_job_cards(list_of_elements):
    for element in list_of_elements:
        try:
            linked_in_id = element.get_attribute("data-job-id")
            link = "https://www.linkedin.com/jobs/view/" + linked_in_id
            # FIXME: getting some empty grabs that are currently caused by exception handler
            aria_label = element.find_element(By.CSS_SELECTOR, 'a.job-card-container__link[aria-label][tabindex="0"]')
            title = aria_label.get_attribute("aria-label")
            company = element.find_element(
                By.XPATH, ".//span[contains(@class, 'job-card-container__primary-description')]").text
            scraped_job_listings[linked_in_id] = {
                'link': link,
                'title': title,
                'company': company,
                'time_when_scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'time_since_post': element.find_element(By.CSS_SELECTOR, 'time').text
            }
        except NoSuchElementException:
            continue


def get_next_page():
    # When there is only 1 page of results, LinkedIn does not display a number at the bottom of the page
    try:
        current_page_button = driver.find_element(By.XPATH, "//button[@aria-current='true']")
    except NoSuchElementException:
        return None
    current_page_label = current_page_button.get_attribute("aria-label")
    # Though LinkedIn can show "..." instead of a page number, the aria-label will always have the Page # due to ADA
    next_page_number = int(current_page_label.split()[1]) + 1
    try:
        next_page_button = driver.find_element(By.XPATH, f"//button[@aria-label='Page {next_page_number}']")
        return next_page_button
    except NoSuchElementException:
        return None


def write_to_csv(job_listings, filepath):
    with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['linked_in_id', 'title', 'company', 'link', 'time_when_scraped', 'time_since_post']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for linked_in_id, listing in job_listings.items():
            writer.writerow({
                'linked_in_id': linked_in_id,
                'title': listing['title'],
                'company': listing['company'],
                'link': listing['link'],
                'time_when_scraped': listing['time_when_scraped'],
                'time_since_post': listing['time_since_post']
            })


def scrape_job_pages():
    reset_job_filters()
    apply_job_filters()
    while True:
        time.sleep(random.uniform(3, 6))
        scroll_to_end(driver.find_element(By.CLASS_NAME, "jobs-search-results-list"))
        scrape_job_cards(driver.find_elements(By.CSS_SELECTOR, "[data-job-id]"))
        time.sleep(random.uniform(3, 6))
        if get_next_page() is None:
            break
        get_next_page().click()
        time.sleep(random.uniform(5, 10))
        scroll_to_end(driver.find_element(By.CLASS_NAME, "jobs-search-results-list"))
        scrape_job_cards(driver.find_elements(By.CSS_SELECTOR, "[data-job-id]"))
    

def reset_job_filters():
    # Clear out any filters if there are any from previous uses or being signed in to LinkedIn etc.:
    try:
        reset_applied_filters = WebDriverWait(driver, 5).until(ec.element_to_be_clickable(
            (By.XPATH, "//button[@aria-label='Reset applied filters' and span[text()='Reset']]"))
        )
        reset_applied_filters.click()
    except NoSuchElementException:
        pass
    except TimeoutException:
        pass


def apply_job_filters():
    # aria-label="Show all filters. Clicking this button displays all available filter options."
    all_filters_button = wait.until(ec.element_to_be_clickable((
        By.CSS_SELECTOR, "button.search-reusables__all-filters-pill-button")))
    all_filters_button.click()
    # Job cards don't show how long ago something was posted on the card, unless sorted by most recent:
    most_recent_filter = wait.until(ec.element_to_be_clickable((By.XPATH, "//span[text()='Most recent']")))
    most_recent_filter.click()
    previous_day_filter = wait.until(ec.element_to_be_clickable((By.XPATH, "//span[text()='Past 24 hours']")))
    previous_day_filter.click()
    time.sleep(5)  # Give time to process search results to let the button grab be reliable
    show_results = wait.until(
        ec.element_to_be_clickable((By.CSS_SELECTOR, "button.search-reusables__secondary-filters-show-results-button")))
    show_results.click()


def read_config_file():
    config_file_path = os.path.join(os.path.join(os.environ['USERPROFILE'], 'Desktop'), 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config


def generate_filepath():
    output_dir = os.path.join(os.path.join(os.environ['USERPROFILE'], 'Desktop'), 'JobScraper')
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f'LinkedIn_{timestamp}.csv'
    filepath = os.path.join(output_dir, filename)
    return filepath


def sign_in():
    # TODO: Account for auto-sign in from Google etc., probably check for page title?
    config = read_config_file()
    username = config['credentials']['username']
    password = config['credentials']['password']
    username_box = wait.until(ec.element_to_be_clickable((By.ID, "session_key")))
    username_box.send_keys(username)
    username_box = wait.until(ec.element_to_be_clickable((By.ID, "session_password")))
    username_box.send_keys(password)
    sign_in_button = wait.until(ec.element_to_be_clickable((By.XPATH, "//button[@data-id='sign-in-form__submit-btn']")))
    sign_in_button.click()
    try:
        WebDriverWait(driver, 10).until(ec.title_contains("Security Verification | LinkedIn"))
        security_verification()  # TODO: Just a wait time to get past verification, need logic for it later
    except NoSuchElementException:
        pass
    # Wait to check that we are on the homepage:
    wait.until(ec.title_contains("Feed | LinkedIn"))


def minimize_message_window():
    # Minimize messaging for better view when testing:
    # FIXME: fix whatever is causing the crash here, then reimplement
    minimize_chevron = wait.until(ec.element_to_be_clickable(
        (By.XPATH, "//div[contains(@class, 'msg-overlay-bubble-header__controls')]//use[@href='#chevron-down-small']"))
    )
    minimize_chevron.click()


def navigate_to_jobs():
    jobs_page = wait.until(ec.element_to_be_clickable(
        (By.XPATH, "//a[contains(@class, 'app-aware-link') and @href='https://www.linkedin.com/jobs/?']"))
    )
    jobs_page.click()
    wait.until(ec.title_contains("Jobs | LinkedIn"))


def input_search_keywords():
    config = read_config_file()
    keyword_box = wait.until(
        ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'jobs-search-box-keyword')]")))
    search_one_keywords = config['searchOne']['keywords']
    search_one_location = config['searchOne']['location']
    keyword_box.send_keys(search_one_keywords)
    time.sleep(random.uniform(1, 2))
    location_box = wait.until(
        ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'jobs-search-box-location')]")))
    location_box.send_keys(search_one_location)
    time.sleep(random.uniform(1, 2))
    keyword_box.send_keys(Keys.ENTER)
    time.sleep(random.uniform(1, 2))


def security_verification():
    # There's 6 bull images we have to pick the one where the head is completely upright
    # There's not an easy way to solve this without AI, maybe pixel analysis for which way head is pointing?
    time.sleep(45)
# NOTE: re-enable headless mode after this is fleshed out
# from selenium.webdriver.chrome.options import Options
#
# options = Options()
# options.add_argument('--headless')

# driver = webdriver.Chrome(options=options)


driver = webdriver.Chrome()
driver.maximize_window()
driver.get('https://www.linkedin.com')
wait = WebDriverWait(driver, 10)
sign_in()
navigate_to_jobs()
input_search_keywords()
scraped_job_listings = {}
scrape_job_pages()
csv_filepath = generate_filepath()
write_to_csv(scraped_job_listings, csv_filepath)
driver.quit()
