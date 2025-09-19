import os
import mysql.connector
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.mysql_conn = None
        self.mongo_client = None
        self.mongo_db = None
    
    def get_mysql_connection(self):
        try:
            if not self.mysql_conn or not self.mysql_conn.is_connected():
                self.mysql_conn = mysql.connector.connect(
                    host=os.getenv('MYSQL_HOST', 'localhost'),
                    port=int(os.getenv('MYSQL_PORT', 3306)),
                    user=os.getenv('MYSQL_USER', 'root'),
                    password=os.getenv('MYSQL_PASSWORD', '1234'),
                    database=os.getenv('MYSQL_DATABASE', 'masters'),
                    autocommit=True
                )
                logger.info("MySQL connection established successfully")
            return self.mysql_conn
        except Exception as e:
            logger.error(f"MySQL connection error: {str(e)}")
            raise e
    
    def get_mongo_database(self):
        try:
            if not self.mongo_client:
                mongo_url = os.getenv('MONGODB_URL', 'mongodb://eveeziot:Eveez%24I0T%25@eveez.in:37017/eveezlivedata?authSource=admin')
                self.mongo_client = MongoClient(mongo_url)
                self.mongo_db = self.mongo_client[os.getenv('MONGODB_DATABASE', 'eveezlivedata')]
                # Test the connection
                self.mongo_client.admin.command('ping')
                logger.info("MongoDB connection established successfully")
            return self.mongo_db
        except Exception as e:
            logger.error(f"MongoDB connection error: {str(e)}")
            raise e

# Global database instance
db = Database()
