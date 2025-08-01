import numpy as np
import flet as ft
import pandas as pd

def generate_plot():
    # Simulación de datos aleatorios
    np.random.seed(0)
    x = np.linspace(0, 50, 200)
    y1 = np.sin(x / 2) * 30 + np.random.normal(0, 5, size=len(x)) + 50
    y2 = np.cos(x / 3) * 25 + np.random.normal(0, 5, size=len(x)) + 50

    # Normalizar X para que esté entre 0 y 14 (como el gráfico anterior)
    x_normalized = np.interp(x, (x.min(), x.max()), (0, 14))
    y1_normalized = np.interp(y1, (y1.min(), y1.max()), (0, 4))
    y2_normalized = np.interp(y2, (y2.min(), y2.max()), (0, 4))

    # Crear data_points para cada serie
    data_series = [
        ft.LineChartData(
            data_points=[
                ft.LineChartDataPoint(float(x_), float(y_))
                for x_, y_ in zip(x_normalized, y1_normalized)
            ],
            stroke_width=2,
            color="#00bcd4",
            curved=True,
            stroke_cap_round=True,
        ),
        ft.LineChartData(
            data_points=[
                ft.LineChartDataPoint(float(x_), float(y_))
                for x_, y_ in zip(x_normalized, y2_normalized)
            ],
            stroke_width=2,
            color="#66ffcc",
            curved=True,
            stroke_cap_round=True,
        )
    ]

    chart = ft.LineChart(
        data_series=data_series,
        min_y=0,
        max_y=4,
        min_x=0,
        max_x=14,
        left_axis=ft.ChartAxis(labels_size=40),
        bottom_axis=ft.ChartAxis(labels_size=32),
        tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY),
        expand=True,
    )

    return chart
