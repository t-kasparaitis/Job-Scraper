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


options = Options()
# options.add_argument('--headless')  # Disable headless mode if you are watching it run for troubleshooting/demo
driver = webdriver.Chrome(options=options)
driver.maximize_window()
driver.get('https://www.indeed.com')