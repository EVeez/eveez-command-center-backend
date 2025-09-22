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
                # Support both existing and new env var names without breaking changes
                mysql_host = os.getenv('MYSQL_HOST', 'localhost')
                mysql_port = int(os.getenv('MYSQL_PORT', os.getenv('MYSQL_TCP_PORT', 3306)))
                mysql_user = os.getenv('MYSQL_USER', 'root')
                mysql_password = os.getenv('MYSQL_PASSWORD', '1234')
                mysql_db = os.getenv('MYSQL_DB', os.getenv('MYSQL_DATABASE', 'masters'))

                self.mysql_conn = mysql.connector.connect(
                    host=mysql_host,
                    port=mysql_port,
                    user=mysql_user,
                    password=mysql_password,
                    database=mysql_db,
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
                # Support both existing and new env var names without breaking changes
                mongo_uri = os.getenv('MONGODB_URI', os.getenv('MONGODB_URL', 'mongodb://eveeziot:Eveez%24I0T%25@eveez.in:37017/eveezlivedata?authSource=admin'))
                self.mongo_client = MongoClient(mongo_uri)
                mongo_db_name = os.getenv('MONGODB_DB', os.getenv('MONGODB_DATABASE', 'eveezlivedata'))
                self.mongo_db = self.mongo_client[mongo_db_name]
                # Test the connection
                self.mongo_client.admin.command('ping')
                logger.info("MongoDB connection established successfully")
                # Ensure indexes are created
                self.ensure_mongo_indexes()
            return self.mongo_db
        except Exception as e:
            logger.error(f"MongoDB connection error: {str(e)}")
            raise e
    
    def ensure_mongo_indexes(self):
        """Ensure required MongoDB indexes exist for optimal performance"""
        try:
            if self.mongo_db:
                # Create compound index for service_requests analytics
                service_requests = self.mongo_db['service_requests']
                service_requests.create_index([
                    ("date", 1),
                    ("status.done.check", 1),
                    ("location", 1)
                ], background=True)
                logger.info("MongoDB indexes ensured successfully")
        except Exception as e:
            logger.warning(f"Failed to create MongoDB indexes: {str(e)}")
            # Don't raise exception as this is not critical for basic functionality

# Global database instance
db = Database()
