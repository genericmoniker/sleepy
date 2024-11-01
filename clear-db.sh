#! /bin/bash

# Delete all data from the "sleepy" InfluxDB bucket.

# Usage:

# export API_TOKEN=your_api_token
# ./clear-db.sh

curl -X POST \
  "http://localhost:8086/api/v2/delete?org=sleepy&bucket=sleepy" \
  -H "Authorization: Token ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
        "start": "1970-01-01T00:00:00Z",
        "stop": "2100-01-01T00:00:00Z",
        "predicate": ""
      }'
echo
