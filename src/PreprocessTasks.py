import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

import pandas as pd
from datetime import datetime
from main import CClickUpMiddleWare
from datetime import datetime, timedelta
from ClickUpDB import CClickUpDB


class GanttChart:
    def __init__(self):
        self.tasks = []

    def add_task(self, task_name, person, start_datetime, duration, color=None, pattern=None, bar_width=None):
        end_datetime = start_datetime + duration
        self.tasks.append({
            'Task': task_name,
            'Person': person,
            'Start': start_datetime,
            'Finish': end_datetime,
            'Color': color,
            'Pattern': pattern,
            'BarWidth': bar_width
        })

    def create_chart(self, title="Gantt Chart", height=800, width=1800, bar_thickness=0.5):
        df = pd.DataFrame(self.tasks)
        
        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Person", color="Task",
                          title=title, height=height, width=width)
        
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Person",
            xaxis=dict(
                rangeslider=dict(visible=True),
            ),
            yaxis=dict(
                fixedrange=False
            )
        )
        
        for i, task in enumerate(fig.data):
            task.text = df['Task'].iloc[i]
            task.textposition = 'inside'
            
            if df['Color'].iloc[i]:
                task.marker.color = df['Color'].iloc[i]
            
            if df['Pattern'].iloc[i]:
                task.marker.pattern = {'shape': df['Pattern'].iloc[i]}
            
            if df['BarWidth'].iloc[i]:
                task.width = df['BarWidth'].iloc[i]
            else:
                task.width = bar_thickness
        
        return fig
    
if __name__ == "__main__":
    # Example input
    listIds = ['901600183071']

    # list_id = "901600183071"  # Replace with your actual ListID
    start_date = "15-07-2024"  # Replace with your desired start date
    end_date = "20-08-2024"    # Replace with your desired end date
    bDebug = True

    # Fetch tasks based on the criteria
    tasks = CClickUpDB.MSGetTasksByListIDs(listIds, start_date, end_date)
    employee_tasks = CClickUpMiddleWare.MSGroupTaskEmployeeWise(tasks)
    # dictAllocatedDateWiseTask = CClickUpMiddleWare.MSCreateEmpDateWiseTasksList(employee_tasks, bDebug=False)
    # print(dictAllocatedDateWiseTask)
    print(employee_tasks)
    input_dict = CClickUpMiddleWare.MSSortDF(employee_tasks, bDebug=True)
    print("input_dict-------------------------------------\n",input_dict)
    # Initialize the GanttChart
    chart = GanttChart()

    # Loop through input dict to add tasks
    for person, tasks in input_dict.items():
        for task in tasks:
            # Parse start date and time
            start_time_str = task['TaskExecutionDate']
            if task['TaskCreatedDate']:
                try:
                    start_time_str += ' ' + task['TaskCreatedDate'].split(' ')[1]
                except IndexError:
                    start_time_str += ' 00:00:00'  # Default to midnight if no time is present
            else:
                start_time_str += ' 00:00:00'  # Default to midnight if no time is present

            try:
                start_time = datetime.strptime(start_time_str, '%d-%m-%Y')
            except ValueError:
                print("start_time",start_time_str)
                start_time = datetime.strptime(task['TaskExecutionDate'], '%d-%m-%Y')
            
            # Determine task duration
            duration = timedelta(minutes=task.get('AllocatedTimeMin', 0))
            
            # Add task to chart
            chart.add_task(task['TaskSubject'], person, start_time, duration)

    # Create and show the chart
    fig = chart.create_chart(title="Gantt Chart Example")
    fig.show()
