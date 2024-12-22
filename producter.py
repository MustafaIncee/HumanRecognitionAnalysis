from confluent_kafka import Producer
import pandas as pd
import random
import json
import time

# Kafka Producer yapılandırması
producer = Producer({'bootstrap.servers': 'localhost:9092'})

csv_file = "/home/geokdeniz/PycharmProjects/PythonProject1/random_forest_predictions.csv"
dataframe = pd.read_csv(csv_file)


# Sentetik veri üretme
def generate_synthetic_data_from_csv(row, anomaly_rate=0.1):
    synthetic_data = {}
    for column in row.index:
        if column in ['Predicted', 'Actual', 'subject']:
            continue  # Bu sütunları işleme dahil etme

        original_value = row[column]

        # Normal veri üretimi
        if random.random() > anomaly_rate:
            value = original_value + random.uniform(-0.05, 0.05)  # Orijinal değere yakın sapma
        else:
            # Anomali üretimi
            if random.choice([True, False]):
                value = original_value + random.uniform(2.1, 3.0)  # +2.1 ile +3 arasında anomali
            else:
                value = original_value - random.uniform(2.1, 3.0)  # -2.1 ile -3 arasında anomali

        synthetic_data[column] = round(value, 6)  # Veriyi yuvarla ve ekle

    return synthetic_data


# Verileri Kafka'ya gönderme
def send_data_to_kafka(topic, dataframe, anomaly_rate=0.1, num_records=100, interval=1):
    for i in range(num_records):
        # Dataframe'den rastgele bir satır seç
        row = dataframe.sample(1).iloc[0]
        synthetic_data = generate_synthetic_data_from_csv(row, anomaly_rate=anomaly_rate)

        producer.produce(topic, key=str(i), value=json.dumps(synthetic_data))
        producer.flush()
        print(f"Gönderilen veri: {synthetic_data}")
        time.sleep(interval)


# Kafka'ya veri gönderimi
try:
    send_data_to_kafka('sensor_data', dataframe, anomaly_rate=0.1, num_records=100, interval=2)
except KeyboardInterrupt:
    print("Veri gönderimi durduruldu.")
finally:
    producer.flush()

