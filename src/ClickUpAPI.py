import requests
from datetime import datetime
from DBHelper import DBHelper
import json

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
    def MSFetchTaskOnListID(list_id):
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
                # "due_date_gt": date_limit  # Fetch tasks created before the end of September
            }
            
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
        # Assuming `DBHelper.MSInsertORUpdateTask` is a function that inserts or updates task data in your database.
        DBHelper.MSInsertORUpdateTask(task_data)

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
    pass
    # # Example usage
    # list_id = "901601699012"
    # ClickUpHelper.MSFetchTaskOnListID(list_id)
    ClickUpHelper.MSFetchTaskOnListsOfIDs()
    
    