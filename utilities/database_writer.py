import configparser
import os
import shutil
from pyspark.sql import SparkSession
from pyspark.sql.functions import col


def read_config_file():
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'configurations')
    config_file_path = os.path.join(config_dir, 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config


def write_to_database(filepath):
    config = read_config_file()
    spark = SparkSession.builder.appName("Job Listing Loader").getOrCreate()
    host = config['database']['host']
    port = config['database']['port']
    database = config['database']['database']
    connection_url = f"jdbc:postgresql://{host}:{port}/{database}"
    connection_properties = {
        "user": config['database']['username'],
        "password": config['database']['password'],
        "driver": "org.postgresql.Driver"
    }
    dataframe = (spark.read.option("encoding", "utf-8")
                 .option("multiline", "true")
                 .option("escapeQuote", "true")
                 .csv(filepath, header=True))

    if dataframe.first()['source'] == "LinkedIn":
        dataframe = dataframe.filter(~col('listing_id').rlike('[^0-9]'))

    db_dataframe = (spark.read.jdbc(url=connection_url, table="job_listings", properties=connection_properties)
                    .select("listing_id", "source"))
    dataframe = dataframe.join(db_dataframe, on=["listing_id", "source"], how="left_anti")
    # It's entirely possible that a dataframe is empty/already scraped for specific or less popular search terms:
    if dataframe.isEmpty():
        print(f"The DataFrame is empty for file: {filepath}")
        return
    (dataframe.select(
        ["listing_id",
         "source",
         "title",
         "company",
         "link",
         col("time_when_scraped").cast("timestamp"),
         "location",
         "compensation"])
     .write.jdbc(url=connection_url, table="job_listings", mode="append", properties=connection_properties))


def get_csv_files():
    csv_files = []
    folder_path = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'JobScraper')
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            csv_files.append(os.path.join(folder_path, file))
    return csv_files


def move_csv_file(csv_file):
    destination_folder = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'JobScraper', 'Processed')
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    destination_path = os.path.join(destination_folder, os.path.basename(csv_file))
    shutil.move(csv_file, destination_path)
    print(f"Moved {csv_file} to {destination_path}")


for csv in get_csv_files():
    try:
        write_to_database(csv)
        move_csv_file(csv)
    except Exception as e:
        # TODO: actually start writing errors to a log file
        print(f"An error occurred: {e} while handling this csv: {csv}")
