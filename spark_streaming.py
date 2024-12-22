from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, DoubleType
from pyspark.sql.functions import col, from_json, when

# Spark oturumunu başlat
spark = SparkSession.builder \
    .appName("Kafka Spark Streaming") \
    .getOrCreate()

# Kafka'dan gelen JSON veriler için şema tanımlaması
schema = StructType([
    StructField("tBodyAcc-mean()-X", DoubleType(), True),
    StructField("tBodyAcc-mean()-Y", DoubleType(), True),
    StructField("tBodyAcc-mean()-Z", DoubleType(), True),
    StructField("tBodyAcc-std()-X", DoubleType(), True),
    StructField("tBodyAcc-std()-Y", DoubleType(), True),
    StructField("tBodyAcc-std()-Z", DoubleType(), True),
])

# Kafka'dan veri oku
input_stream = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "sensor_data") \
    .load()

# Kafka'dan gelen veriyi JSON formatında ayrıştır
parsed_stream = input_stream.selectExpr("CAST(value AS STRING) as json") \
    .select(from_json(col("json"), schema).alias("data")) \
    .select("data.*")

# Anomali tespiti için eşik değerleri
min_threshold = -3.0
max_threshold = 3.0

# Anomaliyi işaretlemek için sütun ekleme
processed_stream = parsed_stream.withColumn(
    "is_anomaly",
    when(
        (col("tBodyAcc-mean()-X") < min_threshold) | (col("tBodyAcc-mean()-X") > max_threshold) |
        (col("tBodyAcc-mean()-Y") < min_threshold) | (col("tBodyAcc-mean()-Y") > max_threshold) |
        (col("tBodyAcc-mean()-Z") < min_threshold) | (col("tBodyAcc-mean()-Z") > max_threshold) |
        (col("tBodyAcc-std()-X") < min_threshold) | (col("tBodyAcc-std()-X") > max_threshold) |
        (col("tBodyAcc-std()-Y") < min_threshold) | (col("tBodyAcc-std()-Y") > max_threshold) |
        (col("tBodyAcc-std()-Z") < min_threshold) | (col("tBodyAcc-std()-Z") > max_threshold),
        True
    ).otherwise(False)
)

# Anomalileri Kafka'ya yaz
anomalies = processed_stream.filter(col("is_anomaly") == True)
anomalies.selectExpr("to_json(struct(*)) AS value").writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("topic", "anomalies") \
    .option("checkpointLocation", "/tmp/checkpoints/anomalies") \
    .start()

# Normal verileri Kafka'ya yaz
normal_data = processed_stream.filter(col("is_anomaly") == False)
normal_data.selectExpr("to_json(struct(*)) AS value").writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("topic", "normal_data") \
    .option("checkpointLocation", "/tmp/checkpoints/normal_data") \
    .start()

# Streaming işlemini başlat ve bekle
spark.streams.awaitAnyTermination()
