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
from ClickUpHelper import CClickUpHelper


class CClickUpMiddleWare:
    # Purpose - Sort Task Base on Score : Priority Wise =  Normal or Low - 1, High - 2, Urgent - 3 , use list of task for plot
    
    @staticmethod
    def MSGroupTaskEmployeeWise(lsTasks, include_toughness=False, bDebug= False,bSaveFilteredExcelSheet=False, strFilterTaskDirPath= r"Data/"):
        """
        Purpose - To clean list of task such as handling null values or none or Empty values
        """
        dictUserName = {
        'mitul@riveredgeanalytics.com':"Mitul Solanki", 'mansi@riveredgeanalytics.com':"Mansi Solanki", 'hr@riveredgeanalytics.com':"Nidhi",
        'devanshi@riveredgeanalytics.com':"Devanshi Joshi", 'dhruvin@riveredgeanalytics.com':"Dhruvin Kapadiya",
        'mohit.intern@riveredgeanalytics.com':"Mohit", 'harshil@riveredgeanalytics.com':"Harshil Chauhan","fenil@riveredgeanalytics.com":"Fenil","punesh@riveredgeanalytics.com":"Punesh","ankita@riveredgeanalytics.com":"Ankita","nikhil@riveredgeanalytics.com":"Nikhil","mansip@riveredgeanalytics.com":"Mansi P","zahid@riveredgeanalytics.com":"Zahid"
    
        }
        # Creating a DataFrame from the list of tasks
        df = pd.DataFrame(lsTasks)
        
        df['TaskPriority'] = df['TaskPriority'].apply(lambda x: json.loads(x) if x != 'null' else None)
        df['TaskAssigneesList'] = df['TaskAssigneesList'].apply(json.loads)
        
        # Determine Each Task - Task Score Base on Several Criteria
        df['TaskScore'] = df.apply(CClickUpHelper.MSCalculateTaskScore, include_toughness=include_toughness, axis=1)
        
        # Filter Task List - no Estimated Time is Provided
        df = df[df['EstimatedTime'].apply(CClickUpHelper.MSIsEstimatedTimeProvided)]

        # Drop columns except the specified list
        columns_to_keep = ['ListName', 'TaskID', 'TaskSubject', 'TaskStartDate', 'TaskDueDate', 'TaskStatus',
                        'EstimatedTime', 'TaskPriority', 'TaskAssigneesList', 
                        'TaskIsMilestone', 'TaskIntensity', 'TaskScore','TaskCreatedDate']
        
        df = df[columns_to_keep]
        
        
        # Add new columns - for further processing 
        df['EstimatedTime'] = df['EstimatedTime'].apply(json.loads)
        df['TotalTskEstInMins'] = df['EstimatedTime'].apply(lambda x: (x['hrs'] * 60 + x['mins']) if x else 0)
        df['TaskExecutionDate'] = df['TaskStartDate']
        # 2. 'AssignTo' - extract username from the first entry in 'TaskAssigneesList'  || WARN - (Remaining Task) In Case of Multiple Assignees EDGE Case Must Handle 
        df['AssignTo'] = df['TaskAssigneesList'].apply(
            lambda x: x[0]['username'] if x and x[0].get('username') else (x[0]['email'] if x else None)
        )

        # 3. 'TaskPriority' - extract priority
        df['TaskPriority'] = df['TaskPriority'].apply(lambda x: x['priority'] if x else None)

        # 4. 'TaskStatus'
        df['TaskStatus'] = df['TaskStatus'].apply(json.loads)
        df['TaskStatus'] = df['TaskStatus'].apply(lambda x: x['status'] if isinstance(x, dict) else None)

        # df['TaskColorDetails'] = {df['TaskColorDetails'].apply(json.loads)}
        # Creating employee-wise task lists
        dictFilteredEmpWiseTsk = {}
        for _, row in df.iterrows():
            assignees = row['TaskAssigneesList']
            if assignees:
                for assignee in assignees:
                    emailId = assignee['email']
                    username = dictUserName.get(emailId, assignee.get("username")) 
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
    
    @staticmethod
    def MSSt_EdDate(tasks, key="TaskStartDate"):
        if not tasks:
            return None, None
        
        # Extract start and due dates from tasks
        start_dates = [datetime.strptime(task[key], '%d-%m-%Y') for task in tasks]
        due_dates = [datetime.strptime(task['TaskDueDate'], '%d-%m-%Y') for task in tasks]
        
        # Get earliest start date and latest due date
        first_start_date = min(start_dates).strftime('%d-%m-%Y')
        last_due_date = max(due_dates).strftime('%d-%m-%Y')
        
        return first_start_date, last_due_date
    
    @staticmethod
    def MSGetTskByExcDate(tasks, task_execution_date, key = "TaskStartDate"):
        # Convert task_execution_date to datetime for comparison
        task_execution_date = datetime.strptime(task_execution_date, '%d-%m-%Y')
        
        # Filter tasks with the same execution date
        filtered_tasks = [task for task in tasks if datetime.strptime(task[key], '%d-%m-%Y') == task_execution_date]
        
        return filtered_tasks

    @staticmethod
    def MSSortDF(employee_tasks, bDebug, bSaveReportToExcel = False):
        dictEmployeeWiseTaskList = {}

        for EmpName in employee_tasks.keys():
            dictEmployeeWiseTaskList[EmpName] = []
            lsEmployeeTsks = employee_tasks[EmpName]
            if bDebug:
                print("1. Employee Name - ", EmpName)
                print("2. Date Wise Tasks Arrangement - ", lsEmployeeTsks)

            # Get the start and due dates
            strTskExcStDate, strTskDueDate = CClickUpMiddleWare.MSSt_EdDate(lsEmployeeTsks, key='TaskExecutionDate')
            
            if bDebug:
                print(f"3. Employee Task Start Date - {strTskExcStDate}, Task End Date - {strTskDueDate}")
            
            # Convert start and end dates to datetime objects
            current_date = datetime.strptime(strTskExcStDate, '%d-%m-%Y')
            end_date = datetime.strptime(strTskDueDate, '%d-%m-%Y')
            dictAvailableMinDateTemplate = {
                        'ListName': '', 'TaskID': '', 'TaskSubject': '{Employee} is available on day "{strDate}" for {RemainingMin} minutes.', 'TaskStartDate': '', 'TaskDueDate': '', 'TaskStatus': '', 'EstimatedTime': {}, 'TaskPriority': '', 'TaskAssigneesList': [], 'TaskIsMilestone': 0, 'TaskIntensity': 0, 'TaskScore': 0, 'TaskCreatedDate': '', 'TotalTskEstInMins': 0, 'TaskExecutionDate': '', 'AssignTo': '','IsConflict':False,'ConflictTimeMin':0,'AllocatedTimeMin':0
                    }
            # Iterate from start date to due date
            while current_date <= end_date:
                # Convert current_date to string in the required format
                strCurrentDate = current_date.strftime('%d-%m-%Y')

                # Initialize available minutes
                iTotalExcDateRemainingMin = 480  # 8 hours in minutes
                
                # Fetch tasks for the current date
                lsTskExcDate = CClickUpMiddleWare.MSGetTskByExcDate(lsEmployeeTsks, strCurrentDate,  key="TaskExecutionDate")

                # Sort the fetched tasks by TaskScore (descending) and TaskCreatedDate
                lsSortedTsks = sorted(
                    lsTskExcDate,
                    key=lambda x: (-x['TaskScore'], datetime.strptime(x['TaskCreatedDate'], '%d-%m-%Y %H:%M:%S'))
                )

                # Add sorted tasks to the employee's task list
                # dictEmployeeWiseTaskList[EmpName].extend(lsSortedTsks)
                for taskDetail in lsSortedTsks:
                    dictTskDetail = copy.deepcopy(taskDetail)
                    # Access Task Properties
                    iTotalTskEstMin = dictTskDetail['TotalTskEstInMins']
                    strTskExcDate = dictTskDetail['TaskExecutionDate']
                    
                    # add new properties for further processing
                    bIsTskDueDateLater = (dictTskDetail['TaskExecutionDate'] != dictTskDetail['TaskDueDate'])
                    
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
                        if not bIsTskDueDateLater:
                            # Mark Task Conflict as True, when no more days available (Task Exc Date == Task Due Date)
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
                                # Push to the next available date
                                strTskNextExcDate = CClickUpMiddleWare.MSGetNextDate(strTskExcDate)
                                dictNextExcDateTskDetails = copy.deepcopy(taskDetail)
                                dictNextExcDateTskDetails['TaskExecutionDate'] = strTskNextExcDate
                                # add new task for next closest execution date
                                lsEmployeeTsks.append(dictNextExcDateTskDetails)
                                continue
                            else:
                                # Push remaining part of the task to the next date
                                iNextExcDateEstimateMin = iTotalTskEstMin - iTotalExcDateRemainingMin
                                strTskNextExcDate = CClickUpMiddleWare.MSGetNextDate(strTskExcDate)
                                # for current start date
                                dictTskDetail['IsConflict'] =  False
                                dictTskDetail['ConflictTimeMin'] = 0
                                dictTskDetail['AllocatedTimeMin'] = iTotalExcDateRemainingMin
                                
                                dictNextExcDateTskDetails = copy.deepcopy(taskDetail)
                                # Add the remaining part of the task to the next date
                                dictNextExcDateTskDetails['TotalTskEstInMins'] = iNextExcDateEstimateMin
                                dictNextExcDateTskDetails['TaskExecutionDate'] = strTskNextExcDate
                                lsEmployeeTsks.append(dictNextExcDateTskDetails)
                                # Set iTotalExcDateRemainingMin to 0 as it has been exhausted
                                iTotalExcDateRemainingMin = 0
                    dictEmployeeWiseTaskList[EmpName].append(dictTskDetail)
                if iTotalExcDateRemainingMin > 0:
                    dictAvailableTime = copy.deepcopy(dictAvailableMinDateTemplate)
                    dictAvailableTime['TaskSubject'] = dictAvailableTime['TaskSubject'].format(
                        Employee=EmpName, 
                        strDate=strCurrentDate, 
                        RemainingMin=iTotalExcDateRemainingMin
                    )
                    dictAvailableTime['AssignTo'] = EmpName
                    dictAvailableTime['TaskStartDate'] = strCurrentDate
                    dictAvailableTime['TaskDueDate'] = strCurrentDate
                    dictAvailableTime['TaskCreatedDate'] = strCurrentDate
                    dictAvailableTime['TaskExecutionDate'] = strCurrentDate
                    dictAvailableTime['TaskStatus'] = 'idle time'
                    dictAvailableTime['TaskPriority'] = ''
                    # Allocate Idle Time Min
                    dictAvailableTime['AllocatedTimeMin'] = iTotalExcDateRemainingMin
                    dictAvailableTime['TotalTskEstInMins'] = iTotalExcDateRemainingMin
                    dictEmployeeWiseTaskList[EmpName].append(dictAvailableTime)
                if bDebug:
                    print(f"4. Execution Date - {strCurrentDate}, Task List - {lsTskExcDate}")

                # Move to the next day
                current_date += timedelta(days=1)

        if bDebug:
            print("Allocated Task - ", dictEmployeeWiseTaskList)
        if bSaveReportToExcel:
            CClickUpMiddleWare.MSExportEmployeeTask(dictEmployeeWiseTaskList, strTskExcStDate, strTskDueDate)
        return dictEmployeeWiseTaskList

    @staticmethod
    def MSExportEmployeeTask(dictEmployeeWiseTaskList, task_start_date, task_end_date, output_directory=r'Data/'):
        # Iterate over the dictionary containing employee task lists
        for emp_name, task_list in dictEmployeeWiseTaskList.items():
            # Convert the task list to a DataFrame
            df = pd.DataFrame(task_list)
            
            # Construct the file name using the employee name, start date, and end date
            filename = f"{output_directory}/{emp_name}_{task_start_date}_to_{task_end_date}.xlsx"
            
            # Export the DataFrame to an Excel file
            df.to_excel(filename, index=False)
            print(f"Exported tasks for {emp_name} to {filename}")

def update_task_dict(task_dict):
    updated_dict = {}

    # Loop through each employee and their tasks
    for employee, tasks in task_dict.items():
        updated_dict[employee] = []  # Initialize an empty list for updated tasks

        # Iterate over each task for the employee
        for task in tasks:

            # If the task has a conflict and AllocatedTimeMin > 0, split into two tasks
            if task.get('IsConflict', False) and task.get('AllocatedTimeMin', 0) > 0:
                # Create two new tasks based on AllocatedTimeMin and ConflictTimeMin

                # Task with AllocatedTimeMin
                allocated_time_task = task.copy()
                allocated_time_task['AllocatedTimeMin'] = task.get('AllocatedTimeMin', 0)
                allocated_time_task['IsConflict'] = False
                updated_dict[employee].append(allocated_time_task)

                # Task with ConflictTimeMin
                conflict_time_task = task.copy()
                conflict_time_task['AllocatedTimeMin'] = task.get('ConflictTimeMin', 0)
                updated_dict[employee].append(conflict_time_task)
                continue
            # Add the original task to the list
            updated_dict[employee].append(task)
    return updated_dict

        
if __name__ == "__main__":
    pass
    # listIds = ['901601699012', '901604046396', '901600183071', '901604035672', '901604046411', '901604272654', '901603806927', '901603898346']

    # # list_id = "901600183071"  # Replace with your actual ListID
    # start_date = "02-08-2024"  # Replace with your desired start date
    # end_date = "20-09-2024"    # Replace with your desired end date
    # bDebug = True
    
    # # Fetch tasks based on the criteria
    # tasks = CClickUpDB.MSGetTasksByListIDs(listIds, start_date, end_date)
    # employee_tasks = CClickUpMiddleWare.MSGroupTaskEmployeeWise(tasks)
    # # dictAllocatedDateWiseTask = CClickUpMiddleWare.MSCreateEmpDateWiseTasksList(employee_tasks, bDebug=False)
    # # print(dictAllocatedDateWiseTask)
    # print(employee_tasks)
    # input_dict = CClickUpMiddleWare.MSSortDF(employee_tasks, bDebug=True)
    # CClickUpMiddleWare.MSSortEmpDateWiseTskList(dictAllocatedDateWiseTask=dictAllocatedDateWiseTask,employee_tasks=employee_tasks,bDebug=bDebug)
    
    # Example input
    # task_dict = {
    #     "Mitul Solanki": [
    #         {
    #             "ListName": "ERPNext",
    #             "TaskID": "86cw7wkbw",
    #             "TaskSubject": "Restore V14 Data in V15",
    #             "TaskStartDate": "04-08-2024",
    #             "TaskDueDate": "05-08-2024",
    #             "TaskStatus": "delivered",
    #             "EstimatedTime": {"hrs": 24, "mins": 0, "time_estimate": 86400000},
    #             "TaskPriority": "urgent",
    #             "TaskAssigneesList": [
    #                 {"id": 67390920, "color": "", "email": "mitul@riveredgeanalytics.com", "initials": "MS", "username": "Mitul Solanki", "profilePicture": "https://attachments.clickup.com/profilePictures/67390920_BGd.jpg"}
    #             ],
    #             "TaskIsMilestone": 0,
    #             "TaskIntensity": 1,
    #             "TaskScore": 3,
    #             "TaskCreatedDate": "14-08-2024 12:34:56",
    #             "TotalTskEstInMins": 90,
    #             "TaskExecutionDate": "05-09-2024",
    #             "AssignTo": "Mitul Solanki",
    #             "IsConflict": False,
    #             "ConflictTimeMin": 0,
    #             "AllocatedTimeMin": 90,
    #             "RemainingMin": ""
    #         },
    #         {
    #             "ListName": "ERPNext",
    #             "TaskID": "86cw7wkbw",
    #             "TaskSubject": "Restore V14 Data in V15",
    #             "TaskStartDate": "04-08-2024",
    #             "TaskDueDate": "05-08-2024",
    #             "TaskStatus": "delivered",
    #             "EstimatedTime": {"hrs": 24, "mins": 0, "time_estimate": 86400000},
    #             "TaskPriority": "urgent",
    #             "TaskAssigneesList": [
    #                 {"id": 67390920, "color": "", "email": "mitul@riveredgeanalytics.com", "initials": "MS", "username": "Mitul Solanki", "profilePicture": "https://attachments.clickup.com/profilePictures/67390920_BGd.jpg"}
    #             ],
    #             "TaskIsMilestone": 0,
    #             "TaskIntensity": 1,
    #             "TaskScore": 3,
    #             "TaskCreatedDate": "14-08-2024 12:34:56",
    #             "TotalTskEstInMins": 480,
    #             "TaskExecutionDate": "05-09-2024",
    #             "AssignTo": "Mitul Solanki",
    #             "IsConflict": True,
    #             "ConflictTimeMin": 90,
    #             "AllocatedTimeMin": 390,
    #             "RemainingMin": ""
    #         },
    #         {
    #             "ListName": "ERPNext",
    #             "TaskID": "86cw7x8v2",
    #             "TaskSubject": "Mitul - Department & Module Access",
    #             "TaskStartDate": "06-08-2024",
    #             "TaskDueDate": "06-08-2024",
    #             "TaskStatus": "delivered",
    #             "EstimatedTime": {"hrs": 1, "mins": 0, "time_estimate": 3600000},
    #             "TaskPriority": "urgent",
    #             "TaskAssigneesList": [
    #                 {"id": 67390920, "color": "", "email": "mitul@riveredgeanalytics.com", "initials": "MS", "username": "Mitul Solanki", "profilePicture": "https://attachments.clickup.com/profilePictures/67390920_BGd.jpg"}
    #             ],
    #             "TaskIsMilestone": 0,
    #             "TaskIntensity": 1,
    #             "TaskScore": 2,
    #             "TaskCreatedDate": "14-08-2024 13:34:34",
    #             "TotalTskEstInMins": 240,
    #             "TaskExecutionDate": "06-08-2024",
    #             "AssignTo": "Mitul Solanki",
    #             "IsConflict": False,
    #             "RemainingMin": "",
    #             "AllocatedTimeMin": 240,
    #             "ConflictTimeMin": 0
    #         }
    #     ]
    # }

    # # Call the function
    # updated_dict = update_task_dict(task_dict)

    # # Print updated dict
    # import pprint
    # pprint.pprint(updated_dict)
