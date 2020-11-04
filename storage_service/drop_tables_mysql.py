import mysql.connector

azure_host = 'kafka-acit3855.canadacentral.cloudapp.azure.com'


db_conn = mysql.connector.connect(host=azure_host, user="mike",
password="P@ssw0rd", database="sensor_readings")


c = db_conn.cursor()
c.execute('''
          DROP TABLE air_reading, env_reading
          ''')


db_conn.commit()
db_conn.close()