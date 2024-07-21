import csv
import os
import platform
import time
import json
import configparser
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


class Scraper:
    logger = None  # Allows logger to be used in our Scraper (parent) functions in addition to child classes.
    LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')

    def __init__(self, source, site_url, **kwargs):
        if not self.__class__.logger:
            self.__class__.setup_logger()
        default_wait_time = 10
        default_headless = True
        self.wait_time = kwargs.get('wait_time', default_wait_time)
        self.headless = kwargs.get('headless', default_headless)
        self.options = Options()
        if self.headless:
            self.options.add_argument('--headless=new')
        self.user_agent = kwargs.get('user_agent')
        user_agent = kwargs.get('user_agent')
        if user_agent:
            self.options.add_argument(f'--user-agent={user_agent}')
        self.scraped_job_listings = {}
        self.source = source
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.maximize_window()
        self.driver.get(site_url)
        self.wait = WebDriverWait(self.driver, self.wait_time)

    @classmethod
    def setup_logger(cls):
        # Make sure the log directory exists:
        if not os.path.exists(cls.LOG_DIR):
            os.makedirs(cls.LOG_DIR)
        cls.logger = logging.getLogger(cls.__name__)
        cls.logger.setLevel(logging.DEBUG)
        # Remove any existing handlers to avoid duplicate logs:
        if cls.logger.hasHandlers():
            cls.logger.handlers.clear()
        formatter = logging.Formatter('[%(asctime)s.%(msecs)03d] | %(name)s | %(levelname)s | %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        log_file_path = os.path.join(cls.LOG_DIR, f'{cls.__name__}.log')
        handler = logging.FileHandler(log_file_path)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        cls.logger.addHandler(handler)

    @classmethod
    def read_config_file(cls):
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'configurations')
        config_file_path = os.path.join(config_dir, 'config.ini')
        config = configparser.ConfigParser()
        try:
            config.read(config_file_path)
            if not config.sections():
                cls.logger.critical("Failure: Configuration file is empty or incorrectly formatted")
                raise
            cls.logger.info("Success: Loaded config file from {}".format(config_file_path))
            return config
        except Exception as e:
            cls.logger.critical("Failure: Could not load config file from {}: {}".format(config_file_path, e))
            raise

    @classmethod
    def read_json_file(cls):
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'configurations')
        json_file_path = os.path.join(config_dir, 'search_terms.json')
        try:
            with open(json_file_path, 'r') as json_file:
                json_data = json.load(json_file)
                cls.logger.info("Success: JSON file loaded from {}".format(json_file_path))
            return json_data
        except Exception as e:
            cls.logger.critical("Failure: Could not load JSON file from {}: {}".format(json_file_path, e))
            raise

    def write_to_csv(self, job_listings, filepath):
        with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['listing_id',
                          'source',
                          'title',
                          'company',
                          'link',
                          'time_when_scraped',
                          'location',
                          'compensation']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for listing_id, listing in job_listings.items():
                writer.writerow({
                    'listing_id': listing_id,
                    'source': self.source,
                    'title': listing['title'],
                    'company': listing['company'],
                    'link': listing['link'],
                    'time_when_scraped': listing['time_when_scraped'],
                    'location': listing['location'],
                    'compensation': listing['compensation']
                })
        self.logger.info(f"Success: Wrote scraped-data CSV to {filepath}")

    def generate_filepath(self):
        config = self.read_config_file()
        username = config['windows_credentials']['username']
        env_platform = platform.system()
        # This logic accounts for running scrapers as a script on Windows directly or as a DAG from Apache Airflow
        # running on WSL in a Linux environment. If any of the environment assumptions change it would need refactored:
        if env_platform == 'Windows':
            output_dir = os.path.join(os.path.join(os.environ['USERPROFILE'], 'Desktop'), 'JobScraper')
        elif env_platform == 'Linux':
            output_dir = os.path.join('/mnt/c/Users', username, 'Desktop', 'JobScraper')
        else:
            self.__class__.logger.critical("Failure: Unsupported Operating System, not Windows or Linux on WSL")
            raise EnvironmentError("Failure: Unsupported Operating System")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f'{self.source}_{timestamp}.csv'
        filepath = os.path.join(output_dir, filename)
        return filepath

    # This method exists for script runs to give a window to bypass bot detection manually. It will need to be updated
    # and possibly individualized for different site scrapers to bypass bot detection later.
    def security_verification(self):
        self.logger.info("Failure: Triggered Security Verification")
        time.sleep(45)

    def close(self):
        self.driver.quit()
        self.__class__.logger.info("Success: Driver closed")
