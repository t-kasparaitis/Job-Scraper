import configparser
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

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
driver.get('https://www.linkedin.com')
wait = WebDriverWait(driver, 10)
username_box = wait.until(EC.element_to_be_clickable((By.ID, "session_key")))
username_box.send_keys(username)
username_box = wait.until(EC.element_to_be_clickable((By.ID, "session_password")))
username_box.send_keys(password)
sign_in_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-id='sign-in-form__submit-btn']")))
sign_in_button.click()

# Wait to check that we are on the homepage:
wait.until(EC.title_contains("Feed | LinkedIn"))
# Minimize messaging for better view when testing:
# FIXME: fix whatever is causing the crash here:
# messaging_minimize_button = wait.until(EC.element_to_be_clickable(
#     (By.XPATH, "//div[contains(@class, 'msg-overlay-bubble-header__controls')]//use[@href='#chevron-down-small']"))
# )
# messaging_minimize_button.click()

# Go to jobs page
jobs_page = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//a[contains(@class, 'app-aware-link') and @href='https://www.linkedin.com/jobs/?']"))
)
jobs_page.click()
wait.until(EC.title_contains("Jobs | LinkedIn"))
keyword_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'jobs-search-box-keyword')]")))
search_one_keywords = config['searchOne']['keywords']
search_one_location = config['searchOne']['location']
keyword_box.send_keys(search_one_keywords)
location_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'jobs-search-box-location')]")))
location_box.send_keys(search_one_location)
keyword_box.send_keys(Keys.ENTER)

# Clear out any filters if there are any from previous uses or being signed in to LinkedIn etc.:
try:
    reset_applied_filters = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
        (By.XPATH, "//button[@aria-label='Reset applied filters' and span[text()='Reset']]"))
    )
    reset_applied_filters.click()
except NoSuchElementException:
    pass
# FIXME: TimeoutException is being triggered
except TimeoutException:
    print(TimeoutException)
    pass

# TODO: apply filter for remote for SearchOne
elements = driver.find_elements(By.CSS_SELECTOR, "[data-job-id")
for element in elements:
    try:
        element.click()
        data_job_id = element.get_attribute("data-job-id")
        job_link = "https://www.linkedin.com/jobs/view/" + data_job_id
        # Aria label is an accessibility label which seems to have the job title (a more reliable grab):
        aria_label = element.find_element(By.CSS_SELECTOR, "[aria-label]")
        job_title = aria_label.get_attribute("aria-label")
        job_company = driver.find_element(
            By.XPATH, "//span[contains(@class, 'job-card-container__primary-description ')]").text
        print(data_job_id + " | " + job_link + " | " + job_title + " | " + job_company)
    except NoSuchElementException:
        pass

# LinkedIn returns 25 search results per page, without scrolling this for element in elements only picks up 7



# TODO: maybe think about an indefinite amount of searches, how to read the config.ini in that case & iterate
# TODO: idea - feed jobs found to ChatGPT to filter out things I don't want
# TODO: check for unique job identifiers (for example Indeed has repeats where jk=# is repeated among different pages)
# TODO: automate the run for every X hours using scheduler.py along with Windows Task Scheduler


input("Press any key in the run window to exit session")  # This pauses the script until the user does something
driver.quit()  # This closes the browser window and exits the WebDriver session
