# Setup

## PyCharm, PySpark & PostgreSQL
- Download & install PyCharm from: https://www.jetbrains.com/pycharm/download/?section=windows
- Go to Terminal from PyCharm & type: `pip install selenium`
- Go to Terminal from PyCharm & type: `pip install pyspark`
- Download & install Java (required for pyspark): https://www.oracle.com/java/technologies/downloads/
  - Edit Environment variables => create JAVA_HOME
  - Set to C:\Program Files\Java\jdk-22 (example, replace with your own)
  - Check in CMD that it works by typing: java -version
  - Restart PyCharm if it was running
- Download & install PostgreSQL from: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
- Download PostgreSQL driver: https://jdbc.postgresql.org/download/
- Place in Job Scraper/.venv/Lib/site-packages/pyspark/jars

### DBeaver (DBMS)
- Download & install from https://dbeaver.io/download/
- Open up DBeaver and then run the Database Setup.SQL script
- **Note: checkmark "Show all databases" when creating the connection in DBeaver (not sure why this isn't default)**

### Creating the config.ini file
- Make sure you can view file extensions, create a text file & rename it to config.ini
- This will store your credentials, change it to your username etc.

```
[credentials]
username = youremail@someprovider.com
password = yourpassword
[database]
host = localhost
port = 1111
database = dbname
username = user
password = password
```

### Editing the searchTerms.json file
- This file is located in the first level of the project directory and stores search terms to go through during a run

## Possible future DB options
### Cassandra
- Download: https://cassandra.apache.org/_/download.html
- Extract with 7zip: https://www.7-zip.org/
- https://phoenixnap.com/kb/install-cassandra-on-windows
### Mongo DB
- Download: https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-windows/
