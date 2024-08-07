# Setup

## PyCharm, PySpark & PostgreSQL
- Download & install PyCharm from: https://www.jetbrains.com/pycharm/download/?section=windows
- Clone https://github.com/t-kasparaitis/Job-Scraper
- Download & install Python: https://www.python.org/downloads/
  - Checkmark "Add python.exe to PATH" before installing
  - If PyCharm was open during Python install, restart PyCharm
- Set up the Virtual Environment:
  - Go to **File > Settings**, then click **Project: Job-Scraper**
  - Click **Python Interpreter**, then **Add Interpreter**, then **Add Local Interpreter...**
  - Go with defaults, click **OK** and then **Apply**
  - Go to **C:\Users\JobScraper\PycharmProjects\Job-Scraper\venv\Scripts** (your path will vary)
  - Run activate.ps1 (PowerShell)
- Go to Terminal from PyCharm & type:
- `pip install selenium`
- `pip install pyspark`
- `pip install fake-useragent`
- Download & install Java (required for pyspark): https://www.oracle.com/java/technologies/downloads/
  - Edit Environment variables => create JAVA_HOME
  - Set to C:\Program Files\Java\jdk-22 (example, replace with your own)
  - Check in CMD that it works by typing: java -version
  - If PyCharm was open during Java install/config, restart PyCharm

- Download & install PostgreSQL from: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
- Download PostgreSQL driver: https://jdbc.postgresql.org/download/
  - Place in Job-Scraper/venv/Lib/site-packages/pyspark/jars

### Apache Airflow
- In Windows Environment Variables create a system variable called `PYTHONPATH`
- Set the variable value to `C:\Users\JobScraper\PycharmProjects\Job-Scraper`
- Restart IDE, command prompt, powershell etc. for settings to take effect
- Run PowerShell as an administrator and install WSL2 (a prerequisite for Airflow on Windows)
```
wsl --install -d openSUSE-Tumbleweed
```

- Note: All Linux commands can be run directly from PowerShell by typing wsl to access Linux!
- A system restart will be needed for installation, after restart create an admin account
- After creating the admin account run the following:

```
# First we make sure openSUSE Tumbleweed is up to date:
sudo zypper refresh
sudo zypper dup
# Then we get Python and set up a virtual environment:
sudo zypper install python3
sudo zypper install python3-virtualenv
virtualenv ~/airflow_env
source ~/airflow_env/bin/activate
# We need to install Java which will later be used by PySpark.
# PySpark supports Java 8, 11 & 17. Amazon has an optimized JDK for 17:
sudo zypper addrepo https://yum.corretto.aws/corretto.repo
sudo zypper refresh
sudo zypper install java-17-amazon-corretto-devel
# Also need to install chrome & chromedriver for running the scrapers:
sudo zypper ar http://dl.google.com/linux/chrome/rpm/stable/x86_64 Google-Chrome
sudo rpm --import https://dl.google.com/linux/linux_signing_key.pub
sudo zypper ref
sudo zypper install google-chrome-stable
sudo zypper install chromedriver
# We will need PostgreSQL to run Airflow in production mode isntead of standalone:
sudo zypper install postgresql postgresql-server
# postgresql-server installs with a default user but you need to set a password first:
sudo passwd postgres
# Create data directory & initialize the database:
sudo mkdir -p /var/lib/pgsql/data
sudo chown postgres:postgres /var/lib/pgsql/data
sudo su - postgres
initdb -D /var/lib/pgsql/data
exit
# Installation needs this directory for logging, but it's not created automatically:
sudo mkdir -p /run/postgresql
sudo chown postgres:postgres /run/postgresql
sudo chmod 775 /run/postgresql
# Start the postgres server:
sudo su - postgres -c "pg_ctl start -D /var/lib/pgsql/data"
# Note: for some reason db ownership needs to go to the created user to fix this error:
# sqlalchemy.exc.ProgrammingError: (psycopg2.errors.InsufficientPrivilege) permission denied for schema public
# Need to create an airflow_user for the database:
sudo su - postgres
psql
CREATE DATABASE airflow_db;
CREATE USER airflow_user WITH ENCRYPTED PASSWORD 'airflow_pass';
GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow_user;
ALTER USER airflow_user SET search_path = public;
ALTER DATABASE airflow_db OWNER TO airflow_user;
\q
# We also need to install the same dependencies as in the Project environment:
pip install selenium
pip install pyspark
pip install fake-useragent
# Psycopg2 is the airflow-recommended driver:
pip install psycopg2-binary
# Add postgres subpackage:
pip install 'apache-airflow[postgres]'
# We are now using bash commands to make a directory on our C drive:
cd /mnt/c/Users/JobScraper/Documents
mkdir airflow
# Get the JDBC PostgreSQL driver for our WSL venv:
cd /home/tkasparaitis/airflow_env/lib/python3.11/site-packages/pyspark/jars
# Double check it matches the jar in the Windows venv for consistency:
wget https://jdbc.postgresql.org/download/postgresql-42.7.3.jar
# Install nano for convenience, then create an environment variable:
sudo zypper install nano
sudo nano ~/.bashrc
# Add the following to bashrc:
export AIRFLOW_HOME=/mnt/c/Users/JobScraper/Documents/airflow
# This allows Airflow to access project classes to run:
export PYTHONPATH=$PYTHONPATH:/mnt/c/Users/JobScraper/PycharmProjects/Job-Scraper
# This might be needed for helping find the classes also, not sure yet (troubleshooting):
export PATH=$PATH:/home/tkasparaitis/airflow_env/bin
# This sets JAVA_HOME that will be used for PySpark:
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
export PATH=$JAVA_HOME/bin:$PATH
# This is the driver needed for PySpark to communicate with Postgre:
export CLASSPATH=$CLASSPATH:/home/tkasparaitis/airflow_env/lib/python3.11/site-packages/pyspark/jars/postgresql-42.7.3.jar
# The following avoids having to activate the venv each time a new WSL session starts.
# This needs to be at the end of the bashrc file:
source /home/tkasparaitis/airflow_env/bin/activate
# Save changes and exit nano, then run the following to apply changes:
source ~/.bashrc

```
- Exit PowerShell and reopen it (allows for environment variable changes to take effect)
```
wsl
cd $AIRFLOW_HOME
source ~/airflow_env/bin/activate

# Install Apache Airflow from pip:
AIRFLOW_VERSION=2.9.2
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"


cd $AIRFLOW_HOME
# db init is now deprecated, have to use db migrate:
airflow db migrate
# create an admin account:
airflow users create \
          --username admin \
          --firstname Tomas \
          --lastname Kasparaitis \
          --role Admin \
          --email tkasparaitis@gmail.com
# if admin account exits, then change the password:
airflow users reset-password --username admin
# airflow standalone is for single-task development only, start separately for production:
airflow webserver -p 8080 &
airflow scheduler &


```

- In the airflow installation directory, modify airflow.cfg
```
# Look for this line:
dags_folder = /mnt/c/Users/JobScraper/Documents/airflow/dags
# Change it to the project folder:
dags_folder = /mnt/c/Users/JobScraper/PycharmProjects/Job-Scraper/dags/production
# Look for these two parameters and change them to False:
load_examples = False
dags_are_paused_at_creation = False
# Dags paused at creation seems to have caused an issue where the only way to start
# the dag after making a new one is to run it manually, but then it also starts a scheduled
# run at the same time. Restarting the airflow server is also not ideal.
# There may be some other parameters to help with this, but this works for now.
# Look for executor and change it to LocalExecutor (single-machine production):
executor = LocalExecutor
# Look for sql_alchemy_conn & change it to:
sql_alchemy_conn = postgresql+psycopg2://airflow_user:airflow_pass@localhost/airflow_db

```
- Go to localhost:8080 and sign in to Airflow

### Starting Airflow
```
# This directory is needed for logging, but doesn't persist between reboots on WSL as it is at temp dir:
sudo mkdir -p /run/postgresql
sudo chown postgres:postgres /run/postgresql
sudo chmod 775 /run/postgresql
# After creating the dir, can start the PostgreSQL server:
sudo su - postgres -c "pg_ctl start -D /var/lib/pgsql/data"
# Afterwards can start the airflow scheduler & webserver as background processes:
airflow webserver -p 8080 &
airflow scheduler &
```

### DBeaver (DBMS)
- Download & install from https://dbeaver.io/download/
- Open up DBeaver and then run the Database Setup.SQL script
- **Note: checkmark "Show all databases" when creating the connection in DBeaver (not sure why this isn't default)**

### Creating the config.ini file
- Make sure you can view file extensions, create a text file & rename it to config.ini
- This will store your credentials, change it to your username etc.

```
[linkedin_credentials]
username = youremail@someprovider.com
password = yourpassword
[database]
host = localhost
port = 1111
database = dbname
username = user
password = password
```

- If you have an existing config.ini file, you can instead move it to Job-Scraper/configurations
### Editing the searchTerms.json file
- This file is located in the first level of the project directory and stores search terms to go through during a run

## Possible future DB options
### Cassandra
- Download: https://cassandra.apache.org/_/download.html
- Extract with 7zip: https://www.7-zip.org/
- https://phoenixnap.com/kb/install-cassandra-on-windows
### Mongo DB
- Download: https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-windows/
