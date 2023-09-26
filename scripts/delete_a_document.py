import pymongo
from gridfs import GridFS
from settings import configuration
from bson.objectid import ObjectId

prom_con_obj=configuration()

print("Enter the details to delete a docoment : ")
database_name=input("Enter the database name : ")
collection_name=input("Enter the collection name : ")
document_id=input("Enter the document ID : ")

decision = input("This will delete a document in the database. Are you sure you want to proceed? (y/n) ")

if decision == "y":
    mongo_connection_string=prom_con_obj.mongo_connection_string
    client = pymongo.MongoClient(mongo_connection_string)
    db=client[database_name]
    collection = db[collection_name]
    document=collection.find_one({'_id': ObjectId(document_id)})

    counter=0
    if document:
        print(f"Document found with ID : '{document_id}'")
        all_gridfs_referenced_ids = document.get("all_gridfs_referenced_ids")
        fs = GridFS(db)
        for file_id in all_gridfs_referenced_ids:
            counter+=1
            print(f"{counter} : deleting ", file_id)
            fs.delete(file_id=file_id)
            
        result = collection.delete_one({'_id': ObjectId(document_id)})
        if result.deleted_count == 1:
            print(f"Document with ID '{document_id}' deleted successfully.")
        else:
            print(f"ERROR : No document found with ID '{document_id}'.")
    else:
        print(f"No document found with ID '{document_id}'.")
else:
    print("Exiting ... ")


