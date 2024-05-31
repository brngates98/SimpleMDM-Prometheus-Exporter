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
installed_app_count = Gauge('simplemdm_installed_app_count', 'Total number of installed apps for each device', ['device_id', 'device_name', 'app_id', 'app_name'])
app_install_count = Gauge('simplemdm_app_install_count', 'Total number of installs for each app', ['app_id', 'app_name'])
app_type_count = Counter('simplemdm_app_type_count', 'Count of apps by type', ['app_type'])
device_os_version_count = Counter('simplemdm_device_os_version_count', 'Count of devices by OS version', ['os_version'])
enrollment_count = Gauge('simplemdm_enrollment_count', 'Total number of enrollments')
enrollment_user_enrollment = Gauge('simplemdm_enrollment_user_enrollment', 'User enrollment status', ['enrollment_id'])
enrollment_welcome_screen = Gauge('simplemdm_enrollment_welcome_screen', 'Welcome screen status', ['enrollment_id'])
enrollment_authentication = Gauge('simplemdm_enrollment_authentication', 'Authentication status', ['enrollment_id'])
dep_server_count = Gauge('simplemdm_dep_server_count', 'Total number of DEP servers')
dep_server_token_expiry = Gauge('simplemdm_dep_server_token_expiry', 'Token expiry time for DEP server', ['server_id', 'server_name'])
dep_server_last_synced = Gauge('simplemdm_dep_server_last_synced', 'Last synced time for DEP server', ['server_id', 'server_name'])
profile_count = Gauge('simplemdm_profile_count', 'Total number of profiles managed by SimpleMDM')
profile_device_count = Gauge('simplemdm_profile_device_count', 'Total number of devices associated with each profile', ['profile_id', 'profile_name', 'profile_type', 'profile_identifier', 'user_scope', 'group_count', 'reinstall_after_os_update'])
push_certificate_expiry = Gauge('simplemdm_push_certificate_expiry', 'Expiry date of the push certificate', ['apple_id', 'expires_at'])

# Commented out for now: log_event_details = Counter('simplemdm_log_event_details', 'Log event details', ['namespace', 'event_type', 'level', 'source', 'account_id', 'user_id', 'user_email', 'timestamp'])

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

# Function to get DEP servers
def get_dep_servers():
    return fetch_data('dep_servers')

# Function to get push certificate
def get_push_certificate():
    response = requests.get(f'{BASE_URL}/push_certificate', auth=(API_KEY, ''))
    response.raise_for_status()
    return response.json()

# Function to get logs (disabled for now)
# def get_logs():
#     return fetch_data('logs')

# Function to get profiles
def get_profiles():
    return fetch_data('profiles')

# Function to get installed apps for a specific device
def get_installed_apps(device_id):
    endpoint = f'devices/{device_id}/installed_apps'
    return fetch_data(endpoint)

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

        logger.info('Collecting DEP server metrics...')
        dep_servers = get_dep_servers()
        logger.info(f'Collected {len(dep_servers)} DEP servers')

        logger.info('Collecting profile metrics...')
        profiles = get_profiles()
        logger.info(f'Collected {len(profiles)} profiles')

        logger.info('Collecting push certificate metrics...')
        push_certificate = get_push_certificate()
        logger.info(f'Collected push certificate')

        # Commented out for now
        # logger.info('Collecting log metrics...')
        # logs = get_logs()
        # logger.info(f'Collected {len(logs)} log entries')

        device_count.set(len(devices))
        app_count.set(len(apps))
        enrollment_count.set(len(enrollments))
        dep_server_count.set(len(dep_servers))
        profile_count.set(len(profiles))

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

            # Collect installed apps for the device
            installed_apps = get_installed_apps(device_id)
            for app in installed_apps:
                app_id = app['id']
                app_name = app['attributes']['name']
                installed_app_count.labels(device_id=device_id, device_name=device_name, app_id=app_id, app_name=app_name).set(1)

        for app in apps:
            app_id = app['id']
            app_name = app['attributes']['name']
            app_type = app['attributes']['app_type']
            installs = app['attributes'].get('installations_count', 0)
            app_install_count.labels(app_id=app_id, app_name=app_name).set(installs)
            app_type_count.labels(app_type=app_type).inc()

        for server in dep_servers:
            server_id = server['id']
            server_name = server['attributes']['server_name']
            try:
                token_expiry_timestamp = parser.isoparse(server['attributes']['token_expires_at']).timestamp()
                dep_server_token_expiry.labels(server_id=server_id, server_name=server_name).set(token_expiry_timestamp)
            except ValueError as e:
                logger.error(f"Error parsing token expiry date for DEP server {server_id}: {e}")
            try:
                last_synced_timestamp = parser.isoparse(server['attributes']['last_synced_at']).timestamp()
                dep_server_last_synced.labels(server_id=server_id, server_name=server_name).set(last_synced_timestamp)
            except ValueError as e:
                logger.error(f"Error parsing last synced date for DEP server {server_id}: {e}")

        for enrollment in enrollments:
            enrollment_id = enrollment['id']
            user_enrollment = enrollment['attributes']['user_enrollment']
            welcome_screen = enrollment['attributes']['welcome_screen']
            authentication = enrollment['attributes']['authentication']
            enrollment_user_enrollment.labels(enrollment_id=enrollment_id).set(user_enrollment)
            enrollment_welcome_screen.labels(enrollment_id=enrollment_id).set(welcome_screen)
            enrollment_authentication.labels(enrollment_id=enrollment_id).set(authentication)

        for profile in profiles:
            profile_id = profile['id']
            profile_name = profile['attributes']['name']
            profile_type = profile['type']
            profile_identifier = profile['attributes']['profile_identifier']
            user_scope = profile['attributes']['user_scope']
            group_count = profile['attributes']['group_count']
            reinstall_after_os_update = profile['attributes'].get('reinstall_after_os_update', False)
            associated_device_count = profile['attributes']['device_count']
            profile_device_count.labels(
                profile_id=profile_id,
                profile_name=profile_name,
                profile_type=profile_type,
                profile_identifier=profile_identifier,
                user_scope=user_scope,
                group_count=group_count,
                reinstall_after_os_update=reinstall_after_os_update
            ).set(associated_device_count)

        # Push certificate
        apple_id = push_certificate['data']['attributes']['apple_id']
        expires_at_str = push_certificate['data']['attributes']['expires_at']
        expires_at_timestamp = parser.isoparse(expires_at_str).timestamp()
        push_certificate_expiry.labels(apple_id=apple_id, expires_at=expires_at_str).set(expires_at_timestamp)

        # Commented out for now
        # for log in logs:
        #     log_id = log['id']
        #     namespace = log['attributes']['namespace']
        #     event_type = log['attributes']['event_type']
        #     level = log['attributes']['level']
        #     source = log['attributes']['source']
        #     timestamp = log['attributes']['at']
        #     account_id = log['attributes']['relationships']['account']['data']['id'] if 'account' in log['attributes']['relationships'] else 'unknown'
        #     user_id = log['attributes']['relationships']['user']['data']['id'] if 'user' in log['attributes']['relationships'] else 'unknown'
        #     user_email = log['attributes']['relationships']['user']['data']['email'] if 'user' in log['attributes']['relationships'] else 'unknown'
        #     log_event_details.labels(namespace=namespace, event_type=event_type, level=level, source=source, account_id=account_id, user_id=user_id, user_email=user_email, timestamp=timestamp).inc()

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
