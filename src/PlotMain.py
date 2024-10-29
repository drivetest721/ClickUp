import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import plotly.colors as pc
from datetime import datetime, timedelta
from ClickUpDB import CClickUpDB
from ClickUpHelper import CClickUpHelper
from main import CClickUpMiddleWare
import os
import random
import json
from ClickUpAPI import CClickUpAPI
from helperFunc import readJson,generate_random_alphanumeric_code, GetTimeInHrsAndMins

temp_rules= readJson(r"resource\recurring_task.json")

class GanttChart:
    strEmployeeConfig = r"resource\employeeConfig.json"
    dictEmployee = readJson(strEmployeeConfig)
    
    def __init__(self):
        self.tasks = []
        self.dictProjectColors = {}
        self.dictProjectPattern = {}
        self.patterns = [
            ".",  # Dot pattern  P1
            "x",  # Cross-hatch pattern  P2
            "/",  # Forward slash pattern   
            "\\",  # Backward slash pattern
            "+",  # Plus sign pattern
            "-",  # Horizontal line pattern
            "|",  # Vertical line pattern
            ""  # Solid fill (no pattern)  P0
        ]
        self.patternIndex = 0
        self.SelectedColors = {}
        self.SelectedPattern = {}
        
        
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
        
    #     fig = px.timeline(df, x_start="Start", x_end="Finish", y="Person", color="Task",
    #                       title=title, height=height, width=width)  # Use the Date column to create animation frames)
        
    #     fig.update_yaxes(autorange="reversed")
    #     fig.update_layout(
    #         xaxis_title="Time",
    #         yaxis_title="Person",
    #         xaxis=dict(
    #             rangeslider=dict(visible=True),  # Add horizontal scrollbar
    #         ),
    #         yaxis=dict(
    #             fixedrange=False  # Allow vertical scrolling
    #         ),
    #         showlegend=False  # Turn off the legend
    #     )
    #     # Add zoom control buttons for 1 Day and 1 Week
    #     fig.update_layout(
    #         updatemenus=[
    #             dict(
    #                 type="buttons",
    #                 direction="left",
    #                 x=0.5,
    #                 y=1.2,
    #                 buttons=list([
    #                     dict(
    #                         args=[{"xaxis.range": [df['Start'].min(), df['Start'].min() + pd.DateOffset(days=1)]}],
    #                         label="1 Day",
    #                         method="relayout"
    #                     ),
    #                     dict(
    #                         args=[{"xaxis.range": [df['Start'].min(), df['Start'].min() + pd.DateOffset(weeks=1)]}],
    #                         label="1 Week",
    #                         method="relayout"
    #                     ),
    #                     dict(
    #                         args=[{"xaxis.autorange": True}],  # Reset to full zoom
    #                         label="Reset",
    #                         method="relayout"
    #                     )
    #                 ]),
    #                 showactive=True,
    #                 xanchor="center"
    #             )
    #         ]
    #     )
    #     # Add task names on the bars and apply custom colors, patterns, and bar widths
    #     for i, task in enumerate(fig.data):
    #         task.text = df['Task'].iloc[i]
    #         task.textposition = 'inside'
            
    #         if df['Color'].iloc[i]:
    #             task.marker.color = df['Color'].iloc[i]
            
    #         if df['Pattern'].iloc[i]:
    #             task.marker.pattern = {'shape': df['Pattern'].iloc[i]}
            
    #         # Apply custom bar width if specified
    #         if df['BarWidth'].iloc[i]:
    #             task.width = df['BarWidth'].iloc[i]
    #         else:
    #             task.width = bar_thickness

    #         # Update hover template to display strLegendData
    #         task.hovertemplate = df['strLegendData'].iloc[i]  # Customize hover text
    #     return fig

    def create_chart(self, title="Gantt Chart", height=900, width=1800, bar_thickness=0.5):
        df = pd.DataFrame(self.tasks)

        # Create the Gantt chart using Plotly
        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Person", color="Task",
                        title=title, height=height, width=width)
        
        # Update y-axis to reverse order (for Gantt charts)
        fig.update_yaxes(autorange="reversed")
        
        # Add layout configurations
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Person",
            xaxis=dict(
                rangeslider=dict(visible=True),  # Add horizontal scrollbar
                fixedrange=False,  # Allow panning/zooming horizontally
                side="top"  # Position x-axis on top for better Gantt chart view
            ),
            yaxis=dict(
                fixedrange=False,  # Allow vertical scrolling
                automargin=True,  # Adjust margins to accommodate labels
            ),
            showlegend=False,  # Turn off the legend
            height=height,
            width=width
        )

        # Add alternating date background shades
        min_date = df['Start'].min().floor('D')
        max_date = df['Finish'].max().ceil('D')
        num_days = (max_date - min_date).days + 1
        
        shapes = []
        light_grey = "rgba(211, 215, 223,0.5)"  # Soft, subtle gray for light sections
        dark_grey = "rgb(122, 136, 159,0.5)"  # Slightly brighter but still subtle for alternating sections

        for i in range(num_days):
            start_date = min_date + pd.Timedelta(days=i)
            end_date = start_date + pd.Timedelta(days=1)
            
            # Alternate the color based on the day index
            color = light_grey if i % 2 == 0 else dark_grey
            
            # Add shape to the list
            shapes.append(dict(
                type="rect",
                x0=start_date, x1=end_date,
                y0=0, y1=1,  # Extend the rectangle vertically across the plot
                xref="x", yref="paper",  # x-axis refers to data, y-axis spans full plot height
                fillcolor=color,
                opacity=0.3,
                layer="below",  # Ensure it is behind the chart elements
                line_width=0
            ))
        
        # Add the shapes to the chart layout
        fig.update_layout(shapes=shapes)

        # Create buttons for zooming to specific dates and months
        unique_dates = sorted(df['Start'].dt.date.unique())
        unique_months = sorted(df['Start'].dt.to_period("M").unique())

        date_buttons = [
            dict(
                args=[{"xaxis.range": [pd.Timestamp(date), pd.Timestamp(date) + pd.Timedelta(days=1)]}],
                label=date.strftime("%Y-%m-%d"),
                method="relayout"
            ) for date in unique_dates
        ]

        month_buttons = [
            dict(
                args=[{"xaxis.range": [pd.Timestamp(str(month)), pd.Timestamp(str(month)) + pd.DateOffset(months=1)]}],
                label=str(month),
                method="relayout"
            ) for month in unique_months
        ]

        # Add zoom control buttons for 1 Day, 1 Week, specific dates, and specific months
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    x=0.5,
                    y=1.2,
                    buttons=list([
                        dict(
                            args=[{"xaxis.range": [df['Start'].min(), df['Start'].min() + pd.DateOffset(days=1)]}],
                            label="1 Day",
                            method="relayout"
                        ),
                        dict(
                            args=[{"xaxis.range": [df['Start'].min(), df['Start'].min() + pd.DateOffset(weeks=1)]}],
                            label="1 Week",
                            method="relayout"
                        ),
                        dict(
                            args=[{"xaxis.autorange": True}],  # Reset to full zoom
                            label="Reset",
                            method="relayout"
                        )
                    ]),
                    showactive=True,
                    xanchor="center"
                ),
                dict(
                    type="dropdown",
                    direction="down",
                    x=0.6,
                    y=1.2,
                    buttons=date_buttons,
                    showactive=True,
                    xanchor="center",
                ),
                dict(
                    type="dropdown",
                    direction="down",
                    x=0.7,
                    y=1.2,
                    buttons=month_buttons,
                    showactive=True,
                    xanchor="center",
                )
            ]
        )
        
        # Add task names on the bars and apply custom colors, patterns, and bar widths
        for i, task in enumerate(fig.data):
            task.text = df['Task'].iloc[i]
            task.textposition = 'inside'
            task.hoverinfo = "skip"  # Disable the default hoverinfo to avoid extra tooltips
            
            if df['Color'].iloc[i]:
                task.marker.color = df['Color'].iloc[i]

            if df['Pattern'].iloc[i]:
                task.marker.pattern = {'shape': df['Pattern'].iloc[i]}

            # Apply custom bar width if specified
            if df['BarWidth'].iloc[i]:
                task.width = df['BarWidth'].iloc[i]
            else:
                task.width = bar_thickness

            # Update hover template to display strLegendData
            task.hovertemplate = df['strLegendData'].iloc[i]  # Customize hover text

        return fig



    @staticmethod
    def Main(lsListIDs=["901600183071"], 
             strTskStDate=(datetime.now() - timedelta(weeks=1)).strftime('%d-%m-%Y'), 
             strTskEndDate=(datetime.now() + timedelta(weeks=3)).strftime('%d-%m-%Y'), 
             lsEmployees=[],
             bDebug=True,include_toughness=False):
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
            # tasks = CClickUpDB.MSGetTasksByListIDs(lsListIDs, strTskStDate, strTskEndDate)
            tasks = CClickUpDB.MSGetTasksByListIDsWithEmpFilter(lsListIDs, strTskStDate, strTskEndDate, lsEmployees, bDebug=False)

            # If there is any employee filter criteria, apply here (assumed logic)
            # employee_filter = 'John Doe' # Example: filter for a specific employee, if needed
            # employee_tasks = filter_tasks_by_employee(tasks, employee_filter)
            
            # Group tasks employee-wise
            employee_tasks = CClickUpMiddleWare.MSGroupTaskEmployeeWise(tasks,include_toughness=include_toughness)
            extendedEmployeeTasks = CClickUpMiddleWare.MSExpandTasksBasedOnRules(employee_tasks, temp_rules = temp_rules)
            if bDebug:
                print(f"Employee tasks: {employee_tasks}")

            # Sort tasks and return sorted employee-wise task dictionary
            input_dict = CClickUpMiddleWare.MSSortDF(extendedEmployeeTasks, bDebug=bDebug, bSaveReportToExcel= False)
            
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
        list_name = task_detail.get('ListName', 'Not Mention')
        execution_date = task_detail.get('TaskExecutionDate', 'No Execution Date')
        due_date = task_detail.get('TaskDueDate', 'No Due Date')
        status = task_detail.get('TaskStatus', 'No Status')
        priority = task_detail.get('TaskPriority', 'No Priority')
        estimated_time = task_detail.get('TotalTskEstInMins', 'No Estimate')
        allocated_time = task_detail.get('AllocatedTimeMin', 'No Allocated Estimate')
        assignees = task_detail.get('TaskAssigneesList', [])
        score = task_detail.get('TaskScore', "Not Found")
        conflict = task_detail.get("IsConflict",False)
        conflict_time = task_detail.get('ConflictTimeMin', 0)
        
        # Format assignees
        assignee_details = []
        for assignee in assignees:
            name = assignee.get('username', 'Unknown')
            email = assignee.get('email', 'No Email')
            assignee_details.append(f"{name} - {email}")
        assignees_str = ', '.join(assignee_details) if assignee_details else 'No Assignees'

        # Adjust font size and style based on priority
        if priority == "urgent":
            font_size = "25px"
            font_style = "font-weight: bold;"
        elif priority == "high":
            font_size = "21px"
            font_style = "font-style: italic;"
        elif priority in ["low", "normal"]:
            font_size = "12px"
            font_style = ""
        else:
            font_size = "12px"
            font_style = ""
        priority_display = priority if priority in ["urgent", "high", "low", "normal"] else "No Priority"

        # Create the legend string with priority-based font size
        strTskSubject = (
            f"<span style='font-size:{font_size}; {font_style}'>{task_subject} ({status}, {priority_display}, {assignees_str})</span>"
        )
        # Create the legend string with better formatting for readability
        legend = (
            f"<b>Task Subject</b>: {strTskSubject} <br>"
            f"{f'<b>Conflicted Task Time</b>: {GetTimeInHrsAndMins(conflict_time)}<br>' if conflict else f'<b>Allocated Task Est Time: {GetTimeInHrsAndMins(allocated_time)}</b><br>'}"
            f"{f'<b>Project: {list_name}</b><br><b>Score</b>: {score}<br><b>TaskID</b>: {taskId}<br>' if status != 'idle time' else ''}"
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
            self.SelectedColors[CClickUpHelper.rgb_to_color_name(status_color_rgb)] = dictTskDetails.get("TaskStatus")
            return status_color_rgb
    
    def MGetPattern(self, dictDimensionConfig, dictTskDetails):
        # Convert dictDimensionConfig keys to lowercase
        dictDimensionConfig = {k.lower(): v for k, v in dictDimensionConfig.items()}
        
        dictPatternDimConfig = dictDimensionConfig.get("pattern")
        strSelectedPatternDim = dictPatternDimConfig.get("selected")
        
        # Two Option - Priority , Status
        if strSelectedPatternDim == "project":
            strTskListName = dictTskDetails.get("ListName")
            if strTskListName not in self.dictProjectPattern.keys():
                strSelectedPattern = self.patterns[self.patternIndex]
                self.dictProjectPattern[strTskListName] = strSelectedPattern
                self.patternIndex+=1
                self.SelectedPattern[strSelectedPattern] = strTskListName
            return self.dictProjectPattern[strTskListName]
        elif strSelectedPatternDim == "priority":
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
            defaultThickness = priority_thickness_map.get("normal",0.4)
            # Assign priority thickness based on task priority
            if dictTskDetails.get("TaskPriority") is None:
                # assume priority to normal when no priority selected
                dictTskDetails["TaskPriority"] = "normal" 
            priority_thickness = priority_thickness_map.get(dictTskDetails.get("TaskPriority").lower(), defaultThickness)  # Default thickness
            return priority_thickness
        else:
            # Mapping task status to thickness
            status_thickness_map = dictThicknessDimConfig.get("optiondetails", {}).get("status", {})
            defaultThickness = status_thickness_map.get("open",0.4)
            # Assign status thickness based on task status
            status_thickness = status_thickness_map.get(dictTskDetails.get("TaskStatus", "open").lower(), defaultThickness)  # Default thickness
            return status_thickness
    
    @staticmethod
    def Master(lsEmps, lsProjects, StartDate="25-08-2024", EndDate="20-09-2024", bTaskIntensityInclude=False, bFetchLatest=False,bShowPlot=False):
        try:
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
                            uniqueCode = generate_random_alphanumeric_code()
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
                            # elif task.get("TaskStatus").lower() == "idle time":
                            #     color = "rgb(197, 197, 197)"
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
                                # assume priority to normal when no priority selected
                                priority = "normal" 
                            # Handle task conflict color
                            strTaskDetail = objGanttChart.MSGenerateLegend(task)
                            
                            # strTskSubject = f"<b>{count}. {task.get('TaskSubject', '')}</b> {status} {priority}"
                            # strTskSubject =  f"<span style='font-size:20px;'><b>{count}. {task.get('TaskSubject', '')}</b> {status} {priority}</span>"
                            if priority == "urgent":
                                strTskSubject = f"<span style='font-size:30px;'><b> {task.get('TaskSubject', '')}</b> {status} {priority}, {uniqueCode}</span>"
                            elif priority =="high":
                                strTskSubject = f"<span style='font-size:22px;'><i> {task.get('TaskSubject', '')}</i> {status} {priority}, {uniqueCode}</span>"
                            elif priority in ["low","normal"]:
                                strTskSubject = f"<span style='font-size:12px;'> {task.get('TaskSubject', '')} {status} {priority}, {uniqueCode}</span>"
                            else:
                                strTskSubject = f"<span style='font-size:12px;'> {task.get('TaskSubject', '')} {status} No-Priority, {uniqueCode}</span>"
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
                        uniqueCode = generate_random_alphanumeric_code()
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
                            # elif taskDetail.get("TaskStatus").lower() == "idle time":
                            #     color = "rgb(197, 197, 197)"
                            #     print("Idle color choosen ---------------",color)
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
                        priority = taskDetail.get("TaskPriority", "normal")
                        if priority is None:
                            # assume priority to normal when no priority selected
                            priority = "normal" 
                        # Handle task conflict color
                        strTaskDetail = objGanttChart.MSGenerateLegend(taskDetail)
                        # strTskSubject = f"<b>{count}. {taskDetail.get('TaskSubject', '')}</b> {status} {priority}"
                        # strTskSubject = f"<span style='font-size:20px;'><b>{count}. {taskDetail.get('TaskSubject', '')}</b> {status} {priority}</span>"

                        if priority == "urgent":
                            strTskSubject = f"<span style='font-size:30px;'><b> {taskDetail.get('TaskSubject', '')}</b> {status} {priority}, {uniqueCode}</span>"
                        elif priority == "high":
                            strTskSubject = f"<span style='font-size:22px;'><i> {taskDetail.get('TaskSubject', '')}</i> {status} {priority}, {uniqueCode}</span>"
                        elif priority in ["low","normal"]:
                            strTskSubject = f"<span style='font-size:12px;'> {taskDetail.get('TaskSubject', '')} {status} {priority}, {uniqueCode}</span>"
                        else:
                            strTskSubject = f"<span style='font-size:12px;'> {taskDetail.get('TaskSubject', '')} {status} No-Priority, {uniqueCode}</span>"
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
            if bShowPlot:
                fig.show()
            return fig
        except Exception as e:
            print("Error Occur", e)
if __name__ == "__main__":
    # with open(r"resource\dimension_config.json") as f:
    #     dictDimensionConfig = json.load(f)
    # isThicknessEnabled = (dictDimensionConfig.get("thickness").get("selected")) != ""
    # isPatternEnabled = (dictDimensionConfig.get("pattern").get("selected")) != ""
    # isColorEnabled =  (dictDimensionConfig.get("color").get("selected")) != ""
    
    # # Assuming the GanttChart class is already defined
    # objGanttChart = GanttChart()
    # lsSelectedEmployee = ["Mitul Solanki","mansi solanki","Mohit parmar","Nidhi"]
    # # Fetching employee tasks for the given date range
    # dictEmptasks = objGanttChart.Main(lsListIDs= ['901601699012', '901600183071', '901603806927',"901604664293","901604664323","901604664325","901604664326","901604664327","901604664329","901604664340"], strTskStDate="25-09-2024", strTskEndDate="20-11-2024")
    # strColorType = "status"  # Could also be "priority"

    # # Dictionary to store the last task end time for each employee per day
    # last_task_end_time_per_emp = {}

    # # Iterate over employees and their tasks
    # Idx = 0
    # for EmpName, lsEmpTasks in dictEmptasks.items():
    #     lsColors = ['rgb(127, 0, 0)','rgb(0, 0, 64)', 'rgb(255, 0, 0)']
    #     count = 1
    #     for taskDetail in lsEmpTasks:
            
            
    #         # Check if the task has a conflict and if AllocatedTimeMin > 0
    #         if taskDetail.get("IsConflict", False) and taskDetail.get("AllocatedTimeMin", 0) > 0:
    #             # Split into two tasks: allocated time and conflict time

    #             # Task with AllocatedTimeMin
    #             allocated_time_task = taskDetail.copy()
    #             allocated_time_task['AllocatedTimeMin'] = taskDetail.get('AllocatedTimeMin', 0)
    #             allocated_time_task['IsConflict'] = False

    #             # Task with ConflictTimeMin
    #             conflict_time_task = taskDetail.copy()

    #             conflict_time_task['TotalTskEstInMins'] = allocated_time_task['TotalTskEstInMins'] - allocated_time_task['AllocatedTimeMin']
    #             conflict_time_task['AllocatedTimeMin'] = taskDetail.get('ConflictTimeMin', 0)
    #             conflict_time_task['IsConflict'] = True

    #             # Process the allocated task
    #             for task in [allocated_time_task, conflict_time_task]:
    #                 start_time_str = task['TaskExecutionDate']
    #                 if task['TaskExecutionDate']:
    #                     try:
    #                         start_time_str += ' ' + task['TaskExecutionDate'].split(' ')[1]
    #                     except IndexError:
    #                         start_time_str += ' 00:00:00'  # Default to midnight if no time is present
    #                 else:
    #                     start_time_str += ' 00:00:00'  # Default to midnight if no time is present

    #                 # Convert the start_time_str to a datetime object
    #                 try:
    #                     start_time = datetime.strptime(start_time_str, '%d-%m-%Y %H:%M:%S')
    #                 except ValueError:
    #                     print(f"Error parsing start time: {start_time_str}")
    #                     start_time = datetime.strptime(task['TaskExecutionDate'], '%d-%m-%Y')

    #                 # Determine task duration (in minutes)
    #                 duration = timedelta(minutes=task.get('AllocatedTimeMin', 0))

    #                 # Track the last end time for each employee and day
    #                 task_date = start_time.date()

    #                 if EmpName not in last_task_end_time_per_emp:
    #                     last_task_end_time_per_emp[EmpName] = {}

    #                 if task_date in last_task_end_time_per_emp[EmpName]:
    #                     # Start the task from the previous task's end time
    #                     start_time = last_task_end_time_per_emp[EmpName][task_date]
    #                 else:
    #                     # It's a new day for this employee, start as per the task's TaskExecutionDate
    #                     last_task_end_time_per_emp[EmpName][task_date] = start_time

    #                 # Calculate the task's end time (start_time + duration)
    #                 end_time = start_time + duration
    #                 # Update the last task end time for this date
    #                 last_task_end_time_per_emp[EmpName][task_date] = end_time

    #                 # Get color based on color type (status or priority)
    #                 if task.get("IsConflict",False):
    #                     color = "rgb(255, 0, 0)"
    #                     print("Conflict color choosen ---------------",color)
    #                 elif task.get("TaskStatus").lower() == "idle time":
    #                     color = "rgb(197, 197, 197)"
    #                 else:
    #                     color = objGanttChart.MGetTskColor(dictDimensionConfig=dictDimensionConfig, dictTskDetails=task)
    #                 if isThicknessEnabled:
    #                     bar_width = GanttChart.MSGetThickness(dictDimensionConfig=dictDimensionConfig, dictTskDetails=task)


    #                 pattern = objGanttChart.MGetPattern(dictDimensionConfig=dictDimensionConfig, dictTskDetails=task)
    #                 # Get pattern based on task status
    #                 status = task.get("TaskStatus", "open")  # Assuming status is a string
    #                 # print("status", status, "pattern---------", pattern, "bar_width", bar_width)
    #                 priority = task.get("TaskPriority", "low")
    #                 if priority is None:
    #                     priority = "low" 
    #                 # Handle task conflict color
    #                 strTaskDetail = objGanttChart.MSGenerateLegend(task)
                    
    #                 # strTskSubject = f"<b>{count}. {task.get('TaskSubject', '')}</b> {status} {priority}"
    #                 # strTskSubject =  f"<span style='font-size:20px;'><b>{count}. {task.get('TaskSubject', '')}</b> {status} {priority}</span>"
    #                 if priority == "urgent":
    #                     strTskSubject = f"<span style='font-size:20px;'><b>{count}. {task.get('TaskSubject', '')}</b> ({status}, {priority})</span>"
    #                 elif priority in ["normal", "high"]:
    #                     strTskSubject = f"<span style='font-size:20px;'><i>{count}. {task.get('TaskSubject', '')}</i> ({status}, {priority})</span>"
    #                 elif priority == "low":
    #                     strTskSubject = f"<span style='font-size:20px;'>{count}. {task.get('TaskSubject', '')} ({status}, {priority})</span>"
    #                 else:
    #                     strTskSubject = f"<span style='font-size:20px;'>{count}. {task.get('TaskSubject', '')} ({status}, No-Priority)</span>"
    #                 # Add task to Gantt chart
    #                 objGanttChart.add_task(
    #                     task_name=strTskSubject,
    #                     person=EmpName,
    #                     start_datetime=start_time,
    #                     duration=duration,
    #                     color=color,
    #                     pattern=pattern,
    #                     bar_width=bar_width,
    #                     strLegendData=strTaskDetail
    #                 )
    #                 count+=1
    #         else:
    #             # Process the task as usual if there is no conflict
    #             start_time_str = taskDetail['TaskExecutionDate']
    #             if taskDetail['TaskExecutionDate']:
    #                 try:
    #                     start_time_str += ' ' + taskDetail['TaskExecutionDate'].split(' ')[1]
    #                 except IndexError:
    #                     start_time_str += ' 00:00:00'  # Default to midnight if no time is present
    #             else:
    #                 start_time_str += ' 00:00:00'  # Default to midnight if no time is present

    #             # Convert the start_time_str to a datetime object
    #             try:
    #                 start_time = datetime.strptime(start_time_str, '%d-%m-%Y %H:%M:%S')
    #             except ValueError:
    #                 print(f"Error parsing start time: {start_time_str}")
    #                 start_time = datetime.strptime(taskDetail['TaskExecutionDate'], '%d-%m-%Y')

    #             # Determine task duration (in minutes)
    #             if taskDetail.get("IsConflict", False) and taskDetail.get("ConflictTimeMin", 0) > 0:
    #                 duration = timedelta(minutes=taskDetail.get('ConflictTimeMin', 0))
    #             else:
    #                 duration = timedelta(minutes=taskDetail.get('AllocatedTimeMin', 0))
    #             # Track the last end time for each employee and day
    #             task_date = start_time.date()

    #             if EmpName not in last_task_end_time_per_emp:
    #                 last_task_end_time_per_emp[EmpName] = {}

    #             if task_date in last_task_end_time_per_emp[EmpName]:
    #                 # Start the task from the previous task's end time
    #                 start_time = last_task_end_time_per_emp[EmpName][task_date]
    #             else:
    #                 # It's a new day for this employee, start as per the task's TaskExecutionDate
    #                 last_task_end_time_per_emp[EmpName][task_date] = start_time

    #             # Calculate the task's end time (start_time + duration)
    #             end_time = start_time + duration
    #             # Update the last task end time for this date
    #             last_task_end_time_per_emp[EmpName][task_date] = end_time

    #             # Get color based on color type (status or priority)
    #             if isColorEnabled:
    #                 if taskDetail.get("IsConflict",False):
    #                     color = "rgb(255, 0, 0)"
    #                     print("Conflict color choosen ---------------",color)
    #                 elif taskDetail.get("TaskStatus").lower() == "idle time":
    #                     color = "rgb(197, 197, 197)"
    #                     print("Idle color choosen ---------------",color)
    #                 else:
    #                     color = objGanttChart.MGetTskColor(dictDimensionConfig=dictDimensionConfig, dictTskDetails=taskDetail)
    #             else:
    #                 color = None
                    
    #             if isThicknessEnabled:
    #                 bar_width = GanttChart.MSGetThickness(dictDimensionConfig=dictDimensionConfig, dictTskDetails=taskDetail)
    #             else:
    #                 bar_width = None

    #             if isPatternEnabled:
    #                 pattern = objGanttChart.MGetPattern(dictDimensionConfig=dictDimensionConfig, dictTskDetails=taskDetail)
    #             else:
    #                 pattern = None
                
    #             # Get pattern based on task status
    #             status = taskDetail.get("TaskStatus", "open")  # Assuming status is a string
    #             priority = taskDetail.get("TaskPriority", "low")
    #             if priority is None:
    #                 priority = "low" 
    #             # Handle task conflict color
    #             strTaskDetail = objGanttChart.MSGenerateLegend(taskDetail)
    #             # strTskSubject = f"<b>{count}. {taskDetail.get('TaskSubject', '')}</b> {status} {priority}"
    #             # strTskSubject = f"<span style='font-size:20px;'><b>{count}. {taskDetail.get('TaskSubject', '')}</b> {status} {priority}</span>"

    #             if priority == "urgent":
    #                 strTskSubject = f"<span style='font-size:20px;'><b>{count}. {taskDetail.get('TaskSubject', '')}</b> ({status}, {priority})</span>"
    #             elif priority in ["normal", "high"]:
    #                 strTskSubject = f"<span style='font-size:20px;'><i>{count}. {taskDetail.get('TaskSubject', '')}</i> ({status}, {priority})</span>"
    #             elif priority == "low":
    #                 strTskSubject = f"<span style='font-size:20px;'>{count}. {taskDetail.get('TaskSubject', '')} ({status}, {priority})</span>"
    #             else:
    #                 strTskSubject = f"<span style='font-size:20px;'>{count}. {taskDetail.get('TaskSubject', '')} ({status}, No-Priority)</span>"
    #             # Add task to Gantt chart
    #             objGanttChart.add_task(
    #                 task_name=strTskSubject,
    #                 person=EmpName,
    #                 start_datetime=start_time,
    #                 duration=duration,
    #                 color=color,
    #                 pattern=pattern,
    #                 bar_width=bar_width,
    #                 strLegendData=strTaskDetail
    #             )
    #             count +=1
    #     Idx +=1
    # print("---------------------",objGanttChart.tasks)
    # # Create and display the Gantt chart
    # fig = objGanttChart.create_chart(title="Employee Wise Gantt Chart")
    # fig.show()
    
    objFigure = GanttChart.Master(lsEmps= [
        'mitul@riveredgeanalytics.com', 'mansi@riveredgeanalytics.com', 'hr@riveredgeanalytics.com',
        'devanshi@riveredgeanalytics.com', 'dhruvin@riveredgeanalytics.com',
        'mohit.intern@riveredgeanalytics.com', 'harshil@riveredgeanalytics.com',"fenil@riveredgeanalytics.com","punesh@riveredgeanalytics.com","ankita@riveredgeanalytics.com","nikhil@riveredgeanalytics.com","mansip@riveredgeanalytics.com","zahid@riveredgeanalytics.com"
    ], lsProjects=['901601699012', '901600183071', '901603806927',"901604664293","901604664323","901604664325","901604664326","901604664327","901604664329","901604664340"], StartDate="01-09-2024",EndDate="01-12-2024",bTaskIntensityInclude=False, bFetchLatest=False,bShowPlot=True)
    
#     objFigure = GanttChart.Master(lsEmps= [
# "ankita@riveredgeanalytics.com", "fenil@riveredgeanalytics.com"

#     ], lsProjects=['901601699012', '901600183071', '901603806927',"901604664293","901604664323","901604664325","901604664326","901604664327","901604664329","901604664340"], StartDate="22-10-2024",EndDate="24-10-2024",bTaskIntensityInclude=False, bFetchLatest=False,bShowPlot=True)
    
    
    # GanttChart.Main(lsListIDs=['901601699012', '901600183071', '901603806927',"901604664293","901604664323","901604664325","901604664326","901604664327","901604664329","901604664340"], 
    #          strTskStDate=(datetime.now() - timedelta(weeks=1)).strftime('%d-%m-%Y'), 
    #          strTskEndDate=(datetime.now() + timedelta(weeks=3)).strftime('%d-%m-%Y'), 
    #          lsEmployees=[
    #     'mitul@riveredgeanalytics.com', 'mansi@riveredgeanalytics.com', 'hr@riveredgeanalytics.com',
    #     'devanshi@riveredgeanalytics.com', 'dhruvin@riveredgeanalytics.com',
    #     'mohit.intern@riveredgeanalytics.com', 'harshil@riveredgeanalytics.com',"fenil@riveredgeanalytics.com","punesh@riveredgeanalytics.com","ankita@riveredgeanalytics.com","nikhil@riveredgeanalytics.com","mansip@riveredgeanalytics.com","zahid@riveredgeanalytics.com"
    # ],
    #          bDebug=True,include_toughness=False)
