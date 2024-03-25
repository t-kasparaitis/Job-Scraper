import configparser
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

config_file_path = os.path.join(os.path.join(os.environ['USERPROFILE'], 'Desktop'), 'config.ini')
config = configparser.ConfigParser()
config.read(config_file_path)
username = config['credentials']['username']
password = config['credentials']['password']

## TODO: re-enable headless mode after this is fleshed out
# from selenium.webdriver.chrome.options import Options
#
# options = Options()
# options.add_argument('--headless')

# driver = webdriver.Chrome(options=options)

# Uses credentials from config file to sign in to LinkedIn
## TODO: Account for auto-sign in from Google etc., probably check for page title?
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
# TODO: fix whatever is causing the crash here:
wait.until(EC.element_to_be_clickable((By.XPATH, "//use[@href='#chevron-down-small']")))

# Go to jobs page
jobs_page = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'app-aware-link') and @href='https://www.linkedin.com/jobs/?']")))
jobs_page.click()
wait.until(EC.title_contains("Jobs | LinkedIn"))
keyword_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'jobs-search-box-keyword')]")))
search_one_keywords = config['searchOne']['keywords']
search_one_location = config['searchOne']['location']
keyword_box.send_keys(search_one_keywords)
location_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[contains(@id, 'jobs-search-box-location')]")))
location_box.send_keys(search_one_location)

#TODO: maybe think about an indefinite amount of searches, how to read the config.ini in that case & iterate

input("Press any key in the run window to exit session")  # This pauses the script until the user does something
driver.quit()  # This closes the browser window and exits the WebDriver session
