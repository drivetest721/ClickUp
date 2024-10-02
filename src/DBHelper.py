import mysql.connector
from mysql.connector import Error
import json
import re
from datetime import datetime

"""
    assignee can be null
    
"""
    
class DBHelper:
    
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
                host=DBHelper.DATABASE_URL_DEV,
                user=DBHelper.DATABASE_USER,
                password=DBHelper.DATABASE_PASSWORD_DEV,
                database=DBHelper.DATABASE_NAME,
                port=DBHelper.DATABASE_PORT
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
            connection = DBHelper.MSCreateServerConnection()
            cursor = connection.cursor()

            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DBHelper.DATABASE_NAME}")
            print(f"Database `{DBHelper.DATABASE_NAME}` created or already exists.")

            # Switch to the new database
            cursor.execute(f"USE {DBHelper.DATABASE_NAME}")

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

    @staticmethod
    def MSReadTasKByID(task_id):
        # Read data from ClickUpList table
        try:
            connection = DBHelper.MSCreateServerConnection()
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
            connection =  DBHelper.MSCreateServerConnection()
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
            start_date = DBHelper.MSConvertTimeStampToDate(data.get('start_date', None))
            due_date = DBHelper.MSConvertTimeStampToDate(data.get('due_date', None))
            parent_task_id = data.get('parent', '')
            estimated_time = json.dumps(DBHelper.MSConvertMilliSecondsToHrs(data.get('time_estimate', 0)))
            task_priority = json.dumps(data['priority'])
            task_status = json.dumps(data['status'])
            creator_name = json.dumps(data['creator'])
            task_assignees_list = json.dumps(data.get('assignees', []))  # Convert list to JSON string
            watchers_list = json.dumps(data.get('watchers', []))  # Convert list to JSON string
            task_created_date = DBHelper.MSConvertTimeStampToDate(data.get('date_created', None))
            task_update_date = DBHelper.MSConvertTimeStampToDate(data.get('date_updated', None))
            task_date_closed = DBHelper.MSConvertTimeStampToDate(data.get('date_closed', None))
            task_date_done = DBHelper.MSConvertTimeStampToDate(data.get('date_done', None))
            task_tags = json.dumps(data.get('tags', []))  # Convert list to JSON string
            task_dependencies = json.dumps(data.get('dependencies', []))  # Convert list to JSON string
            task_is_milestone = DBHelper.MSIsTaskMileStone(task_subject)
            task_intensity = DBHelper.MSGetTaskIntensity(task_subject)
            TaskCheckLists = json.dumps(data.get('checklists',None))
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
                    TaskIsMilestone = %s, TaskIntensity = %s, TaskCheckLists = %s
                WHERE TaskID = %s
                """
                update_values = (
                    list_name, list_id, folder_name, space_id, task_subject, start_date, due_date, parent_task_id,
                    estimated_time, task_priority, task_status, creator_name, task_assignees_list, watchers_list,
                    task_created_date, task_update_date, task_date_closed, task_date_done, task_tags, task_dependencies,
                    task_is_milestone, task_intensity, TaskCheckLists, data['id']
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
                    TaskTags, TaskDependencies, TaskIsMilestone, TaskIntensity, TaskCheckLists
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                insert_values = (
                    list_name, list_id, folder_name, space_id, data['id'], task_subject, start_date, due_date,
                    parent_task_id, estimated_time, task_priority, task_status, creator_name, task_assignees_list,
                    watchers_list, task_created_date, task_update_date, task_date_closed, task_date_done,
                    task_tags, task_dependencies, task_is_milestone, task_intensity, TaskCheckLists
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
    def MSGetTaskIntensity(strTaskSubject):
        # Regular expression to find T1, T2, T3, <T1>, <T2>, <T3>
        match = re.search(r'(T[123]|<T[123]>)', strTaskSubject, re.IGNORECASE)

        # Determine the task intensity based on the match
        if match:
            intensity = match.group().strip('<>')  # Remove <> if present
            if intensity.lower()=="t1":
                intensity = 1
            elif intensity.lower() == "t2":
                intensity = 2
            else:
                intensity = 3 
        else:
            intensity = 1  # Default to 'T1'(normal - 1) if no match is found
        
        return intensity
        
    @staticmethod
    def MSIsTaskMileStone(strTaskSubject):
        # Regular expression to find HLO or <HLO>
        match = re.search(r'(HLO|<HLO>)', strTaskSubject, re.IGNORECASE)

        # Return True if a match is found, otherwise False
        return bool(match)

    @staticmethod
    def MSConvertTimeStampToDate(timestamp):
        if timestamp is not None and timestamp!="None":
            # Convert timestamp (in milliseconds) to a datetime object
            date_obj = datetime.fromtimestamp(int(timestamp) / 1000)
            # Format datetime object to 'DD-MM-YYYY' format
            formatted_date = date_obj.strftime('%d-%m-%Y')
            return formatted_date
        else:
            return timestamp
    
    @staticmethod
    def MSConvertMilliSecondsToHrs(time_estimate):
        if time_estimate is not None and time_estimate!="None":
            # Convert milliseconds to total minutes
            total_minutes = time_estimate / (1000 * 60)
            
            # Calculate hours and minutes
            hrs = int(total_minutes // 60)
            mins = int(total_minutes % 60)
            
            return {'hrs': hrs, 'mins': mins, 'time_estimate':time_estimate}
        else:
            # You can choose to return None or a default value
            return {'hrs': 0, 'mins': 0,'time_estimate':time_estimate}
    
    @staticmethod
    def MSReadTasks(filters):
        try:
            connection = DBHelper.MSCreateServerConnection()
            cursor = connection.cursor(dictionary=True)

            # Base SQL query
            sql_query = "SELECT * FROM ClickUpList WHERE 1=1"

            # Dynamic query conditions based on filters
            conditions = []
            values = []

            # Filter by ListIDs
            if 'list_of_list_ids' in filters:
                conditions.append("ListID IN (%s)" % ','.join(['%s'] * len(filters['list_of_list_ids'])))
                values.extend(filters['list_of_list_ids'])

            # Filter by Assignee Names, AssignByPersonDetails, or TaskTags
            if 'list_of_assignee_names' in filters:
                assignee_filter = " OR ".join([
                    "AssignByPersonDetails IN (%s)" % ','.join(['%s'] * len(filters['list_of_assignee_names'])),
                    "TaskAssigneesList LIKE %s",
                    "TaskTags LIKE %s"
                ])
                conditions.append(f"({assignee_filter})")
                values.extend(filters['list_of_assignee_names'])
                values.append('%' + json.dumps(filters['list_of_assignee_names']) + '%')  # Assignee JSON match
                values.append('%' + json.dumps(filters['list_of_assignee_names']) + '%')  # Tags JSON match

            # Filter by date range for TaskStartDate
            if 'start_date_range' in filters:
                conditions.append("(TaskStartDate BETWEEN %s AND %s)")
                values.append(filters['start_date_range'][0])
                values.append(filters['start_date_range'][1])

            # Filter by date range for TaskDueDate
            if 'due_date_range' in filters:
                conditions.append("(TaskDueDate BETWEEN %s AND %s)")
                values.append(filters['due_date_range'][0])
                values.append(filters['due_date_range'][1])

            # Filter by TaskStatus
            if 'task_status_list' in filters:
                conditions.append("TaskStatus IN (%s)" % ','.join(['%s'] * len(filters['task_status_list'])))
                values.extend(filters['task_status_list'])

            # Filter by Milestone
            if 'show_milestone' in filters and filters['show_milestone']:
                conditions.append("TaskIsMilestone = %s")
                values.append(True)

            # # Apply ScoreBaseOnIntensity toggle
            # if 'score_based_on_intensity' in filters and filters['score_based_on_intensity']:
            #     conditions.append("TaskIntensity IS NOT NULL")

            # # Apply ScoreBaseOnAssignBy toggle
            # if 'score_based_on_assign_by' in filters and filters['score_based_on_assign_by']:
            #     conditions.append("AssignByPersonDetails IS NOT NULL")

            # # Apply ScoreBaseOnDependency toggle
            # if 'score_based_on_dependency' in filters and filters['score_based_on_dependency']:
            #     conditions.append("TaskDependencies IS NOT NULL")

            # Append conditions to the base query
            if conditions:
                sql_query += " AND " + " AND ".join(conditions)

            # Execute the query
            cursor.execute(sql_query, values)
            result = cursor.fetchall()

            return result

        except Error as e:
            print(f"Error: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
# Example usage
if __name__ == "__main__":
    # DBHelper.MSCreateDatabaseAndTables()
    # Sample data to insert or update
    sample_data = { "id": "86cw75tp8", "custom_id": "None", "custom_item_id": 0, "name": " Mansi - Manager Monthly Review Form",
        "status": {
            "status": "review",
            "id": "subcat901600183071_subcat901600182452_subcat900202016677_subcat900202016557_subcat900202016465_subcat900201647299_subcat900201617233_subcat900201614169_sc900201614016_29RxMBmm",
            "color": "#5f55ee",
            "type": "custom",
            "orderindex": 2
        },
        "orderindex": "-0.10713958714285718000000000000000",
        "date_created": "1723459274067",
        "date_updated": "1726736497500",
        "date_closed": "None",
        "date_done": "None",
        "archived": False,
        "creator": {
            "id": 67390920,
            "username": "Mitul Solanki",
            "color": "",
            "email": "mitul@riveredgeanalytics.com",
            "profilePicture": "https://attachments.clickup.com/profilePictures/67390920_BGd.jpg"
        },
        "assignees": [
            {
                "id": 88895068,
                "username": "mansi solanki",
                "color": "#622aea",
                "initials": "MS",
                "email": "mansi@riveredgeanalytics.com",
                "profilePicture": "https://attachments.clickup.com/profilePictures/88895068_IUP.jpg"
            }
        ],
        "watchers": [
            {
                "id": 67390920,
                "username": "Mitul Solanki",
                "color": "",
                "initials": "MS",
                "email": "mitul@riveredgeanalytics.com",
                "profilePicture": "https://attachments.clickup.com/profilePictures/67390920_BGd.jpg"
            }
        ],
        "checklists": [],
        "tags": [],
        "parent": "86cwbwvhm",
        "priority": {
            "color": "#f50000",
            "id": "1",
            "orderindex": "1",
            "priority": "urgent"
        },
        "due_date": "1726047000000",
        "start_date": "1725834600000",
        "points": "None",
        "time_estimate": 57600000,
        "custom_fields": [],
        "dependencies": [
            {
                "task_id": "86cw75tp8",
                "depends_on": "86cwbxgrd",
                "type": 1,
                "date_created": "1724915558505",
                "userid": "67390920",
                "workspace_id": "9002161791",
                "chain_id": "None"
            },
            {
                "task_id": "86cw75tp8",
                "depends_on": "86cwby8ct",
                "type": 1,
                "date_created": "1724918747977",
                "userid": "67390920",
                "workspace_id": "9002161791",
                "chain_id": "None"
            },
            {
                "task_id": "86cw75tp8",
                "depends_on": "86cwby8mb",
                "type": 1,
                "date_created": "1724918787986",
                "userid": "67390920",
                "workspace_id": "9002161791",
                "chain_id": "None"
            }
        ],
        "team_id": "9002161791",
        "permission_level": "create",
        "list": {
            "id": "901600183071",
            "name": "ERPNext",
            "access": True
        },
        "project": {
            "id": "90162478296",
            "name": "REAL Office",
            "hidden": False,
            "access": True
        },
        "folder": {
            "id": "90162478296",
            "name": "REAL Office",
            "hidden": False,
            "access": True
        },
        "space": {
            "id": "90020386592"
        }
    }
    # DBHelper.MSInsertORUpdateTask(sample_data)
    # print(DBHelper.MSReadTasKByID("86cw75tp8"))
    # print(DBHelper.MSGetTaskIntensity("IKIO - COGSAnalyzer -<t-3>klsfjldsjft3sdfgt4"))
    # print(DBHelper.MSIsTaskMileStone("IKIO - COGSAnalyzer -<t-3>klsfjldsjft3sdfgt4hlokjsadf"))
    # print(DBHelper.MSConvertTimeStampToDate("1726047000000"))
    # print(DBHelper.MSConvertMilliSecondsToHrs(312900000))
    filters = {
        'list_of_list_ids': ['901601699012', '901600183071'],
        'list_of_assignee_names': ['Mitul Solanki', 'Mansi Solanki'],
        'start_date_range': ['2024-01-01', '2024-12-31'],
        'due_date_range': ['2024-01-01', '2024-12-31'],
        'task_status_list': ['Open', 'In Progress'],
        'show_milestone': True,
        'score_based_on_intensity': True,
        'score_based_on_assign_by': False,
        'score_based_on_dependency': True
    }

    tasks = DBHelper.MSReadTasks(filters)
    for task in tasks:
        print(task)