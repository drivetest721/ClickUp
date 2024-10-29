import random
import string
import json
import pandas as pd

def readJson(strFileName):
    dictData = None
    with open(strFileName,'r') as file:
        dictData = json.load(file)
    return dictData

# Function to get unique customers and projects
def get_filtered_data(data, customer=None):
    if customer:
        filtered_data = [entry for entry in data if entry['Customer'] == customer]
    else:
        filtered_data = data
    return filtered_data

# Helper function to convert minutes to "hours and minutes" format
def GetTimeInHrsAndMins(minutes):
    if minutes <= 0:
        return "0 minutes"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    time_str = (f"{hours} hrs " if hours > 0 else "") + (f"{remaining_minutes} mins" if remaining_minutes > 0 else "")
    return time_str

def FilterOutIdleTasks(lsEmpTasks):
    """
    Filters out tasks with the status 'idle time' from the input list of tasks.
    
    Args:
    - lsEmpTasks (list): List of task dictionaries.
    
    Returns:
    - list: Filtered list of tasks without 'idle time' status.
    """
    # Convert list of tasks to DataFrame
    df_tasks = pd.DataFrame(lsEmpTasks)
    
    # Filter out rows where TaskStatus is 'idle time'
    df_filtered = df_tasks[df_tasks['TaskStatus'].str.lower() != 'idle time']
    
    # Convert the filtered DataFrame back to a list of dictionaries
    filtered_tasks = df_filtered.to_dict(orient='records')
    
    return filtered_tasks



def generate_random_alphanumeric_code(length=5):
    """
    Generates a random alphanumeric code of the specified length.
    
    Args:
    - length (int): The length of the alphanumeric code (default is 5).
    
    Returns:
    - str: A random alphanumeric code.
    """
    characters = string.ascii_letters + string.digits
    random_code = ''.join(random.choices(characters, k=length))
    return random_code



def find_employee_info(employee_name, employee_dict):
    """
    Finds the email and name of an employee given the employee's name.

    Parameters:
    - employee_name (str): The name of the employee to search for.
    - employee_dict (dict): A dictionary with email as keys and full names as values.

    Returns:
    - tuple: (email, full_name) if a match is found, else None.
    """
    for email, full_name in employee_dict.items():
        if full_name == employee_name:
            return email, full_name
    return False