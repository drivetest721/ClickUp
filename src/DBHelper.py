import mysql.connector
from mysql.connector import Error
import json
import re
from datetime import datetime

"""
    assignee can be null
    
"""
    
class CDBHelper:
    
    # Database connection details
    DATABASE_NAME = 'DBClickUp'
    DATABASE_USER = 'root'
    DATABASE_PASSWORD_DEV = 'riveredge'
    DATABASE_URL_DEV = 'localhost'
    DATABASE_PORT = 3306
    
    @staticmethod
    def MSCreateServerConnection():
        # Connect to MySQL Server (without specifying the database)
        try:
            connection = mysql.connector.connect(
                host=CDBHelper.DATABASE_URL_DEV,
                user=CDBHelper.DATABASE_USER,
                password=CDBHelper.DATABASE_PASSWORD_DEV,
                database=CDBHelper.DATABASE_NAME,
                port=CDBHelper.DATABASE_PORT
            )
            if connection.is_connected():
                print("Successfully connected to MySQL server")
            return connection
        except Error as e:
            print(f"Error: {e}")
            return None
    
    @staticmethod
    def MSCreateDatabaseAndTables():
        # Create the database and table
        try:
            connection = CDBHelper.MSCreateServerConnection()
            cursor = connection.cursor()

            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {CDBHelper.DATABASE_NAME}")
            print(f"Database `{CDBHelper.DATABASE_NAME}` created or already exists.")

            # Switch to the new database
            cursor.execute(f"USE {CDBHelper.DATABASE_NAME}")

            # Create table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS ClickUpList (
                ListName VARCHAR(255),
                ListID VARCHAR(255),
                FolderName VARCHAR(255),
                SpaceID VARCHAR(255),
                TaskID VARCHAR(255) PRIMARY KEY,
                TaskSubject VARCHAR(255),
                TaskStartDate VARCHAR(255),
                TaskDueDate VARCHAR(255),
                ParentTaskID VARCHAR(255),
                EstimatedTime JSON,
                TaskPriority JSON,
                TaskStatus JSON,
                AssignByPersonDetails JSON,
                TaskAssigneesList JSON,
                WatchersList JSON,
                TaskCreatedDate VARCHAR(255),
                TaskUpdateDate VARCHAR(255),
                TaskDateClosed VARCHAR(255),
                TaskDateDone VARCHAR(255),
                TaskTags JSON,
                TaskDependencies JSON,
                TaskIsMilestone BOOLEAN DEFAULT FALSE,
                TaskIntensity INT DEFAULT 0,
                TaskCheckLists JSON
            );
            """
            cursor.execute(create_table_query)
            print("Table `ClickUpList` created or already exists.")

        except Error as e:
            print(f"Error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

  
# Example usage
if __name__ == "__main__":
    pass
    # CDBHelper.MSCreateDatabaseAndTables()
    # Sample data to insert or update