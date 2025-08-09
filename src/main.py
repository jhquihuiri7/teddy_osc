import flet as ft
import socket
from pythonosc import dispatcher, osc_server
from threading import Thread
from utils import generate_plot, process_csv_file
from metrics import MetricsCalculator
import logging
from collections import deque
from datetime import datetime
from preprocess import ChanelProcessor
import threading

# UI Configuration Constants
BACKGROUND_COLOR = "#111827"
CARD_COLOR = "#1f2937"
CARD_RADIUS = 10
CARD_PADDING = ft.padding.symmetric(horizontal=20, vertical=10)
BUTTON_PADDING = ft.padding.symmetric(horizontal=20, vertical=0)
ROW_ALIGNMENT = ft.MainAxisAlignment.SPACE_BETWEEN

osc_servers = {}

# Chart Configuration Variables
eeg_charts = []
channel_charts = []
metrics_charts = []  # Nuevo arreglo para métricas
active_charts = []
eeg_data_series = {}
max_points = 100
channel_data_series = [deque(maxlen=max_points) for _ in range(5)]
metrics_data_series = [deque(maxlen=max_points) for _ in range(5)]  # 5 métricas
chart_colors = ["#FF5733", "#33C1FF", "#75FF33", "#FF33A8", "#F3FF33", "#9D33FF"]
eeg_channels = ["TP9", "Fp1", "Fp2", "TP10", "DRL", "REF"]
absolute_channels = ['delta', 'theta', 'alpha', 'beta', 'gamma']
chart_number = 1

# Data processors and writers
chanelProcessor = ChanelProcessor()
metricsCalculator = MetricsCalculator()

# Buffered data storage
buffered_eeg_data = {}
buffered_channel_data = [[] for _ in range(5)]
buffered_metrics_data = [[] for _ in range(5)]  # Buffer para métricas
update_interval_seconds = 2.0

def buffer_eeg_data(timestamp, values):
    for i, value in enumerate(values):
        if i not in buffered_eeg_data:
            buffered_eeg_data[i] = []
        buffered_eeg_data[i].append((timestamp, value))

def buffer_channel_data(timestamp, values):
    for i in range(min(len(values), 5)):
        buffered_channel_data[i].append((timestamp, values[i]))

def buffer_metrics_data(timestamp, values):
    for i in range(min(len(values), 5)):
        buffered_metrics_data[i].append((timestamp, values[i]))

def update_charts_periodically():
    # EEG Charts
    for i in range(len(eeg_charts)):
        if i in buffered_eeg_data:
            new_points = buffered_eeg_data[i]
            for point in new_points:
                dt = datetime.fromisoformat(point[0])
                label = dt.strftime("%H:%M:%S")
                eeg_data_series.setdefault(i, deque(maxlen=max_points)).append((label, point[1]))
            buffered_eeg_data[i] = []

            chart = eeg_charts[i]
            if is_chart_ready(chart):
                chart.data_series = [
                    ft.LineChartData(
                        data_points=[
                            ft.LineChartDataPoint(j, p[1])
                            for j, p in enumerate(eeg_data_series[i])
                        ],
                        stroke_width=2,
                        color=chart_colors[i],
                        curved=True,
                        stroke_cap_round=True,
                    )
                ]
                chart.bottom_axis.labels = [
                    ft.ChartAxisLabel(
                        j,
                        ft.Text(value=p[0], size=10, color=ft.Colors.WHITE)
                    )
                    for j, p in enumerate(eeg_data_series[i]) if j % (max_points // 10) == 0
                ]
                chart.update()

    # Channel Charts
    updated = False
    for i in range(5):
        if buffered_channel_data[i]:
            for point in buffered_channel_data[i]:
                dt = datetime.fromisoformat(point[0])
                label = dt.strftime("%H:%M:%S")
                channel_data_series[i].append((label, point[1]))
            buffered_channel_data[i] = []
            updated = True

    if updated and channel_charts:
        chart = channel_charts[0]
        if is_chart_ready(chart):
            chart.data_series = [
                ft.LineChartData(
                    data_points=[
                        ft.LineChartDataPoint(j, p[1])
                        for j, p in enumerate(channel_data_series[i])
                    ],
                    stroke_width=2,
                    color=chart_colors[i],
                    curved=True,
                    stroke_cap_round=True,
                )
                for i in range(5)
            ]
            chart.bottom_axis.labels = [
                ft.ChartAxisLabel(
                    j,
                    ft.Text(value=p[0], size=10, color=ft.Colors.WHITE)
                )
                for j, p in enumerate(channel_data_series[0]) if j % (max_points // 10) == 0
            ]
            chart.update()

    # Metrics Charts
    metrics_updated = False
    for i in range(5):
        if buffered_metrics_data[i]:
            for point in buffered_metrics_data[i]:
                dt = datetime.fromisoformat(point[0])
                label = dt.strftime("%H:%M:%S")
                metrics_data_series[i].append((label, point[1]))
            buffered_metrics_data[i] = []
            metrics_updated = True

    if metrics_updated and metrics_charts:
        chart = metrics_charts[0]
        if is_chart_ready(chart):
            chart.data_series = [
                ft.LineChartData(
                    data_points=[
                        ft.LineChartDataPoint(j, p[1])
                        for j, p in enumerate(metrics_data_series[i])
                    ],
                    stroke_width=2,
                    color=chart_colors[i],
                    curved=True,
                    stroke_cap_round=True,
                )
                for i in range(5)
            ]
            chart.bottom_axis.labels = [
                ft.ChartAxisLabel(
                    j,
                    ft.Text(value=p[0], size=10, color=ft.Colors.WHITE)
                )
                for j, p in enumerate(metrics_data_series[0]) if j % (max_points // 10) == 0
            ]
            chart.update()

    threading.Timer(update_interval_seconds, update_charts_periodically).start()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def is_chart_ready(chart):
    try:
        return chart.page is not None
    except:
        return False

def osc_handler(address, *args):
    global chart_number
    timestamp = datetime.now().isoformat()
    args_str = ','.join(str(arg) for arg in args)

    if address.startswith("/muse/eeg"):
        if len(args) >= 2:
            chart_number = len(args)
            y_values = [float(arg) for arg in args]
            buffer_eeg_data(timestamp, y_values)

    elif address.startswith("/muse/elements/"):
        channel = address.split("/")[-1]
        data = chanelProcessor.process_data(args_str, channel)
        if data:
            chart_number = 1
            y_values = [float(value) for value in data[:5]]
            metrics_results = metricsCalculator.process(timestamp, *y_values)
            if metrics_results is not None:
                buffer_metrics_data(timestamp, metrics_results)  # Guardar métricas en buffer
            buffer_channel_data(timestamp, y_values)

def start_osc_server(port):
    if port in osc_servers:
        return
    disp = dispatcher.Dispatcher()
    disp.set_default_handler(osc_handler)
    server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", port), disp)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    osc_servers[port] = server

def stop_osc_server(port):
    if port in osc_servers:
        osc_servers[port].shutdown()
        del osc_servers[port]

def main(page: ft.Page):
    page.title = "OSC Data Monitor"
    page.bgcolor = BACKGROUND_COLOR
    page.horizontal_alignment = "center"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = CARD_PADDING

    global chart_column, active_charts, eeg_charts, channel_charts, metrics_charts

    ip_text = ft.Text(f"{get_local_ip()}", size=14, color="#7e8bc0", weight="bold")

    common_ports = ft.Dropdown(width=160, options=[ft.dropdown.Option(str(p)) for p in [3333, 8338, 8000, 9000]], value="3333", bgcolor=ft.Colors.BLUE_GREY_800, color=ft.Colors.WHITE)

    listening_ports = ft.Dropdown(width=160, hint_text="Now Listening...", bgcolor=ft.Colors.BLUE_GREY_800, color=ft.Colors.WHITE)

    def add_port_click(e):
        port = int(common_ports.value)
        start_osc_server(port)
        if str(port) not in [opt.key for opt in listening_ports.options]:
            listening_ports.options.append(ft.dropdown.Option(str(port)))
            listening_ports.value = str(port)
            page.snack_bar = ft.SnackBar(ft.Text(f"Started OSC server on port: {port}"))
            page.snack_bar.open = True
            page.update()

    def stop_port_click(e):
        if listening_ports.value and listening_ports.value != "None":
            port = int(listening_ports.value)
            stop_osc_server(port)
            listening_ports.options = [opt for opt in listening_ports.options if opt.key != str(port)]
            listening_ports.value = None
            listening_ports.hint_text = "Now Listening..."
            page.snack_bar = ft.SnackBar(ft.Text(f"Stopped OSC server on port: {port}"))
            page.snack_bar.open = True
            page.update()

    eeg_charts.clear()
    channel_charts.clear()
    metrics_charts.clear()

    for i in range(6):
        eeg_charts.append(generate_plot())
    channel_charts = [generate_plot(height=600)]
    metrics_charts = [generate_plot(height=600)]  # Gráfica vacía por defecto

    active_charts = eeg_charts

    chart_column = ft.Column()
    for i, ch in enumerate(eeg_charts):
        chart_column.controls.append(
            ft.Row(
                controls=[ch, ft.Text(eeg_channels[i], color=chart_colors[i])],
                alignment=ROW_ALIGNMENT
            )
        )

    def show_eeg_charts(e):
        global active_charts
        active_charts = eeg_charts
        chart_column.controls.clear()
        for i, ch in enumerate(eeg_charts):
            chart_column.controls.append(
                ft.Row(
                    controls=[ch, ft.Text(eeg_channels[i], color=chart_colors[i])],
                    alignment=ROW_ALIGNMENT
                )
            )
        page.update()

    def show_channel_charts(e):
        global active_charts
        active_charts = channel_charts
        chart_column.controls.clear()
        chart_column.controls.append(
            ft.Column([
                channel_charts[0],
                ft.Row([
                    ft.Text(ch, color=chart_colors[i])
                    for i, ch in enumerate(absolute_channels)
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
            ])
        )
        page.update()

    def show_metrics_charts(e):
        global active_charts
        active_charts = metrics_charts
        chart_column.controls.clear()
        chart_column.controls.append(
            ft.Column([
                metrics_charts[0],
                ft.Row([
                    ft.Text(f"Metric {i+1}", color=chart_colors[i])
                    for i in range(5)
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
            ])
        )
        page.update()

    eeg_button = ft.ElevatedButton("EEG", on_click=show_eeg_charts)
    channel_button = ft.ElevatedButton("CHANNELS", on_click=show_channel_charts)
    metrics_button = ft.ElevatedButton("METRICS", on_click=show_metrics_charts)

    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    def on_file_selected(e: ft.FilePickerResultEvent):
        if e.files:
            selected_file = e.files[0].path
            process_csv_file(selected_file)
            page.snack_bar = ft.SnackBar(ft.Text(f"Archivo cargado: {selected_file}"))
            page.snack_bar.open = True
            page.update()

    file_picker.on_result = on_file_selected

    page.add(
        ft.Column([
            ft.Container(ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.SETTINGS_INPUT_ANTENNA, size=20, color="#808bf7"),
                    ft.Text("Teddy OSC Data Monitor", size=20, weight="bold", color=ft.Colors.WHITE)
                ]),
                ft.Row([
                    ft.Text("IP ADDRESS:", size=14, color=ft.Colors.WHITE),
                    ft.Container(content=ip_text, bgcolor="#374151", padding=5, border_radius=5)
                ]),
                ft.Row([eeg_button, channel_button, metrics_button])
            ], alignment="spaceBetween"), bgcolor=CARD_COLOR, padding=CARD_PADDING, border_radius=CARD_RADIUS),
            ft.Container(ft.Column([chart_column]), bgcolor=CARD_COLOR, padding=CARD_PADDING, border_radius=CARD_RADIUS, height=700),
            ft.Container(ft.Column([
                ft.Text("Connection Settings", size=16, weight="bold", color=ft.Colors.WHITE),
                ft.Row([
                    ft.Text("List with common OSC ports:", color=ft.Colors.BLUE_GREY_200),
                    common_ports,
                    ft.ElevatedButton("Add Port", on_click=add_port_click)
                ], alignment=ROW_ALIGNMENT),
                ft.Row([
                    ft.Text("Now listening to OSC ports:", color=ft.Colors.BLUE_GREY_200),
                    listening_ports,
                    ft.ElevatedButton("Stop Listening", on_click=stop_port_click, bgcolor="#dc2626", color="white")
                ], alignment=ROW_ALIGNMENT)
            ]), bgcolor=CARD_COLOR, padding=CARD_PADDING, border_radius=CARD_RADIUS),
            ft.Container(ft.Row([
                ft.Text("Historical charts", size=16, color=ft.Colors.WHITE, weight="bold"),
                ft.ElevatedButton("Choose files...", on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["csv"]))
            ]), bgcolor=CARD_COLOR, padding=CARD_PADDING, border_radius=CARD_RADIUS)
        ], spacing=20)
    )

    # Iniciar actualización de gráficos
    update_charts_periodically()

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
