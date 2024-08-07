import configparser
import os
import shutil
import traceback
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import logging
import platform


class DatabaseWriter:
    logger = None  # Allows logger to be used in our Scraper (parent) functions in addition to child classes.
    LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
    
    def __init__(self):
        if not self.__class__.logger:
            self.__class__.setup_logger()
        self.config = self.read_config_file()
        self.spark = SparkSession.builder.appName("Job Listing Loader").getOrCreate()
        self.logger.info(f"Success: {self.__class__.__name__} initialized")

    def run(self):
        try:
            files = self.get_csv_files()
            for csv in files:
                try:
                    self.write_to_database(csv)
                    folder = 'Processed'
                    self.move_csv_file(csv, folder)
                except Exception as e:
                    stack_trace = traceback.format_exc()
                    self.logger.debug(f"Failure: {e}\n While handling {csv}\n{stack_trace}")
                    continue
            self.logger.info(f"Success: {self.__class__.__name__} finished writing CSVs")
        except Exception as e:
            stack_trace = traceback.format_exc()
            self.logger.error(f"Failure: {type(e).__name__}, {e}\n{stack_trace}")
            raise

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

    def write_to_database(self, csv_file):
        host = self.config['database']['host']
        port = self.config['database']['port']
        database = self.config['database']['database']
        connection_url = f"jdbc:postgresql://{host}:{port}/{database}"
        connection_properties = {
            "user": self.config['database']['username'],
            "password": self.config['database']['password'],
            "driver": "org.postgresql.Driver"
        }
        try:
            dataframe = (self.spark.read.option("encoding", "utf-8")
                         .option("multiline", "true")
                         .option("escapeQuote", "true")
                         .csv(csv_file, header=True))

            # Sometimes a CSV will have no results only a header:
            if dataframe is None or dataframe.rdd.isEmpty():
                self.logger.warning(f"Warning: The DataFrame is empty or None for file: {csv_file}")
                return

            # LinkedIn logic currently grabs some things that may not be valid IDs (numbers only). This needs filtered:
            if dataframe.first()['source'] == "LinkedIn":
                dataframe = dataframe.filter(~col('listing_id').rlike('[^0-9]'))

            db_dataframe = (self.spark.read.jdbc(
                url=connection_url,
                table="job_listings",
                properties=connection_properties
            ).select("listing_id", "source"))

            dataframe = dataframe.join(db_dataframe, on=["listing_id", "source"], how="left_anti")

            # It's possible that there's no new unique listings for specific search terms since the last run:
            if dataframe.isEmpty():
                self.logger.warning(f"Warning: No new data to write to the database for file: {csv_file}")
                return

            dataframe.select(
                ["listing_id",
                 "source",
                 "title",
                 "company",
                 "link",
                 col("time_when_scraped").cast("timestamp"),
                 "location",
                 "compensation"]
            ).write.jdbc(url=connection_url, table="job_listings", mode="append", properties=connection_properties)

        except Exception as e:
            stack_trace = traceback.format_exc()
            self.logger.error(f"Failure: {type(e).__name__}, {e}\n{stack_trace}")
            folder = 'Errors'
            self.move_csv_file(csv_file, folder)
            raise

    def get_csv_files(self):
        csv_path = self.get_base_path()
        csv_files = []
        for file in os.listdir(csv_path):
            if file.endswith(".csv"):
                csv_files.append(os.path.join(csv_path, file))
        return csv_files

    def move_csv_file(self, csv_file, folder):
        destination_folder = os.path.join(self.get_base_path(), folder)
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
        destination_path = os.path.join(destination_folder, os.path.basename(csv_file))
        shutil.move(csv_file, destination_path)
        self.logger.info(f"Success: Moved processed CSV to {destination_path}")

    def get_base_path(self):
        env_platform = platform.system()
        username = self.config['windows_credentials']['username']
        if env_platform == 'Windows':
            return os.path.join(os.environ['USERPROFILE'], 'Desktop', 'JobScraper')
        elif env_platform == 'Linux':
            return os.path.join('/mnt/c/Users', username, 'Desktop', 'JobScraper')
        else:
            self.__class__.logger.critical("Failure: Unsupported Operating System, not Windows or Linux on WSL")
            raise EnvironmentError("Failure: Unsupported Operating System")


if __name__ == "__main__":
    db_writer = DatabaseWriter()
    db_writer.run()
