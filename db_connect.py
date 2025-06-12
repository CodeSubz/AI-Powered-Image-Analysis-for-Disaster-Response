# db_connect.py

from pymongo import MongoClient

def get_database():
    # Connect to local MongoDB server
    client = MongoClient("mongodb://localhost:27017/")

    # Access the GeoNews database (will auto-create if doesn't exist)
    db = client["GeoNews"]

    return db
