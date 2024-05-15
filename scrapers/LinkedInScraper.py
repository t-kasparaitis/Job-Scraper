import time
import random
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from Scraper import Scraper


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
            listing_id = element.get_attribute("data-job-id")
            link = "https://www.linkedin.com/jobs/view/" + listing_id
            # FIXME: getting some empty grabs that are currently caused by exception handler
            aria_label = element.find_element(By.CSS_SELECTOR, 'a.job-card-container__link[aria-label][tabindex="0"]')
            title = aria_label.get_attribute("aria-label")
            company = element.find_element(
                By.XPATH, ".//span[contains(@class, 'job-card-container__primary-description')]").text
            location = element.find_element(
                By.XPATH, ".//div[contains(@class, 'artdeco-entity-lockup__caption')]").text
            compensation = element.find_element(
                By.XPATH, ".//div[contains(@class, 'artdeco-entity-lockup__metadata')]").text
            scraper.scraped_job_listings[listing_id] = {
                'link': link,
                'source': "LinkedIn",
                'title': title,
                'company': company,
                'time_when_scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'time_since_post': element.find_element(By.CSS_SELECTOR, 'time').text,
                'location': location,
                'compensation': compensation
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


def scrape_job_pages(location):
    reset_job_filters()
    apply_job_filters(location)
    time.sleep(random.uniform(3, 6))
    while True:
        scroll_to_end(driver.find_element(By.CLASS_NAME, "jobs-search-results-list"))
        scrape_job_cards(driver.find_elements(By.CSS_SELECTOR, "[data-job-id]"))
        time.sleep(random.uniform(3, 6))
        if get_next_page() is None:
            break
        get_next_page().click()
        time.sleep(random.uniform(7, 12))  # Introduced higher floor for "things aren't loading" (rate-limiting?)


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


def apply_job_filters(location):
    # aria-label="Show all filters. Clicking this button displays all available filter options."
    all_filters_button = wait.until(ec.element_to_be_clickable((
        By.CSS_SELECTOR, "button.search-reusables__all-filters-pill-button")))
    all_filters_button.click()
    time.sleep(2)
    # Job cards don't show how long ago something was posted on the card, unless sorted by most recent:
    most_recent_filter = wait.until(ec.element_to_be_clickable((By.XPATH, "//span[text()='Most recent']")))
    most_recent_filter.click()
    time.sleep(2)
    previous_day_filter = wait.until(ec.element_to_be_clickable((By.XPATH, "//span[text()='Past 24 hours']")))
    previous_day_filter.click()
    time.sleep(2)
    # Putting remote in the search box is not enough for remote jobs, on-site/hybrid roles still show up without this:
    if location == 'Remote':
        first_element_found = False
        scroll_increment = 500
        for _ in range(10):
            try:
                if not first_element_found:
                    time.sleep(.5)
                    target = driver.find_element(By.XPATH, "//span[text()='Remote']")
                    target.click()
                    first_element_found = True
                if first_element_found:
                    break
            except (NoSuchElementException, StaleElementReferenceException):
                driver.execute_script(f"arguments[0].scrollBy(0, {scroll_increment});",
                                      driver.find_element(By.CLASS_NAME, "artdeco-modal__content"))
    # Similarly, if you are looking for local hybrid, remote will show up unless you checkmark on-site/hybrid:
    # TODO: make a function that takes a list of elements as a parameter, where it checks each one is found
    # TODO: add distance slider using action chains
    else:
        scroll_increment = 500
        first_element_found = False
        second_element_found = False
        for _ in range(10):
            try:
                time.sleep(.5)
                if not first_element_found:
                    target = driver.find_element(By.XPATH, "//span[text()='On-site']")
                    target.click()
                    first_element_found = True
                if not second_element_found:
                    target = driver.find_element(By.XPATH, "//span[text()='Hybrid']")
                    target.click()
                    second_element_found = True
                if first_element_found and second_element_found:
                    break
            except (NoSuchElementException, StaleElementReferenceException):
                driver.execute_script(f"arguments[0].scrollBy(0, {scroll_increment});",
                                      driver.find_element(By.CLASS_NAME, "artdeco-modal__content"))
    time.sleep(5)  # Give time to process search results to let the button grab be reliable
    show_results = wait.until(
        ec.element_to_be_clickable((By.CSS_SELECTOR, "button.search-reusables__secondary-filters-show-results-button")))
    show_results.click()
    time.sleep(5)


def sign_in():
    # TODO: Account for auto-sign in from Google etc., probably check for page title?
    config = scraper.read_config_file()
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
        scraper.security_verification()  # TODO: Just a wait time to get past verification, need logic for it later
    except TimeoutException:
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


def input_search_keywords(keyword, location):
    keyword_box = wait.until(
        ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'jobs-search-box-keyword')]")))
    keyword_box.send_keys(keyword)
    time.sleep(random.uniform(1, 2))
    location_box = wait.until(
        ec.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'jobs-search-box-location')]")))
    location_box.send_keys(location)
    time.sleep(random.uniform(1, 2))
    keyword_box.send_keys(Keys.ENTER)
    time.sleep(random.uniform(1, 2))


def scrape_search_terms():
    search_terms = scraper.read_json_file()
    for term in search_terms['LinkedIn_Search_Terms']:
        scraper.scraped_job_listings = {}
        keyword = term['keyword']
        location = term['location']
        navigate_to_jobs()
        input_search_keywords(keyword, location)
        scrape_job_pages(location)
        csv_filepath = scraper.generate_filepath()
        scraper.write_to_csv(scraper.scraped_job_listings, csv_filepath)


scraper = Scraper(source="LinkedIn", site_url="https://www.linkedin.com", headless=False)
wait = scraper.wait
driver = scraper.driver
sign_in()
scrape_search_terms()
