import os
import argparse
from datetime import datetime
from pyspark.sql import SparkSession

def create_spark_session(run_date):
    """Initialize Spark Session with configurations loaded from spark-defaults.conf inside Docker container."""
    builder = SparkSession.builder.appName(f"FlightBooking_Minio_Loader_{run_date}")
    
    # Iceberg configurations are loaded automatically via spark-defaults.conf of Spark in Docker
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def main():

    
    # Configure to pass date parameter from command line (default to current date)
    parser = argparse.ArgumentParser(description="MinIO to Bronze Loader")
    parser.add_argument(
        "--date", 
        type=str, 
        help="Date to load data (Format: YYYY-MM-DD)", 
        default=datetime.now().strftime("%Y-%m-%d")
    )
    args = parser.parse_args()
    
    run_date = args.date

    # Initialize Spark Session
    spark = create_spark_session(run_date)

    print(f"Starting MinIO to Iceberg Bronze data load process for date: {run_date}")

    tables = ["pnr_records", "passengers", "flight_segments", "tickets", "payments", "booking_events"]


    for table in tables:
        # Update path to only read directory of the requested event_date
        topic_path = f"s3a://datalake/topics/FlightBookingCDC.dbo.{table}/event_date={run_date}/"
        bronze_table = f"demo.bronze.{table}"
        
        print(f"\nReading data from path: {topic_path}")
        try:
            # Read raw parquet data from topic
            raw_df = spark.read.parquet(topic_path)
            
            # Append data to the corresponding Bronze Iceberg table
            raw_df.write.format("iceberg").mode("append").saveAsTable(bronze_table)
            print(f"\033[92mSuccessfully wrote data to Bronze Iceberg table: {bronze_table}\033[0m")
            
        except Exception as e:
            # If there is no data for the day, Spark will throw a Path does not exist error
            print(f"\033[91mFailed to load data for table {table} on date {run_date}. Error details: {str(e)[:100]}...\033[0m")

    print("\n\033[92mCompleted data ingestion from MinIO to Bronze layer!\033[0m")


if __name__ == "__main__":
    main()