from kafka import KafkaAdminClient,KafkaConsumer
bootstrap_servers = 'localhost:9092'
admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
topics= admin_client.list_topics()
topics.sort()
for i in topics:
    print(i)
# print(len(topics))
# consumer_groups = admin_client.list_consumer_groups()
# print(consumer_groups)

# for topic in topics:
#     topic_description = admin_client.describe_topics(topic)
#     print(topic_description)