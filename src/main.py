"""
OSC Data Monitor Application

This application provides a graphical interface for monitoring and visualizing OSC (Open Sound Control) data,
particularly from EEG devices like Muse headsets. It includes real-time charting of EEG signals and frequency bands,
logging capabilities, and network configuration options.

Key Features:
- Real-time visualization of EEG data and frequency bands (delta, theta, alpha, beta, gamma)
- Multiple OSC port listening capability
- Data logging to files with buffered writing
- Responsive UI with dark theme
"""

import flet as ft
import socket
from pythonosc import dispatcher, osc_server
from threading import Thread
from utils import generate_plot
from metrics import MetricsCalculator
import logging
import time
from collections import deque
from datetime import datetime
from preprocess import ChanelProcessor
from processor import BufferedFileWriter
import threading

# UI Configuration Constants
BACKGROUND_COLOR = "#111827"
CARD_COLOR = "#1f2937"
CARD_RADIUS = 10
CARD_PADDING = ft.padding.symmetric(horizontal=20, vertical=10)
BUTTON_PADDING = ft.padding.symmetric(horizontal=20, vertical=0)
ROW_ALIGNMENT = ft.MainAxisAlignment.SPACE_BETWEEN

# Logging Configuration
MAX_LOG_LINES = 1000
log_buffer = deque(maxlen=MAX_LOG_LINES)
osc_servers = {}
log_box = None

# Chart Configuration Variables
eeg_charts = []
channel_charts = []
active_charts = []  # Contains currently active charts
eeg_data_series = {}
max_points = 100
channel_data_series = [deque(maxlen=max_points) for _ in range(5)]
chart_colors = ["#FF5733", "#33C1FF", "#75FF33", "#FF33A8", "#F3FF33", "#9D33FF"]
eeg_channels = ["TP9", "Fp1", "Fp2", "TP10", "DRL", "REF"]
absolute_channels = ['delta', 'theta', 'alpha', 'beta', 'gamma']
chart_number = 1

# Initialize data processors and writers
chanelProcessor = ChanelProcessor()
metricsCalculator = MetricsCalculator()
eeg_writer = BufferedFileWriter("eeg", header=eeg_channels)
channels_writer = BufferedFileWriter("channels", header=absolute_channels)

def get_local_ip():
    """Get the local IP address of the machine"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def start_flush_threads():
    """Start periodic flush threads for file writers"""
    def flush_periodically(writer, interval=5):
        while True:
            time.sleep(interval)
            writer.flush()
    
    # Thread for EEG data
    threading.Thread(target=flush_periodically, args=(eeg_writer,), daemon=True).start()
    # Thread for Channel data
    threading.Thread(target=flush_periodically, args=(channels_writer,), daemon=True).start()

def osc_handler(address, *args):
    """Handle incoming OSC messages"""
    global chart_number
    timestamp = datetime.now().isoformat()
    args_str = ','.join(str(arg) for arg in args)
    msg = None

    if address.startswith("/muse/eeg"):
        msg = f"{timestamp},{args_str}\n"
        try:
            if len(args) >= 2:
                chart_number = len(args)
                y_values = [float(arg) for arg in args]
                log_buffer.append(msg)
                eeg_writer.write(msg)
                update_chart(timestamp, y_values)
        except Exception as e:
            logging.error(f"Error processing EGG data: {e}")

    elif address.startswith("/muse/elements/"):
        try:
            # Process data to get the 5 frequency bands
            channel = address.split("/")[-1]
            data = chanelProcessor.process_data(args_str, channel)
            if data:
                chart_number = 1
                args_str = ','.join(str(arg) for arg in data)
                msg = f"{timestamp},{args_str}\n"
                # Convert values to float
                y_values = [float(value) for value in data[:5]]  # Take first 5 values
                result = metricsCalculator.process(
                    timestamp=timestamp, 
                    delta=y_values[0], theta=y_values[1], alpha=y_values[2], beta=y_values[3], gamma=y_values[4]
                    )
                log_buffer.append(msg)
                channels_writer.write(msg)
                update_chart(timestamp, y_values, type="channels")
        except Exception as e:
            logging.error(f"Error processing Channels data: {e}")

def log_updater():
    """Update the log display periodically"""
    while True:
        if log_box and log_buffer:
            while log_buffer:
                msg = log_buffer.popleft()
                if len(log_box.controls) >= MAX_LOG_LINES:
                    log_box.controls.pop(0)
                log_box.controls.append(ft.Text(msg, size=12, color="#267443", font_family="Roboto Mono"))
            log_box.update()
        time.sleep(0.2)

def start_osc_server(port):
    """Start an OSC server on the specified port"""
    if port in osc_servers:
        return
    disp = dispatcher.Dispatcher()
    disp.set_default_handler(osc_handler)
    server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", port), disp)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    osc_servers[port] = server

def stop_osc_server(port):
    """Stop the OSC server on the specified port"""
    if port in osc_servers:
        osc_servers[port].shutdown()
        del osc_servers[port]

def is_chart_ready(chart):
    """Check if a chart is ready for updates"""
    try:
        return chart.page is not None
    except:
        return False
    
def update_chart(timestamp, values, type="eeg"):
    """Update the charts with new data"""
    if type == "eeg":
        if not eeg_charts:
            return

        try:
            dt = datetime.fromisoformat(timestamp)
            x_label = dt.strftime("%H:%M:%S")
        except:
            x_label = timestamp

        for i, y_value in enumerate(values):
            if i not in eeg_data_series:
                eeg_data_series[i] = deque(maxlen=max_points)

            eeg_data_series[i].append((x_label, y_value))

            if i < len(eeg_charts):
                chart = eeg_charts[i]
                if is_chart_ready(chart):
                    chart.data_series = [
                        ft.LineChartData(
                            data_points=[
                                ft.LineChartDataPoint(j, point[1])
                                for j, point in enumerate(eeg_data_series[i])
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
                            ft.Text(value=point[0], size=10, color=ft.Colors.WHITE)
                        )
                        for j, point in enumerate(eeg_data_series[i]) if j % (max_points // 10) == 0
                    ]
                    chart.update()

    elif type == "channels":
        if not channel_charts:
            return

        try:
            dt = datetime.fromisoformat(timestamp)
            x_label = dt.strftime("%H:%M:%S")
        except:
            x_label = timestamp

        for i in range(5):
            if i < len(values):
                channel_data_series[i].append((x_label, values[i]))

        chart = channel_charts[0]
        if is_chart_ready(chart):
            chart.data_series = [
                ft.LineChartData(
                    data_points=[
                        ft.LineChartDataPoint(j, point[1])
                        for j, point in enumerate(channel_data_series[i])
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
                    ft.Text(value=point[0], size=10, color=ft.Colors.WHITE)
                )
                for j, point in enumerate(channel_data_series[0]) if j % (max_points // 10) == 0
            ]
            chart.update()

def show_eeg_charts(e):
    """Display EEG charts"""
    global active_charts
    active_charts = eeg_charts
    chart_column.controls.clear()
    for i, ch in enumerate(eeg_charts):
        chart_column.controls.append(
            ft.Row(
                controls=[
                    ch,
                    ft.Text(eeg_channels[i], color=chart_colors[i])
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
    e.page.update()
    log_buffer.append("Showing EEG charts")

def show_channel_charts(e):
    """Display frequency band charts"""
    global active_charts
    active_charts = channel_charts
    chart_column.controls.clear()
    chart_column.controls.append(
        ft.Column(
            controls=[
                channel_charts[0],
                ft.Row(
                    [ft.Text(ch, color=chart_colors[i]) 
                     for i, ch in enumerate(absolute_channels)],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY
                )
            ]
        )
    )
    e.page.update()
    log_buffer.append("Showing channel charts")

def main(page: ft.Page):
    """Main application function"""
    page.title = "OSC Data Monitor"
    page.bgcolor = BACKGROUND_COLOR
    page.horizontal_alignment = "center"
    page.scroll = ft.ScrollMode.AUTO
    page.padding = CARD_PADDING

    global log_box, chart_column, active_charts, eeg_charts, channel_charts
    log_box = ft.Column(auto_scroll=True, expand=True, scroll=ft.ScrollMode.ADAPTIVE)

    ip_text = ft.Text(f"{get_local_ip()}", size=14, color="#7e8bc0", weight="bold")

    common_ports = ft.Dropdown(
        width=160,
        options=[ft.dropdown.Option(str(p)) for p in [3333, 8338, 8000, 9000]],
        value="3333",
        bgcolor=ft.Colors.BLUE_GREY_800,
        color=ft.Colors.WHITE,
        border_color=ft.Colors.TRANSPARENT
    )

    listening_ports = ft.Dropdown(
        width=160,
        hint_text="Now Listening...",
        bgcolor=ft.Colors.BLUE_GREY_800,
        color=ft.Colors.WHITE,
        border_color=ft.Colors.TRANSPARENT
    )

    def update_layout(e=None):
        """Update UI layout on window resize"""
        page_width = page.window.width
        top_controls.width = page_width / 2 - 40
        osc_graph.width = page_width - 40
        live_log.width = page_width / 2 - 80
        page.update()

    def add_port_click(e):
        """Handle add port button click"""
        try:
            port = int(common_ports.value)
            start_osc_server(port)
            if str(port) not in [opt.key for opt in listening_ports.options]:
                listening_ports.options.append(ft.dropdown.Option(str(port)))
                listening_ports.update()
                log_buffer.append(f"Listening to port: {port}")
        except Exception as ex:
            log_buffer.append(f"Error: {ex}")

    def stop_port_click(e):
        """Handle stop port button click"""
        if listening_ports.value:
            port = int(listening_ports.value)
            stop_osc_server(port)
            listening_ports.options = [opt for opt in listening_ports.options if opt.key != str(port)]
            listening_ports.update()
            log_buffer.append(f"Stopped listening to port: {port}")

    # Initialize EEG and channel charts
    eeg_charts.clear()
    channel_charts.clear()
    for i in range(6):
        eeg_charts.append(generate_plot())
    channel_charts = [generate_plot(height=600)]
    active_charts = eeg_charts
    
    chart_column = ft.Column()
    for i, ch in enumerate(eeg_charts):
        chart_column.controls.append(
            ft.Row(
                controls=[
                    ch,
                    ft.Text(eeg_channels[i], color=chart_colors[i])
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    # UI Elements
    eeg_button = ft.ElevatedButton(
        "EEG",
        bgcolor="#4f46e5",
        color="white",
        on_click=show_eeg_charts,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=CARD_RADIUS),
            padding=BUTTON_PADDING
        )
    )

    channel_button = ft.ElevatedButton(
        "CHANNELS",
        bgcolor="#374151",
        color="white",
        on_click=show_channel_charts,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=CARD_RADIUS),
            padding=BUTTON_PADDING
        )
    )

    def update_button_styles(active_button):
        """Update button styles based on which is active"""
        if active_button == "eeg":
            eeg_button.bgcolor = "#4f46e5"
            channel_button.bgcolor = "#374151"
        else:
            eeg_button.bgcolor = "#374151"
            channel_button.bgcolor = "#4f46e5"
        page.update()

    def show_eeg_charts_wrapper(e):
        """Wrapper for EEG chart display"""
        show_eeg_charts(e)
        update_button_styles("eeg")

    def show_channel_charts_wrapper(e):
        """Wrapper for channel chart display"""
        show_channel_charts(e)
        update_button_styles("channel")

    eeg_button.on_click = show_eeg_charts_wrapper
    channel_button.on_click = show_channel_charts_wrapper

    top_controls = ft.Container(
        content=ft.Column([
            ft.Text("Connection Settings", size=16, weight="bold", color=ft.Colors.WHITE),
            ft.Row([
                ft.Text("List with common OSC ports:", color=ft.Colors.BLUE_GREY_200),
                common_ports,
                ft.CupertinoButton("Add Port", on_click=add_port_click, bgcolor="#4f46e5", color="white", icon=ft.Icons.ADD, icon_color="white", padding=BUTTON_PADDING, border_radius=CARD_RADIUS)
            ], alignment=ROW_ALIGNMENT),
            ft.Row([
                ft.Text("Now listening to OSC ports:", color=ft.Colors.BLUE_GREY_200),
                listening_ports,
                ft.CupertinoButton("Stop Listening", on_click=stop_port_click, bgcolor="#dc2626", color="white", icon=ft.Icons.STOP_CIRCLE, icon_color="white", padding=BUTTON_PADDING, border_radius=CARD_RADIUS)
            ], alignment=ROW_ALIGNMENT),
        ]),
        bgcolor=CARD_COLOR,
        padding=CARD_PADDING,
        border_radius=CARD_RADIUS,
        width=page.window.width / 2 - 40
    )

    live_log = ft.Container(
        content=log_box,
        bgcolor=ft.Colors.BLACK,
        padding=10,
        border_radius=5,
        height=110,
        width=page.window.width / 2 - 80
    )

    buttons_row = ft.Row(
        controls=[
            eeg_button,
            channel_button
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=20
    )

    osc_graph = ft.Container(
        content=ft.Column([
            chart_column
        ]),
        bgcolor=CARD_COLOR,
        padding=CARD_PADDING,
        border_radius=CARD_RADIUS,
        height=700,
        width=page.window.width - 40
    )

    page.on_resized = update_layout

    # Build the main UI layout
    page.add(
        ft.Column([
            ft.Container(
                bgcolor=CARD_COLOR,
                padding=CARD_PADDING,
                border_radius=CARD_RADIUS,
                content=ft.Row([
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SETTINGS_INPUT_ANTENNA, size=20, color="#808bf7"),
                            ft.Text("Teddy OSC Data Monitor", size=20, weight="bold", color=ft.Colors.WHITE),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("IP ADDRESS:", size=14, color=ft.Colors.WHITE),
                            ft.Container(content=ip_text, alignment=ft.alignment.center_right, expand=True, bgcolor="#374151", padding=5, border_radius=5)
                        ]
                    ),
                    buttons_row
                ], alignment="spaceBetween"),
            ),
            ft.Container(
                osc_graph
            ),
            ft.Row([
                top_controls,
                ft.Container(
                    bgcolor=CARD_COLOR,
                    padding=CARD_PADDING,
                    border_radius=CARD_RADIUS,
                    content=ft.Column(
                        controls=[
                            ft.Text("Live Log", size=16, color=ft.Colors.WHITE),
                            live_log,
                        ]
                    )
                )
            ], alignment="spaceBetween", vertical_alignment="start", spacing=20),
        ], spacing=20, expand=True),
    )

    update_button_styles("eeg")
    Thread(target=log_updater, daemon=True).start()
    

if __name__ == "__main__":
    start_flush_threads()
    ft.app(target=main, view=ft.AppView.FLET_APP)