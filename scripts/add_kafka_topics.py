from config_vars import *
from kafka import KafkaAdminClient

# consumer_groups = admin_client.list_consumer_groups()
# print(consumer_groups)

# for topic in topics:
#     topic_description = admin_client.describe_topics(topic)
#     print(topic_description)

class kafka_topics:
    def __init__(self,stack_obj):
        self.stack_obj = stack_obj
        self.pnode = self.stack_obj.execute_kafka_topics_script_in
        
    def add_topics_to_report(self):
        try:
            self.bootstrap_server = f'{self.pnode}:9092'
            admin_client = KafkaAdminClient(bootstrap_servers=self.bootstrap_server)
            topics= list(sorted(admin_client.list_topics()))
            self.stack_obj.log.info(f"Kafka topics found are : {topics}")

            return {"format":"list",
                    "schema":{},
                    "data":topics
                    }
            
        except Exception as e:
            self.stack_obj.log.error(f"Error while fetching kafka topics : {str(e)}")
            return None

if __name__ == "__main__":
    class StackObject:
        def __init__(self):
            self.execute_kafka_topics_script_in = None  # This will hold the value 's1c1pn1'

    stack_obj = StackObject()
    stack_obj.execute_kafka_topics_script_in = "s1c1pn1"

    kaf = kafka_topics(stack_obj)
    print(kaf.add_topics_to_report())
