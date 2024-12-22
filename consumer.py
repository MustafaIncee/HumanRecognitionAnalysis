from confluent_kafka import Consumer, Producer
import json

# Kafka Consumer yapılandırması
consumer_config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'activity_anomaly_group',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(consumer_config)

# Kafka Producer yapılandırması
producer = Producer({'bootstrap.servers': 'localhost:9092'})

# Topic isimleri
input_topic = 'sensor_data'
normal_data_topic = 'normal_data'
anomalies_topic = 'anomalies'


# Anomali tespiti fonksiyonu
def detect_anomaly(data):
    anomalies = {}
    for key, value in data.items():
        if isinstance(value, (int, float)) and not (-5.0 <= value <= 6.0):  # Min-Max kontrolü
            anomalies[key] = value
    return anomalies


# Veriyi işleme ve uygun topic'e gönderme
def process_and_forward_messages():
    consumer.subscribe([input_topic])

    try:
        while True:
            msg = consumer.poll(1.0)  # Mesajı 1 saniye bekle

            if msg is None:
                continue
            if msg.error():
                print(f"Hata: {msg.error()}")
                continue

            record = json.loads(msg.value().decode('utf-8'))
            print(f"Gelen veri: {record}")

            # Anomali tespiti
            anomalies = detect_anomaly(record)
            if anomalies:
                record['anomalies'] = anomalies
                print(f"[ANOMALİ] Tespit edilen veri:")
                for key, value in anomalies.items():
                    print(f"  {key}: {value} (ANOMALİ)")

                producer.produce(anomalies_topic, value=json.dumps(record))
            else:
                print(f"[NORMAL] Veri: {record}")
                producer.produce(normal_data_topic, value=json.dumps(record))

            producer.flush()

    except KeyboardInterrupt:
        print("Consumer durduruldu.")
    finally:
        consumer.close()


# Tüketici başlatma
if __name__ == '__main__':
    process_and_forward_messages()
