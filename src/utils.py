import numpy as np
import flet as ft
import pandas as pd

def generate_plot(height=100):
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