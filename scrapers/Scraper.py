import csv
import os
import time
import json
import configparser
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


class Scraper:
    def __init__(self, source, site_url, **kwargs):
        default_wait_time = 10
        default_headless = True

        self.wait_time = kwargs.get('wait_time', default_wait_time)
        self.headless = kwargs.get('headless', default_headless)

        self.options = Options()
        if self.headless:
            self.options.add_argument('--headless')
        self.source = source
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.maximize_window()
        self.driver.get(site_url)
        self.wait = WebDriverWait(self.driver, self.wait_time)

    @staticmethod
    def read_config_file():
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'configurations')
        config_file_path = os.path.join(config_dir, 'config.ini')
        config = configparser.ConfigParser()
        config.read(config_file_path)
        return config

    @staticmethod
    def read_json_file():
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'configurations')
        json_file_path = os.path.join(config_dir, 'search_terms.json')
        with open(json_file_path, 'r') as json_file:
            return json.load(json_file)

    def write_to_csv(self, job_listings, filepath):
        with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['listing_id',
                          'source',
                          'title',
                          'company',
                          'link',
                          'time_when_scraped',
                          'time_since_post',
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
                    'time_since_post': listing['time_since_post'],
                    'location': listing['location'],
                    'compensation': listing['compensation']
                })

    def generate_filepath(self):
        output_dir = os.path.join(os.path.join(os.environ['USERPROFILE'], 'Desktop'), 'JobScraper')
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f'{self.source}_{timestamp}.csv'
        filepath = os.path.join(output_dir, filename)
        return filepath

    @staticmethod
    def security_verification():
        time.sleep(45)

    def close(self):
        self.driver.quit()
