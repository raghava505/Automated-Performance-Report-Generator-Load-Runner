import pymongo
# from gridfs import GridFS
from settings import configuration
from bson.objectid import ObjectId
import shutil,os

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
        # all_gridfs_referenced_ids = document.get("all_gridfs_referenced_ids")
        # fs = GridFS(db)
        # for file_id in all_gridfs_referenced_ids:
        #     counter+=1
        #     print(f"{counter} : deleting ", file_id)
        #     fs.delete(file_id=file_id)
            
        result = collection.delete_one({'_id': ObjectId(document_id)})
        BASE_GRAPHS_PATH = os.path.join(os.path.dirname(prom_con_obj.ROOT_PATH),'graphs')
        graphs_path=f"{BASE_GRAPHS_PATH}/{database_name}/{collection_name}/{document_id}"
        BASE_PDFS_PATH = os.path.join(os.path.dirname(prom_con_obj.ROOT_PATH),'pdfs')
        pdfs_path=f"{BASE_PDFS_PATH}/{database_name}/{collection_name}/{document_id}"
        BASE_HTMLS_PATH = os.path.join(os.path.dirname(prom_con_obj.ROOT_PATH),'htmls')
        htmls_path=f"{BASE_HTMLS_PATH}/{database_name}/{collection_name}/{document_id}"
        try:
            shutil.rmtree(graphs_path)
            print(f"Folder deleted: {graphs_path}")
            try:
                shutil.rmtree(pdfs_path)
                print(f"Folder deleted: {pdfs_path}")
            except FileNotFoundError:
                print(f"Folder not found: {pdfs_path}")
            try:
                shutil.rmtree(htmls_path)
                print(f"Folder deleted: {htmls_path}")
            except FileNotFoundError:
                print(f"Folder not found: {htmls_path}")
            except Exception as e:
                print(f"An error occurred while deleting the folders: {e}")
        except FileNotFoundError:
            print(f"Folder not found: {graphs_path}")
        except Exception as e:
            print(f"An error occurred while deleting the folders: {e}")
        if result.deleted_count == 1:
            print(f"Document with ID '{document_id}' deleted successfully.")
        else:
            print(f"ERROR : delete count not equal to 1 '{document_id}'.")
    else:
        print(f"No document found with ID '{document_id}'.")
else:
    print("Exiting ... ")


