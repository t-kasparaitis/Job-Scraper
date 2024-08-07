from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from scrapers import IndeedScraper
import pendulum


default_args = {
    'owner': 'airflow',
    # A start date of 2024-07-01 would mean the task triggers at 2024-07-01T23:59. This provides enough wiggle room
    # to make sure that the DAG starts at the next 8-hour interval. When Airflow is turned on with catchup=False
    # then there is no catch up and it runs at the next scheduled interval (8 hours in our case).
    'start_date': pendulum.datetime(2024, 7, 1, tz="America/New_York"),
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=15)
}

dag = DAG(
    'IndeedScraper_dag',
    # Trying to catch up could mean that multiples of the same scraper would try to run at once. This would trigger
    # bot detection through rate limiting or probably cause some other unwanted side effects:
    catchup=False,
    default_args=default_args,
    description='This DAG scrapes Indeed based on search_terms.json and writes each result set to a CSV file.',
    schedule_interval=timedelta(hours=8),
    tags=['scraper', 'Indeed']
)


def run_scraper():
    scraper = IndeedScraper()
    scraper.run()


Indeed_scraper_task = PythonOperator(
    task_id='run_Indeed_scraper',
    # Note: run_scraper passes the function reference to defer executing it until the task is run. This is necessary
    # to avoid issues with airflow initializing as it will crash if DAGs are not loaded in less than 30 seconds.
    python_callable=run_scraper,
    dag=dag
)
