import configparser
import os
import shutil
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_extract, when, from_unixtime, unix_timestamp, regexp_replace
from pyspark.sql.types import IntegerType


def read_config_file():
    config_file_path = os.path.join(os.path.join(os.environ['USERPROFILE'], 'Desktop'), 'config.ini')
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
    dataframe = spark.read.csv(filepath, header=True)
    # TODO: introduce filtering based on 'source' if not all sources have numeric ids (Indeed etc.)
    dataframe = dataframe.filter(~col('listing_id').rlike('[^0-9]'))
    # Filter out IDs that are already in the database, atm there is no way to do ON CONFLICT DO NOTHING using pyspark
    # https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT
    db_dataframe = (spark.read.jdbc(url=connection_url, table="job_listings", properties=connection_properties)
                    .select("listing_id"))
    dataframe = dataframe.join(db_dataframe, on="listing_id", how="left_anti")
    # FIXME: Had one weird run that failed to grab the company name for 1 page - should have some error logging for this
    # dataframe = dataframe.filter(dataframe.company.isNotNull())
    # It's entirely possible that a dataframe is empty/already scraped for specific or less popular search terms:
    if dataframe.isEmpty():
        print(f"The DataFrame is empty for file: {filepath}")
        return
    num_col = regexp_extract(col("time_since_post"), r"(\d+)\s(\w+)", 1).cast(IntegerType()).alias("num_col")
    unit_col = regexp_extract(col("time_since_post"), r"(\d+)\s(\w+)", 2).alias("unit_col")
    # If you catch something right as it posted, the text will be "Just now" but adding a .when for "now" or "just"
    # doesn't work as you'd expect. Dataframe.show() spits out regex in the seconds_col name, so this is a workaround
    dataframe = dataframe.withColumn("time_since_post", regexp_replace(dataframe["time_since_post"],
                                                                       "Just now", "1 minute ago"))
    seconds_col = (when(unit_col.contains("minute"), num_col * 60)
                   .when(unit_col.contains("hour"), num_col * 60 * 60)
                   .when(unit_col.contains("day"), num_col * 60 * 60 * 24))
    time_when_posted_col = (from_unixtime(unix_timestamp(
        col("time_when_scraped")) - seconds_col, "yyyy-MM-dd HH:mm:ss")
                            .cast("timestamp").alias("time_when_posted"))
    dataframe = dataframe.withColumn("time_when_posted", time_when_posted_col)
    dataframe.select(
        ["listing_id", "source", "title", "company", "link", "time_when_posted", "location", "compensation"]
    ).write.jdbc(url=connection_url, table="job_listings", mode="append", properties=connection_properties)


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
