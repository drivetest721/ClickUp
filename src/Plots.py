import copy
import mysql.connector
from mysql.connector import Error
import json
import re
import pandas as pd
from datetime import datetime
from DBHelper import CDBHelper
from datetime import datetime, timedelta
from ClickUpDB import CClickUpDB
import os

class CClickUpMiddleWare:
    # Purpose - Sort Task Base on Score : Priority Wise =  Normal or Low - 1, High - 2, Urgent - 3 , use list of task for plot
    
    @staticmethod
    def MSGroupTaskEmployeeWise(lsTasks, bDebug= False,bSaveFilteredExcelSheet=False, strFilterTaskDirPath= r"Data/"):
        """
        Purpose - To clean list of task such as handling null values or none or Empty values
        """
        # Creating a DataFrame from the list of tasks
        df = pd.DataFrame(lsTasks)
        
        df['TaskPriority'] = df['TaskPriority'].apply(lambda x: json.loads(x) if x != 'null' else None)
        df['TaskAssigneesList'] = df['TaskAssigneesList'].apply(json.loads)
        
        # Determine Each Task - Task Score Base on Several Criteria
        df['TaskScore'] = df.apply(CClickUpDB.MSCalculateTaskScore, include_toughness=False, axis=1)
        
        # Filter Task List - no Estimated Time is Provided
        df = df[df['EstimatedTime'].apply(CClickUpDB.MSIsEstimatedTimeProvided)]

        # Drop columns except the specified list
        columns_to_keep = ['ListName', 'TaskID', 'TaskSubject', 'TaskStartDate', 'TaskDueDate', 'TaskStatus',
                        'EstimatedTime', 'TaskPriority', 'TaskAssigneesList', 
                        'TaskIsMilestone', 'TaskIntensity', 'TaskScore','TaskCreatedDate']
        
        df = df[columns_to_keep]
        
        
        # Add new columns - for further processing 
        df['EstimatedTime'] = df['EstimatedTime'].apply(json.loads)
        df['TotalTskEstInMins'] = df['EstimatedTime'].apply(lambda x: (x['hrs'] * 60 + x['mins']) if x else 0)

        # 2. 'AssignTo' - extract username from the first entry in 'TaskAssigneesList'  || WARN - (Remaining Task) In Case of Multiple Assignees EDGE Case Must Handle 
        df['AssignTo'] = df['TaskAssigneesList'].apply(lambda x: x[0]['username'] if x and len(x) > 0 else None)

        # 3. 'TaskPriority' - extract priority
        df['TaskPriority'] = df['TaskPriority'].apply(lambda x: x['priority'] if x else None)

        # 4. 'TaskStatus'
        df['TaskStatus'] = df['TaskStatus'].apply(json.loads)
        df['TaskStatus'] = df['TaskStatus'].apply(lambda x: x['status'] if isinstance(x, dict) else None)

        # Creating employee-wise task lists
        dictFilteredEmpWiseTsk = {}
        for _, row in df.iterrows():
            assignees = row['TaskAssigneesList']
            if assignees:
                for assignee in assignees:
                    username = assignee['username']
                    if username not in dictFilteredEmpWiseTsk:
                        dictFilteredEmpWiseTsk[username] = []
                    # Convert the row to a dictionary and append to the list
                    dictFilteredEmpWiseTsk[username].append(row.to_dict())

        if bSaveFilteredExcelSheet:
            # Directory to save the Excel files
            output_directory = strFilterTaskDirPath
            os.makedirs(output_directory, exist_ok=True)  # Create the directory if it doesn't exist

            # Save employee-wise task lists to Excel files
            for username, tasks in dictFilteredEmpWiseTsk.items():
                # Create a DataFrame from the list of task dictionaries
                df_employee = pd.DataFrame(tasks)
                # Create a filename based on the username
                filename = f"{username.replace(' ', '_')}_tasks.xlsx"
                # Construct the full path
                file_path = os.path.join(output_directory, filename)
                # Save the DataFrame to an Excel file
                df_employee.to_excel(file_path, index=False)

            if bDebug:
                print("Employee-wise task details have been saved to the 'Data/' directory.")
        
        if bDebug:
            print(f"1. DataFrame - {df}")
            
        # Return the dictionary where keys are employee names and values are lists of task dictionaries
        return dictFilteredEmpWiseTsk

    @staticmethod
    def MSCreateEmpDateWiseTasksList(dictFilteredEmpWiseTsk, bDebug=True):
        # Purpose - Group Employee Tasks Start Date or Execution Date Wise 
        dictEmpDateWiseTaskList = {}
        
        for EmpName, EmpTaskList in dictFilteredEmpWiseTsk.items():
            dictEmpDateWiseTaskList[EmpName] = {}
            if bDebug:
                print("1. Employee Name - ", EmpName)
                print("2. User Tasks - ", EmpTaskList)
            
            for idx, EmpTaskDetails in enumerate(EmpTaskList):
                # Use Task Properties
                strTskStDate = EmpTaskDetails['TaskStartDate']
                strTskID = EmpTaskDetails['TaskID']
                iTskTotalEstInMin = EmpTaskDetails['TotalTskEstInMins']
                strTskEndDate = EmpTaskDetails['TaskDueDate']
                
                # Add new Properties in Task Details
                EmpTaskDetails['TaskExecutionDate'] = strTskStDate
                # When Task Due Date and Task Start Date are Different
                EmpTaskDetails['isTaskMovable'] = (strTskStDate != strTskEndDate)
                
                # Check if the start date already exists in the structure
                if strTskStDate not in dictEmpDateWiseTaskList[EmpName]:
                    # Initialize the start date entry if not present
                    dictEmpDateWiseTaskList[EmpName][strTskStDate] = {
                        "TotalWorkMin": 8 * 60,  # Assuming 8 working hours in a day
                        "AllocatedWorkingMin": 0,  # Initialize allocated working hours
                        "IsConflict": False,  # Initialize IsConflict as False
                        "AllocatedTask": {}  # Dictionary to store task ID and detailed task data
                    }
                
                # Add the task details to the 'AllocatedTask' dictionary
                dictEmpDateWiseTaskList[EmpName][strTskStDate]["AllocatedTask"][strTskID] = EmpTaskDetails
                
                # Update the allocated working minutes
                dictEmpDateWiseTaskList[EmpName][strTskStDate]["AllocatedWorkingMin"] += iTskTotalEstInMin
                
                # Check for conflict and update IsConflict
                iAllocatedMin = dictEmpDateWiseTaskList[EmpName][strTskStDate]["AllocatedWorkingMin"]
                iTotalWorkMin = dictEmpDateWiseTaskList[EmpName][strTskStDate]["TotalWorkMin"]
                dictEmpDateWiseTaskList[EmpName][strTskStDate]["IsConflict"] = iAllocatedMin > iTotalWorkMin
                
                # Assume both dates are not null
                if bDebug:
                    print(f"3. Task Details {idx+1} - {EmpTaskDetails}")
                    print(f"4. Updated Structure - {dictEmpDateWiseTaskList[EmpName][strTskStDate]}")
        
        return dictEmpDateWiseTaskList

    @staticmethod
    def MSGetNextDate(strTskStDate):
        """Utility function to get the next date in 'DD-MM-YYYY' format."""
        date_obj = datetime.strptime(strTskStDate, '%d-%m-%Y')
        next_date_obj = date_obj + timedelta(days=1)
        return next_date_obj.strftime('%d-%m-%Y')

    @staticmethod
    def MSCheckForTskExcDateConflicts(day_data):
        """
        This method takes a dictionary representing a day's work data and checks if there is a conflict.
        
        Args:
        - day_data (dict): A dictionary containing "TotalWorkMin" and "AllocatedWorkingMin".
        
        Returns:
        - bool: True if there is a conflict, False otherwise.
        """
        total_work_min = day_data.get("TotalWorkMin", 0)
        allocated_working_min = day_data.get("AllocatedWorkingMin", 0)
        
        # Determine if there is a conflict
        is_conflict = allocated_working_min > total_work_min
        
        # Return the conflict status
        return is_conflict
    
    def MSSortEmpDateWiseTskList(dictAllocatedDateWiseTask, employee_tasks, bDebug=True):
        """
        Purpose - to sort task in executed date according to task score , split task when task due date is later then start date
        
        
        Task Details additional Properties - 
        1. TaskExecutionDate
        2. IsConflict
        3. isTaskMovable
        4. ConflictTimeMin
        5. AllocatedTimeMin
        """
        
        for EmpName, dictTskDetailsExcStDateWise in dictAllocatedDateWiseTask.items():
            if bDebug:
                print("1. Employee Name - ", EmpName)
                print("2. Date Wise Tasks Arrangement - ", dictTskDetailsExcStDateWise)

            for strTskExcDate, dictExcDateTskDetails in list(dictTskDetailsExcStDateWise.items()):  # Use list to avoid runtime modification errors
                IsConflictInTskExcDate = CClickUpMiddleWare.MSCheckForTskExcDateConflicts(dictExcDateTskDetails)
                
                if IsConflictInTskExcDate:
                    if bDebug:
                        print("3. Task Start Date- ", strTskExcDate)
                        print("4. Execution Date - Tasks Details - ", dictExcDateTskDetails)

                    # Get all task details for this date
                    lsTsks = list(dictExcDateTskDetails.get("AllocatedTask", {}).values())

                    # Sort tasks by TaskScore (highest to lowest) and then by TaskCreatedDate (latest to earliest)
                    lsSortedTsks = sorted(
                        lsTsks,
                        key=lambda x: (-x['TaskScore'], datetime.strptime(x['TaskCreatedDate'], '%d-%m-%Y'))
                    )

                    # Initialize available minutes
                    iTotalExcDateRemainingMin = 480  # 8 hours in minutes

                    # Create a list to keep track of sorted task IDs
                    lsTskScoreOrder = []

                    # Iterate through sorted tasks to allocate time and check conflicts
                    for dictTskDetail in lsSortedTsks:
        
                        # Access Task Properties
                        strTskID = dictTskDetail['TaskID']
                        iTotalTskEstMin = dictTskDetail['TotalTskEstInMins']
                        strTskExcDate = dictTskDetail['TaskExecutionDate']
                        
                        # add new properties for further processing
                        dictTskDetail['isTaskMovable'] = (dictTskDetail['TaskStartDate'] != dictTskDetail['TaskDueDate'])
                        
                        # Check if the task can be allocated within the available time
                        if iTotalTskEstMin <= iTotalExcDateRemainingMin:
                            # Mark the task as not in conflict
                            dictTskDetail['IsConflict'] = False
                            dictTskDetail['ConflictTimeMin'] = 0
                            # Allocate the full task estimated time
                            dictTskDetail['AllocatedTimeMin'] = iTotalTskEstMin
                            # Subtract the estimated minutes from the available time
                            iTotalExcDateRemainingMin -= iTotalTskEstMin
                        else:
                            # Task Estimated Time > Execution Date Remaining Time (Minutes)
                            
                            # Task Due Date > Current Task Execution Date then TaskMovable - True else False (on same task due date and task execution date)
                            if not dictTskDetail['isTaskMovable']:
                                # Mark Task Conflict as no more days available (Task Exc Date == Task Due Date)
                                dictTskDetail['IsConflict'] = True
                                
                                # check do i have remaining mins to work for this execution date if so then utilize Minutes else show remaining task estimate time in conflict time
                                if iTotalExcDateRemainingMin <= 0:
                                    dictTskDetail['AllocatedTimeMin'] = 0
                                    dictTskDetail['ConflictTimeMin'] = iTotalTskEstMin
                                else:
                                    # Allocate remaining available minutes
                                    dictTskDetail['AllocatedTimeMin'] = iTotalExcDateRemainingMin
                                    dictTskDetail['ConflictTimeMin'] = iTotalTskEstMin - iTotalExcDateRemainingMin
                                    # Set iTotalExcDateRemainingMin to 0 as it has been exhausted
                                    iTotalExcDateRemainingMin = 0
                            
                            # Check if the task due date is later or greater than task execution date
                            else:
                                # No remaining min availabel in Task Execution Date then move current task to next closest date
                                if iTotalExcDateRemainingMin <= 0:
                                    
                                    # Remove the dictTskDetail from the current date
                                    dictExcDateTskDetails['AllocatedTask'].pop(strTskID)
                                    
                                    # Push to the next available date
                                    strTskNextExcDate = CClickUpMiddleWare.MSGetNextDate(strTskExcDate)
                                    
                                    # Mark Task Conflict Status False as Tsk Due Date is Later
                                    dictTskDetail['IsConflict'] = False
                                    # Move entire task to the next execution. Date assigned time and conflict time would be zero.
                                    dictTskDetail['AllocatedTimeMin'] = 0
                                    dictTskDetail['ConflictTimeMin'] = 0
                                    dictTskDetail['TaskExecutionDate'] = strTskNextExcDate
                                    
                                    if strTskNextExcDate not in dictTskDetailsExcStDateWise:
                                        # Initialize the next date if it doesn't exist
                                        dictTskDetailsExcStDateWise[strTskNextExcDate] = {
                                            "TotalWorkMin": 480,
                                            "AllocatedWorkingMin": iTotalTskEstMin,
                                            "IsConflict": iTotalTskEstMin > 480,
                                            "AllocatedTask": {strTskID:dictTskDetail}
                                        }
                                        continue
                                    
                                    # Add the task to the next date's task list
                                    dictTskDetailsExcStDateWise[strTskNextExcDate]["AllocatedTask"][strTskID] = dictTskDetail
                                    dictTskDetailsExcStDateWise[strTskNextExcDate]["AllocatedWorkingMin"] += iTotalTskEstMin
                                    dictTskDetailsExcStDateWise[strTskNextExcDate]["IsConflict"] =  dictTskDetailsExcStDateWise[strTskNextExcDate]["AllocatedWorkingMin"] > dictTskDetailsExcStDateWise[strTskNextExcDate]["TotalWorkMin"]
                                    dictTskDetailsExcStDateWise[strTskNextExcDate]["AllocatedTask"][strTskID]['isTaskMovable'] = strTskNextExcDate != dictTskDetailsExcStDateWise[strTskNextExcDate]["AllocatedTask"][strTskID]['TaskDueDate']
                                    
                                else:
                                    # Push remaining part of the task to the next date
                                    remaining_min = iTotalTskEstMin - iTotalExcDateRemainingMin
                                    strTskNextExcDate = CClickUpMiddleWare.MSGetNextDate(strTskExcDate)
                                    
                                    # for current start date
                                    dictTskDetail['IsConflict'] =  False
                                    dictTskDetail['ConflictTimeMin'] = 0
                                    dictTskDetail['AllocatedTimeMin'] = iTotalExcDateRemainingMin
                                    
                                    # Add the remaining part of the task to the next date
                                    new_task_details = dictTskDetail.copy()
                                    new_task_details['TotalTskEstInMins'] = remaining_min
                                    new_task_details['isTaskMovable'] = strTskNextExcDate != new_task_details['TaskDueDate']
                                    new_task_details['TaskExecutionDate'] = strTskNextExcDate
                                    if strTskNextExcDate not in dictTskDetailsExcStDateWise:
                                        new_task_details['AllocatedTimeMin'] = remaining_min if remaining_min < 480 else 480-remaining_min
                                        # Initialize the next date if it doesn't exist
                                        dictTskDetailsExcStDateWise[strTskNextExcDate] = {
                                            "TotalWorkMin": 480,
                                            "AllocatedWorkingMin": remaining_min,
                                            "IsConflict": remaining_min > 480,
                                            "AllocatedTask": {strTskID:new_task_details}
                                        }
                                        iTotalExcDateRemainingMin = 0
                                        continue
                                    
                                    availbleNextDateWorkingMin = dictTskDetailsExcStDateWise[strTskNextExcDate]["TotalWorkMin"] - dictTskDetailsExcStDateWise[strTskNextExcDate]["AllocatedWorkingMin"]
                                    new_task_details['AllocatedTimeMin'] = remaining_min if remaining_min <=  availbleNextDateWorkingMin else availbleNextDateWorkingMin
                                    dictTskDetailsExcStDateWise[strTskNextExcDate]["AllocatedTask"][strTskID] = new_task_details
                                    dictTskDetailsExcStDateWise[strTskNextExcDate]["IsConflict"] = (dictTskDetailsExcStDateWise[strTskNextExcDate]["AllocatedWorkingMin"] + remaining_min) > dictTskDetailsExcStDateWise[strTskNextExcDate]["TotalWorkMin"]
                                    dictTskDetailsExcStDateWise[strTskNextExcDate]["AllocatedWorkingMin"] += new_task_details['AllocatedTimeMin']
                                    # Set iTotalExcDateRemainingMin to 0 as it has been exhausted
                                    iTotalExcDateRemainingMin = 0
                                        

                        # Add the task ID to the ordered list
                        lsTskScoreOrder.append(strTskID)

                        if bDebug:
                            print(f"TaskID - {strTskID}, EstimatedMin - {iTotalTskEstMin}, Task Movable - {dictTskDetail['isTaskMovable']}, IsConflict - {dictTskDetail['IsConflict']}")
                            print(f"AllocatedTimeMin - {dictTskDetail.get('AllocatedTimeMin', 'N/A')}, ConflictTimeMin - {dictTskDetail.get('ConflictTimeMin', 'N/A')}")
                            print(f"Remaining Available Minutes - {iTotalExcDateRemainingMin}")

                    # Update the dictionary with the ordered task IDs
                    dictExcDateTskDetails['TaskScoreWiseOrder'] = lsTskScoreOrder

        return dictAllocatedDateWiseTask

if __name__ == "__main__":
    
    list_id = "901600183071"  # Replace with your actual ListID
    start_date = "01-08-2024"  # Replace with your desired start date
    end_date = "01-09-2024"    # Replace with your desired end date
    bDebug = True
    
    # Fetch tasks based on the criteria
    tasks = CClickUpDB.MSGetTasksByListID(list_id, start_date, end_date)
    employee_tasks = CClickUpMiddleWare.MSGroupTaskEmployeeWise(tasks)
    dictAllocatedDateWiseTask = CClickUpMiddleWare.MSCreateEmpDateWiseTasksList(employee_tasks, bDebug=bDebug)
    CClickUpMiddleWare.MSSortEmpDateWiseTskList(dictAllocatedDateWiseTask=dictAllocatedDateWiseTask,employee_tasks=employee_tasks,bDebug=bDebug)