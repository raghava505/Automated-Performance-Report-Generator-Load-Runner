import pandas as pd
from pymongo import MongoClient

# Assuming you have a DataFrame named 'df' with multiple index columns
data = {
    'name': ['John', 'Alice', 'Bob'],
    'age': [28, 24, 22],
    'city': ['New York', 'San Francisco', 'Seattle']
}

df = pd.DataFrame(data)
df.set_index(['name', 'age'], inplace=True)  # Example: Using two columns as an index

# Convert DataFrame to a dictionary
data_dict = df.to_dict(orient='index')

# Connect to your MongoDB instance



# Create a sample DataFrame
client = MongoClient('mongodb://localhost:27017/')
db = client['Osquery_LoadTests']  # Replace 'your_database_name' with your actual database name
collection = db['Testing']  # Replace 'your_collection_name' with your actual collection name
# Insert data into MongoDB
collection.insert_one({"haha":data_dict})
