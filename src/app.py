from msvcrt import getch
import dash
import json
from dash import dcc, html, Input, Output, State
from datetime import datetime, timedelta
from PlotMain import GanttChart
from ClickUpAPI import CClickUpAPI
from ClickUpDB import CClickUpDB

# Initialize the Dash app
app = dash.Dash(__name__)

# Helper function to calculate default dates
def get_default_dates():
    current_date = datetime.now()
    start_date = current_date - timedelta(weeks=1)
    end_date = current_date + timedelta(weeks=3)
    return start_date.date(), end_date.date()

# Get default start and end dates
default_start_date, default_end_date = get_default_dates()

# Define layout
app.layout = html.Div([
    # Select Employee Name (with 'All' option)
    html.Label('Select Employee Name:'),
    dcc.Checklist(
        id='select-all-employees',
        options=[{'label': 'All', 'value': 'all'}],
        value=[]
    ),
    dcc.Dropdown(
        id='employee-names',
        options=[
            {'label': 'Mitul Solanki', 'value': 'mitul@riveredgeanalytics.com'},
            {'label': 'Mansi', 'value': 'mansi@riveredgeanalytics.com'},
            {'label': 'Nidhi', 'value': 'hr@riveredgeanalytics.com'},
            {'label': 'Devanshi', 'value': 'devanshi@riveredgeanalytics.com'},
            {'label': 'Dhruvin Kapadiya', 'value': 'dhruvin@riveredgeanalytics.com'},
            {'label': 'Mohit Parmar', 'value': 'mohit.intern@riveredgeanalytics.com'},
            {'label': 'Harshil Chauhan', 'value': 'harshil@riveredgeanalytics.com'},
        ],
        multi=True,
        value=[]
    ),
    
    # Select Project Name (with 'All' option)
    html.Label('Select Project Name:'),
    dcc.Checklist(
        id='select-all-projects',
        options=[{'label': 'All', 'value': 'all'}],
        value=[]
    ),
    dcc.Dropdown(
        id='project-names',
        options=[
            {'label': 'AccuVelocity', 'value': '901601699012'},
            {'label': 'ERPNext', 'value': 'ERPNext'},
            {'label': 'ClickUp', 'value': 'ClickUp'}
        ],
        multi=True,
        value=[]
    ),
    
    # Start Date and End Date Input
    html.Label('Select Start and End Date:'),
    dcc.DatePickerRange(
        id='date-range',
        min_date_allowed=datetime(2020, 1, 1),
        max_date_allowed=datetime(2030, 12, 31),
        start_date=default_start_date,
        end_date=default_end_date
    ),

    # Task Intensity Wise Score Checkbox
    html.Label('Task Intensity Wise Score:'),
    dcc.Checklist(
        id='task-intensity-wise-score',
        options=[{'label': 'Task Intensity Wise Score', 'value': 'True'}],
        value=[]
    ),

    # Fetch Latest Date Checkbox
    html.Label('Fetch Latest Date:'),
    dcc.Checklist(
        id='fetch-latest-date',
        options=[{'label': 'Fetch Latest Date', 'value': 'True'}],
        value=[]
    ),
    
    # Submit Button
    html.Button('Submit', id='submit-button', n_clicks=0),

    # Output Div to display selected inputs
    html.Div(id='output-data')
])

# Callback for selecting/deselecting all employees
@app.callback(
    Output('employee-names', 'value'),
    [Input('select-all-employees', 'value')],
    [State('employee-names', 'options')]
)
def select_all_employees(select_all, employee_options):
    if 'all' in select_all:
        return [opt['value'] for opt in employee_options]
    return []

# Callback for selecting/deselecting all projects
@app.callback(
    Output('project-names', 'value'),
    [Input('select-all-projects', 'value')],
    [State('project-names', 'options')]
)
def select_all_projects(select_all, project_options):
    if 'all' in select_all:
        return [opt['value'] for opt in project_options]
    return []

# Callback for handling form submission and displaying output
@app.callback(
    Output('output-data', 'children'),
    [Input('submit-button', 'n_clicks')],
    [
        State('employee-names', 'value'),
        State('project-names', 'value'),
        State('date-range', 'start_date'),
        State('date-range', 'end_date'),
        State('task-intensity-wise-score', 'value'),
        State('fetch-latest-date', 'value')
    ]
)
def display_user_inputs(n_clicks, employee_names, project_names, start_date, end_date, task_intensity, fetch_latest):
    if n_clicks > 0:
        task_intensity_value = True if 'True' in task_intensity else False
        fetch_latest_value = True if 'True' in fetch_latest else False
        
        return html.Div([
            html.P(f'Selected Employees: {employee_names}'),
            html.P(f'Selected Projects: {project_names}'),
            html.P(f'Start Date: {start_date}'),
            html.P(f'End Date: {end_date}'),
            html.P(f'Task Intensity Wise Score: {task_intensity_value}'),
            html.P(f'Fetch Latest Date: {fetch_latest_value}')
        ])
    return ""

def update_gantt_chart(n_clicks, employee_names, project_names, start_date, end_date, task_intensity, fetch_latest):
    if n_clicks > 0:
        # Simulate fetching employee tasks (replace with actual logic)
        with open(r"resource\dimension_config.json") as f:
            dictDimensionConfig = json.load(f) 
        # Assuming the GanttChart class is already defined
        objGanttChart = GanttChart()
        lsSelectedEmployee = employee_names
        dictEmptasks = objGanttChart.Main(lsListIDs=project_names, 
                                          strTskStDate=start_date, strTskEndDate=end_date)
        strColorType = "status"  # Could also be "priority"

        # Dictionary to store the last task end time for each employee per day
        last_task_end_time_per_emp = {}

        Idx = 0
        for EmpName, lsEmpTasks in dictEmptasks.items():
            lsColors = ['rgb(127, 0, 0)', 'rgb(0, 0, 64)', 'rgb(255, 0, 0)']
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

                        bar_width = GanttChart.MSGetThickness(dictDimensionConfig=dictDimensionConfig, dictTskDetails=task)


                        pattern = GanttChart.MSGetPattern(dictDimensionConfig=dictDimensionConfig, dictTskDetails=task)
                        # Get pattern based on task status
                        status = task.get("TaskStatus", "open").lower()  # Assuming status is a string
                        print("status", status, "pattern---------", pattern, "bar_width", bar_width)

                        # Handle task conflict color
                        strTaskDetail = objGanttChart.MSGenerateLegend(task)
                        strTskSubject = f"{count}. "+ taskDetail.get("TaskSubject", "")
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
                    if taskDetail.get("IsConflict",False):
                        color = "rgb(255, 0, 0)"
                        print("Conflict color choosen ---------------",color)
                    elif taskDetail.get("TaskStatus").lower() == "idle time":
                        color = "rgb(197, 197, 197)"
                        print("Idle color choosen ---------------",color)
                    else:
                        color = objGanttChart.MGetTskColor(dictDimensionConfig=dictDimensionConfig, dictTskDetails=taskDetail)

                    bar_width = GanttChart.MSGetThickness(dictDimensionConfig=dictDimensionConfig, dictTskDetails=taskDetail)


                    pattern = GanttChart.MSGetPattern(dictDimensionConfig=dictDimensionConfig, dictTskDetails=taskDetail)

                    # Get pattern based on task status
                    status = taskDetail.get("TaskStatus", "open").lower()  # Assuming status is a string
                    print("status", status, "pattern---------", pattern, "bar_width", bar_width)

                    # Handle task conflict color
                    strTaskDetail = objGanttChart.MSGenerateLegend(taskDetail)
                    strTskSubject = f"{count}. "+ taskDetail.get("TaskSubject", "")
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
            Idx += 1
        
        # Create the Gantt chart
        fig = objGanttChart.create_chart(title="Employee Wise Gantt Chart")
        
        return fig
    else:
        return {}
    

def Master(lsEmps, lsProjects, StartDate, EndDate, bFetchLatest=False):
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
    
        
# Run the app
if __name__ == '__main__':
    # app.run_server(debug=True)
    # fetch new clickup data
    CClickUpAPI.MSFetchTaskFromConfigFile(strConfigPath = r"resource\clickup_config.json")
    # tasks, taskStatics = CClickUpDB.MSGetTasksByListIDsWithEmpFilter(["901600183071"], "10-09-2024",  "25-09-2024",  ['mitul@riveredgeanalytics.com','mansi@riveredgeanalytics.com', 'hr@riveredgeanalytics.com'])
    # print(tasks)
    # print()
    # print(taskStatics)
# if __name__ == '__main__':
#     app.run_server(debug=True)
