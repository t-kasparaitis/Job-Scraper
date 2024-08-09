from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from utilities import DatabaseWriter
import pendulum


default_args = {
    'owner': 'airflow',
    # Our scraper DAGs have a start time of midnight. Adding 1 hour offset as mostly this is how long it should take
    # to run. An alternative would be to call the DatabaseWrite_dag.py at the end of each Scraper run.
    'start_date': pendulum.datetime(2024, 7, 1, 1, 0, tz="America/New_York"),
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=15)
}

dag = DAG(
    'DatabaseWriter_dag',
    catchup=False,
    default_args=default_args,
    description='This DAG reads CSV files from the JobScraper directory and writes them to AWS RDS Postgre database.',
    schedule_interval=timedelta(hours=4),
    tags=['csv', 'DatabaseWriter']
)


def run_writer():
    writer = DatabaseWriter()
    writer.run()


DatabaseWriter_task = PythonOperator(
    task_id='run_DatabaseWriter',
    # Note: run_scraper passes the function reference to defer executing it until the task is run. This is necessary
    # to avoid issues with airflow initializing as it will crash if DAGs are not loaded in less than 30 seconds.
    python_callable=run_writer,
    dag=dag
)
