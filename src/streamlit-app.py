import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta
from PlotMain import GanttChart
from ClickUpAPI import CClickUpAPI
from helperFunc import readJson, FilterOutIdleTasks, get_filtered_data


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

# Initialize Streamlit app and JSON data
json_data = readJson(r"resource\clickup_config.json")  # Replace with actual JSON file path

# Extract unique customers and projects for dropdown options
customers = sorted(set(entry['Customer'] for entry in json_data))

# Get default start and end dates
default_start_date, default_end_date = get_default_dates()

# Streamlit App
st.set_page_config(layout="wide")
st.title("Task Management Dashboard")

# Define the status and their corresponding RGB colors
status_colors = {
    "open": "rgb(255, 255, 255)",
    "in progress": "rgb(0, 255, 255)",
    "review": "rgb(144, 238, 144)",
    "delievered": "rgb(0, 100, 0)",
    "on hold": "rgb(255, 105, 180)",
    "idle time": "rgb(238, 237, 9)"
}

# Create columns dynamically based on the number of statuses
cols = st.columns(len(status_colors))  # Create columns for each status

# Iterate over each status and display the colored box with the status name in a single row
for idx, (status, color) in enumerate(status_colors.items()):
    with cols[idx]:  # Use each column for each status
        st.markdown(
            f"""
            <div style="display: flex; align-items: center;">
                <div style="
                    width: 20px;
                    height: 20px;
                    background-color: {color};
                    border: 1px solid #000;
                    border-radius: 4px;
                    margin-right: 5px;
                "></div>
                <span style="font-size: 14px;">{status.capitalize()}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
# Sidebar Section
st.sidebar.header("Filters")

st.sidebar.subheader("Select Employee Name:")
select_all_employees = st.sidebar.checkbox("Select All Employees", False)
employee_names = st.sidebar.multiselect(
    "Employees",
    options=[
        'mitul@riveredgeanalytics.com', 'mansi@riveredgeanalytics.com', 'hr@riveredgeanalytics.com',
        'devanshi@riveredgeanalytics.com', 'dhruvin@riveredgeanalytics.com','manthan@riveredgeanalytics.com',
        'mohit.intern@riveredgeanalytics.com', 'harshil@riveredgeanalytics.com',"fenil@riveredgeanalytics.com","punesh@riveredgeanalytics.com","ankita@riveredgeanalytics.com","nikhil@riveredgeanalytics.com","mansip@riveredgeanalytics.com","zahid@riveredgeanalytics.com"
    ],
    default=[] if not select_all_employees else [
        'mitul@riveredgeanalytics.com', 'mansi@riveredgeanalytics.com', 'hr@riveredgeanalytics.com',
        'devanshi@riveredgeanalytics.com', 'dhruvin@riveredgeanalytics.com',
        'mohit.intern@riveredgeanalytics.com', 'harshil@riveredgeanalytics.com','manthan@riveredgeanalytics.com',"fenil@riveredgeanalytics.com","punesh@riveredgeanalytics.com","ankita@riveredgeanalytics.com","nikhil@riveredgeanalytics.com","mansip@riveredgeanalytics.com","zahid@riveredgeanalytics.com"
    ]
)
# Customer filter with "Select All" functionality
st.sidebar.subheader("Select Customer Name:")
select_all_customers = st.sidebar.checkbox("Select All Customers", False)
selected_customers = st.sidebar.multiselect(
    "Customers",
    options=customers,
    default=customers if select_all_customers else []
)

# Project filter based on selected customers with "Select All" functionality
filtered_projects = [
    entry for entry in json_data if entry['Customer'] in selected_customers
]
projects = sorted(set(entry['Project'] for entry in filtered_projects))

st.sidebar.subheader("Select Project Name:")
select_all_projects = st.sidebar.checkbox("Select All Projects", False)
selected_projects = st.sidebar.multiselect(
    "Projects",
    options=projects,
    default=projects if select_all_projects else []
)

# Filter data based on selected customers and projects
selected_data = [
    entry for entry in json_data 
    if entry['Customer'] in selected_customers and entry['Project'] in selected_projects
]

# Prepare ListIDs for the master method based on selected data
project_names = [entry['ListID'] for entry in selected_data]

# project_names = st.sidebar.multiselect(
#     "Projects",
#     options=['901601699012', '901600183071', '901603806927',"901604664293","901604664323","901604664325","901604664326","901604664327","901604664329","901604664340"],
#     default=[] if not select_all_projects else ['901601699012', '901600183071', '901603806927',"901604664293","901604664323","901604664325","901604664326","901604664327","901604664329","901604664340"]
# )

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
    fig = GanttChart.Master(
        lsEmps=employee_names, 
        lsProjects=project_names, 
        StartDate=start_date, 
        EndDate=end_date,
        bTaskIntensityInclude=task_intensity_value, 
        bFetchLatest=fetch_latest_value,
        bShowPlot = False
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
        # uncomment below code to filter our idle time status rows from listoftasks
        # lsFilteredTasks = FilterOutIdleTasks(lsEmpTasks)
        # lsEmpTasks = lsFilteredTasks
        df_tasks = pd.DataFrame(lsEmpTasks)
        st.subheader(f"Tasks for {EmpName}")
        st.dataframe(df_tasks)
        
        
# streamlit run src\streamlit-app.py



