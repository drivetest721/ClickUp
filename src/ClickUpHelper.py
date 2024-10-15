import json
import os
import re
from datetime import datetime
import pandas as pd
import webcolors


class CClickUpHelper:
    
    @staticmethod
    def get1stAssigneeEmailId(dictTaskAssigneeDetails):
        assignees_list = dictTaskAssigneeDetails
        # Deserialize TaskAssigneesList if it's a JSON string
        if isinstance(assignees_list, str):
            try:
                assignees_list = json.loads(assignees_list)
            except json.JSONDecodeError:
                print(f"Error decoding TaskAssigneesList for task")
                return []
        if isinstance(assignees_list,list) and len(assignees_list) > 0:
            # Normalize the username by removing spaces and converting to lowercase
            emailId = assignees_list[0].get('email', '').lower()
        else:
            emailId = None
        return emailId
    
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
    def MSConvertTimeStampToDate(timestamp, format='%d-%m-%Y'):
        if timestamp is not None and timestamp != "None":
            # Convert timestamp (in milliseconds) to a datetime object
            date_obj = datetime.fromtimestamp(int(timestamp) / 1000)
            # Format datetime object to 'DD-MM-YYYY HH:MM:SS %H:%M:%S' format
            formatted_date = date_obj.strftime(format)
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
    def MSCalculateTaskScore(row, include_toughness=False, bIncludeAssignBy=False):
        # Priority scoring
        priority_score = 1  # Default score
        if row['TaskPriority'] and row['TaskPriority'] != 'null':
            priority = row['TaskPriority'].get('priority', 'normal')
            if priority == 'urgent':
                priority_score = 3
            elif priority == 'high':
                priority_score = 2
            elif priority in ['normal', 'low']:
                priority_score = 1

        # Toughness scoring
        toughness_score = row['TaskIntensity'] if include_toughness else 0

        # AssignByDetails and WatchersList scoring
        assign_by_score = 0  # Default to 0 if not including assign-by score
        if bIncludeAssignBy:
            email_list = []

            # Extract email from AssignByDetails
            assign_by_details = row.get("AssignByPersonDetails", {})
            assign_by_email = assign_by_details.get("email", "")
            if assign_by_email:
                email_list.append(assign_by_email)

            # Extract emails from WatchersList
            watchers_list = row.get("WatchersList", [])
            for watcher in watchers_list:
                watcher_email = watcher.get("email", "")
                if watcher_email:
                    email_list.append(watcher_email)

            # Check for specific email categories
            if any(email in email_list for email in ["anirudh@riveredgeanalytics.com", "smeeta@riveredgeanalytics.com"]):
                assign_by_score += 2
            elif any(email in email_list for email in ["nikhil@riveredgeanalytics.com", "harshil@riveredgeanalytics.com", "hr@riveredgeanalytics.com"]):
                assign_by_score += 1

        # Total score
        return priority_score + toughness_score + assign_by_score

    @staticmethod
    def MSIsEstimatedTimeProvided(estimated_time):
      
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
        df['TaskScore'] = df.apply(CClickUpHelper.MSCalculateTaskScore, include_toughness=False, axis=1)
        
        df = df[df['EstimatedTime'].apply(CClickUpHelper.MSIsEstimatedTimeProvided)]

        # Convert 'TaskStartDate' to datetime for sorting
        df['TaskStartDate'] = pd.to_datetime(df['TaskStartDate'], format='%d-%m-%Y')

        # Sort tasks by 'TaskStartDate' ascending, then by 'TaskScore' ascending within the same date
        df = df.sort_values(by=['TaskStartDate', 'TaskScore'])
        
        # Drop columns except the specified list
        columns_to_keep = ['ListName', 'TaskID', 'TaskSubject', 'TaskStartDate', 'TaskDueDate', 
                        'EstimatedTime', 'TaskPriority', 'TaskAssigneesList', 
                        'TaskIsMilestone', 'TaskIntensity', 'TaskScore','TaskAssigneeEmailId']
        df = df[columns_to_keep]
        
        # Creating employee-wise DataFrames
        employee_tasks = {}
        for _, row in df.iterrows():
            assignees = row['TaskAssigneesList']
            if assignees:
                for assignee in assignees:
                    username = assignee['username']
                    camelcase_username = ' '.join([word.capitalize() for word in username.split()])
                    # Add tasks to the dictionary
                    if camelcase_username not in employee_tasks:
                        employee_tasks[camelcase_username] = []
                    employee_tasks[camelcase_username].append(row)

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
    
    def rgb_to_color_name(rgb_string):
        # Extract the RGB values from the input string
        try:
            rgb_values = rgb_string.strip('rgb()').split(',')
            rgb_values = [int(val.strip()) for val in rgb_values]
            
            # Get the color name closest to the given RGB value
            try:
                # If exact match found
                color_name = webcolors.rgb_to_name(rgb_values)
            except ValueError:
                # If no exact match found, find the closest color
                closest_color = CClickUpHelper.closest_color_name(rgb_values)
                color_name = f"Closest match: {closest_color}"
            
            return color_name
        except Exception as e:
            return f"Error parsing the input: {e}"

    def closest_color_name(requested_rgb):
        # Find the closest color name by calculating the Euclidean distance between the input and known colors
        min_diff = float('inf')
        closest_name = ""
        for hex_color, name in webcolors.CSS3_HEX_TO_NAMES.items():
            r, g, b = webcolors.hex_to_rgb(hex_color)
            diff = (r - requested_rgb[0]) ** 2 + (g - requested_rgb[1]) ** 2 + (b - requested_rgb[2]) ** 2
            if diff < min_diff:
                min_diff = diff
                closest_name = name
        return closest_name