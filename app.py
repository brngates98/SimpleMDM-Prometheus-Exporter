from prometheus_client import start_http_server, Gauge
import time
import requests

API_KEY = 'your_simplemdm_api_key'
BASE_URL = 'https://a.simplemdm.com/api/v1/'

# Basic Authentication using API Key
auth = (API_KEY, '')

# Prometheus metrics
dep_device_count = Gauge('simplemdm_dep_device_count', 'Number of DEP devices per server', ['dep_server_id', 'dep_server_name'])
device_group_device_count = Gauge('simplemdm_device_group_device_count', 'Number of devices in each device group', ['device_group_id', 'device_group_name'])

# Metric for device battery level
device_battery = Gauge(
    'simplemdm_device_battery', 
    'Battery level of each device', 
    ['device_id', 'name', 'simplemdm_name']
)

# Metric for device location
simplemdm_latitude = Gauge(
    'simplemdm_latitude', 
    'Latitude of each device', 
    ['device_id', 'name', 'simplemdm_name']
)
simplemdm_longitude = Gauge(
    'simplemdm_longitude', 
    'Longitude of each device', 
    ['device_id', 'name', 'simplemdm_name']
)

# Metric for device details including all available attributes and relationships
device_info = Gauge(
    'simplemdm_device_info', 
    'Detailed information about each device including its attributes and relationships', 
    [
        'device_id', 'name', 'simplemdm_name', 'status', 'os_version', 'build_version', 'model_name', 'model',
        'product_name', 'unique_identifier', 'serial_number', 'processor_architecture', 
        'imei', 'meid', 'device_capacity', 'available_device_capacity', 
        'modem_firmware_version', 'iccid', 'bluetooth_mac', 'wifi_mac', 'current_carrier_network', 
        'sim_carrier_network', 'subscriber_carrier_network', 'carrier_settings_version', 
        'phone_number', 'voice_roaming_enabled', 'data_roaming_enabled', 'is_roaming', 
        'subscriber_mcc', 'subscriber_mnc', 'simmnc', 'current_mcc', 'current_mnc', 
        'hardware_encryption_caps', 'passcode_present', 'passcode_compliant', 
        'passcode_compliant_with_profiles', 'is_supervised', 'is_dep_enrollment', 
        'is_user_approved_enrollment', 'is_device_locator_service_enabled', 
        'is_do_not_disturb_in_effect', 'personal_hotspot_enabled', 'itunes_store_account_is_active', 
        'cellular_technology', 'last_cloud_backup_date', 'is_activation_lock_enabled', 
        'is_cloud_backup_enabled', 'filevault_enabled', 'filevault_recovery_key', 
        'firmware_password_enabled', 'recovery_lock_password_enabled', 'remote_desktop_enabled', 
        'firmware_password', 'recovery_lock_password', 'managed_apple_id', 'firewall_enabled', 
        'firewall_block_all_incoming', 'firewall_stealth_mode', 'system_integrity_protection_enabled', 
        'os_update_info', 'location_latitude', 'location_longitude', 'location_accuracy',
        'last_seen_at', 'last_seen_ip', 'enrolled_at', 'device_group_id', 'device_group_name',
        'dep_server_id', 'dep_server_name'
    ]
)

# Predefine the custom attributes metric
simplemdm_custom_attributes = Gauge(
    'simplemdm_custom_attributes',
    'Custom attributes of each device',
    ['device_id', 'name', 'simplemdm_name'] + [f'custom_attr_{i}' for i in range(10)]  # Assuming a maximum of 10 custom attributes
)

def create_custom_attributes_metric(device_id, name, simplemdm_name, custom_attributes):
    # Core labels
    labels = {
        'device_id': device_id,
        'name': name,
        'simplemdm_name': simplemdm_name,
    }
    
    # Add custom attributes as additional labels
    for i, (attr_key, attr_value) in enumerate(custom_attributes.items()):
        labels[f'custom_attr_{i}'] = attr_value
    
    # Ensure that any unused custom attribute slots are set to "unknown"
    for i in range(len(custom_attributes), 10):
        labels[f'custom_attr_{i}'] = 'unknown'

    # Set the value for the gauge
    simplemdm_custom_attributes.labels(**labels).set(1)

def fetch_all_pages(endpoint):
    """Fetch all pages for an endpoint, handling pagination."""
    data = []
    params = {'limit': 100}  # Start with a limit of 100
    while True:
        response = requests.get(f'{BASE_URL}{endpoint}', auth=auth, params=params)
        response.raise_for_status()
        result = response.json()
        data.extend(result['data'])
        if not result.get('has_more', False):
            break
        params['starting_after'] = result['data'][-1]['id']  # Use the last object's ID as the cursor
    return data

def fetch_dep_servers():
    return fetch_all_pages('dep_servers')

def fetch_dep_devices(dep_server_id):
    return fetch_all_pages(f'dep_servers/{dep_server_id}/dep_devices')

def fetch_device_groups():
    return fetch_all_pages('device_groups')

def fetch_device_details(device_id):
    response = requests.get(f'{BASE_URL}devices/{device_id}', auth=auth)
    response.raise_for_status()
    return response.json()

def collect_metrics():
    # Fetch all device groups to map group_id to group_name
    device_groups_response = fetch_device_groups()
    group_mapping = {group['id']: group['attributes']['name'] for group in device_groups_response}
    
    # Initialize device group metrics
    for group_id, group_name in group_mapping.items():
        device_group_device_count.labels(device_group_id=group_id, device_group_name=group_name).set(0)
    
    # DEP devices per server
    dep_servers = fetch_dep_servers()
    for server in dep_servers:
        dep_server_id = server['id']
        dep_server_name = server['attributes']['server_name']
        dep_devices = fetch_dep_devices(dep_server_id)
        
        # Set the total number of devices for the DEP server
        dep_device_count.labels(dep_server_id, dep_server_name).set(len(dep_devices))

        # For each device, fetch details and expose as metrics
        for device in dep_devices:
            device_id = device['relationships']['device']['data']['id']
            device_details = fetch_device_details(device_id)

            # Extract attributes
            attributes = device_details['data']['attributes']
            relationships = device_details['data']['relationships']
            
            # Fetch device group information
            group_info = relationships.get('device_group', {}).get('data', {})
            group_id = group_info.get('id', 'unknown')
            group_name = group_mapping.get(group_id, 'Unknown Group')

            # Custom attributes
            custom_attributes = relationships.get('custom_attribute_values', {}).get('data', [])
            custom_attributes_dict = {attr['id']: attr['attributes']['value'] for attr in custom_attributes}

            # Create the custom attributes metric
            create_custom_attributes_metric(device_id, attributes.get('name', 'unknown'), attributes.get('device_name', 'unknown'), custom_attributes_dict)

            # OS update information
            os_update_info = attributes.get('os_update', {})
            os_update_label = ','.join(
                f"{key}={value}" for key, value in os_update_info.items() if value is not None
            )

            # Firewall attributes
            firewall_info = attributes.get('firewall', {})
            firewall_enabled = firewall_info.get('enabled', 'unknown')
            firewall_block_all_incoming = firewall_info.get('block_all_incoming', 'unknown')
            firewall_stealth_mode = firewall_info.get('stealth_mode', 'unknown')

            # Battery level metric
            battery_level = attributes.get('battery_level', 'unknown')
            if battery_level is not None and battery_level != 'unknown' and battery_level.endswith('%'):
                battery_level = float(battery_level.rstrip('%'))
                device_battery.labels(
                    device_id=device_id,
                    name=attributes.get('name', 'unknown'),
                    simplemdm_name=attributes.get('device_name', 'unknown')
                ).set(battery_level)

            # Set the location metrics
            latitude = attributes.get('location_latitude', None)
            longitude = attributes.get('location_longitude', None)
            if latitude is not None:
                simplemdm_latitude.labels(
                    device_id=device_id,
                    name=attributes.get('name', 'unknown'),
                    simplemdm_name=attributes.get('device_name', 'unknown')
                ).set(float(latitude))
            if longitude is not None:
                simplemdm_longitude.labels(
                    device_id=device_id,
                    name=attributes.get('name', 'unknown'),
                    simplemdm_name=attributes.get('device_name', 'unknown')
                ).set(float(longitude))

            # Increment device count in the group
            if group_id != 'unknown':
                device_group_device_count.labels(device_group_id=group_id, device_group_name=group_name).inc()

            # Set the device_info metric with DEP server info and simplemdm_name included
            device_info.labels(
                device_id=device_id,
                name=attributes.get('name', 'unknown'),
                simplemdm_name=attributes.get('device_name', 'unknown'),
                status=attributes.get('status', 'unknown'),
                os_version=attributes.get('os_version', 'unknown'),
                build_version=attributes.get('build_version', 'unknown'),
                model_name=attributes.get('model_name', 'unknown'),
                model=attributes.get('model', 'unknown'),
                product_name=attributes.get('product_name', 'unknown'),
                unique_identifier=attributes.get('unique_identifier', 'unknown'),
                serial_number=attributes.get('serial_number', 'unknown'),
                processor_architecture=attributes.get('processor_architecture', 'unknown'),
                imei=attributes.get('imei', 'unknown'),
                meid=attributes.get('meid', 'unknown'),
                device_capacity=attributes.get('device_capacity', 'unknown'),
                available_device_capacity=attributes.get('available_device_capacity', 'unknown'),
                modem_firmware_version=attributes.get('modem_firmware_version', 'unknown'),
                iccid=attributes.get('iccid', 'unknown'),
                bluetooth_mac=attributes.get('bluetooth_mac', 'unknown'),
                wifi_mac=attributes.get('wifi_mac', 'unknown'),
                current_carrier_network=attributes.get('current_carrier_network', 'unknown'),
                sim_carrier_network=attributes.get('sim_carrier_network', 'unknown'),
                subscriber_carrier_network=attributes.get('subscriber_carrier_network', 'unknown'),
                carrier_settings_version=attributes.get('carrier_settings_version', 'unknown'),
                phone_number=attributes.get('phone_number', 'unknown'),
                voice_roaming_enabled=str(attributes.get('voice_roaming_enabled', 'unknown')),
                data_roaming_enabled=str(attributes.get('data_roaming_enabled', 'unknown')),
                is_roaming=str(attributes.get('is_roaming', 'unknown')),
                subscriber_mcc=attributes.get('subscriber_mcc', 'unknown'),
                subscriber_mnc=attributes.get('subscriber_mnc', 'unknown'),
                simmnc=attributes.get('simmnc', 'unknown'),
                current_mcc=attributes.get('current_mcc', 'unknown'),
                current_mnc=attributes.get('current_mnc', 'unknown'),
                hardware_encryption_caps=attributes.get('hardware_encryption_caps', 'unknown'),
                passcode_present=str(attributes.get('passcode_present', 'unknown')),
                passcode_compliant=str(attributes.get('passcode_compliant', 'unknown')),
                passcode_compliant_with_profiles=str(attributes.get('passcode_compliant_with_profiles', 'unknown')),
                is_supervised=str(attributes.get('is_supervised', 'unknown')),
                is_dep_enrollment=str(attributes.get('is_dep_enrollment', 'unknown')),
                is_user_approved_enrollment=str(attributes.get('is_user_approved_enrollment', 'unknown')),
                is_device_locator_service_enabled=str(attributes.get('is_device_locator_service_enabled', 'unknown')),
                is_do_not_disturb_in_effect=str(attributes.get('is_do_not_disturb_in_effect', 'unknown')),
                personal_hotspot_enabled=str(attributes.get('personal_hotspot_enabled', 'unknown')),
                itunes_store_account_is_active=str(attributes.get('itunes_store_account_is_active', 'unknown')),
                cellular_technology=attributes.get('cellular_technology', 'unknown'),
                last_cloud_backup_date=attributes.get('last_cloud_backup_date', 'unknown'),
                is_activation_lock_enabled=str(attributes.get('is_activation_lock_enabled', 'unknown')),
                is_cloud_backup_enabled=str(attributes.get('is_cloud_backup_enabled', 'unknown')),
                filevault_enabled=str(attributes.get('filevault_enabled', 'unknown')),
                filevault_recovery_key=attributes.get('filevault_recovery_key', 'unknown'),
                firmware_password_enabled=str(attributes.get('firmware_password_enabled', 'unknown')),
                recovery_lock_password_enabled=str(attributes.get('recovery_lock_password_enabled', 'unknown')),
                remote_desktop_enabled=str(attributes.get('remote_desktop_enabled', 'unknown')),
                firmware_password=attributes.get('firmware_password', 'unknown'),
                recovery_lock_password=attributes.get('recovery_lock_password', 'unknown'),
                managed_apple_id=attributes.get('managed_apple_id', 'unknown'),
                firewall_enabled=str(firewall_enabled),
                firewall_block_all_incoming=str(firewall_block_all_incoming),
                firewall_stealth_mode=str(firewall_stealth_mode),
                system_integrity_protection_enabled=str(attributes.get('system_integrity_protection_enabled', 'unknown')),
                os_update_info=os_update_label,
                location_latitude=attributes.get('location_latitude', 'unknown'),
                location_longitude=attributes.get('location_longitude', 'unknown'),
                location_accuracy=attributes.get('location_accuracy', 'unknown'),
                last_seen_at=attributes.get('last_seen_at', 'unknown'),
                last_seen_ip=attributes.get('last_seen_ip', 'unknown'),
                enrolled_at=attributes.get('enrolled_at', 'unknown'),
                device_group_id=group_id,
                device_group_name=group_name,
                dep_server_id=dep_server_id,
                dep_server_name=dep_server_name
            ).set(1)  # Setting this to 1 just to register the gauge metric for this device

if __name__ == '__main__':
    # Start up the server to expose the metrics
    start_http_server(8000)
    while True:
        collect_metrics()
        time.sleep(60)  # Fetch and expose metrics every 60 seconds
