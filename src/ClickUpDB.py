import mysql.connector
from mysql.connector import Error
import json
import re
import os
import pandas as pd
from datetime import datetime
from DBHelper import CDBHelper
from ClickUpHelper import CClickUpHelper
"""
    assignee can be null
    
"""
class CClickUpDB:

    @staticmethod
    def MSReadTasKByID(task_id):
        # Read data from ClickUpList table
        try:
            connection = CDBHelper.MSCreateServerConnection()
            cursor = connection.cursor(dictionary=True)

            sql = "SELECT * FROM ClickUpList WHERE TaskID = %s"
            cursor.execute(sql, (task_id,))

            result = cursor.fetchall()
            return result

        except Error as e:
            print(f"Error: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @staticmethod
    def MSInsertORUpdateTask(data):
        try:
            connection =  CDBHelper.MSCreateServerConnection()
            cursor = connection.cursor()

            # Check if the task ID already exists
            check_sql = "SELECT COUNT(*) FROM ClickUpList WHERE TaskID = %s"
            cursor.execute(check_sql, (data['id'],))
            result = cursor.fetchone()

            # Extracting values and converting complex types to strings
            list_name = data['list'].get('name', '')
            list_id = data['list'].get('id', '')
            folder_name = data['folder'].get('name', '')
            space_id = data['space'].get('id', '')
            task_subject = data.get('name', '')
            start_date = CClickUpHelper.MSConvertTimeStampToDate(data.get('start_date', None))
            due_date = CClickUpHelper.MSConvertTimeStampToDate(data.get('due_date', None))
            parent_task_id = data.get('parent', '')
            estimated_time = json.dumps(CClickUpHelper.MSConvertMilliSecondsToHrs(data.get('time_estimate', 0)))
            task_priority = json.dumps(data['priority'])
            task_status = json.dumps(data['status'])
            creator_name = json.dumps(data['creator'])
            task_assignees_list = json.dumps(data.get('assignees', []))  # Convert list to JSON string
            task_assignee_email_id = CClickUpHelper.get1stAssigneeEmailId(dictTaskAssigneeDetails=data.get('assignees', None))
            watchers_list = json.dumps(data.get('watchers', []))  # Convert list to JSON string
            task_created_date = CClickUpHelper.MSConvertTimeStampToDate(data.get('date_created', None), format='%d-%m-%Y %H:%M:%S')
            task_update_date = CClickUpHelper.MSConvertTimeStampToDate(data.get('date_updated', None),format='%d-%m-%Y %H:%M:%S')
            task_date_closed = CClickUpHelper.MSConvertTimeStampToDate(data.get('date_closed', None),format='%d-%m-%Y %H:%M:%S')
            task_date_done = CClickUpHelper.MSConvertTimeStampToDate(data.get('date_done', None),format='%d-%m-%Y %H:%M:%S')
            task_tags = json.dumps(data.get('tags', []))  # Convert list to JSON string
            task_dependencies = json.dumps(data.get('dependencies', []))  # Convert list to JSON string
            task_is_milestone = CClickUpHelper.MSIsTaskMileStone(task_subject)
            task_intensity = CClickUpHelper.MSGetTaskIntensity(task_subject)
            TaskCheckLists = json.dumps(data.get('checklists',None))
            task_color_details =None #json.dumps(CClickUpDB.MSGetTaskColorDetails(data.get('priority'), data['status']))
            if result[0] > 0:
                # Update the existing entry
                update_sql = """
                UPDATE ClickUpList
                SET ListName = %s, ListID = %s, FolderName = %s, SpaceID = %s,
                    TaskSubject = %s, TaskStartDate = %s, TaskDueDate = %s, ParentTaskID = %s,
                    EstimatedTime = %s, TaskPriority = %s, TaskStatus = %s,
                    AssignByPersonDetails = %s, TaskAssigneesList = %s, WatchersList = %s,
                    TaskCreatedDate = %s, TaskUpdateDate = %s, TaskDateClosed = %s,
                    TaskDateDone = %s, TaskTags = %s, TaskDependencies = %s,
                    TaskIsMilestone = %s, TaskIntensity = %s, TaskCheckLists = %s, TaskAssigneeEmailId=%s
                WHERE TaskID = %s
                """
                update_values = (
                    list_name, list_id, folder_name, space_id, task_subject, start_date, due_date, parent_task_id,
                    estimated_time, task_priority, task_status, creator_name, task_assignees_list, watchers_list,
                    task_created_date, task_update_date, task_date_closed, task_date_done, task_tags, task_dependencies,
                    task_is_milestone, task_intensity, TaskCheckLists, task_assignee_email_id, data['id']
                )
                cursor.execute(update_sql, update_values)
                print(f"TaskID {data['id']} updated successfully.")
            else:
                # Insert a new entry
                insert_sql = """
                INSERT INTO ClickUpList (
                    ListName, ListID, FolderName, SpaceID, TaskID, TaskSubject,
                    TaskStartDate, TaskDueDate, ParentTaskID, EstimatedTime, TaskPriority,
                    TaskStatus, AssignByPersonDetails, TaskAssigneesList, WatchersList,
                    TaskCreatedDate, TaskUpdateDate, TaskDateClosed, TaskDateDone,
                    TaskTags, TaskDependencies, TaskIsMilestone, TaskIntensity, TaskCheckLists, TaskAssigneeEmailId
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                insert_values = (
                    list_name, list_id, folder_name, space_id, data['id'], task_subject, start_date, due_date,
                    parent_task_id, estimated_time, task_priority, task_status, creator_name, task_assignees_list,
                    watchers_list, task_created_date, task_update_date, task_date_closed, task_date_done,
                    task_tags, task_dependencies, task_is_milestone, task_intensity, TaskCheckLists,task_assignee_email_id
                )
                cursor.execute(insert_sql, insert_values)
                print(f"TaskID {data['id']} inserted successfully.")
            
            connection.commit()

        except Error as e:
            print(f"Error: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    
    @staticmethod
    def MSGetTasksByListIDs(list_id, start_date, end_date):
        """
        Retrieves tasks from ClickUpList based on ListID, TaskStartDate, and TaskDueDate.

        :param list_id: The ID of the list to filter tasks.
        :param start_date: The start date (inclusive) in 'YYYY-MM-DD' format.
        :param end_date: The due date (inclusive) in 'YYYY-MM-DD' format.
        :return: A list of dictionaries representing the tasks.
        """
        try:
            connection = CDBHelper.MSCreateServerConnection()
            cursor = connection.cursor(dictionary=True)  # Fetch results as dictionaries

            # Use the specified database
            cursor.execute(f"USE {CDBHelper.DATABASE_NAME}")
            placeholders = ', '.join(['%s'] * len(list_id))  # Create a placeholder for each ListID
            # Define the query with parameter placeholders
            query = f"""
                SELECT *
                FROM ClickUpList
                WHERE ListID IN ({placeholders})
                AND STR_TO_DATE(TaskStartDate, '%d-%m-%Y') >= STR_TO_DATE(%s, '%d-%m-%Y')
                AND STR_TO_DATE(TaskDueDate, '%d-%m-%Y') <= STR_TO_DATE(%s, '%d-%m-%Y')
            """
            params = list_id + [start_date, end_date]  # Combine list of ListIDs with other parameters

            # Execute the query using a database cursor
            cursor.execute(query, params)

            # Fetch all matching records
            tasks = cursor.fetchall()

            print(f"Retrieved {len(tasks)} task(s) from ListID {list_id} between {start_date} and {end_date}.")
            return tasks

        except Error as e:
            print(f"Error while fetching tasks: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    @staticmethod
    def MSGetTasksByListIDsWithEmpFilter(list_id, start_date, end_date, lsEmployees=None, bDebug=False):
        """
        Retrieves tasks from ClickUpList based on ListID, TaskStartDate, TaskDueDate, and optional TaskAssigneeEmailId.
        Additionally, returns the unique assignees with their respective task counts.

        :param list_id: The ID of the list to filter tasks.
        :param start_date: The start date (inclusive) in 'YYYY-MM-DD' format.
        :param end_date: The due date (inclusive) in 'YYYY-MM-DD' format.
        :param lsEmployees: (Optional) A list of employee email addresses to filter tasks by TaskAssigneeEmailId.
        :return: A tuple containing:
                - tasks: A list of dictionaries representing the filtered tasks.
                - assignee_counts: A dictionary where the key is the assignee email and the value is the count of tasks.
        """
        try:
            connection = CDBHelper.MSCreateServerConnection()
            cursor = connection.cursor(dictionary=True)  # Fetch results as dictionaries

            # Use the specified database
            cursor.execute(f"USE {CDBHelper.DATABASE_NAME}")
            
            placeholders_list_id = ', '.join(['%s'] * len(list_id))  # Create placeholders for ListIDs
            
            # Create placeholders for employee email filtering if provided
            if lsEmployees:
                placeholders_email = ', '.join(['%s'] * len(lsEmployees))
                email_condition = f"AND LOWER(TRIM(TaskAssigneeEmailId)) IN ({placeholders_email})"
                email_params = [email.lower() for email in lsEmployees]
            else:
                email_condition = ""  # No filtering by email if lsEmployees is not provided
                email_params = []

            # Define the query with conditional email filtering
            query = f"""
                SELECT TaskAssigneeEmailId, COUNT(*) as TaskCount
                FROM ClickUpList
                WHERE ListID IN ({placeholders_list_id})
                AND STR_TO_DATE(TaskStartDate, '%d-%m-%Y') >= STR_TO_DATE(%s, '%d-%m-%Y')
                AND STR_TO_DATE(TaskDueDate, '%d-%m-%Y') <= STR_TO_DATE(%s, '%d-%m-%Y')
                {email_condition}
                GROUP BY TaskAssigneeEmailId
            """
            
            # Combine list of ListIDs, dates, and employee emails
            params = list_id + [start_date, end_date] + email_params

            # Execute the query
            cursor.execute(query, params)

            # Fetch all matching records
            assignee_counts = cursor.fetchall()

            # Now, fetch detailed task data (without aggregation) for task-level details
            query_tasks = f"""
                SELECT *
                FROM ClickUpList
                WHERE ListID IN ({placeholders_list_id})
                AND STR_TO_DATE(TaskStartDate, '%d-%m-%Y') >= STR_TO_DATE(%s, '%d-%m-%Y')
                AND STR_TO_DATE(TaskDueDate, '%d-%m-%Y') <= STR_TO_DATE(%s, '%d-%m-%Y')
                {email_condition}
            """
            
            cursor.execute(query_tasks, params)
            tasks = cursor.fetchall()

            # Create a dictionary mapping assignee emails to task counts
            assignee_counts_dict = {row['TaskAssigneeEmailId']: row['TaskCount'] for row in assignee_counts}

            if bDebug:
                print("assignee_counts_dict",assignee_counts_dict)
                print(f"Retrieved {len(tasks)} task(s) from ListID {list_id} between {start_date} and {end_date}.")
            return tasks

        except Error as e:
            print(f"Error while fetching tasks: {e}")
            return []
        # finally:
        #     if connection.is_connected():
        #         cursor.close()
        #         connection.close()

    # Adding the 'TaskScore' column
    

    
        
        
# Example usage
if __name__ == "__main__":
    # CDBHelper.MSCreateDatabaseAndTables()
    # Sample data to insert or update
    print(CClickUpDB.MSGetTasksByListIDsWithEmpFilter(['901601699012', '901600183071', '901603806927',"901604664293","901604664323","901604664325","901604664326","901604664327","901604664329","901604664340"], "10-09-2024",  "25-11-2024",  [
        'mitul@riveredgeanalytics.com', 'mansi@riveredgeanalytics.com', 'hr@riveredgeanalytics.com',
        'devanshi@riveredgeanalytics.com', 'dhruvin@riveredgeanalytics.com',
        'mohit.intern@riveredgeanalytics.com', 'harshil@riveredgeanalytics.com',"fenil@riveredgeanalytics.com","punesh@riveredgeanalytics.com","ankita@riveredgeanalytics.com","nikhil@riveredgeanalytics.com","mansip@riveredgeanalytics.com","zahid@riveredgeanalytics.com"
    ]))
    # CClickUpDB.MSInsertORUpdateTask(sample_data)
    # print(CClickUpDB.MSReadTasKByID("86cw75tp8"))
    # print(CClickUpHelper.MSGetTaskIntensity("IKIO - COGSAnalyzer -<t-3>klsfjldsjft3sdfgt4"))
    # print(CClickUpHelper.MSIsTaskMileStone("IKIO - COGSAnalyzer -<t-3>klsfjldsjft3sdfgt4hlokjsadf"))
    # print(CClickUpHelper.MSConvertTimeStampToDate("1726047000000"))
    # print(CClickUpHelper.MSConvertMilliSecondsToHrs(312900000))
    
    # Define your query parameters
    # list_id = ["901600183071"]  # Replace with your actual ListID
    # start_date = "01-06-2024"  # Replace with your desired start date
    # end_date = "01-10-2024"    # Replace with your desired end date

    # # Fetch tasks based on the criteria
    # tasks = CClickUpDB.MSGetTasksByListID(list_id, start_date, end_date)
    # print(tasks)
    # print(len(tasks))
    # status_color_map = {
    #             "low": "#48d2ff",  # light blue
    #             "normal": "#48d2ff",  # light blue
    #             "high": "#FFA500",  # orange
    #             "urgent": "#FF00FF"  # magenta
    #         }
    # lsColors = []
    # for value in status_color_map.values():
    #     lsColors.append(CClickUpDB.hex_to_rgb(value))
    # print(lsColors)
    