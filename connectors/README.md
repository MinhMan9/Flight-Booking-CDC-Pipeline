# Hướng dẫn kết nối Connector

## Lệnh kích hoạt Source Connector
```bash
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ -d @connectors/debezium-source.json
```
*(Lưu ý: Nhớ chỉnh lại `PASSWORD`, `HOSTNAME` database trong `debezium-source.json` theo trên máy của bạn và các `PORT` nếu cần):*

## Lệnh kích hoạt Sink Connector
```bash
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ -d @connectors/minio-sink.json
```
*(Lưu ý: Nhớ tạo trước `bucket` trên MinIO và điền đúng `tên bucket` trong `minio-sink.json`. Nếu quên thì tạo lại rồi chạy lệnh `curl -X POST localhost:8083/connectors/minio-s3-sink-connector/restart`):*