import connexion
import yaml
import logging.config
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import os.path
import json
import requests


with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

AIR_EVENT = 'Air Reading'
ENV_EVENT = 'Env. Reading'

AIR_URL = app_config['eventstore']['air_url']
ENV_URL = app_config['eventstore']['env_url']
FILE = app_config['datastore']['filename']

def populate_stats():
    """Periodically update stats"""
    logger.info(f"------------------Starting Periodic Processing----------")

    if os.path.isfile('data.json'):
        with open('data.json', 'r') as file:
            stats = file.read()
            stats = json.loads(stats)
            file.close()
    else:
        stats = {}
        stats['num_aq_readings'] = 0
        stats['max_so2_reading'] = 0
        stats['max_co_reading'] = 0
        stats['num_eq_readings'] = 0
        stats['max_ws_reading'] = 0
        stats['last_check'] = datetime.datetime.now()

    last_check = stats['last_check']
    air_response = requests.get(AIR_URL, params={'timestamp': last_check},  headers={'content-type': 'application/json'})
    env_response = requests.get(ENV_URL, params={'timestamp': last_check},  headers={'content-type': 'application/json'})
    air_stats = json.loads(air_response.text)
    env_stats = json.loads(env_response.text)

    if air_response.status_code != 200:
        logger.error(f"Did not receive 200 response: {air_response.status_code}")
    else:
        logger.info(f"Recieved {AIR_EVENT} {len(air_stats)} events")

    if env_response.status_code != 200:
        logger.error(f"Did not receive 200 response: {env_response.status_code}")
    else:
        logger.info(f"Recieved {ENV_EVENT} {len(env_stats)} events")

    for reading in air_stats:
        if reading['so2'] > stats['max_so2_reading']:
            stats['max_so2_reading'] = reading['so2']
        if reading['co'] > stats['max_co_reading']:
            stats['max_co_reading'] = reading['co']

    for reading in env_stats:
        if reading['wind_dir'] > stats['max_ws_reading']:
            stats['max_ws_reading'] = reading['wind_dir']

    stats['num_aq_readings'] += len(air_stats)
    stats['num_eq_readings'] += len(env_stats)
    stats['last_check'] = str(datetime.datetime.now())
    with open('data.json', 'w') as file:
        file.write(json.dumps(stats, indent=4))

    logger.debug(f"AQ Readings: {stats['num_aq_readings']}"
                 f" ENV Readings: {stats['num_eq_readings']} "
                 f"Max so2: {stats['max_so2_reading']} "
                 f"Max co: {stats['max_co_reading']} "
                 f"Max Wind Speed: {stats['max_ws_reading']}")
    logger.info("---------------Periodic Processing Has Ended----------")


def init_scheduler():
    """Initiate and start scheduler"""
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,
                  'interval',
                  seconds=app_config['scheduler']['period_sec'])
    sched.start()


def get_stats():
    """Returns stats"""
    logging.info('Request has begun.')

    if os.path.isfile(FILE):
        with open(FILE, 'r') as file:
            stats = file.read()
            stats = json.loads(stats)
            file.close()
    else:
        logging.error(f'{FILE} does not exist')
        return 'Statistics do not exist', 404

    logging.debug(stats)
    logging.info('Request Completed')
    return stats, 200


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)


if __name__ == "__main__":
    # run scheduler
    init_scheduler()
    app.run(port=8100, use_reloader=False)