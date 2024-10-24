import dash
import pandas as pd
from dash import dash_table
import dash_bootstrap_components as dbc  # Import Bootstrap components
from dash import dcc, html, Input, Output, State
from datetime import datetime, timedelta
from PlotMain import GanttChart
from ClickUpAPI import CClickUpAPI
from ClickUpDB import CClickUpDB
from helperFunc import readJson

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
dictEmptasks = {}

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
    html.H2("Task Management Dashboard", style={'textAlign': 'center', 'padding': '10px 0'}),

    # Container for Sidebar and Plot
    html.Div([
        # Sidebar (30%)
        html.Div([
            # Toggle Button for Report Overview
            dbc.Button("Report Overview ▶", id="toggle-overview", n_clicks=0, color="primary", style={
                'width': '100%', 'textAlign': 'left'
            }),
            
            # Collapsible Section for Report Overview
            dbc.Collapse(
                id='report-overview',
                is_open=False,
                children=html.Div([
                    html.P(f'Selected Employees: ...'),  # Placeholder content
                    html.P(f'Selected Projects: ...'),
                    html.P(f'Start Date: ...'),
                    html.P(f'End Date: ...'),
                    html.P(f'Task Intensity Wise Score: ...'),
                    html.P(f'Fetch Latest Date: ...')
                ], style={'padding': '10px'})
            ),

            # Inputs Section
            html.Label('Select Employee Name:', style={'fontWeight': 'bold'}),
            html.Div([
                dcc.Checklist(
                    id='select-all-employees',
                    options=[{'label': 'All', 'value': 'all'}],
                    value=[],
                    inline=True
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
                    value=[],
                    placeholder="Select employees...",
                    style={'marginTop': '5px'}
                ),
            ], style={'marginBottom': '15px'}),

            # Additional inputs (Projects, Dates, Task Intensity, Fetch Latest)
            html.Label('Select Project Name:', style={'fontWeight': 'bold'}),
            dcc.Checklist(
                id='select-all-projects',
                options=[{'label': 'All', 'value': 'all'}],
                value=[],
                inline=True
            ),
            dcc.Dropdown(
                id='project-names',
                options=[
                    {'label': 'AccuVelocity', 'value': '901601699012'},
                    {'label': 'ERPNext', 'value': '901600183071'},
                    {'label': 'ClickUp', 'value': '901603806927'}
                ],
                multi=True,
                value=[],
                placeholder="Select projects...",
                style={'marginTop': '5px'}
            ),

            html.Label('Select Start and End Date:', style={'fontWeight': 'bold'}),
            dcc.DatePickerRange(
                id='date-range',
                min_date_allowed=datetime(2020, 1, 1),
                max_date_allowed=datetime(2030, 12, 31),
                start_date=default_start_date,
                end_date=default_end_date,
                display_format='DD-MM-YYYY',
                persistence=True,
                persistence_type='session',  # Keep the value across sessions
                style={'marginBottom': '15px', 'marginTop': '5px'}
            ),

            html.Label('Task Intensity Wise Score:', style={'fontWeight': 'bold'}),
            dcc.Checklist(
                id='task-intensity-wise-score',
                options=[{'label': 'Task Intensity Wise Score', 'value': 'True'}],
                value=[],
                inline=True,
                style={'marginBottom': '15px', 'marginTop': '5px'}
            ),

            html.Label('Fetch Latest Date:', style={'fontWeight': 'bold'}),
            dcc.Checklist(
                id='fetch-latest-date',
                options=[{'label': 'Fetch Latest Date', 'value': 'True'}],
                value=[],
                inline=True,
                style={'marginBottom': '15px', 'marginTop': '5px'}
            ),
            
            html.Div([
                html.Button('Generate Report', id='submit-button', n_clicks=0, 
                            style={'backgroundColor': '#007bff', 'color': 'white', 'border': 'none',
                                   'padding': '10px 20px', 'cursor': 'pointer', 'width': '100%'})
            ], style={'textAlign': 'center', 'paddingTop': '15px', 'paddingBottom': '15px'}),
        ], style={'width': '30%', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'float': 'left'}),

        # Plot Area (60%)
        html.Div(id='plot-area', style={'width': '60%', 'float': 'left', 'padding': '10px'})
    ], style={'display': 'flex', 'width': '100%'}),
])

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

# Callback for the collapsible report overview
@app.callback(
    Output("report-overview", "is_open"),
    [Input("toggle-overview", "n_clicks")],
    [State("report-overview", "is_open")]
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

# @app.callback(
#     Output('plot-area', 'children'),
#     [
#         Input('submit-button', 'n_clicks'),
#         State('employee-names', 'value'),
#         State('project-names', 'value'),
#         State('date-range', 'start_date'),
#         State('date-range', 'end_date'),
#         State('task-intensity-wise-score', 'value'),
#         State('fetch-latest-date', 'value')
#     ]
# )
# def update_dashboard(n_clicks, employee_names, project_names, start_date, end_date, task_intensity, fetch_latest):
#     return display_user_inputs(n_clicks, employee_names, project_names, start_date, end_date, task_intensity, fetch_latest)


def clean_task_data(dictEmptasks):
    """
    Cleans and filters each employee's task data to ensure all values are of valid types
    for the Dash DataTable (string, number, boolean). Only includes selected columns.

    Parameters:
        dictEmptasks (dict): Dictionary containing employee task data.

    Returns:
        dict: Cleaned and filtered dictionary with all values converted to appropriate types.
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
                # Ensure the key exists in the task dictionary before processing
                value = task.get(key, None)
                
                # Convert None values to empty strings
                if value is None:
                    cleaned_task[key] = ''
                # Convert unsupported types (like lists, dicts) to strings
                elif isinstance(value, (list, dict)):
                    cleaned_task[key] = str(value)
                # Keep valid types (string, number, boolean) as is
                elif isinstance(value, (str, int, float, bool)):
                    cleaned_task[key] = value
                else:
                    # For any other type, convert to string
                    cleaned_task[key] = str(value)
            
            cleaned_tasks.append(cleaned_task)
        
        cleaned_dict[emp_name] = cleaned_tasks
    
    return cleaned_dict

# Callback to generate and show plot
@app.callback(
    Output('plot-area', 'children'),
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
        
        # Convert start_date and end_date to "DD-MM-YYYY" format
        start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        
        # Assume Master returns a plotly figure based on inputs
        fig = Master(
            lsEmps=employee_names, 
            lsProjects=project_names, 
            StartDate=start_date, 
            EndDate=end_date,
            bTaskIntensityInclude=task_intensity_value, 
            bFetchLatest=fetch_latest_value
        )
        
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

        # Create data tables for each employee
        for EmpName, lsEmpTasks in cleaned_dictEmptasks.items():
            # Convert the cleaned task details to a DataFrame
            df_tasks = pd.DataFrame(lsEmpTasks)
            
            # Create a Dash DataTable for the current employee
            table = dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in df_tasks.columns],
                data=df_tasks.to_dict('records'),
                style_table={'overflowX': 'scroll', 'width': '100%', 'marginTop': '20px'},
                style_header={'backgroundColor': 'lightgrey'},
                style_cell={'textAlign': 'left'},
                style_data={'whiteSpace': 'normal', 'height': 'auto'}
            )
            
            # Append a header and the table to the list
            employee_data_tables.append(html.H3(f"Tasks for {EmpName}", style={'marginTop': '30px'}))
            employee_data_tables.append(table)

        # Return the graph and employee data tables
        return html.Div([
            html.Div(
                dcc.Graph(figure=fig, config={'responsive': True}), 
                style={'marginBottom': '50px'}
            ),
            html.Div(employee_data_tables, style={'padding': '20px'})
        ])

    return html.P("Please generate a report to view the plot.")

    

def Master(lsEmps, lsProjects, StartDate="25-08-2024", EndDate="20-09-2024", bTaskIntensityInclude = False, bFetchLatest=False):
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
                priority = priority if priority else ""
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
    # fig.show()
    
        
# Run the app
if __name__ == '__main__':
    # app.run_server(debug=True)
    # fetch new clickup data
    # CClickUpAPI.MSFetchTaskFromConfigFile(strConfigPath = r"resource\clickup_config.json")
    # tasks, taskStatics = CClickUpDB.MSGetTasksByListIDsWithEmpFilter(["901600183071"], "10-09-2024",  "25-09-2024",  ['mitul@riveredgeanalytics.com','mansi@riveredgeanalytics.com', 'hr@riveredgeanalytics.com'])
    # print(tasks)
    # print()
    # print(taskStatics)
    app.run_server(debug=True)
    # objGanttChart = GanttChart()
    # employee_data_tables = []
    # # Assuming the GanttChart class is already defined
    # # Fetching employee tasks for the given date range
    # dictEmptasks = objGanttChart.Main(lsListIDs= ["901600183071"], strTskStDate="01-08-2024", strTskEndDate="01-10-2024", lsEmployees=["mitul@riveredgeanalytics.com"],include_toughness=False)
    # cleaned_dictEmptasks = clean_task_data(dictEmptasks)

    # # Create data tables for each employee
    # for EmpName, lsEmpTasks in cleaned_dictEmptasks.items():
    #     # Convert the cleaned task details to a DataFrame
    #     df_tasks = pd.DataFrame(lsEmpTasks)
        
    #     # Create a Dash DataTable for the current employee
    #     table = dash_table.DataTable(
    #         columns=[{"name": i, "id": i} for i in df_tasks.columns],
    #         data=df_tasks.to_dict('records'),
    #         style_table={'overflowX': 'scroll', 'width': '100%', 'marginTop': '20px'},
    #         style_header={'backgroundColor': 'lightgrey'},
    #         style_cell={'textAlign': 'left'},
    #         style_data={'whiteSpace': 'normal', 'height': 'auto'}
    #     )
        
    #     # Append a header and the table to the list
    #     employee_data_tables.append(html.H3(f"Tasks for {EmpName}", style={'marginTop': '30px'}))
    #     employee_data_tables.append(table)
    # print("-----------------")
    # print(employee_data_tables)
