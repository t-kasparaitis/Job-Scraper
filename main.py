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
from selenium.webdriver.common.action_chains import ActionChains


# NOTE: explain what this does also in comments later
def is_scroll_at_bottom(scrollable_element):
    return driver.execute_script("return arguments[0].scrollTop == "
                                 "(arguments[0].scrollHeight - arguments[0].offsetHeight);", scrollable_element)


def scroll_to_end(scrollable_element):
    while not is_scroll_at_bottom(scrollable_element):
        # NOTE: explain what this does in comments later
        # scrollBy(width, height) -> scrolls by those amounts, here we set width to 0
        driver.execute_script("arguments[0].scrollBy(0, arguments[0].offsetHeight);", scrollable_element)
        time.sleep(random.uniform(1, 2))


def scrape_job_cards(list_of_elements):
    try:
        for element in list_of_elements:
            linked_in_id = element.get_attribute("data-job-id")
            link = "https://www.linkedin.com/jobs/view/" + linked_in_id
            # FIXME: something wrong here with the way title & company are being grabbed that causes a crash on first page
            aria_label = element.find_element(By.CSS_SELECTOR, 'a.job-card-container__link[aria-label][tabindex="0"]')
            title = aria_label.get_attribute("aria-label")
            # FIXME: maybe change the code below to get attribute after locating element?
            company = element.find_element(
                By.XPATH, ".//span[contains(@class, 'job-card-container__primary-description')]").text
            scraped_job_listings[linked_in_id] = {
                'link': link,
                'title': title,
                'company': company
            }
    except NoSuchElementException:
        pass


def get_next_page():
    current_page_button = driver.find_element(By.XPATH, "//button[@aria-current='true']")
    current_page_label = current_page_button.get_attribute("aria-label")
    # Though LinkedIn can show "..." instead of a page number, the aria-label will always have the Page # due to ADA
    next_page_number = int(current_page_label.split()[1]) + 1
    try:
        next_page_button = driver.find_element(By.XPATH, f"//button[@aria-label='Page {next_page_number}']")
        return next_page_button
    except NoSuchElementException:
        return None


def write_to_csv(job_listings):
    output_dir = os.path.join(os.path.join(os.environ['USERPROFILE'], 'Desktop'), 'JobScraper')
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename = f'LinkedIn_{timestamp}.csv'
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['linked_in_id', 'title', 'company', 'link']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for linked_in_id, listing in job_listings.items():
            writer.writerow({
                'linked_in_id': linked_in_id,
                'title': listing['title'],
                'company': listing['company'],
                'link': listing['link']
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
    button = WebDriverWait(driver, 10).until(ec.element_to_be_clickable((By.ID, "searchFilter_timePostedRange")))
    button.click()
    previous_day = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.XPATH, "//span[text()='Past 24 hours']")))
    previous_day.click()
    show_results = WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.CSS_SELECTOR, '[data-control-name="filter_show_results"]')))
    show_results.click()


config_file_path = os.path.join(os.path.join(os.environ['USERPROFILE'], 'Desktop'), 'config.ini')
config = configparser.ConfigParser()
config.read(config_file_path)
username = config['credentials']['username']
password = config['credentials']['password']

# NOTE: re-enable headless mode after this is fleshed out
# from selenium.webdriver.chrome.options import Options
#
# options = Options()
# options.add_argument('--headless')

# driver = webdriver.Chrome(options=options)

# Uses credentials from config file to sign in to LinkedIn
# TODO: Account for auto-sign in from Google etc., probably check for page title?
driver = webdriver.Chrome()
driver.maximize_window()
driver.get('https://www.linkedin.com')
wait = WebDriverWait(driver, 10)
actions = ActionChains(driver)
username_box = wait.until(ec.element_to_be_clickable((By.ID, "session_key")))
username_box.send_keys(username)
username_box = wait.until(ec.element_to_be_clickable((By.ID, "session_password")))
username_box.send_keys(password)
sign_in_button = wait.until(ec.element_to_be_clickable((By.XPATH, "//button[@data-id='sign-in-form__submit-btn']")))
sign_in_button.click()

# Wait to check that we are on the homepage:
wait.until(ec.title_contains("Feed | LinkedIn"))
# Minimize messaging for better view when testing:
# FIXME: fix whatever is causing the crash here:
# messaging_minimize_button = wait.until(EC.element_to_be_clickable(
#     (By.XPATH, "//div[contains(@class, 'msg-overlay-bubble-header__controls')]//use[@href='#chevron-down-small']"))
# )
# messaging_minimize_button.click()

# Go to jobs page
jobs_page = wait.until(ec.element_to_be_clickable(
    (By.XPATH, "//a[contains(@class, 'app-aware-link') and @href='https://www.linkedin.com/jobs/?']"))
)
jobs_page.click()
wait.until(ec.title_contains("Jobs | LinkedIn"))
keyword_box = wait.until(ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'jobs-search-box-keyword')]")))
search_one_keywords = config['searchOne']['keywords']
search_one_location = config['searchOne']['location']
keyword_box.send_keys(search_one_keywords)
time.sleep(random.uniform(1, 2))
location_box = wait.until(ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'jobs-search-box-location')]")))
location_box.send_keys(search_one_location)
time.sleep(random.uniform(1, 2))
keyword_box.send_keys(Keys.ENTER)
time.sleep(random.uniform(1, 2))

scraped_job_listings = {}
scrape_job_pages()
write_to_csv(scraped_job_listings)

# TODO: apply filter for remote for SearchOne; add DatePosted as a measure of system time - what they have on listing
# TODO: think about some search options since LI/Indeed search isn't great - for example developer I, SDE I etc.
# TODO: maybe think about an indefinite amount of searches, how to read the config.ini in that case & iterate
# TODO: idea - feed jobs found to ChatGPT to filter out things I don't want
# TODO: check for unique job identifiers (for example Indeed has repeats where jk=# is repeated among different pages)
# TODO: automate the run for every X hours using scheduler.py along with Windows Task Scheduler

input("Press any key in the run window to exit session")  # This pauses the script until the user does something
driver.quit()  # This closes the browser window and exits the WebDriver session
