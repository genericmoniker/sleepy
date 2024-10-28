# sleepy

**Work in progress**

Sleep data dashboard.

Test using `docker compose up` where docker-compose.yaml will run InfluxDB and
Grafana saving data into volumes.

.env file has secrets, referenced by launch.json. Environment variables are read
in the config.py module.

Fitbit credentials: https://dev.fitbit.com/apps

Google credentials: https://console.cloud.google.com

1. Create a project
2. Add the Google Drive API
3. Create credentials
4. Choose the application type "Web app"
5. Set the redirect URI to http://localhost:8000
