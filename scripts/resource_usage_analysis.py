from pymongo import MongoClient
from bson import ObjectId


class resource_analysis:
    def __init__(self,prom_con_obj,dbname,collection,id1,id2):
        client = MongoClient(prom_con_obj.mongo_connection_string)
        db = client[dbname]  # Replace 'your_database_name' with your actual database name
        self.collection = db[collection]  # Replace 'your_collection_name' with your actual collection name
        self.id1=ObjectId(id1)
        self.id2=ObjectId(id2)
        # {"_id" : ObjectId(id1)}
        



if __name__=='__main__':
    from settings import configuration
    id1=""
    id2=""
    obj = resource_analysis(configuration() , "Osquery_LoadTests","Testing",id1,id2)