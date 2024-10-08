import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import plotly.colors as pc

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

    def generate_color_family(self, base_rgb, num_colors=5):
        """
        Generate a family of colors based on a given base color.
        
        :param base_color: A string representing the base color ('red', 'green', 'blue', etc.)
        :param num_colors: The number of colors to generate
        :return: A list of RGB color strings
        """
        colors = []
        for i in range(num_colors):
            # Calculate the shade factor
            factor = 0.5 + (i / (num_colors - 1)) * 0.5
            
            # Apply the factor to each RGB component
            r = int(base_rgb[0] * factor)
            g = int(base_rgb[1] * factor)
            b = int(base_rgb[2] * factor)
            
            # Ensure the values are within the valid range (0-255)
            r = max(0, min(r, 255))
            g = max(0, min(g, 255))
            b = max(0, min(b, 255))
            
            colors.append(f"rgb({r}, {g}, {b})")
        
        return colors
    
    def get_common_base_colors(self):
        """
        Returns a dictionary of common base colors with their RGB values.
        
        :return: A dictionary where keys are color names and values are RGB tuples.
        """
        return {
            # 'red': (255, 0, 0),
            # 'green': (0, 255, 0),
            # 'blue': (0, 0, 255),
            # 'yellow': (255, 255, 0),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255),
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            # 'gray': (128, 128, 128),
            # 'orange': (255, 165, 0),
            'purple': (128, 0, 128),
            'brown': (165, 42, 42),
            'pink': (255, 192, 203),
            'lime': (0, 255, 0),
            'teal': (0, 128, 128),
            'navy': (0, 0, 128)
        }
    
    def get_patterns(self):
        """
        Returns a list of different fill patterns for Gantt chart tasks.
        
        :return: A list of strings representing different fill patterns.
        """
        return [
            "",  # Solid fill (no pattern)  P0
            ".",  # Dot pattern  P1
            "x",  # Cross-hatch pattern  P2
            "/",  # Forward slash pattern   
            "\\",  # Backward slash pattern
            "+",  # Plus sign pattern
            "-",  # Horizontal line pattern
            "|"  # Vertical line pattern
        ]


# Example usage of generate_color_family method
if __name__ == "__main__":
    chart = GanttChart()
    
    # Generate a family of red colors
    red_family = chart.generate_color_family(chart.get_common_base_colors()['teal'], 8)
    
    # Generate a family of blue colors
    blue_family = chart.generate_color_family(chart.get_common_base_colors()['navy'], 6)
    
    # Use the generated colors in tasks
    start_time = datetime(2023, 5, 1, 9, 0)  # May 1, 2023, 9:00 AM
    for i, color in enumerate(red_family):
        chart.add_task(f"Red Task {i+1}", "Mitul", start_time + timedelta(hours=i*2), timedelta(hours=2), color=color, pattern=chart.get_patterns()[i], bar_width=i*0.1 +0.1)
    
    for i, color in enumerate(blue_family):
        chart.add_task(f"Blue Task {i+1}", "Person B", start_time + timedelta(hours=i*3), timedelta(hours=3), color=color, pattern=chart.get_patterns()[i], bar_width=i*0.2 +0.2)

    
    # Create and show the chart
    fig = chart.create_chart(title="Color Family Example")
    fig.show()


# # Example usage
# if __name__ == "__main__":
#     chart = GanttChart()
    
#     # Adding tasks with custom colors and patterns
#     start_time = datetime(2023, 5, 1, 9, 0)  # May 1, 2023, 9:00 AM
#     chart.add_task("Cleanup Clickup", "Mitul", start_time, timedelta(hours=4), color="rgb(255, 0, 0)", pattern="\\")
#     chart.add_task("Task 2", "Person B", start_time + timedelta(hours=2), timedelta(days=1), color="rgb(0, 255, 0)", pattern="/")
#     chart.add_task("Ver 3.0 HR Module", "Mitul", start_time + timedelta(days=1), timedelta(hours=12), color="rgb(0, 0, 255)", pattern="x")
    
#     # Create and show the chart
#     fig = chart.create_chart()
#     fig.show()