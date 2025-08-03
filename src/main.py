import flet as ft
import socket
from pythonosc import dispatcher, osc_server
from threading import Thread
from utils import generate_plot
import logging
import time
from collections import deque
from datetime import datetime
from preprocess import ChanelProcessor

BACKGROUND_COLOR = "#111827"
CARD_COLOR = "#1f2937"
CARD_RADIUS = 10
CARD_PADDING = ft.padding.symmetric(horizontal=20, vertical=10)
BUTTON_PADDING = ft.padding.symmetric(horizontal=20, vertical=0)
ROW_ALIGNMENT = ft.MainAxisAlignment.SPACE_BETWEEN

MAX_LOG_LINES = 1000
log_buffer = deque(maxlen=MAX_LOG_LINES)
osc_servers = {}
log_box = None

# Variables para manejar los gráficos
eeg_charts = []
channel_charts = []
active_charts = []  # Contendrá los gráficos activos actualmente
eeg_data_series = {}
max_points = 100
channel_data_series = [deque(maxlen=max_points) for _ in range(5)]
chart_colors = ["#FF5733", "#33C1FF", "#75FF33", "#FF33A8", "#F3FF33", "#9D33FF"]
eeg_channels = ["TP9", "Fp1", "Fp2", "TP10", "DRL", "REF"]
absolute_channels = ['delta', 'theta', 'alpha', 'beta', 'gamma']
chart_number = 1
chanelProcessor = ChanelProcessor()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def osc_handler(address, *args):
    global chart_number
    timestamp = datetime.now().isoformat()
    args_str = ', '.join(str(arg) for arg in args)
    msg = None

    if address.startswith("/muse/eeg"):
        msg = f"{timestamp},{args_str}"
        try:
            if len(args) >= 2:
                chart_number = len(args)
                y_values = [float(arg) for arg in args]
                log_buffer.append(msg)
                update_chart(timestamp, y_values)
        except Exception as e:
            logging.error(f"Error processing EGG data: {e}")

    elif address.startswith("/muse/elements/"):
        try:
            # Procesamos los datos para obtener las 5 bandas
            
            data = chanelProcessor.process_data(args_str)
            if data:
                chart_number = 1
                args_str = ','.join(str(arg) for arg in data)
                msg = f"{timestamp},{args_str}"
                # Convertimos los valores a float
                y_values = [float(value) for value in data[:5]]  # Tomamos los primeros 5 valores
                log_buffer.append(msg)
                update_chart(timestamp, y_values, type="channels")
        except Exception as e:
            logging.error(f"Error processing Channels data: {e}")

    if msg:
        with open("egg_new.txt", "a") as file:
            file.write(msg + "\n")

def log_updater():
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

def is_chart_ready(chart):
    try:
        return chart.page is not None
    except:
        return False
    
def update_chart(timestamp, values, type="eeg"):
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
    log_buffer.append("Mostrando gráficos EEG")

def show_channel_charts(e):
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
    log_buffer.append("Mostrando gráficos de canales")

def main(page: ft.Page):
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
        page_width = page.window.width
        top_controls.width = page_width / 2 - 40
        osc_graph.width = page_width - 40
        live_log.width = page_width / 2 - 80
        page.update()

    def add_port_click(e):
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
        if listening_ports.value:
            port = int(listening_ports.value)
            stop_osc_server(port)
            listening_ports.options = [opt for opt in listening_ports.options if opt.key != str(port)]
            listening_ports.update()
            log_buffer.append(f"Stopped listening to port: {port}")

    # Inicializar gráficos EEG y de canales
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
        if active_button == "eeg":
            eeg_button.bgcolor = "#4f46e5"
            channel_button.bgcolor = "#374151"
        else:
            eeg_button.bgcolor = "#374151"
            channel_button.bgcolor = "#4f46e5"
        page.update()

    def show_eeg_charts_wrapper(e):
        show_eeg_charts(e)
        update_button_styles("eeg")

    def show_channel_charts_wrapper(e):
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
    ft.app(target=main, view=ft.AppView.FLET_APP)