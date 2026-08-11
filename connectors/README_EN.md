# Connector Configuration Guide

## Command to Register Source Connector
```bash
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ -d @connectors/debezium-source.json
```
*(Note: Remember to update the database `PASSWORD` and `HOSTNAME` inside `debezium-source.json` according to your local setup, as well as `PORT` if necessary).*

## Command to Register Sink Connector
```bash
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ -d @connectors/minio-sink.json
```
*(Note: Remember to create the `bucket` on MinIO beforehand and enter the correct `bucket name` in `minio-sink.json`. If you forget, create the bucket and restart the connector using: `curl -X POST localhost:8083/connectors/minio-s3-sink-connector/restart`).*

## Command to Check Connector Status
```bash
curl -s localhost:8083/connectors/sqlserver-flightbooking-connector/status | jq 
```

## Command to Delete Connector
```bash
curl -X DELETE http://localhost:8083/connectors/sqlserver-flightbooking-connector
```
