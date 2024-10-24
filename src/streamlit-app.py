import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
from PlotMain import GanttChart
from ClickUpAPI import CClickUpAPI
from helperFunc import readJson

# Helper function to calculate default dates
def get_default_dates():
    current_date = datetime.now()
    start_date = current_date - timedelta(weeks=1)
    end_date = current_date + timedelta(weeks=3)
    return start_date.date(), end_date.date()

def clean_task_data(dictEmptasks):
    """
    Cleans and filters each employee's task data to ensure all values are of valid types.
    Only includes selected columns.
    """
    selected_columns = [
        'TaskID', 'TaskSubject', 'TaskStatus', 'TaskPriority', 'AssignTo',
        'TaskScore', 'TaskExecutionDate', 'TaskStartDate', 'TaskDueDate',
        'IsConflict', 'ConflictTimeMin', 'AllocatedTimeMin'
    ]
    
    cleaned_dict = {}

    for emp_name, task_list in dictEmptasks.items():
        cleaned_tasks = []
        
        for task in task_list:
            cleaned_task = {}
            for key in selected_columns:
                value = task.get(key, None)
                if value is None:
                    cleaned_task[key] = ''
                elif isinstance(value, (list, dict)):
                    cleaned_task[key] = str(value)
                elif isinstance(value, (str, int, float, bool)):
                    cleaned_task[key] = value
                else:
                    cleaned_task[key] = str(value)
            
            cleaned_tasks.append(cleaned_task)
        
        cleaned_dict[emp_name] = cleaned_tasks
    
    return cleaned_dict

def Master(lsEmps, lsProjects, StartDate="25-08-2024", EndDate="20-09-2024", bTaskIntensityInclude=False, bFetchLatest=False):
    """
    Placeholder Master function returning a dummy Plotly figure.
    """
    """
        Input:-  1. lsEmps - List of Employee uniquely identified emailIds
                 2. lsProjects - List of clickup unique ListID
                 3. StartDate - date range start date
                 4. EndDate - date range end date
                 5. bFetchLatest - to fetch new data then perform further operation
    """      
    if bFetchLatest:
        # lsProjects - Clickup Unique ListIDs
        CClickUpAPI.MSFetchTaskOnListsOfIDs(lsListIDs=lsProjects)
    
    dictDimensionConfig = readJson(r"resource\dimension_config.json")
    isThicknessEnabled = (dictDimensionConfig.get("thickness").get("selected")) != ""
    isPatternEnabled = (dictDimensionConfig.get("pattern").get("selected")) != ""
    isColorEnabled =  (dictDimensionConfig.get("color").get("selected")) != ""
    
    # Assuming the GanttChart class is already defined
    objGanttChart = GanttChart()
    
    # Fetching employee tasks for the given date range
    dictEmptasks = objGanttChart.Main(lsListIDs= lsProjects, strTskStDate=StartDate, strTskEndDate=EndDate, lsEmployees=lsEmps,include_toughness=bTaskIntensityInclude)


    # Dictionary to store the last task end time for each employee per day
    last_task_end_time_per_emp = {}

    for EmpName, lsEmpTasks in dictEmptasks.items():
        count = 1
        for taskDetail in lsEmpTasks:
            
            
            # Check if the task has a conflict and if AllocatedTimeMin > 0
            if taskDetail.get("IsConflict", False) and taskDetail.get("AllocatedTimeMin", 0) > 0:
                # Split into two tasks: allocated time and conflict time

                # Task with AllocatedTimeMin
                allocated_time_task = taskDetail.copy()
                allocated_time_task['AllocatedTimeMin'] = taskDetail.get('AllocatedTimeMin', 0)
                allocated_time_task['IsConflict'] = False

                # Task with ConflictTimeMin
                conflict_time_task = taskDetail.copy()

                conflict_time_task['TotalTskEstInMins'] = allocated_time_task['TotalTskEstInMins'] - allocated_time_task['AllocatedTimeMin']
                conflict_time_task['AllocatedTimeMin'] = taskDetail.get('ConflictTimeMin', 0)
                conflict_time_task['IsConflict'] = True

                # Process the allocated task
                for task in [allocated_time_task, conflict_time_task]:
                    start_time_str = task['TaskExecutionDate']
                    if task['TaskExecutionDate']:
                        try:
                            start_time_str += ' ' + task['TaskExecutionDate'].split(' ')[1]
                        except IndexError:
                            start_time_str += ' 00:00:00'  # Default to midnight if no time is present
                    else:
                        start_time_str += ' 00:00:00'  # Default to midnight if no time is present

                    # Convert the start_time_str to a datetime object
                    try:
                        start_time = datetime.strptime(start_time_str, '%d-%m-%Y %H:%M:%S')
                    except ValueError:
                        print(f"Error parsing start time: {start_time_str}")
                        start_time = datetime.strptime(task['TaskExecutionDate'], '%d-%m-%Y')

                    # Determine task duration (in minutes)
                    duration = timedelta(minutes=task.get('AllocatedTimeMin', 0))

                    # Track the last end time for each employee and day
                    task_date = start_time.date()

                    if EmpName not in last_task_end_time_per_emp:
                        last_task_end_time_per_emp[EmpName] = {}

                    if task_date in last_task_end_time_per_emp[EmpName]:
                        # Start the task from the previous task's end time
                        start_time = last_task_end_time_per_emp[EmpName][task_date]
                    else:
                        # It's a new day for this employee, start as per the task's TaskExecutionDate
                        last_task_end_time_per_emp[EmpName][task_date] = start_time

                    # Calculate the task's end time (start_time + duration)
                    end_time = start_time + duration
                    # Update the last task end time for this date
                    last_task_end_time_per_emp[EmpName][task_date] = end_time

                    # Get color based on color type (status or priority)
                    if task.get("IsConflict",False):
                        color = "rgb(255, 0, 0)"
                        print("Conflict color choosen ---------------",color)
                    elif task.get("TaskStatus").lower() == "idle time":
                        color = "rgb(197, 197, 197)"
                    else:
                        color = objGanttChart.MGetTskColor(dictDimensionConfig=dictDimensionConfig, dictTskDetails=task)
                    if isThicknessEnabled:
                        bar_width = GanttChart.MSGetThickness(dictDimensionConfig=dictDimensionConfig, dictTskDetails=task)


                    pattern = objGanttChart.MGetPattern(dictDimensionConfig=dictDimensionConfig, dictTskDetails=task)
                    # Get pattern based on task status
                    status = task.get("TaskStatus", "open")  # Assuming status is a string
                    # print("status", status, "pattern---------", pattern, "bar_width", bar_width)
                    priority = task.get("TaskPriority", "low")
                    if priority is None:
                        priority = "low" 
                    # Handle task conflict color
                    strTaskDetail = objGanttChart.MSGenerateLegend(task)
                    
                    # strTskSubject = f"<b>{count}. {task.get('TaskSubject', '')}</b> {status} {priority}"
                    # strTskSubject =  f"<span style='font-size:20px;'><b>{count}. {task.get('TaskSubject', '')}</b> {status} {priority}</span>"
                    if priority == "urgent":
                        strTskSubject = f"<span style='font-size:20px;'><b>{count}. {task.get('TaskSubject', '')}</b> {status} {priority}</span>"
                    elif priority in ["normal", "high"]:
                        strTskSubject = f"<span style='font-size:20px;'><i>{count}. {task.get('TaskSubject', '')}</i> {status} {priority}</span>"
                    elif priority == "low":
                        strTskSubject = f"<span style='font-size:20px;'>{count}. {task.get('TaskSubject', '')} {status} {priority}</span>"
                    else:
                        strTskSubject = f"<span style='font-size:20px;'>{count}. {task.get('TaskSubject', '')} {status} No-Priority</span>"
                    # Add task to Gantt chart
                    objGanttChart.add_task(
                        task_name=strTskSubject,
                        person=EmpName,
                        start_datetime=start_time,
                        duration=duration,
                        color=color,
                        pattern=pattern,
                        bar_width=bar_width,
                        strLegendData=strTaskDetail
                    )
                    count+=1
            else:
                # Process the task as usual if there is no conflict
                start_time_str = taskDetail['TaskExecutionDate']
                if taskDetail['TaskExecutionDate']:
                    try:
                        start_time_str += ' ' + taskDetail['TaskExecutionDate'].split(' ')[1]
                    except IndexError:
                        start_time_str += ' 00:00:00'  # Default to midnight if no time is present
                else:
                    start_time_str += ' 00:00:00'  # Default to midnight if no time is present

                # Convert the start_time_str to a datetime object
                try:
                    start_time = datetime.strptime(start_time_str, '%d-%m-%Y %H:%M:%S')
                except ValueError:
                    print(f"Error parsing start time: {start_time_str}")
                    start_time = datetime.strptime(taskDetail['TaskExecutionDate'], '%d-%m-%Y')

                # Determine task duration (in minutes)
                if taskDetail.get("IsConflict", False) and taskDetail.get("ConflictTimeMin", 0) > 0:
                    duration = timedelta(minutes=taskDetail.get('ConflictTimeMin', 0))
                else:
                    duration = timedelta(minutes=taskDetail.get('AllocatedTimeMin', 0))

                # Track the last end time for each employee and day
                task_date = start_time.date()

                if EmpName not in last_task_end_time_per_emp:
                    last_task_end_time_per_emp[EmpName] = {}

                if task_date in last_task_end_time_per_emp[EmpName]:
                    # Start the task from the previous task's end time
                    start_time = last_task_end_time_per_emp[EmpName][task_date]
                else:
                    # It's a new day for this employee, start as per the task's TaskExecutionDate
                    last_task_end_time_per_emp[EmpName][task_date] = start_time

                # Calculate the task's end time (start_time + duration)
                end_time = start_time + duration
                # Update the last task end time for this date
                last_task_end_time_per_emp[EmpName][task_date] = end_time

                # Get color based on color type (status or priority)
                if isColorEnabled:
                    if taskDetail.get("IsConflict",False):
                        color = "rgb(255, 0, 0)"
                        print("Conflict color choosen ---------------",color)
                    elif taskDetail.get("TaskStatus").lower() == "idle time":
                        color = "rgb(197, 197, 197)"
                        print("Idle color choosen ---------------",color)
                    else:
                        color = objGanttChart.MGetTskColor(dictDimensionConfig=dictDimensionConfig, dictTskDetails=taskDetail)
                else:
                    color = None
                    
                if isThicknessEnabled:
                    bar_width = GanttChart.MSGetThickness(dictDimensionConfig=dictDimensionConfig, dictTskDetails=taskDetail)
                else:
                    bar_width = None

                if isPatternEnabled:
                    pattern = objGanttChart.MGetPattern(dictDimensionConfig=dictDimensionConfig, dictTskDetails=taskDetail)
                else:
                    pattern = None
                
                # Get pattern based on task status
                status = taskDetail.get("TaskStatus", "open")  # Assuming status is a string
                priority = taskDetail.get("TaskPriority", "low")
                if priority is None:
                    priority = "low" 
                # Handle task conflict color
                strTaskDetail = objGanttChart.MSGenerateLegend(taskDetail)
                # strTskSubject = f"<b>{count}. {taskDetail.get('TaskSubject', '')}</b> {status} {priority}"
                # strTskSubject = f"<span style='font-size:20px;'><b>{count}. {taskDetail.get('TaskSubject', '')}</b> {status} {priority}</span>"

                if priority == "urgent":
                    strTskSubject = f"<span style='font-size:20px;'><b>{count}. {taskDetail.get('TaskSubject', '')}</b> {status} {priority}</span>"
                elif priority in ["normal", "high"]:
                    strTskSubject = f"<span style='font-size:20px;'><i>{count}. {taskDetail.get('TaskSubject', '')}</i> {status} {priority}</span>"
                elif priority == "low":
                    strTskSubject = f"<span style='font-size:20px;'>{count}. {taskDetail.get('TaskSubject', '')} {status} {priority}</span>"
                else:
                    strTskSubject = f"<span style='font-size:20px;'>{count}. {taskDetail.get('TaskSubject', '')} {status} No-Priority</span>"
                # Add task to Gantt chart
                objGanttChart.add_task(
                    task_name=strTskSubject,
                    person=EmpName,
                    start_datetime=start_time,
                    duration=duration,
                    color=color,
                    pattern=pattern,
                    bar_width=bar_width,
                    strLegendData=strTaskDetail
                )
                count +=1
    # Create and display the Gantt chart
    fig = objGanttChart.create_chart(title="Employee Wise Gantt Chart")
    return fig

# Get default start and end dates
default_start_date, default_end_date = get_default_dates()

# Streamlit App
st.set_page_config(layout="wide")
st.title("Task Management Dashboard")

# Sidebar Section
st.sidebar.header("Filters")

# Toggle Button for Report Overview (Use expander in Streamlit)
with st.sidebar.expander("Report Overview ▶", expanded=False):
    st.write("Selected Employees: ...")
    st.write("Selected Projects: ...")
    st.write(f"Start Date: {default_start_date}")
    st.write(f"End Date: {default_end_date}")
    st.write("Task Intensity Wise Score: ...")
    st.write("Fetch Latest Date: ...")

# Inputs Section
st.sidebar.subheader("Select Employee Name:")
select_all_employees = st.sidebar.checkbox("Select All Employees", False)
employee_names = st.sidebar.multiselect(
    "Employees",
    options=[
        'mitul@riveredgeanalytics.com', 'mansi@riveredgeanalytics.com', 'hr@riveredgeanalytics.com',
        'devanshi@riveredgeanalytics.com', 'dhruvin@riveredgeanalytics.com',
        'mohit.intern@riveredgeanalytics.com', 'harshil@riveredgeanalytics.com',"fenil@riveredgeanalytics.com","punesh@riveredgeanalytics.com","ankita@riveredgeanalytics.com","nikhil@riveredgeanalytics.com","mansip@riveredgeanalytics.com","zahid@riveredgeanalytics.com"
    ],
    default=[] if not select_all_employees else [
        'mitul@riveredgeanalytics.com', 'mansi@riveredgeanalytics.com', 'hr@riveredgeanalytics.com',
        'devanshi@riveredgeanalytics.com', 'dhruvin@riveredgeanalytics.com',
        'mohit.intern@riveredgeanalytics.com', 'harshil@riveredgeanalytics.com',"fenil@riveredgeanalytics.com","punesh@riveredgeanalytics.com","ankita@riveredgeanalytics.com","nikhil@riveredgeanalytics.com","mansip@riveredgeanalytics.com","zahid@riveredgeanalytics.com"
    ]
)
"""
IKIO - https://app.clickup.com/9002231030/v/li/901604664293
Bright Future - https://app.clickup.com/9002231030/v/li/901604664323
DHOA - https://app.clickup.com/9002231030/v/li/901604664325
EKam - https://app.clickup.com/9002231030/v/li/901604664326
Royalux - https://app.clickup.com/9002231030/v/li/901604664327
RV - https://app.clickup.com/9002231030/v/li/901604664329
IKIO 150 Industrial - https://app.clickup.com/9002231030/v/li/901604664340

"""
st.sidebar.subheader("Select Project Name:")
select_all_projects = st.sidebar.checkbox("Select All Projects", False)
project_names = st.sidebar.multiselect(
    "Projects",
    options=['901601699012', '901600183071', '901603806927',"901604664293","901604664323","901604664325","901604664326","901604664327","901604664329","901604664340"],
    default=[] if not select_all_projects else ['901601699012', '901600183071', '901603806927',"901604664293","901604664323","901604664325","901604664326","901604664327","901604664329","901604664340"]
)

st.sidebar.subheader("Select Start and End Date:")
start_date = st.sidebar.date_input("Start Date", default_start_date)
end_date = st.sidebar.date_input("End Date", default_end_date)

task_intensity_value = st.sidebar.checkbox("Task Intensity Wise Score", False)
fetch_latest_value = st.sidebar.checkbox("Fetch Latest Date", False)



# Generate Report Button
if st.sidebar.button("Generate Report"):
    # Convert start_date and end_date to "DD-MM-YYYY" format
    start_date = start_date.strftime('%d-%m-%Y')
    end_date = end_date.strftime('%d-%m-%Y')

    # Assume Master returns a plotly figure based on inputs
    fig = Master(
        lsEmps=employee_names, 
        lsProjects=project_names, 
        StartDate=start_date, 
        EndDate=end_date,
        bTaskIntensityInclude=task_intensity_value, 
        bFetchLatest=fetch_latest_value
    )
    
    # Create the Plot Area
    st.plotly_chart(fig, use_container_width=True)

    # Prepare list to hold all employee data tables
    employee_data_tables = []

    # Assuming the GanttChart class is already defined
    objGanttChart = GanttChart()
    
    # Fetching employee tasks for the given date range
    dictEmptasks = objGanttChart.Main(
        lsListIDs=project_names, 
        strTskStDate=start_date, 
        strTskEndDate=end_date, 
        lsEmployees=employee_names,
        include_toughness=task_intensity_value
    )
    
    # Clean the task data
    cleaned_dictEmptasks = clean_task_data(dictEmptasks)

    # Display Data Tables for each employee
    for EmpName, lsEmpTasks in cleaned_dictEmptasks.items():
        df_tasks = pd.DataFrame(lsEmpTasks)
        st.subheader(f"Tasks for {EmpName}")
        st.dataframe(df_tasks)
        
        
# streamlit run src\streamlit-app.py



