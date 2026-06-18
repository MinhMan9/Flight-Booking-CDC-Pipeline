# Hướng dẫn kết nối Connector

## Lệnh kích hoạt Debezium
```bash
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/ -d @connectors/debezium-source.json
```
*(Lưu ý: Nhớ chỉnh lại `PASSWORD`, `HOSTNAME` database theo trên máy của bạn và các `PORT` nếu cần):*