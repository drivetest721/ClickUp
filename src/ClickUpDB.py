import mysql.connector
from mysql.connector import Error
import json
import re
import os
import pandas as pd
from datetime import datetime
from DBHelper import CDBHelper
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
            start_date = CClickUpDB.MSConvertTimeStampToDate(data.get('start_date', None))
            due_date = CClickUpDB.MSConvertTimeStampToDate(data.get('due_date', None))
            parent_task_id = data.get('parent', '')
            estimated_time = json.dumps(CClickUpDB.MSConvertMilliSecondsToHrs(data.get('time_estimate', 0)))
            task_priority = json.dumps(data['priority'])
            task_status = json.dumps(data['status'])
            creator_name = json.dumps(data['creator'])
            task_assignees_list = json.dumps(data.get('assignees', []))  # Convert list to JSON string
            watchers_list = json.dumps(data.get('watchers', []))  # Convert list to JSON string
            task_created_date = CClickUpDB.MSConvertTimeStampToDate(data.get('date_created', None))
            task_update_date = CClickUpDB.MSConvertTimeStampToDate(data.get('date_updated', None))
            task_date_closed = CClickUpDB.MSConvertTimeStampToDate(data.get('date_closed', None))
            task_date_done = CClickUpDB.MSConvertTimeStampToDate(data.get('date_done', None))
            task_tags = json.dumps(data.get('tags', []))  # Convert list to JSON string
            task_dependencies = json.dumps(data.get('dependencies', []))  # Convert list to JSON string
            task_is_milestone = CClickUpDB.MSIsTaskMileStone(task_subject)
            task_intensity = CClickUpDB.MSGetTaskIntensity(task_subject)
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
    def MSGetTasksByListID(list_id, start_date, end_date):
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

            # Define the query with parameter placeholders
            query = """
                SELECT *
                FROM ClickUpList
                WHERE ListID = %s
                   AND STR_TO_DATE(TaskStartDate, '%d-%m-%Y') >= STR_TO_DATE(%s, '%d-%m-%Y')
                    AND STR_TO_DATE(TaskDueDate, '%d-%m-%Y') <= STR_TO_DATE(%s, '%d-%m-%Y')
            """

            # Execute the query with provided parameters
            cursor.execute(query, (list_id, start_date, end_date))

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
    
    # Adding the 'TaskScore' column
    @staticmethod
    def calculate_task_score(row, include_toughness=False):
        # Priority scoring
        priority_score = 1  # Default score
        if row['TaskPriority'] and row['TaskPriority'] !='null':
            priority = row['TaskPriority'].get('priority', 'normal')
            if priority == 'urgent':
                priority_score = 3
            elif priority == 'high':
                priority_score = 2
            elif priority in ['normal', 'low']:
                priority_score = 1

        # Toughness scoring
        toughness_score = row['TaskIntensity'] if include_toughness else 0

        # Total score
        return priority_score + toughness_score

    @staticmethod
    def isEstimatedTimeProvided(estimated_time):
      
        # Ensure estimated_time is a dictionary; parse if it's a JSON string
        if isinstance(estimated_time, str):
            estimated_time = json.loads(estimated_time)
        
        # Check if both 'hrs' and 'mins' are 0
        return not (estimated_time.get('hrs', 0) == 0 and estimated_time.get('mins', 0) == 0)

    @staticmethod
    def MSCreateDataframe(lsTasks):
    # Creating a DataFrame from the list of tasks
    
        df = pd.DataFrame(lsTasks)
        # Parsing JSON strings in 'TaskPriority' and 'TaskAssigneesList'
        df['TaskPriority'] = df['TaskPriority'].apply(lambda x: json.loads(x) if x != 'null' else None)
        df['TaskAssigneesList'] = df['TaskAssigneesList'].apply(json.loads)
        df['TaskScore'] = df.apply(CClickUpDB.calculate_task_score, include_toughness=False, axis=1)
        
        df = df[df['EstimatedTime'].apply(CClickUpDB.isEstimatedTimeProvided)]

        # Convert 'TaskStartDate' to datetime for sorting
        df['TaskStartDate'] = pd.to_datetime(df['TaskStartDate'], format='%d-%m-%Y')

        # Sort tasks by 'TaskStartDate' ascending, then by 'TaskScore' ascending within the same date
        df = df.sort_values(by=['TaskStartDate', 'TaskScore'])
        # Creating employee-wise DataFrames
        employee_tasks = {}
        for _, row in df.iterrows():
            print(row)
            assignees = row['TaskAssigneesList']
            if assignees:
                for assignee in assignees:
                    username = assignee['username']
                    if username not in employee_tasks:
                        employee_tasks[username] = []
                    employee_tasks[username].append(row)

        # # Convert the lists into DataFrames
        employee_dataframes = {username: pd.DataFrame(tasks) for username, tasks in employee_tasks.items()}

        # Directory to save the Excel files
        output_directory = r"Data/"
        os.makedirs(output_directory, exist_ok=True)  # Create the directory if it doesn't exist

        # Save employee-wise DataFrames to Excel files
        for username, df in employee_dataframes.items():
            # Create a filename based on the username
            filename = f"{username.replace(' ', '_')}_tasks.xlsx"
            # Construct the full path
            file_path = os.path.join(output_directory, filename)
            # Save the DataFrame to an Excel file
            df.to_excel(file_path, index=False)

        print("Employee-wise task details have been saved to the 'Data/' directory.")
    
# Example usage
if __name__ == "__main__":
    # CDBHelper.MSCreateDatabaseAndTables()
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
    # CClickUpDB.MSInsertORUpdateTask(sample_data)
    # print(CClickUpDB.MSReadTasKByID("86cw75tp8"))
    # print(CClickUpDB.MSGetTaskIntensity("IKIO - COGSAnalyzer -<t-3>klsfjldsjft3sdfgt4"))
    # print(CClickUpDB.MSIsTaskMileStone("IKIO - COGSAnalyzer -<t-3>klsfjldsjft3sdfgt4hlokjsadf"))
    # print(CClickUpDB.MSConvertTimeStampToDate("1726047000000"))
    # print(CClickUpDB.MSConvertMilliSecondsToHrs(312900000))
    
    # Define your query parameters
    # list_id = "901600183071"  # Replace with your actual ListID
    # start_date = "01-08-2024"  # Replace with your desired start date
    # end_date = "01-09-2024"    # Replace with your desired end date

    # # Fetch tasks based on the criteria
    # tasks = CClickUpDB.MSGetTasksByListID(list_id, start_date, end_date)
    # print(tasks)
    # print(len(tasks))
    
    print(CClickUpDB.isEstimatedTimeProvided({'ListName': 'ERPNext', 'ListID': '901600183071', 'FolderName': 'REAL Office', 'SpaceID': '90020386592', 'TaskID': '86cw73j5j', 'TaskSubject': 'Mitul - ERPNext Install & Setup V15', 'TaskStartDate': '13-08-2024', 'TaskDueDate': '21-08-2024', 'ParentTaskID': '86cw76fxd', 'EstimatedTime': '{"hrs": 0, "mins": 0, "time_estimate": 214324234}', 'TaskPriority': {'id': '1', 'color': '#f50000', 'priority': 'urgent', 'orderindex': '1'}, 'TaskStatus': '{"id": "subcat901600183071_subcat901600182452_subcat900202016677_subcat900202016557_subcat900202016465_subcat900201647299_subcat900201617233_subcat900201614169_subcat900201614016_subcat900201613908_subcat900201524923_subcat900900756278_subcat900900756275_subcat900900756272_subcat900600588774_sc900600504232_NTf0x6rB", "type": "closed", "color": "#008844", "status": "delievered", "orderindex": 4}', 'AssignByPersonDetails': '{"id": 67390920, "color": "", "email": "mitul@riveredgeanalytics.com", "username": "Mitul Solanki", "profilePicture": "https://attachments.clickup.com/profilePictures/67390920_BGd.jpg"}', 'TaskAssigneesList': '[{"id": 67390920, "color": "", "email": "mitul@riveredgeanalytics.com", "initials": "MS", "username": "Mitul Solanki", "profilePicture": "https://attachments.clickup.com/profilePictures/67390920_BGd.jpg"}]', 'WatchersList': '[{"id": 67390920, "color": "", "email": "mitul@riveredgeanalytics.com", "initials": "MS", "username": "Mitul Solanki", "profilePicture": "https://attachments.clickup.com/profilePictures/67390920_BGd.jpg"}]', 'TaskCreatedDate': '12-08-2024', 'TaskUpdateDate': '02-09-2024', 'TaskDateClosed': '15-08-2024', 'TaskDateDone': '15-08-2024', 'TaskTags': '[]', 'TaskDependencies': '[{"type": 1, "userid": "67390920", "task_id": "86cw75tb6", "chain_id": null, "depends_on": "86cw73j5j", "date_created": "1723621006884", "workspace_id": "9002161791"}]', 'TaskIsMilestone': 0, 'TaskIntensity': 1, 'TaskCheckLists': '[]'}))
    