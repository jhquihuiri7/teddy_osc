def generate_plot(height=100):
    """Generates a line chart widget with customizable height and default styling.
    
    Creates a Flet LineChart widget with the following characteristics:
    - No animation (instant rendering)
    - Empty data series (to be populated later)
    - Subtle border styling
    - Configured axes with label sizing
    - Tooltip styling
    - Expandable to fill available space
    
    Args:
        height (int, optional): The height of the chart in pixels. Defaults to 100.
        
    Returns:
        ft.LineChart: A configured Flet LineChart widget ready for data population.
    """
    import flet as ft
    return ft.LineChart(
        animate=ft.Animation(duration=0, curve=ft.AnimationCurve.LINEAR),
        data_series=[],
        border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE)),
        left_axis=ft.ChartAxis(
            labels_size=40,
        ),
        bottom_axis=ft.ChartAxis(
            labels_size=40,
        ),
        tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY),
        expand=True,
        height=height
    )


def write_to_file(filename, message):
    """Appends a message to a specified file.
    
    Opens a file in append mode and writes the provided message. The file is
    automatically closed after writing. Creates the file if it doesn't exist.
    
    Args:
        filename (str): Path to the target file for writing
        message (str): Content to be appended to the file
        
    Returns:
        None
    """
    with open(filename, "a") as file:
        file.write(message)