# Import necessary libraries and components
import dash
import pandas as pd
from dash import dash_table
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
from datetime import datetime, timedelta
from PlotMain import GanttChart
from ClickUpAPI import CClickUpAPI
from ClickUpDB import CClickUpDB
from helperFunc import readJson, create_output_data, create_customer_list, create_project_list, clean_task_data
import calendar
from io import BytesIO
import xlsxwriter  # For styling Excel files
import base64

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
dictEmptasks = {}
dictEmpInfo = readJson(r"resource\employeeConfig.json")
dictClickUpConfig = readJson(r"resource\clickup_config.json")
# Define the statuses and their corresponding RGB colors
status_colors = {
    "open": "rgb(255, 255, 255)",
    "in progress": "rgb(0, 255, 255)",
    "review": "rgb(144, 238, 144)",
    "delivered": "rgb(0, 100, 0)",
    "on hold": "rgb(255, 105, 180)",
    "idle time": "rgb(238, 237, 9)"
}
# Helper function to calculate default dates
def get_default_dates():
    current_date = datetime.now()
    start_date = current_date - timedelta(weeks=1)
    end_date = current_date + timedelta(weeks=3)
    return start_date.date(), end_date.date()

# Helper functions for date selection
def get_current_month_dates():
    today = datetime.now().date()
    start_date = today.replace(day=1)
    _, last_day = calendar.monthrange(today.year, today.month)
    end_date = today.replace(day=last_day)
    return start_date, end_date

def get_current_week_dates():
    today = datetime.now().date()
    start_date = today - timedelta(days=today.weekday())  # Monday
    end_date = start_date + timedelta(days=6)  # Sunday
    return start_date, end_date

def get_current_day_date():
    today = datetime.now().date()
    return today, today

# Get default start and end dates
default_start_date, default_end_date = get_current_month_dates()

# Define layout
app.layout = html.Div([
    html.H2("TaskViz Web App", style={'textAlign': 'center', 'padding': '20px 0'}),
    # Row with Filter Panel on the left and App Info (collapsible) on the right
    dbc.Row([
        # Filter Panel Column (30%)
        dbc.Col(
            [
                # Header with Toggle Filter Panel button and Info icon
                html.Div([
                    html.Button(
                        "Toggle Filter Panel",
                        id="filter-panel-collapse",
                        n_clicks=0,
                        style={'backgroundColor': '#007bff', 'color': 'white', 'border': 'none', 
                               'padding': '10px 20px', 'cursor': 'pointer'}
                    ),
                    # Info icon within the header
                    html.Button(
                        "ℹ️", 
                        id="info-icon-button",
                        n_clicks=0,
                        style={'backgroundColor': 'transparent', 'color': '#007bff', 'border': 'none', 
                               'fontSize': '24px', 'cursor': 'pointer', 'marginLeft': '10px'}
                    ),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),
                
                # Collapsible Filter Section
                dbc.Collapse(
                    html.Div([
                        html.Label('Select Employee Name:', style={'fontWeight': 'bold', 'marginTop': '15px'}),
                        html.Div([
                            dcc.Checklist(
                                id='select-all-employees',
                                options=[{'label': 'All', 'value': 'all'}],
                                value=[],
                                inline=True
                            ),
                            dcc.Dropdown(
                                id='employee-names',
                                options=create_output_data(dictEmpInfo),
                                multi=True,
                                value=[],
                                placeholder="Select employees...",
                                style={'marginTop': '5px'}
                            ),
                        ], style={'marginBottom': '15px'}),

                        html.Label('Select Customer Name:', style={'fontWeight': 'bold'}),
                        dcc.Checklist(
                            id='select-all-customers',
                            options=[{'label': 'All', 'value': 'all'}],
                            value=[],
                            inline=True
                        ),
                        dcc.Dropdown(
                            id='customer-names',
                            options=create_customer_list(dictClickUpConfig),
                            multi=False,
                            value='',
                            placeholder="Select customers...",
                            style={'marginTop': '5px'}
                        ),
                        
                        html.Label('Select Project Name:', style={'fontWeight': 'bold'}),
                        dcc.Checklist(
                            id='select-all-projects',
                            options=[{'label': 'All', 'value': 'all'}],
                            value=[],
                            inline=True
                        ),
                        dcc.Dropdown(
                            id='project-names',
                            options=create_project_list(dictClickUpConfig),
                            multi=True,
                            value=[],
                            placeholder="Select projects...",
                            style={'marginTop': '5px'}
                        ),

                        html.Label('Select Date Type:', style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='date-type',
                            options=[
                                {'label': 'Month', 'value': 'month'},
                                {'label': 'Week', 'value': 'week'},
                                {'label': 'Day', 'value': 'day'},
                                {'label': 'Custom', 'value': 'custom'}
                            ],
                            value='month',
                            placeholder="Select date type...",
                            style={'marginBottom': '15px', 'marginTop': '5px'}
                        ),

                        html.Label('Select Start and End Date:', style={'fontWeight': 'bold'}),
                        dcc.DatePickerRange(
                            id='date-range',
                            min_date_allowed=datetime(2020, 1, 1),
                            max_date_allowed=datetime(2030, 12, 31),
                            start_date=default_start_date,
                            end_date=default_end_date,
                            display_format='DD-MM-YYYY',
                            persistence=False,
                            persistence_type='session',  
                            style={'marginBottom': '15px', 'marginTop': '5px'}
                        ),
                        # Plot Size Dropdown
                        html.Div([
                            html.Label('Select Plot Size:', style={'fontWeight': 'bold'}),
                            dcc.Dropdown(
                                id='plot-size',
                                options=[
                                    {'label': '1920 x 1080', 'value': '1920x1080'},
                                    {'label': '2560 x 1440', 'value': '2560x1440'},
                                    {'label': '3840 x 2160', 'value': '3840x2160'}
                                ],
                                value='1920x1080',  # Default value
                                placeholder="Select plot size",
                                style={'marginBottom': '15px', 'marginTop': '5px'}
                            ),
                        ], style={'marginBottom': '15px'}),  # Wrap Dropdown in a Div for spacing
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
                                               'padding': '10px 20px', 'cursor': 'pointer', 'width': '100%'}),
                        ], style={'textAlign': 'center', 'paddingTop': '15px', 'paddingBottom': '15px'}),
                    ], style={'width': '100%', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #ddd'}),
                    id="filter-collapse",
                    is_open=True  # Initially open
                ),
            ],
            width=4  # Set Filter Panel width to 30%
        ),
        
        # App Info Column (70%) - Only shown when expanded
        dbc.Col(
            dbc.Collapse(
                html.Div([
                    html.H4("📘 App Info", style={'fontWeight': 'bold', 'color': '#007bff', 'fontSize': '24px'}),
                    html.P("Welcome to the Task Management Dashboard! Here’s a quick guide to get you started:", 
                        style={'fontSize': '18px', 'fontStyle': 'italic', 'color': '#333'}),
                    html.Ol([
                        html.Li([
                            html.Span("Select employees, customers, or projects ", style={'fontWeight': 'bold', 'color': '#007bff'}),
                            "to view tasks related to each. This allows for focused task management based on your chosen criteria."
                        ], style={'marginBottom': '10px', 'fontSize': '16px'}),
                        
                        html.Li([
                            html.Span("Use the date filter ", style={'fontWeight': 'bold', 'color': '#007bff'}),
                            "to choose tasks from a specific ", 
                            html.Span("month, week, day, or set custom dates.", style={'fontWeight': 'bold'}),
                            html.Br(),
                            "The ",
                            html.Span("Start Date", style={'fontWeight': 'bold', 'color': '#0066cc'}),
                            " is auto-selected based on your choice and is fixed. For example, if ",
                            html.Span("Month", style={'fontStyle': 'italic'}),
                            " is selected, the Start Date will default to the first day of that month. ",
                            html.Br(),
                            html.Span("End Date", style={'fontWeight': 'bold', 'color': '#0066cc'}),
                            " will auto-set to the last day of the selected period, but you may modify it as needed."
                        ], style={'marginBottom': '10px', 'fontSize': '16px'}),

                        html.Li([
                            html.Span("Choose 'Task Intensity Score' ", style={'fontWeight': 'bold', 'color': '#007bff'}),
                            "to view tasks by their intensity levels. This can help prioritize high-intensity tasks."
                        ], style={'marginBottom': '10px', 'fontSize': '16px'}),

                        html.Li([
                            html.Span("Click 'Fetch Latest Date' ", style={'fontWeight': 'bold', 'color': '#007bff'}),
                            "to ensure tasks are updated to the most recent data available. Use this to refresh the task view."
                        ], style={'marginBottom': '10px', 'fontSize': '16px'}),

                        html.Li([
                            html.Span("Select Plot Size ", style={'fontWeight': 'bold', 'color': '#007bff'}),
                            "for visualization. Adjust this setting to choose your preferred resolution for data display."
                        ], style={'marginBottom': '10px', 'fontSize': '16px'}),

                        html.Li([
                            html.Span("Generate reports ", style={'fontWeight': 'bold', 'color': '#007bff'}),
                            "based on your selected filters and ",
                            html.Span("download as an Excel file", style={'fontWeight': 'bold'}),
                            ". This feature allows for easy sharing and further analysis."
                        ], style={'marginBottom': '10px', 'fontSize': '16px'}),
                    ], style={'paddingLeft': '20px', 'color': '#333'}),

                    html.P("Use this dashboard to gain insights into task management and improve team productivity!",
                        style={'fontSize': '16px', 'fontStyle': 'italic', 'color': '#333', 'marginTop': '20px'}),
                ], style={'padding': '20px', 'backgroundColor': '#f0f8ff', 'border': '1px solid #ddd', 'borderRadius': '5px'})
,
                id="info-collapse",
                is_open=False  # Initially collapsed
            ),
            width=8  # Set App Info width to 70%
        )
    ], style={'padding': '20px'}),

    # Download button on a new line
    html.Br(),
    # Button to trigger download, aligned directly below the Toggle Filter Panel button
    html.Button(
        "Download Excel Sheet", 
        id="download-excel-button", 
        n_clicks=0,
        style={'backgroundColor': '#007bff', 'color': 'white', 'border': 'none',
               'padding': '10px 20px', 'cursor': 'pointer', 'marginBottom': '20px', 'marginLeft': '20px'}
    ),

    # Download component
    dcc.Download(id="download-excel"),
    # Status Notation Row
    html.Div([
        html.Label("Status Notation -", style={'fontWeight': 'bold', 'marginRight': '10px'}),
        html.Div([
            html.Div([
                html.Div(style={
                    'width': '20px', 'height': '20px', 'backgroundColor': color,
                    'border': '1px solid #000', 'borderRadius': '4px', 'display': 'inline-block',
                    'marginRight': '5px'
                }),
                html.Span(status.capitalize(), style={'fontSize': '14px', 'marginRight': '15px'})
            ], style={'display': 'flex', 'alignItems': 'center'})
            for status, color in status_colors.items()
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px','marginLeft': '20px'}),

    # Priority Bar Notation Row
    html.Div([
        html.Label("Priority Notation -", style={'fontWeight': 'bold', 'marginRight': '10px'}),
        html.Div([
            # Priority P0 (Urgent) - Tallest box
            html.Div([
                html.Div(style={
                    'width': '20px', 'height': '30px', 'border': '1px solid #000',
                    'marginRight': '5px', 'display': 'inline-block', 'backgroundColor': '#f8f9fa'
                }),
                html.Span("P0 (Urgent)", style={'fontWeight': 'bold', 'marginRight': '15px'})
            ], style={'display': 'flex', 'alignItems': 'center'}),

            # Priority P1 (High) - Medium box
            html.Div([
                html.Div(style={
                    'width': '20px', 'height': '20px', 'border': '1px solid #000',
                    'marginRight': '5px', 'display': 'inline-block', 'backgroundColor': '#f8f9fa'
                }),
                html.Span("P1 (High)", style={'fontStyle': 'italic', 'marginRight': '15px'})
            ], style={'display': 'flex', 'alignItems': 'center'}),

            # Priority P2 (Normal) - Shortest box
            html.Div([
                html.Div(style={
                    'width': '20px', 'height': '10px', 'border': '1px solid #000',
                    'marginRight': '5px', 'display': 'inline-block', 'backgroundColor': '#f8f9fa'
                }),
                html.Span("P2 (Normal)", style={'marginRight': '15px'})
            ], style={'display': 'flex', 'alignItems': 'center'}),
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '20px','marginLeft': '20px'}),
    # Plot Area
    html.Div(id='plot-area', style={'width': '100%', 'padding': '10px'})
])

    
# Callback to toggle both the collapsible Filter Panel and App Info sections
@app.callback(
    [Output("filter-collapse", "is_open"),
     Output("info-collapse", "is_open")],
    [Input("filter-panel-collapse", "n_clicks"),
     Input("info-icon-button", "n_clicks")],
    [State("filter-collapse", "is_open"),
     State("info-collapse", "is_open")]
)
def toggle_panels(filter_click, info_click, filter_is_open, info_is_open):
    # Determine which button was clicked
    ctx = dash.callback_context
    if not ctx.triggered:
        return filter_is_open, info_is_open

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Toggle behavior when the Filter Panel button is clicked
    if triggered_id == "filter-panel-collapse":
        # Toggle the Filter Panel
        new_filter_state = not filter_is_open
        # If closing the Filter Panel, also close the App Info
        new_info_state = False if not new_filter_state else info_is_open
        return new_filter_state, new_info_state

    # Toggle behavior for the Info Panel button
    elif triggered_id == "info-icon-button":
        # Toggle the Info Panel independently
        return filter_is_open, not info_is_open

    # Default case, return the current states
    return filter_is_open, info_is_open


# Callback to update date range based on selected type and start date
@app.callback(
    Output('date-range', 'start_date'),
    Output('date-range', 'end_date'),
    Input('date-type', 'value'),
    Input('date-range', 'start_date')
)
def update_date_range(date_type, start_date):
    if not start_date:
        start_date = datetime.now().date()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    # Logic to adjust end_date based on date_type
    if date_type == 'month':
        start_date = start_date.replace(day=1)
        _, last_day = calendar.monthrange(start_date.year, start_date.month)
        end_date = start_date.replace(day=last_day)
    elif date_type == 'week':
        start_date = start_date - timedelta(days=start_date.weekday())  # Set to the Monday of that week
        end_date = start_date + timedelta(days=6)  # Set to the Sunday of that week
    elif date_type == 'day':
        end_date = start_date  # For "Day" type, set start and end to the same day
    elif date_type == 'custom':
        # Allow manual selection, do not automatically set end_date
        return start_date, None

    return start_date, end_date

# Callback to update project list based on selected customer
@app.callback(
    Output('project-names', 'options'),
    Input('customer-names', 'value')
)
def update_project_options(selected_customer):
    all_projects = create_project_list(dictClickUpConfig)
    
    # Show all projects if no customer is selected or 'All' is selected
    if not selected_customer or selected_customer == 'all':
        return all_projects
    
    # Filter projects based on selected customer
    filtered_projects = [
        project for project in all_projects
        if any(item.get("Customer") == selected_customer and item.get("ListID") == project['value']
               for item in dictClickUpConfig)
    ]
    
    return filtered_projects if filtered_projects else all_projects


@app.callback(
    Output('customer-names', 'value'),        # Controls selected customer
    Output('select-all-customers', 'value'),  # Controls "All" checkbox state
    Input('select-all-customers', 'value'),   # Input from "All" checkbox
    State('customer-names', 'options')        # State of customer options
)
def select_all_customers(select_all, customer_options):
    if 'all' in select_all:
        # Select all customers by returning an empty string or first option as needed
        return '', ['all']
    else:
        # Deselect all customers and uncheck "All"
        return None, []

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
        State('fetch-latest-date', 'value'),
        State('plot-size', 'value')  # New state for plot size
    ]
)
def display_user_inputs(n_clicks, employee_names, project_names, start_date, end_date, task_intensity, fetch_latest,plot_size):
    if n_clicks > 0:
        task_intensity_value = True if 'True' in task_intensity else False
        fetch_latest_value = True if 'True' in fetch_latest else False
        
        # Convert start_date and end_date to "DD-MM-YYYY" format
        start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        
        # Parse width and height from the plot size string (e.g., "1920x1080" to 1920, 1080)
        width, height = map(int, plot_size.split('x'))

        # Generate the Gantt chart using the selected width and height
        fig = GanttChart.Master(
            lsEmps=employee_names, 
            lsProjects=project_names, 
            StartDate=start_date, 
            EndDate=end_date,
            bTaskIntensityInclude=task_intensity_value, 
            bFetchLatest=fetch_latest_value,
            bShowPlot=False,
            width=width,
            height=height
        )
        
        # Prepare list to hold all employee data tables
        # employee_data_tables = []
        
        # Assuming the GanttChart class is already defined
        # objGanttChart = GanttChart()
        
        # # Fetching employee tasks for the given date range
        # dictEmptasks = objGanttChart.Main(
        #     lsListIDs=project_names, 
        #     strTskStDate=start_date, 
        #     strTskEndDate=end_date, 
        #     lsEmployees=employee_names,
        #     include_toughness=task_intensity_value
        # )
        
        # # Clean the task data
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

        # Return the graph and employee data tables
        return html.Div([
            html.Div(
                dcc.Graph(figure=fig, config={'responsive': True}), 
                style={'marginBottom': '50px'}
            )
            # html.Div(employee_data_tables, style={'padding': '20px'})
        ])

    return html.P(
        "Please generate a report to view the plot.",
        style={'marginLeft': '20px'}
    )

    
# Callback to create and download the Excel sheet
@app.callback(
    Output("download-excel", "data"),
    [Input("download-excel-button", "n_clicks")],
    [
        State("employee-names", "value"),
        State("project-names", "value"),
        State("date-range", "start_date"),
        State("date-range", "end_date"),
        State("task-intensity-wise-score", "value"),
    ]
)
def generate_excel(n_clicks, employee_names, project_names, start_date, end_date, task_intensity):
    try:
        if n_clicks == 0:
            return dash.no_update
        task_intensity_value = True if 'True' in task_intensity else False
        # Convert start_date and end_date to "DD-MM-YYYY" format
        start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
            
        
        # Assuming the GanttChart class and Main method are defined
        objGanttChart = GanttChart()
        
        # Fetch employee tasks for the given date range
        dictEmptasks = objGanttChart.Main(
            lsListIDs=project_names, 
            strTskStDate=start_date, 
            strTskEndDate=end_date, 
            lsEmployees=employee_names,
            include_toughness=task_intensity_value
        )
        
        # Clean and prepare the task data
        all_tasks = clean_task_data(dictEmptasks)
        df = pd.DataFrame(all_tasks)


        # Filename for download
        filename = f"TaskViz_{start_date}_{end_date}.xlsx"

        # Create an Excel file with conditional formatting
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name="Tasks")

        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets["Tasks"]

        # Define formats for conditional formatting
        yellow_format = workbook.add_format({'bg_color': 'yellow'})
        green_format = workbook.add_format({'bg_color': 'green'})
        light_green_format = workbook.add_format({'bg_color': '#ccffcc'})  # Light green
        white_format= workbook.add_format({'bg_color': 'white'})
        pink_format= workbook.add_format({'bg_color': '#ff69b4'})
        blue_format = workbook.add_format({'bg_color': '#00FFFF'})
        # Apply conditional formatting based on the "Status" column
        status_column = df.columns.get_loc("TaskStatus")  # Find the column index for "Status"
        for row_num in range(1, len(df) + 1):
            # Check if the row's TaskStatus column is "Idle Time"
            worksheet.conditional_format(row_num, 0, row_num, len(df.columns) - 1, {
                'type': 'formula',
                'criteria': f'INDIRECT("R{row_num+1}C{status_column+1}",0)="Idle Time"',
                'format': yellow_format
            })
            # Check if the row's TaskStatus column is "Open"
            worksheet.conditional_format(row_num, 0, row_num, len(df.columns) - 1, {
                'type': 'formula',
                'criteria': f'INDIRECT("R{row_num+1}C{status_column+1}",0)="Open"',
                'format': white_format
            })
            # Check if the row's TaskStatus column is "In Progress"
            worksheet.conditional_format(row_num, 0, row_num, len(df.columns) - 1, {
                'type': 'formula',
                'criteria': f'INDIRECT("R{row_num+1}C{status_column+1}",0)="In Progress"',
                'format': blue_format
            })
            # Check if the row's TaskStatus column is "On Hold" or "Hold"
            worksheet.conditional_format(row_num, 0, row_num, len(df.columns) - 1, {
                'type': 'formula',
                'criteria': f'OR(INDIRECT("R{row_num+1}C{status_column+1}",0)="On Hold", INDIRECT("R{row_num+1}C{status_column+1}",0)="Hold")',
                'format': pink_format
            })
            # Check if the row's TaskStatus column is "Completed" or "Closed"
            worksheet.conditional_format(row_num, 0, row_num, len(df.columns) - 1, {
                'type': 'formula',
                'criteria': f'OR(INDIRECT("R{row_num+1}C{status_column+1}",0)="Completed", INDIRECT("R{row_num+1}C{status_column+1}",0)="Closed")',
                'format': green_format
            })
            # Check if the row's TaskStatus column is "In Review" or "Review"
            worksheet.conditional_format(row_num, 0, row_num, len(df.columns) - 1, {
                'type': 'formula',
                'criteria': f'OR(INDIRECT("R{row_num+1}C{status_column+1}",0)="In Review", INDIRECT("R{row_num+1}C{status_column+1}",0)="Review")',
                'format': light_green_format
            })

        # Save and close the writer
        writer.close()
        output.seek(0)

        # Prepare the download
        return dcc.send_bytes(output.read(), filename=filename)
    except Exception as e: 
        print("Error = ", e)

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


    # def clean_task_data(dictEmptasks):
    #     """
    #     Cleans and filters each employee's task data to ensure all values are of valid types
    #     for the Dash DataTable (string, number, boolean). Only includes selected columns.

    #     Parameters:
    #         dictEmptasks (dict): Dictionary containing employee task data.

    #     Returns:
    #         dict: Cleaned and filtered dictionary with all values converted to appropriate types.
    #     """
    #     selected_columns = [
    #         'TaskID', 'TaskSubject', 'TaskStatus', 'TaskPriority', 'AssignTo',
    #         'TaskScore', 'TaskExecutionDate', 'TaskStartDate', 'TaskDueDate',
    #         'IsConflict', 'ConflictTimeMin', 'AllocatedTimeMin'
    #     ]
        
    #     cleaned_dict = {}

    #     for emp_name, task_list in dictEmptasks.items():
    #         cleaned_tasks = []
            
    #         for task in task_list:
    #             cleaned_task = {}
    #             for key in selected_columns:
    #                 # Ensure the key exists in the task dictionary before processing
    #                 value = task.get(key, None)
                    
    #                 # Convert None values to empty strings
    #                 if value is None:
    #                     cleaned_task[key] = ''
    #                 # Convert unsupported types (like lists, dicts) to strings
    #                 elif isinstance(value, (list, dict)):
    #                     cleaned_task[key] = str(value)
    #                 # Keep valid types (string, number, boolean) as is
    #                 elif isinstance(value, (str, int, float, bool)):
    #                     cleaned_task[key] = value
    #                 else:
    #                     # For any other type, convert to string
    #                     cleaned_task[key] = str(value)
                
    #             cleaned_tasks.append(cleaned_task)
            
    #         cleaned_dict[emp_name] = cleaned_tasks
        
    #     return cleaned_dict