@staticmethod
    def hex_to_rgb(hex_color):
        """
        Convert hex color code to rgb(r, g, b) format.
        :param hex_color: Hex color code (e.g., '#d8d8d8')
        :return: String in the format 'rgb(r, g, b)'
        """
        hex_color = hex_color.lstrip('#')
        return f"rgb({int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)})"
@staticmethod
    def MSGetTaskColorDetails(task_priority, task_status):
        # Mapping task status to colors
        status_color_map = {
            "open": "#d8d8d8",  # light grey
            "in progress": "#48d2ff",  # light blue
            "delievered": "#008844",  # success green
            "closed": "#008844",  # success green (same as delivered)
            "review": "#9370DB"  # cute purple
        }

        # Mapping task priority to colors
        priority_color_map = {
            "low": "#48d2ff",  # light blue
            "normal": "#48d2ff",  # light blue
            "high": "#FFA500",  # orange
            "urgent": "#FF00FF"  # magenta
        }

        # Assign status color based on task status
        status_color = status_color_map.get(task_status.get("status", "open").lower(), "#48d2ff")  # Default light blue
        # Assign priority color based on task priority
        priority_color = priority_color_map.get(task_priority.get("priority", "low").lower() if task_priority else "low", "#48d2ff")  # Default light blue

        # Convert the hex colors to rgb format
        status_color_rgb = CClickUpDB.hex_to_rgb(status_color)
        priority_color_rgb = CClickUpDB.hex_to_rgb(priority_color)

        # Return the dictionary with RGB color details
        return {
            "statuscolor": status_color_rgb,
            "prioritycolor": priority_color_rgb,
            "conflictcolor": CClickUpDB.hex_to_rgb("#FF0000")  # Red for conflicts
        }