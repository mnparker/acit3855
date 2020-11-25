import connexion
import json
import yaml
import logging.config
from pykafka import KafkaClient
from flask_cors import CORS, cross_origin
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

AIR_EVENT = 'Air Reading'
ENV_EVENT = 'Env. Reading'


def get_air_quality_reading(index):
    """Takes in an air reading, and sends to Data storage service"""
    hostname = "%s:%d" % (app_config["events"]["hostname"],
                          app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[app_config["events"]["topic"]]

    consumer = topic.get_simple_consumer(consumer_group='event_group',
                                         reset_offset_on_start=True,
                                         consumer_timeout_ms=800)
    logger.info("Retrieving AR at index %d" % index)
    count = 0
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        if msg["type"] == "air_reading":
            count += 1
        if count == index:
            payload = msg["payload"]
            logger.info(f"Found AR id: {payload['sensor_id']} at Index: {index}")
            return payload, 200
    logger.error("Could not find AQ at index %d" % index)
    return {"message": "Not Found"}, 404


def get_env_reading(index):
    """Takes in an environment reading, and sends to Data storage service"""
    hostname = "%s:%d" % (app_config["events"]["hostname"],
                          app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[app_config["events"]["topic"]]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
                                         consumer_timeout_ms=800)
    logger.info("Retrieving ER at index %d" % index)
    count = 0
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        if msg["type"] == "env_reading":
            count += 1
        if count == index:
            payload = msg["payload"]
            logger.info(f"Found ER id: {payload['sensor_id']} at Index: {index}")
            return payload, 200
    logger.error("Could not find AQ at index %d" % index)
    return {"message": "Not Found"}, 404


app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yml", base_path="/audit_log", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
    app.run(port=8110)
