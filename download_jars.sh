#!/bin/bash

set -e

# Ensure spark/jars and monitoring directories exist
mkdir -p ./spark/jars ./monitoring

# 1. hadoop-aws-3.3.4.jar (Spark access to MinIO)
if [ ! -f ./spark/jars/hadoop-aws-3.3.4.jar ]; then
  echo "Downloading hadoop-aws jar..."
  curl -L -o ./spark/jars/hadoop-aws-3.3.4.jar https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar
else
  echo "hadoop-aws jar already exists. Skipping download."
fi

# 2. aws-java-sdk-bundle-1.12.262.jar (AWS's Java SDK for interacting with S3)
if [ ! -f ./spark/jars/aws-java-sdk-bundle-1.12.262.jar ]; then
  echo "Downloading aws-java-sdk-bundle jar..."
  curl -L -o ./spark/jars/aws-java-sdk-bundle-1.12.262.jar https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar
else
  echo "aws-java-sdk-bundle jar already exists. Skipping download."
fi

# 3. mssql-jdbc-12.4.2.jre11.jar (Spark access to SQl Server)
if [ ! -f ./spark/jars/mssql-jdbc-12.4.2.jre11.jar ]; then
  echo "Downloading mssql-jdbc jar..."
  curl -L -o ./spark/jars/mssql-jdbc-12.4.2.jre11.jar https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/12.4.2.jre11/mssql-jdbc-12.4.2.jre11.jar
else
  echo "mssql-jdbc jar already exists. Skipping download."
fi

# 4. jmx_prometheus_javaagent-0.19.0.jar (Java agent collect and export metrics to Prometheus)
if [ ! -f ./monitoring/jmx_prometheus_javaagent-0.19.0.jar ]; then
  echo "Downloading jmx_prometheus_javaagent jar..."
  curl -L -o ./monitoring/jmx_prometheus_javaagent-0.19.0.jar https://repo1.maven.org/maven2/io/prometheus/jmx/jmx_prometheus_javaagent/0.19.0/jmx_prometheus_javaagent-0.19.0.jar
else
  echo "jmx_prometheus_javaagent jar already exists. Skipping download."
fi
