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
# We also need to install the same dependencies as in the Project environment:
pip install selenium
pip install pyspark
pip install fake-useragent
# We are now using bash commands to make a directory on our C drive:
cd /mnt/c/Users/JobScraper/Documents
mkdir airflow
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
# Not sure db init is necessary, deprecation warning:
airflow db init
# Following Apache guide, using this for quick development (not meant for production).
# Note: 'airflow standalone' is the command for starting the web server & scheduler in one command:
airflow standalone
# After airflow starts you will see the following:
standalone | Login with username: admin  password: ${redacted}
standalone | Airflow Standalone is for development purposes only. Do not use this in production!
# That username/password will get you access to the webserver running on localhost:8080


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
```
- Go to localhost:8080 and sign in to Airflow

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
