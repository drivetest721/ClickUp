
import json
import pandas as pd

def readJson(strFileName):
    dictData = None
    with open(strFileName,'r') as file:
        dictData = json.load(file)
    return dictData

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


import random
import string

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