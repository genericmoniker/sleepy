# sleepy

**Work in progress**

Sleep data dashboard.

Test using `docker compose up` where docker-compose.yaml will run InfluxDB and
Grafana saving data into volumes.

.env file has secrets, referenced by launch.json. Environment variables are read
in the config.py module.
