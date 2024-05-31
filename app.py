import time
import requests
import logging
from prometheus_client import start_http_server, Gauge, Counter
from dateutil import parser

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
API_KEY = 'your_simplemdm_api_key'  # Replace with your correct API key
BASE_URL = 'https://a.simplemdm.com/api/v1'

# Prometheus metrics definitions
device_count = Gauge('simplemdm_device_count', 'Total number of devices managed by SimpleMDM')
app_count = Gauge('simplemdm_app_count', 'Total number of apps managed by SimpleMDM')
device_last_seen = Gauge('simplemdm_device_last_seen', 'Timestamp of the last seen device', ['device_id', 'device_name', 'os_version', 'build_version', 'simplemdm_name'])
device_enrollment_status = Gauge('simplemdm_device_enrollment_status', 'Enrollment status of the device', ['device_id', 'device_name', 'os_version', 'build_version', 'simplemdm_name'])
app_install_count = Gauge('simplemdm_app_install_count', 'Total number of installs for each app', ['app_id', 'app_name'])
app_type_count = Counter('simplemdm_app_type_count', 'Count of apps by type', ['app_type'])
device_os_version_count = Counter('simplemdm_device_os_version_count', 'Count of devices by OS version', ['os_version'])
enrollment_count = Gauge('simplemdm_enrollment_count', 'Total number of enrollments')

# Function to get data from SimpleMDM API with cursor-based pagination
def fetch_data(endpoint):
    data = []
    params = {'limit': 100}
    while True:
        logger.info(f'Fetching data from endpoint: {endpoint} with params: {params}')
        response = requests.get(f'{BASE_URL}/{endpoint}', auth=(API_KEY, ''), params=params)
        response.raise_for_status()  # Raise an error for bad status codes
        json_data = response.json()
        data.extend(json_data['data'])
        logger.info(f'Received {len(json_data["data"])} items from endpoint: {endpoint}')
        if not json_data.get('has_more', False):
            break
        params['starting_after'] = json_data['data'][-1]['id']
    return data

# Function to get devices
def get_devices():
    return fetch_data('devices')

# Function to get apps
def get_apps():
    return fetch_data('apps')

# Function to get enrollments
def get_enrollments():
    return fetch_data('enrollments')

# Map enrollment status to an integer value
def map_status(status):
    status_map = {
        'enrolled': 1,
        'unenrolled': 0,
        # Add other status mappings if necessary
    }
    return status_map.get(status.lower(), -1)  # Default to -1 if status is unknown

# Function to collect and update Prometheus metrics
def collect_metrics():
    try:
        logger.info('Collecting device metrics...')
        devices = get_devices()
        logger.info(f'Collected {len(devices)} devices')

        logger.info('Collecting app metrics...')
        apps = get_apps()
        logger.info(f'Collected {len(apps)} apps')

        logger.info('Collecting enrollment metrics...')
        enrollments = get_enrollments()
        logger.info(f'Collected {len(enrollments)} enrollments')

        device_count.set(len(devices))
        app_count.set(len(apps))
        enrollment_count.set(len(enrollments))

        for device in devices:
            device_id = device['id']
            device_name = device['attributes']['device_name']
            os_version = device['attributes']['os_version']
            build_version = device['attributes']['build_version']
            simplemdm_name = device['attributes']['name']
            try:
                last_seen_timestamp = parser.isoparse(device['attributes']['last_seen_at']).timestamp()
                device_last_seen.labels(device_id=device_id, device_name=device_name, os_version=os_version, build_version=build_version, simplemdm_name=simplemdm_name).set(last_seen_timestamp)
            except ValueError as e:
                logger.error(f"Error parsing date for device {device_id}: {e}")
            device_enrollment_status.labels(device_id=device_id, device_name=device_name, os_version=os_version, build_version=build_version, simplemdm_name=simplemdm_name).set(map_status(device['attributes']['status']))
            device_os_version_count.labels(os_version=os_version).inc()

        for app in apps:
            app_id = app['id']
            app_name = app['attributes']['name']
            app_type = app['attributes']['app_type']
            installs = app['attributes'].get('installations_count', 0)
            app_install_count.labels(app_id=app_id, app_name=app_name).set(installs)
            app_type_count.labels(app_type=app_type).inc()
        
        logger.info('Metrics collection completed successfully.')
    except Exception as e:
        logger.error(f'Error collecting metrics: {e}')

if __name__ == '__main__':
    logger.info('Starting Prometheus exporter...')
    # Start up the server to expose the metrics.
    start_http_server(8000)
    logger.info('Prometheus exporter started on port 8000.')
    # Continuously collect metrics every 60 seconds.
    while True:
        collect_metrics()
        time.sleep(60)
