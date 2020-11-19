import connexion
from connexion import NoContent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from air_reading import AirReading
from env_reading import EnvReading
import yaml
import logging.config
import datetime
import json
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
import os

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"

with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

# External Logging Configuration
with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)


logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)

user = app_config['datastore']['user']
password = app_config['datastore']['password']
hostname = app_config['datastore']['hostname']
port = app_config['datastore']['port']
db = app_config['datastore']['db']


DB_ENGINE = create_engine(f'mysql+pymysql://{user}:{password}@{hostname}:{port}/{db}')
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)

AIR_EVENT = 'Air Reading'
ENV_EVENT = 'Env. Reading'


def measure_air_quality(body):
    """Stores air quality measurement data"""
    session = DB_SESSION()
    air = AirReading(body['sensor_id'],
                     body['so2'],
                     body['co'],
                     body['no2'],
                     body['timestamp'])

    session.add(air)
    session.commit()
    session.close()
    logger.debug(f'Stored event {AIR_EVENT} request with unique id ({body["sensor_id"]})')
    return NoContent, 201


def measure_environment(body):
    """Store environment measurement data"""
    session = DB_SESSION()
    env = EnvReading(body['sensor_id'],
                     body['humidity'],
                     body['temp'],
                     body['wind_speed'],
                     body['wind_dir'],
                     body['timestamp'])

    session.add(env)
    session.commit()
    session.close()
    logger.debug(f'Stored event {ENV_EVENT} request with unique id ({body["sensor_id"]})')
    return NoContent, 201


def get_air_quality_readings(timestamp):
    """Gets new air quality reading after timestamp"""
    session = DB_SESSION()

    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")

    readings = session.query(AirReading).filter(AirReading.date_created >= timestamp_datetime)
    results_list = []

    for reading in readings:
        results_list.append(reading.to_dict())

    session.close()
    logger.info(f"Query for Air Quality readings after {timestamp} returns {len(results_list)}")
    return results_list, 200


def get_env_quality_readings(timestamp):
    """Gets new environment quality reading after timestamp"""
    session = DB_SESSION()

    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")

    readings = session.query(EnvReading).filter(EnvReading.date_created >= timestamp_datetime)
    results_list = []

    for reading in readings:
        results_list.append(reading.to_dict())

    session.close()
    logger.info(f"Query for Environment Quality readings after {timestamp} returns {len(results_list)}")
    return results_list, 200


def process_messages():
    """ Process event messages """
    hostname = "%s:%d" % (app_config["events"]["hostname"],
                           app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[app_config["events"]["topic"]]

    # Create a consume on a consumer group, that only reads new messages
    # (uncommitted messages) when the service re-starts (i.e., it doesn't
    # read all the old messages from the history in the message queue).
    consumer = topic.get_simple_consumer(consumer_group='event_group',
                                          reset_offset_on_start=False,
                                          auto_offset_reset=OffsetType.LATEST)
    # This is blocking - it will wait for a new message
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
        payload = msg["payload"]
        if msg["type"] == "env_reading": # Change this to your event type
            session = DB_SESSION()
            env = EnvReading(payload['sensor_id'],
                             payload['humidity'],
                             payload['temp'],
                             payload['wind_speed'],
                             payload['wind_dir'],
                             payload['timestamp'])
            session.add(env)
            session.commit()
            session.close()
        elif msg["type"] == "air_reading": # Change this to your event type
            session = DB_SESSION()
            air = AirReading(payload['sensor_id'],
                             payload['so2'],
                             payload['co'],
                             payload['no2'],
                             payload['timestamp'])
            session.add(air)
            session.commit()
            session.close()
        consumer.commit_offsets()


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    logger.info(f'Connecting to DB. Hostname: {hostname}, Port:{port}')
    app.run(port=8090)
