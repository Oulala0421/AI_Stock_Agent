"""
Script to verify MongoDB data existence
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGODB_URI")
print(f"Connecting to: {uri.split('@')[1]}")  # Hide credentials

client = MongoClient(uri)
db = client['stock_agent']
collection = db['daily_snapshots']

count = collection.count_documents({})
print(f"Total documents: {count}")

if count > 0:
    print("Sample document:")
    print(collection.find_one())
else:
    print("Collection is empty!")
