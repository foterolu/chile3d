from pymongo import MongoClient
from dotenv import dotenv_values
from config.initial_data import admins,institution_documents

config = dotenv_values(".env")
MONGO_STRING_CONECTION = config["MONGO_STRING_CONECTION"]
DB_NAME = config["DB_NAME"]
DB_NAME = config["DB_NAME"]
USERNAME = config["MONGO_INITDB_ROOT_USERNAME"]
PASSWORD = config["MONGO_INITDB_ROOT_PASSWORD"]

if USERNAME and PASSWORD:
    mongodb_client = MongoClient(MONGO_STRING_CONECTION
    ,username=USERNAME
    ,password=PASSWORD)
    
else:
    mongodb_client = MongoClient(MONGO_STRING_CONECTION)
# print(mongodb_client, DB_NAME)
if DB_NAME not in mongodb_client.list_database_names():
    database = mongodb_client[config["DB_NAME"]]
database = mongodb_client[DB_NAME]

#load admin initial from admin_collection.json if admin collection not exists

if "admin" not in database.list_collection_names():
    database.create_collection("admin")
    database["admin"].insert_many(admins)

if "institucion" not in database.list_collection_names():
    database.create_collection("institucion")
    database["institucion"].insert_many(institution_documents)




