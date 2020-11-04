import mysql.connector

azure_host = 'kafka-acit3855.canadacentral.cloudapp.azure.com'

db_conn = mysql.connector.connect(host=azure_host, user="mike",
password="P@ssw0rd", database="sensor_readings")

db_cursor = db_conn.cursor()

db_cursor.execute('''
          CREATE TABLE air_reading
          (id INT NOT NULL AUTO_INCREMENT, 
           sensor_id VARCHAR(250) NOT NULL,
           so2 DOUBLE NOT NULL,
           co DOUBLE NOT NULL,
           no2 DOUBLE NOT NULL,
           timestamp VARCHAR(100) NOT NULL,
           date_created VARCHAR(100) NOT NULL,
           CONSTRAINT air_reading_pk PRIMARY KEY (id))
          ''')

db_cursor.execute('''
          CREATE TABLE env_reading
          (id INT NOT NULL AUTO_INCREMENT,
           sensor_id VARCHAR(250) NOT NULL, 
           humidity REAL NOT NULL,
           temp REAL NOT NULL,
           wind_speed REAL NOT NULL,
           wind_dir REAL NOT NULL,
           timestamp VARCHAR(100) NOT NULL,
           date_created VARCHAR(100) NOT NULL,
           CONSTRAINT env_reading_pk PRIMARY KEY (id))
          ''')

db_conn.commit()
db_conn.close()
