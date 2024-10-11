import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import plotly.colors as pc
from datetime import datetime, timedelta
from ClickUpDB import CClickUpDB
from main import CClickUpMiddleWare
import os
import random
import json

class GanttChart:
    
    def __init__(self):
        self.tasks = []
        self.dictProjectColors = {}
        
    def add_task(self, task_name, person, start_datetime, duration, color=None, pattern=None, bar_width=None,strLegendData = None):
        end_datetime = start_datetime + duration
        self.tasks.append({
            'Task': task_name,
            'Person': person,
            'Start': start_datetime,
            'Finish': end_datetime,
            'Color': color,
            'Pattern': pattern,
            'BarWidth': bar_width,
            'strLegendData':strLegendData
        })

    # def create_chart(self, title="Gantt Chart", height=800, width=1800, bar_thickness=0.5):
    #     df = pd.DataFrame(self.tasks)
        
    #     # Define the relative path for saving the data
    #     relative_path = os.path.join("Data", "gantt_chart_data.csv")
        
    #     # Ensure the 'Data' directory exists
    #     os.makedirs(os.path.dirname(relative_path), exist_ok=True)
        
    #     # Save DataFrame as CSV in the 'Data' directory
    #     df.to_csv(relative_path, index=False)

    #     # Generate the Gantt chart without using color="Task"
    #     fig = px.timeline(df, x_start="Start", x_end="Finish", y="Person",
    #                       title=title, height=height, width=width,
    #                       hover_data={'strLegendData': True})  # Add custom legend data as hover info

    #     fig.update_yaxes(autorange="reversed")
    #     fig.update_layout(
    #         xaxis_title="Time",
    #         yaxis_title="Person",
    #         xaxis=dict(
    #             rangeslider=dict(visible=True),  # Add horizontal scrollbar
    #         ),
    #         yaxis=dict(
    #             fixedrange=False  # Allow vertical scrolling
    #         )
    #     )

    #     # Manually apply custom colors, patterns, and widths
    #     for i, task in enumerate(fig.data):
    #         task.text = df['Task'].iloc[i]
    #         task.textposition = 'inside'
            
    #         # Manually set color
    #         if df['Color'].iloc[i]:
    #             task.marker.color = df['Color'].iloc[i]
            
    #         # Manually set pattern
    #         if df['Pattern'].iloc[i]:
    #             task.marker.pattern.shape = df['Pattern'].iloc[i]
            
    #         # Manually set width
    #         if df['BarWidth'].iloc[i]:
    #             task.width = df['BarWidth'].iloc[i]
    #         else:
    #             task.width = bar_thickness
        
    #     return fig
    def create_chart(self, title="Gantt Chart", height=800, width=1800, bar_thickness=0.5):
        df = pd.DataFrame(self.tasks)
        
        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Person", color="Task",
                          title=title, height=height, width=width)
        
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Person",
            xaxis=dict(
                rangeslider=dict(visible=True),  # Add horizontal scrollbar
            ),
            yaxis=dict(
                fixedrange=False  # Allow vertical scrolling
            )
        )
        
        # Add task names on the bars and apply custom colors, patterns, and bar widths
        for i, task in enumerate(fig.data):
            task.text = df['Task'].iloc[i]
            task.textposition = 'inside'
            
            if df['Color'].iloc[i]:
                task.marker.color = df['Color'].iloc[i]
            
            if df['Pattern'].iloc[i]:
                task.marker.pattern = {'shape': df['Pattern'].iloc[i]}
            
            # Apply custom bar width if specified
            if df['BarWidth'].iloc[i]:
                task.width = df['BarWidth'].iloc[i]
            else:
                task.width = bar_thickness
        
        return fig


    @staticmethod
    def Main(lsListIDs=["901600183071"], 
             strTskStDate=(datetime.now() - timedelta(weeks=1)).strftime('%d-%m-%Y'), 
             strTskEndDate=(datetime.now() + timedelta(weeks=3)).strftime('%d-%m-%Y'), 
             bDebug=True):
        try:
            # Ensure the dates are strings
            if isinstance(strTskStDate, datetime):
                strTskStDate = strTskStDate.strftime('%d-%m-%Y')
            if isinstance(strTskEndDate, datetime):
                strTskEndDate = strTskEndDate.strftime('%d-%m-%Y')

            # Debug info
            if bDebug:
                print(f"Task Start Date: {strTskStDate}, Task End Date: {strTskEndDate}")

            # Fetch tasks based on the list IDs and date criteria
            tasks = CClickUpDB.MSGetTasksByListIDs(lsListIDs, strTskStDate, strTskEndDate)

            # If there is any employee filter criteria, apply here (assumed logic)
            # employee_filter = 'John Doe' # Example: filter for a specific employee, if needed
            # employee_tasks = filter_tasks_by_employee(tasks, employee_filter)
            
            # Group tasks employee-wise
            employee_tasks = CClickUpMiddleWare.MSGroupTaskEmployeeWise(tasks)
            if bDebug:
                print(f"Employee tasks: {employee_tasks}")

            # Sort tasks and return sorted employee-wise task dictionary
            input_dict = CClickUpMiddleWare.MSSortDF(employee_tasks, bDebug=bDebug)
            
            if bDebug:
                print(f"Sorted Task list Employee Wise: {input_dict}")
            
            return input_dict
        except Exception as e:
            print("Error - ", e)

    @staticmethod
    def MSGenerateLegend(task_detail):
        """
        Generates a formatted legend string from a task detail dictionary.

        Parameters:
        task_detail (dict): A dictionary containing task details.

        Returns:
        str: A formatted legend string with better readability.
        """
        # Extract task details with default values if keys are missing
        taskId = task_detail.get('TaskID', 'Not Found')
        task_subject = task_detail.get('TaskSubject', 'No Subject')
        list_name = task_detail.get('ListName', 'No List')
        execution_date = task_detail.get('TaskExecutionDate', 'No Execution Date')
        due_date = task_detail.get('TaskDueDate', 'No Due Date')
        status = task_detail.get('TaskStatus', 'No Status')
        priority = task_detail.get('TaskPriority', 'No Priority')
        estimated_time = task_detail.get('TotalTskEstInMins', 'No Estimate')
        allocated_time = task_detail.get('AllocatedTimeMin', 'No Allocated Estimate')
        assignees = task_detail.get('TaskAssigneesList', [])
        score = task_detail.get('TaskScore', "Not Found")
        conflict = task_detail.get("IsConflict",False)
        
        # Format assignees
        assignee_details = []
        for assignee in assignees:
            name = assignee.get('username', 'Unknown')
            email = assignee.get('email', 'No Email')
            assignee_details.append(f"{name} ({email})")
        assignees_str = ', '.join(assignee_details) if assignee_details else 'No Assignees'

        # Create the legend string with better formatting for readability
        legend = (
            f"<b>TaskID</b>: {taskId}<br>"
            f"<b>Task Subject</b>: {task_subject}<br>"
            f"<b>List Name</b>: {list_name}<br>"
            f"<b>Execution Date</b>: {execution_date}<br>"
            f"<b>Due Date</b>: {due_date}<br>"
            f"<b>Status</b>: {status}<br>"
            f"<b>Priority</b>: {priority}<br>"
            f"<b>Total Task Est Time</b>: {estimated_time} minutes<br>"
            f"<b>Allocated Task Est Time</b>: {allocated_time} minutes<br>"
            f"<b>Assignees</b>: {assignees_str}<br>"
            f"<b>Score</b>: {score}"
            f"<b>Conflict</b>: {conflict}"
        )

        return legend
    
    def generate_rgb_shade(ignored_colors=None):
        """
        Generates a random RGB shade while ensuring it is not in the ignored list.

        Args:
            ignored_colors (list): List of colors to ignore in the format 'rgb(r, g, b)'.

        Returns:
            str: A unique RGB color in the format 'rgb(r, g, b)'.
        """
        if ignored_colors is None:
            ignored_colors = []
        
        while True:
            # Generate random RGB values
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            
            # Create the RGB string
            rgb_color = f'rgb({r}, {g}, {b})'
            
            # Check if the color is not in the ignored list
            if rgb_color not in ignored_colors:
                return rgb_color
    
    def MGetTskColor(self, dictDimensionConfig, dictTskDetails):
        # Convert dictDimensionConfig keys to lowercase
        dictDimensionConfig = {k.lower(): v for k, v in dictDimensionConfig.items()}
        
        dictColorDimConfig = dictDimensionConfig.get("color")
        strSelectedColorDim =dictColorDimConfig.get("selected")
        
        if strSelectedColorDim == "project":
            strTskListName = dictTskDetails.get("ListName")
            if strTskListName not in self.dictProjectColors.keys():
                self.dictProjectColors[strTskListName] = GanttChart.generate_rgb_shade(ignored_colors=['rgb(127, 0, 0)', 'rgb(0, 0, 64)', 'rgb(255, 0, 0)'])
            return self.dictProjectColors[strTskListName]
        elif strSelectedColorDim == "priority":
            priority_color_map = dictColorDimConfig.get("optiondetails", {}).get("priority", {})
            # Assign priority color based on task priority
            priority_color_rgb = priority_color_map.get(dictTskDetails.get("TaskPriority", "low").lower(), "rgb(72, 210, 255)")  # Default light blue
            return priority_color_rgb
        else:
            # Mapping task status to colors
            status_color_map = dictColorDimConfig.get("optiondetails", {}).get("status", {})
            # Assign status color based on task status
            status_color_rgb = status_color_map.get(dictTskDetails.get("TaskStatus", "open").lower(), "rgb(216, 216, 216)")  # Default light blue
            return status_color_rgb
    
    @staticmethod
    def MSGetPattern(dictDimensionConfig, dictTskDetails):
        # Convert dictDimensionConfig keys to lowercase
        dictDimensionConfig = {k.lower(): v for k, v in dictDimensionConfig.items()}
        
        dictPatternDimConfig = dictDimensionConfig.get("pattern")
        strSelectedPatternDim = dictPatternDimConfig.get("selected")
        
        # Two Option - Priority , Status
        if strSelectedPatternDim == "priority":
            priority_pattern_map = dictPatternDimConfig.get("optiondetails", {}).get("priority", {})
            # Assign priority pattern based on task priority
            priority_pattern = priority_pattern_map.get(dictTskDetails.get("TaskPriority", "low").lower(), "")  # Default No pattern
            return priority_pattern
        else:
            # Mapping task status to patterns
            status_pattern_map = dictPatternDimConfig.get("optiondetails", {}).get("status", {})
            # Assign status pattern based on task status
            status_pattern = status_pattern_map.get(dictTskDetails.get("TaskStatus", "open").lower(), "")  # Default no pattern
            return status_pattern

    @staticmethod
    def MSGetThickness(dictDimensionConfig, dictTskDetails):
        # Convert dictDimensionConfig keys to lowercase
        dictDimensionConfig = {k.lower(): v for k, v in dictDimensionConfig.items()}
        
        dictThicknessDimConfig = dictDimensionConfig.get("thickness")
        strSelectedThickness = dictThicknessDimConfig.get("selected")
        
        # Two Option - Priority , Status
        if strSelectedThickness == "priority":
            priority_thickness_map = dictThicknessDimConfig.get("optiondetails", {}).get("priority", {})
            # Assign priority thickness based on task priority
            priority_thickness = priority_thickness_map.get(dictTskDetails.get("TaskPriority", "low").lower(), 0.4)  # Default thickness
            return priority_thickness
        else:
            # Mapping task status to thickness
            status_thickness_map = dictThicknessDimConfig.get("optiondetails", {}).get("status", {})
            # Assign status thickness based on task status
            status_thickness = status_thickness_map.get(dictTskDetails.get("TaskStatus", "open").lower(), 0.4)  # Default thickness
            return status_thickness
        
if __name__ == "__main__":
    with open(r"resource\dimension_config.json") as f:
        dictDimensionConfig = json.load(f) 
    # Assuming the GanttChart class is already defined
    objGanttChart = GanttChart()
    lsSelectedEmployee = ["Mitul Solanki","mansi solanki","Mohit parmar","Nidhi"]
    # Fetching employee tasks for the given date range
    dictEmptasks = objGanttChart.Main(lsListIDs= ["901600183071","901604035672","901604046411"], strTskStDate="01-08-2024", strTskEndDate="26-08-2024")
    strColorType = "status"  # Could also be "priority"

    # Dictionary to store the last task end time for each employee per day
    last_task_end_time_per_emp = {}

    # Iterate over employees and their tasks
    Idx = 0
    for EmpName, lsEmpTasks in dictEmptasks.items():
        lsColors = ['rgb(127, 0, 0)','rgb(0, 0, 64)', 'rgb(255, 0, 0)']
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
        Idx +=1
    print("---------------------",objGanttChart.tasks)
    # Create and display the Gantt chart
    fig = objGanttChart.create_chart(title="Employee Wise Gantt Chart")
    fig.show()
