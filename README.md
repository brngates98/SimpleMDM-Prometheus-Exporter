# SimpleMDM Prometheus Exporter

This Python application collects metrics from the SimpleMDM API and exposes them to Prometheus. It gathers information about devices, apps, enrollments, DEP servers, installed apps, and profiles, providing detailed insights into your SimpleMDM-managed environment.

## Features

- Collects metrics for devices, apps, enrollments (including attributes), DEP servers, installed apps, and profiles.
- Exposes these metrics to Prometheus for monitoring and alerting.
- Provides detailed labels for each metric to allow for comprehensive filtering and analysis.

## Installation

1. Clone this repository:

    ```bash
    git clone https://github.com/brngates98/simplemdm-prometheus-exporter.git
    cd simplemdm-prometheus-exporter
    ```

2. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

3. Replace the placeholder `API_KEY` with your actual SimpleMDM API key in the script.

## Usage

1. Start the Prometheus exporter:

    ```bash
    python simplemdm_exporter.py
    ```

2. The exporter will start a web server on port `8000` to expose the metrics.

3. Configure Prometheus to scrape metrics from this exporter by adding the following job to your `prometheus.yml` configuration file:

    ```yaml
    scrape_configs:
      - job_name: 'simplemdm'
        static_configs:
          - targets: ['localhost:8000']
    ```

## Available Metrics and Labels

### Device Metrics

- **`simplemdm_device_count`**: Total number of devices managed by SimpleMDM.

- **`simplemdm_device_last_seen`**: Timestamp of the last seen device.
  - Labels:
    - `device_id`: ID of the device.
    - `device_name`: Name of the device.
    - `os_version`: OS version of the device.
    - `build_version`: Build version of the device.
    - `simplemdm_name`: SimpleMDM name of the device.

- **`simplemdm_device_enrollment_status`**: Enrollment status of the device.
  - Labels:
    - `device_id`: ID of the device.
    - `device_name`: Name of the device.
    - `os_version`: OS version of the device.
    - `build_version`: Build version of the device.
    - `simplemdm_name`: SimpleMDM name of the device.

### App Metrics

- **`simplemdm_app_count`**: Total number of apps managed by SimpleMDM.

- **`simplemdm_app_install_count`**: Total number of installs for each app.
  - Labels:
    - `app_id`: ID of the app.
    - `app_name`: Name of the app.

- **`simplemdm_app_type_count`**: Count of apps by type.
  - Labels:
    - `app_type`: Type of the app.

### Enrollment Metrics

- **`simplemdm_enrollment_count`**: Total number of enrollments.

- **`simplemdm_enrollment_user_enrollment`**: User enrollment status.
  - Labels:
    - `enrollment_id`: ID of the enrollment.
  - Values:
    - `1`: User enrollment enabled.
    - `0`: User enrollment disabled.

- **`simplemdm_enrollment_welcome_screen`**: Welcome screen status.
  - Labels:
    - `enrollment_id`: ID of the enrollment.
  - Values:
    - `1`: Welcome screen enabled.
    - `0`: Welcome screen disabled.

- **`simplemdm_enrollment_authentication`**: Authentication status.
  - Labels:
    - `enrollment_id`: ID of the enrollment.
  - Values:
    - `1`: Authentication enabled.
    - `0`: Authentication disabled.

### DEP Server Metrics

- **`simplemdm_dep_server_count`**: Total number of DEP servers.

- **`simplemdm_dep_server_token_expiry`**: Token expiry time for DEP server.
  - Labels:
    - `server_id`: ID of the DEP server.
    - `server_name`: Name of the DEP server.

- **`simplemdm_dep_server_last_synced`**: Last synced time for DEP server.
  - Labels:
    - `server_id`: ID of the DEP server.
    - `server_name`: Name of the DEP server.

### Profile Metrics

- **`simplemdm_profile_count`**: Total number of profiles managed by SimpleMDM.

- **`simplemdm_profile_device_count`**: Total number of devices associated with each profile.
  - Labels:
    - `profile_id`: ID of the profile.
    - `profile_name`: Name of the profile.
    - `profile_type`: Type of the profile.
    - `profile_identifier`: Identifier of the profile.
    - `user_scope`: User scope status.
    - `group_count`: Number of groups associated with the profile.
    - `reinstall_after_os_update`: Reinstall after OS update status.

### Installed App Metrics

- **`simplemdm_installed_app_count`**: Total number of installed apps for each device.
  - Labels:
    - `device_id`: ID of the device.
    - `device_name`: Name of the device.
    - `app_id`: ID of the installed app.
    - `app_name`: Name of the installed app.

## License

This project is licensed under the GPL 3.0 License. See the `LICENSE` file for details.
