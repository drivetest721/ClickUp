import requests
from datetime import datetime
from DBHelper import CDBHelper
from ClickUpDB import CClickUpDB
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

"""
Improvements - 

1. Maintain date wise Logs
2. Check Assignee in task , subtask , checklist, dependencies task
3. 
"""
class ClickUpHelper:
    API_URL = "https://api.clickup.com/api/v2/list/"
    AUTH_HEADER = {"Authorization": "pk_67390920_KWG9KAUXYQBLX2I4XL7EBXMHNA247V86"}

    @staticmethod
    def MSFetchTaskOnListID(list_id, start_date = None, end_date =  None):
        current_page = 0
        tasks_inserted = 0
        date_limit = int(datetime(2024, 9, 1).timestamp() * 1000)  # Timestamp for September 30, 2024

        while True:
            # Construct query parameters for the API call
            query = {
                "archived": "false",
                "include_markdown_description": "false",
                "page": str(current_page),
                "subtasks": "true",
                "include_closed":"true"
                # "due_date_gt": date_limit  # Fetch tasks created before the end of September
            }
            if start_date is not None:
                # Convert dates to Unix timestamps in milliseconds
                due_date_gt = int(start_date.timestamp() * 1000)
                query["due_date_gt"] = due_date_gt
            if end_date is not None:
                # Convert dates to Unix timestamps in milliseconds
                due_date_lt = int(end_date.timestamp() * 1000)
                query["due_date_lt"] = due_date_lt
            # API call to fetch tasks
            response = requests.get(ClickUpHelper.API_URL + list_id + "/task", headers=ClickUpHelper.AUTH_HEADER, params=query)
            data = response.json()
            print(data.keys())
            print(data)
            if "tasks" in data:
                # Loop through each task and insert it into the database
                for task in data["tasks"]:
                    ClickUpHelper.MSInsertTaskToDB(task)
                    tasks_inserted += 1
                print(f"Inserted {len(data['tasks'])} tasks from page {current_page}.")
            else:
                print("No tasks found in response.")
                break

            # Check if this is the last page of results
            if data.get("last_page", True):
                break
            
            # Increment page to fetch the next set of tasks
            current_page += 1
        
        print(f"Total tasks inserted: {tasks_inserted}")

    @staticmethod
    def MSInsertTaskToDB(task_data):
        # Assuming `CDBHelper.MSInsertORUpdateTask` is a function that inserts or updates task data in your database.
        CClickUpDB.MSInsertORUpdateTask(task_data)

    @staticmethod
    def MSFetchTaskOnListsOfIDs(strConfigPath = r"resource\clickup_config.json"):
        # Read ClickUp Config
        with open(strConfigPath) as f:
            dictClickUpConfig = json.load(f)
        
        # print(dictClickUpConfig)
        
        for dictListProperties in dictClickUpConfig:
            # Unique ListID
            listID = dictListProperties.get("ListID", None)
            # Sync - Decide to fetch new latest for particular List
            sync = dictListProperties.get("sync", True)
            if (listID is not None and sync ):
                ClickUpHelper.MSFetchTaskOnListID(listID)

if __name__ == "__main__":
    ClickUpHelper.MSFetchTaskOnListsOfIDs()
    # pass
    # # Example usage
    # list_id = "901601699012"
    # ClickUpHelper.MSFetchTaskOnListID(list_id)
    # Parse the date strings into datetime objects
    # start_date_str = None
    # end_date_str = None
    # listId = "901600183071"
    
    # # Define the date format based on your input strings
    # date_format = "%d-%m-%Y"
    # start_date = datetime.strptime(start_date_str, date_format) if start_date_str else None
    # end_date = datetime.strptime(end_date_str, date_format) if end_date_str else None
    # ClickUpHelper.MSFetchTaskOnListID(listId,start_date,end_date)
    
    