
# SimpleMDM Prometheus Exporter

This is a Prometheus exporter for [SimpleMDM](https://simplemdm.com/), allowing you to collect and expose metrics from SimpleMDM for monitoring purposes...

## Features

- Exposes device metrics from SimpleMDM in a format consumable by Prometheus.
- Provides insights into device statuses, profiles, apps, and other important data managed via SimpleMDM.
- Easy to deploy with Docker or directly on a host.

## Installation

To install and set up the SimpleMDM Prometheus Exporter, you can clone the repository and follow the steps below:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/brngates98/SimpleMDM-Prometheus-Exporter.git
   cd SimpleMDM-Prometheus-Exporter
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your SimpleMDM API token as an environment variable:**
   ```bash
   export SIMPLEMDM_API_TOKEN=<your_api_token>
   ```

4. **Run the exporter:**
   ```bash
   python app.py
   ```

## Usage

### Using Docker

You can run the SimpleMDM Prometheus Exporter using Docker:

```bash
docker run -d -e SIMPLEMDM_API_TOKEN=<your_api_token> -p 9110:9110 your-docker-image
```

### Running Locally

To run the exporter directly on your host machine, follow the installation steps above.

### Scraping with Prometheus

To scrape metrics from the SimpleMDM Prometheus Exporter using Prometheus, add the following job to your `prometheus.yml` configuration:

```yaml
scrape_configs:
  - job_name: 'simplemdm-exporterapi'
    static_configs:
      - targets: ['simplemdm-exporter-service.simplemdm.svc.cluster.local:8000']
```

### Scraping with Alloy Agent

To scrape metrics using an Alloy agent, you can use the following `config.alloy` configuration:

```hcl
prometheus.scrape "simplemdm" {
  scrape_timeout    = "60s"
  targets           = [ {"__address__" = "simplemdm-exporter-service.simplemdm.svc.cluster.local:8000"}, ]
  params            = { "target" = ["all"] }
  forward_to        = [prometheus.remote_write.metrics_service.receiver]
  job_name          = "simplemdm-exporterapi"
  metrics_path      = "/"

  clustering { enabled = true } #this is optional, i run alloy in kubernetes as a daemonset so it is useful for me
}

prometheus.remote_write "metrics_service" {
  endpoint {
    url = "https://mimir/api/v1/push"
  }
}
```

Replace `simplemdm-exporter-service.simplemdm.svc.cluster.local:8000` with the actual URL or IP address of the exporter, and `https://mimir/api/v1/push` with the URL of your Mimir instance.

## Metrics

The following metrics are exposed by the SimpleMDM Prometheus Exporter:

| Metric Name                          | Description                                      | Labels                                                      | Label Values                                                   |
|--------------------------------------|--------------------------------------------------|-------------------------------------------------------------|----------------------------------------------------------------|
| `simplemdm_dep_device_count`         | Number of DEP devices per server                 | `dep_server_id`, `dep_server_name`                           | DEP Server ID, DEP Server Name                                 |
| `simplemdm_device_group_device_count`| Number of devices in each device group           | `device_group_id`, `device_group_name`                       | Device Group ID, Device Group Name                             |
| `simplemdm_device_battery`           | Battery level of each device                     | `device_id`, `name`, `simplemdm_name`                        | Device ID, Device Name, SimpleMDM Name                         |
| `simplemdm_latitude`                 | Latitude of each device                          | `device_id`, `name`, `simplemdm_name`                        | Device ID, Device Name, SimpleMDM Name                         |
| `simplemdm_longitude`                | Longitude of each device                         | `device_id`, `name`, `simplemdm_name`                        | Device ID, Device Name, SimpleMDM Name                         |
| `simplemdm_device_info`              | Detailed information about each device           | `device_id`, `name`, `simplemdm_name`, `status`, and more... | Various attributes and relationships of the device             |

## Contributing

Feel free to open issues or submit pull requests to improve the exporter.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
