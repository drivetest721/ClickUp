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
class CClickUpAPI:
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
            response = requests.get(CClickUpAPI.API_URL + list_id + "/task", headers=CClickUpAPI.AUTH_HEADER, params=query)
            data = response.json()
            print(data.keys())
            print(data)
            if "tasks" in data:
                # Loop through each task and insert it into the database
                for task in data["tasks"]:
                    CClickUpAPI.MSInsertTaskToDB(task)
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
    def MSFetchTaskFromConfigFile(strConfigPath = r"resource\clickup_config.json"):
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
                CClickUpAPI.MSFetchTaskOnListID(listID)
    
    @staticmethod
    def MSFetchTaskOnListsOfIDs(lsListIDs = []):
        result = True
        for listID in lsListIDs:
            try:
                CClickUpAPI.MSFetchTaskOnListID(listID)
            except:
                print(f"Error occur while fetch task for listId {listID}")
                result = False
        return result

if __name__ == "__main__":
    CClickUpAPI.MSFetchTaskFromConfigFile()
    pass
    # CClickUpAPI.MSFetchTaskOnListsOfIDs(strConfigPath = r"resource\clickup_config.json")
    # # Example usage
    # list_id = "901601699012"
    # CClickUpAPI.MSFetchTaskOnListID(list_id)
    # Parse the date strings into datetime objects
    # start_date_str = None
    # end_date_str = None
    # listId = "901600183071"
    
    # # Define the date format based on your input strings
    # date_format = "%d-%m-%Y"
    # start_date = datetime.strptime(start_date_str, date_format) if start_date_str else None
    # end_date = datetime.strptime(end_date_str, date_format) if end_date_str else None
    # CClickUpAPI.MSFetchTaskOnListID(listId,start_date,end_date)
    
    temp = {
        "86cww95x8":{
            "month":1,
            "count":3
        },
        "86cww95x9":{
            "month":1,
            "count":3
        },
        "86cwwnycp":{
            "days":1,
            "count":40
        },
        "86cwwnyw8":{
            "days":1,
            "count":40
        },
        "86cww3e5j":{
            "days":7,
            "count":8
        },
        "86cww3e7v":{
            "days":14,
            "count":4
        },
        "86cww3e8x":{
            "days":7,
            "count":8
        },
        "86cwwny1p":{
            "days":7,
            "count":8
        },
        "86cww3e4m":{
            "month":1,
            "count":3
        },
        "86cww3e27":{
            "days":7,
            "count":8
        },
        "86cww3e2v":{
            "days":7,
            "count":8
        },
        "86cww3cfz":{
            "days":7,
            "count":8
        },
        "86cww3chd":{
            "days":7,
            "count":8
        },
        "86cww9hjz":{
            "days":7,
            "count":8
        },
        "86cwwnxva":{
            "days":7,
            "count":8
        },
        "86cww3b4m":{
            "days":7,
            "count":8
        },
        "86cwwnxva":{
            "days":7,
            "count":8
        },
        "86cwwnxvf":{
            "days":14,
            "count":4
        },
        "86cwwnyb9":{
            "days":7,
            "count":8
        },
        "86cwwnyb8":{
            "days":7,
            "count":8
        },
        "86cww3y7k":{
            "days":7,
            "count":8
        },
        "86cww3z2j":{
            "month":1,
            "count":3
        },
        "86cww3z0m":{
            "days":7,
            "count":8
        },
        "86cww3yzh":{
            "days":14,
            "count":4
        },
        "86cww404y":{
            "month":1,
            "count":3
        },
        "86cwwnyb4":{
            "days":7,
            "count":8
        },
        "86cww3g0h":{
            "days":7,
            "count":8
        },
        "86cwwn4h7":{
            "days":7,
            "count":8
        },
        "86cww3g6m":{
            "days":7,
            "count":8
        },
        "86cww3g63":{
            "days":7,
            "count":8
        },
        "86cww9fjx":{
            "days":7,
            "count":8
        },
        "86cww3g8f":{
            "days":7,
            "count":8
        },
        "86cwwn4hk":{
            "month":1,
            "count":3
        },
        "86cww3gdj":{
            "days":14,
            "count":4
        },
        "86cwwnyb2":{
            "days":7,
            "count":8
        },
        "86cwwny1k":{
            "days":7,
            "count":8
        },
        "86cwwny1j":{
            "days":7,
            "count":8
        },
        "86cwwn4hr":{
            "days":7,
            "count":8
        },
        "86cww3gpp":{
            "month":1,
            "count":3
        },
        "86cww3gnv":{
            "month":1,
            "count":3
        },
        "86cww3grm":{
            "days":7,
            "count":8
        },
        "86cww3gr4":{
            "month":1,
            "count":3
        },
        "86cww3gtd":{
            "month":1,
            "count":3
        },
        "86cww3h4u":{
            "month":1,
            "count":3
        },
        "86cwwnyb3":{
            "days":7,
            "count":8
        },
        "86cwwnxv5":{
            "days":7,
            "count":8
        },
        "86cww3h7b":{
            "days":7,
            "count":8
        },
        "86cwwny13":{
            "days":7,
            "count":8
        },
        "86cww3h9f":{
            "days":7,
            "count":8
        },
        "86cww3hg9":{
            "month":1,
            "count":3
        },
        "86cww3hf5":{
            "month":1,
            "count":3
        },
        "86cww3heh":{
            "month":1,
            "count":3
        },
        "86cww3hdp":{
            "month":1,
            "count":3
        },
        "86cww3hdb":{
            "month":1,
            "count":3
        },    
        "86cww3hc5":{
            "month":1,
            "count":3
        },   
        "86cww3hbb":{
            "month":1,
            "count":3
        },  
        "86cww3hb5":{
            "month":1,
            "count":3
        },  
        "86cww3han":{
            "month":1,
            "count":3
        },  
        "86cww3hrw":{
            "month":1,
            "count":3
        }, 
        "86cww3hrb":{
            "days":14,
            "count":4
        }, 
        "86cww3hqb":{
            "days":14,
            "count":4
        }, 
        "86cww3hxd":{
            "month":1,
            "count":3
        }, 
        "86cww3hww":{
            "month":1,
            "count":3
        }     
    }