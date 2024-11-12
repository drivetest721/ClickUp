# # from taipy.gui import Gui, Markdown
# # import pandas as pd

# # if __name__ == "__main__":
# #     def table_style(state, index, row):
# #         return "highlight-row" if row.Category == "Burger" else ""

# #     table_properties = {
# #         "class_name": "rows-bordered rows-similar", # optional
# #         "row_class_name": table_style,
# #     }
# #     food_df = pd.DataFrame({
# #         "Meal": ["Lunch", "Dinner", "Lunch", "Lunch", "Breakfast", "Breakfast", "Lunch", "Dinner"],
# #         "Category": ["Food", "Food", "Drink", "Food", "Food", "Drink", "Dessert", "Dessert"],
# #         "Name": ["Burger", "Burger", "Soda", "Soda", "Pasta", "Water", "Ice Cream", "Ice Cream"],
# #         "Calories": [300, 400, 150, 200, 500, 0, 400, 500],
# #     })

# #     # main_md = Markdown("<|{food_df}|table|>")
# #     main_md = Markdown("<|{food_df}|table|group_by[Category]=True|group_by[Name]=True|apply[Calories]=sum|filter=True|properties=table_properties|>")
    
# #     Gui(page=main_md).run()

# # from taipy.gui import Gui, Markdown, notify
# # import pandas as pd


# # def food_df_on_edit(state, var_name, payload):
# #     index = payload["index"] # row index
# #     col = payload["col"] # column name
# #     value = payload["value"] # new value cast to the column type
# #     user_value = payload["user_value"] # new value as entered by the user

# #     old_value = state.food_df.loc[index, col]
# #     new_food_df = state.food_df.copy()
# #     new_food_df.loc[index, col] = value
# #     state.food_df = new_food_df
# #     notify(state, "I", f"Edited value from '{old_value}' to '{value}'. (index '{index}', column '{col}')")


# # def food_df_on_delete(state, var_name, payload):
# #     index = payload["index"] # row index

# #     state.food_df = state.food_df.drop(index=index)
# #     notify(state, "E", f"Deleted row at index '{index}'")


# # def food_df_on_add(state, var_name, payload):
# #     empty_row = pd.DataFrame([[None for _ in state.food_df.columns]], columns=state.food_df.columns)
# #     state.food_df = pd.concat([empty_row, state.food_df], axis=0, ignore_index=True)

# #     notify(state, "S", f"Added a new row.")

# # if __name__ == "__main__":
# #     food_df = pd.DataFrame({
# #         "Meal": ["Lunch", "Dinner", "Lunch", "Lunch", "Breakfast", "Breakfast", "Lunch", "Dinner"],
# #         "Category": ["Food", "Food", "Drink", "Food", "Food", "Drink", "Dessert", "Dessert"],
# #         "Name": ["Burger", "Pizza", "Soda", "Salad", "Pasta", "Water", "Ice Cream", "Cake"],
# #         "Calories": [300, 400, 150, 200, 500, 0, 400, 500],
# #     })

# #     table_properties = {
# #         "class_name": "rows-bordered",
# #         "editable": True,
# #         "filter": True,
# #         "on_edit": food_df_on_edit,
# #         "on_delete": food_df_on_delete,
# #         "on_add": food_df_on_add,
# #         "group_by[Category]": True,
# #         "apply[Calories]": "sum",
# #     }

# #     main_md = Markdown("""
# # # Daily Calorie Tracker

# # <|{food_df}|table|properties=table_properties|row_class_name=even_odd_class|>
# #     """)

# #     Gui(page=main_md).run()

# # Copyright 2021-2024 Avaiga Private Limited
# #
# # Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# # the License. You may obtain a copy of the License at
# #
# #        http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# # an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# # specific language governing permissions and limitations under the License.
# # -----------------------------------------------------------------------------------------
# # To execute this script, make sure that the taipy-gui package is installed in your
# # Python environment and run:
# #     python <script>
# # -----------------------------------------------------------------------------------------
# # import datetime
# from taipy.gui import Gui
# from datetime import datetime

# # Tasks definitions
# tasks = ["Plan", "Research", "Design", "Implement", "Test", "Deliver"]
# # Planned start dates of tasks
# start_dates = [
#     datetime(2022, 10, 15,0,0,0),  # Plan
#     datetime(2022, 11, 7,0,2,0),  # Research
#     datetime(2022, 12, 1,4,0,0),  # Design
#     datetime(2022, 12, 20,4,0,0),  # Implement
#     datetime(2023, 1, 15,5,0,0),  # Test
#     datetime(2023, 2, 1,2,0,0),  # Deliver
# ]

# # Calculate end dates based on start dates and durations
# durations = [50, 30, 30, 40, 15, 10]  # List of task durations (in days)
# # end_dates = [start_date + datetime.timedelta(days=duration) for start_date, duration in zip(start_dates, durations)]

# # Convert to Unix timestamps (seconds since epoch)
# unix_timestamps = [(date - datetime(2022, 10, 15)).total_seconds() for date in start_dates]
# data = {
#     "Task": tasks,
#     "Start": unix_timestamps,  # Use the converted timestamps
#     "End": [t + duration * 86400 for t, duration in zip(unix_timestamps, durations)],  # Calculate end timestamps
# }

# layout = {
#     "xaxis": {
#         "title": {"text": "Start Date & Time"},  # Label the axis
#         "type": "date",  # Attempt to interpret as dates (may not be perfect)
#     },
#     "yaxis": {
#         "autorange": "reversed",
#         "title": {"text": ""},
#     },
# }

# page = """
# <|{data}|chart|type=gantt|x=Start|y=Task|layout={layout}|>
# """

# if __name__ == "__main__":
#     Gui(page).run(title="Gantt Chart")


# from taipy.gui import Gui
# import plotly.express as px
# from PlotMain import GanttChart
# # Create a Plotly figure
# df = px.data.iris()
# # fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species")
# objFigure = GanttChart.Master(lsEmps= [
#         'mitul@riveredgeanalytics.com', 'mansi@riveredgeanalytics.com', 'hr@riveredgeanalytics.com',
#         'devanshi@riveredgeanalytics.com', 'dhruvin@riveredgeanalytics.com',
#         'mohit.intern@riveredgeanalytics.com', 'harshil@riveredgeanalytics.com',"fenil@riveredgeanalytics.com","punesh@riveredgeanalytics.com","ankita@riveredgeanalytics.com","nikhil@riveredgeanalytics.com","mansip@riveredgeanalytics.com","zahid@riveredgeanalytics.com"
#     ], lsProjects=['901601699012', '901600183071', '901603806927',"901604664293","901604664323","901604664325","901604664326","901604664327","901604664329","901604664340"], StartDate="01-09-2024",EndDate="01-12-2024",bTaskIntensityInclude=False, bFetchLatest=False,bShowPlot=False)
    
# # Define the Taipy page
# page = """
# <|chart|figure={objFigure}|>
# """

# # Start the Taipy app
# app = Gui(page)
# app.run()

from taipy.gui import Gui
import plotly.express as px
from PlotMain import GanttChart

# Initialize variables with default values for inputs
lsEmps = [
    'mitul@riveredgeanalytics.com', 'mansi@riveredgeanalytics.com', 'hr@riveredgeanalytics.com',
    'devanshi@riveredgeanalytics.com', 'dhruvin@riveredgeanalytics.com',
    'mohit.intern@riveredgeanalytics.com', 'harshil@riveredgeanalytics.com',
    "fenil@riveredgeanalytics.com", "punesh@riveredgeanalytics.com", "ankita@riveredgeanalytics.com",
    "nikhil@riveredgeanalytics.com", "mansip@riveredgeanalytics.com", "zahid@riveredgeanalytics.com"
]
lsProjects = ['901601699012', '901600183071', '901603806927', "901604664293", "901604664323",
              "901604664325", "901604664326", "901604664327", "901604664329", "901604664340"]
StartDate = "01-09-2024"
EndDate = "01-12-2024"
bTaskIntensityInclude = False
bFetchLatest = False
bShowPlot = False
objFigure = None  # Initialize the chart object

# Function to generate the chart based on user inputs
def generate_chart():
    global objFigure  # Modify the global figure object
    employee_list = [emp.strip() for emp in lsEmps.split(',')] if isinstance(lsEmps, str) else lsEmps
    project_list = [proj.strip() for proj in lsProjects.split(',')] if isinstance(lsProjects, str) else lsProjects
    
    # Generate the Gantt chart figure
    objFigure = GanttChart.Master(
        lsEmps=employee_list,
        lsProjects=project_list,
        StartDate=StartDate,
        EndDate=EndDate,
        bTaskIntensityInclude=bTaskIntensityInclude,
        bFetchLatest=bFetchLatest,
        bShowPlot=bShowPlot
    )

# Define the Taipy page with input fields and a "Generate Chart" button
page = """
# Configure Gantt Chart Parameters

### Employees
<|{lsEmps}|input|label=Employee Emails (comma-separated)|>

### Projects
<|{lsProjects}|input|label=Project IDs (comma-separated)|>

### Start Date
<|{StartDate}|input|type=date|label=Start Date|>

### End Date
<|{EndDate}|input|type=date|label=End Date|>

### Task Intensity Include
<|{bTaskIntensityInclude}|toggle|label=Include Task Intensity|>

### Fetch Latest
<|{bFetchLatest}|toggle|label=Fetch Latest|>

### Show Plot
<|{bShowPlot}|toggle|label=Show Plot|>

<|Generate Chart|button|on_action=generate_chart|>

<|chart|figure={objFigure}|>
"""

# Start the Taipy app
app = Gui(page)
app.run()
